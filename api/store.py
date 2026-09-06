"""The store: every rule memnasium has, in one place.

The HTTP routes and the MCP tools are both thin adapters over these functions —
see design/standards/Code.md#one-definition-of-a-rule. A rule implemented in a
route handler is a rule that will disagree with itself, so none are.

Every refusal is a typed error with a reason, never a silent no-op.
"""

import math
import random
import sqlite3
from collections.abc import Callable, Sequence
from datetime import date

from api import models
from api.config import ALPHA
from api.db import transaction


class StoreError(Exception):
    """Something the store refused, with a machine-readable reason."""

    code = "refused"


class NotFoundError(StoreError):
    """A row that was named does not exist."""

    code = "not_found"


class RefusedError(StoreError):
    """A rule from the design docs forbids this."""

    code = "refused"


def draw_probability(sessions_correct: int) -> float:
    """The chance a pair is drawn today.

    Args:
        sessions_correct: Consecutive correct drills for the pair.

    Returns:
        `e^(-alpha * sessions_correct)`, the per-day inclusion probability from
        design/Data.md#background.
    """
    return math.exp(-ALPHA * sessions_correct)


def corpus(conn: sqlite3.Connection) -> tuple[int, float]:
    """The live corpus: its size, and how big a draw over it is expected to be.

    Both fall out of one histogram of `sessions_correct`. The sum is done here
    rather than as `SUM(exp(...))` because the bundled SQLite does not reliably
    carry the math functions, and because this keeps it beside the `alpha` the
    draw itself uses — see design/Data.md#the-expectation.

    Returns:
        `(pairs, expected)` over every pair that is not retired, on the roll or
        in a group. `expected` is a mean, not a count: it is always shown with a
        `~`.
    """
    rows = conn.execute(
        "SELECT sessions_correct, COUNT(*) AS c FROM recall_pair WHERE retired = 0"
        " GROUP BY sessions_correct"
    ).fetchall()
    pairs = sum(int(r["c"]) for r in rows)
    expected = sum(int(r["c"]) * draw_probability(int(r["sessions_correct"])) for r in rows)
    return pairs, expected


def today() -> str:
    """Today as an ISO date string."""
    return date.today().isoformat()


# --------------------------------------------------------------------------- #
# Row builders
# --------------------------------------------------------------------------- #

_NOTE_SELECT = """
    SELECT n.id, n.statement, n.created_on,
           s.id AS source_id, s.author, s.year, s.publication,
           EXISTS(SELECT 1 FROM placement p WHERE p.note_id = n.id) AS placed
    FROM note n JOIN source s ON s.id = n.source_id
"""

#: Live pairs only. A retired pair is absent from every read — boards, context,
#: group pair counts, the wordsmithing queue — so the filter lives here rather
#: than being remembered by each call site. See design/Data.md#recall-pairs.
_PAIR_SELECT = """
    SELECT r.id, r.placement_id, r.question, r.answer, r.sessions_correct,
           s.id AS source_id, s.author, s.year, s.publication
    FROM recall_pair r
    JOIN placement p ON p.id = r.placement_id
    JOIN note n ON n.id = p.note_id
    JOIN source s ON s.id = n.source_id
    WHERE r.retired = 0
"""


def _source(row: sqlite3.Row) -> models.Source:
    return models.Source(
        id=row["source_id"], author=row["author"], year=row["year"], publication=row["publication"]
    )


def _note(row: sqlite3.Row) -> models.Note:
    return models.Note(
        id=row["id"],
        statement=row["statement"],
        created_on=row["created_on"],
        source=_source(row),
        placed=bool(row["placed"]),
    )


def _pair(row: sqlite3.Row) -> models.Pair:
    return models.Pair(
        id=row["id"],
        placement_id=row["placement_id"],
        question=row["question"],
        answer=row["answer"],
        sessions_correct=row["sessions_correct"],
        source=_source(row),
    )


def _placement(row: sqlite3.Row) -> models.Placement:
    return models.Placement(
        id=row["id"],
        note_id=row["note_id"],
        group_id=row["group_id"],
        pairs_stale=bool(row["pairs_stale"]),
    )


# --------------------------------------------------------------------------- #
# Sources and notes — design/flows/Entry.md
# --------------------------------------------------------------------------- #


def search_sources(conn: sqlite3.Connection, q: str = "") -> list[models.Source]:
    """Sources matching a query over author, year and publication."""
    like = f"%{q}%"
    rows = conn.execute(
        """
        SELECT id AS source_id, author, year, publication FROM source
        WHERE ? = '' OR author LIKE ? OR CAST(year AS TEXT) LIKE ?
           OR IFNULL(publication, '') LIKE ?
        ORDER BY author, year
        """,
        (q, like, like, like),
    ).fetchall()
    return [_source(row) for row in rows]


def create_source(conn: sqlite3.Connection, payload: models.SourceCreate) -> models.Source:
    """Create a source. Author and year are required; publication is optional."""
    cur = conn.execute(
        "INSERT INTO source (author, year, publication) VALUES (?, ?, ?)",
        (payload.author, payload.year, payload.publication),
    )
    return models.Source(
        id=int(cur.lastrowid or 0),
        author=payload.author,
        year=payload.year,
        publication=payload.publication,
    )


def get_note(conn: sqlite3.Connection, note_id: int) -> models.Note:
    """One note, or `NotFoundError`."""
    row = conn.execute(f"{_NOTE_SELECT} WHERE n.id = ?", (note_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"no note {note_id}")
    return _note(row)


def create_note(conn: sqlite3.Connection, payload: models.NoteCreate) -> models.Note:
    """Save a note against its source, dated today."""
    if conn.execute("SELECT 1 FROM source WHERE id = ?", (payload.source_id,)).fetchone() is None:
        raise NotFoundError(f"no source {payload.source_id}")
    cur = conn.execute(
        "INSERT INTO note (source_id, statement, created_on) VALUES (?, ?, ?)",
        (payload.source_id, payload.statement, today()),
    )
    return get_note(conn, int(cur.lastrowid or 0))


def _refuse_if_placed(conn: sqlite3.Connection, note_id: int) -> None:
    placed = conn.execute("SELECT 1 FROM placement WHERE note_id = ?", (note_id,)).fetchone()
    if placed is not None:
        raise RefusedError(
            f"note {note_id} has a placement and is frozen — design/flows/Entry.md"
            "#correcting-a-mistake"
        )


def edit_note(conn: sqlite3.Connection, note_id: int, payload: models.NoteEdit) -> models.Note:
    """Correct a note's statement. Refused once the note has a placement."""
    get_note(conn, note_id)
    _refuse_if_placed(conn, note_id)
    conn.execute("UPDATE note SET statement = ? WHERE id = ?", (payload.statement, note_id))
    return get_note(conn, note_id)


def delete_note(conn: sqlite3.Connection, note_id: int) -> None:
    """Delete a note. Refused once the note has a placement."""
    get_note(conn, note_id)
    _refuse_if_placed(conn, note_id)
    conn.execute("DELETE FROM note WHERE id = ?", (note_id,))


def list_notes(
    conn: sqlite3.Connection,
    *,
    ungrouped: bool = False,
    roll: bool = False,
    group_id: int | None = None,
    source_id: int | None = None,
    q: str | None = None,
) -> list[models.Note]:
    """Notes matching any combination of the filters.

    Args:
        conn: The connection.
        ungrouped: Only notes with no placement at all — the grouping queue.
        roll: Only notes holding a placement with no group.
        group_id: Only notes placed in that group.
        source_id: Only notes from that source.
        q: Only notes whose statement contains this text.

    Returns:
        The matching notes, newest first.
    """
    clauses: list[str] = []
    args: list[object] = []
    if ungrouped:
        clauses.append("NOT EXISTS (SELECT 1 FROM placement p WHERE p.note_id = n.id)")
    if roll:
        clauses.append(
            "EXISTS (SELECT 1 FROM placement p WHERE p.note_id = n.id AND p.group_id IS NULL)"
        )
    if group_id is not None:
        clauses.append(
            "EXISTS (SELECT 1 FROM placement p WHERE p.note_id = n.id AND p.group_id = ?)"
        )
        args.append(group_id)
    if source_id is not None:
        clauses.append("n.source_id = ?")
        args.append(source_id)
    if q:
        clauses.append("n.statement LIKE ?")
        args.append(f"%{q}%")
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(f"{_NOTE_SELECT} {where} ORDER BY n.id DESC", tuple(args)).fetchall()
    return [_note(row) for row in rows]


# --------------------------------------------------------------------------- #
# Groups — design/flows/Grouping.md, design/flows/Regrouping.md
# --------------------------------------------------------------------------- #

_GROUP_SELECT = """
    SELECT g.id, g.name, g.description,
           (SELECT COUNT(*) FROM placement p WHERE p.group_id = g.id) AS note_count,
           (SELECT COUNT(*) FROM recall_pair r JOIN placement p ON p.id = r.placement_id
             WHERE p.group_id = g.id AND r.retired = 0) AS pair_count
    FROM groups g
"""


def _group(row: sqlite3.Row) -> models.Group:
    return models.Group(
        id=row["id"],
        name=row["name"],
        description=row["description"],
        note_count=row["note_count"],
        pair_count=row["pair_count"],
    )


def list_groups(conn: sqlite3.Connection) -> list[models.Group]:
    """Every group with its description, note count and live pair count."""
    rows = conn.execute(f"{_GROUP_SELECT} ORDER BY g.name").fetchall()
    return [_group(row) for row in rows]


def get_group(conn: sqlite3.Connection, group_id: int) -> models.Group:
    """One group, or `NotFoundError`."""
    row = conn.execute(f"{_GROUP_SELECT} WHERE g.id = ?", (group_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"no group {group_id}")
    return _group(row)


def get_group_detail(conn: sqlite3.Connection, group_id: int) -> models.GroupDetail:
    """One group's notes and its live pairs."""
    group = get_group(conn, group_id)
    notes = list_notes(conn, group_id=group_id)
    rows = conn.execute(f"{_PAIR_SELECT} AND p.group_id = ? ORDER BY r.id", (group_id,)).fetchall()
    return models.GroupDetail(group=group, notes=notes, pairs=[_pair(r) for r in rows])


def create_group(conn: sqlite3.Connection, payload: models.GroupCreate) -> models.Group:
    """Coin a group from a name and description the user approved."""
    cur = conn.execute(
        "INSERT INTO groups (name, description) VALUES (?, ?)",
        (payload.name, payload.description),
    )
    return get_group(conn, int(cur.lastrowid or 0))


def update_group(
    conn: sqlite3.Connection, group_id: int, payload: models.GroupEdit
) -> models.Group:
    """Reword a group's name or description."""
    group = get_group(conn, group_id)
    conn.execute(
        "UPDATE groups SET name = ?, description = ? WHERE id = ?",
        (payload.name or group.name, payload.description or group.description, group_id),
    )
    return get_group(conn, group_id)


# --------------------------------------------------------------------------- #
# Placements — design/Data.md#groups-placements-and-the-roll
# --------------------------------------------------------------------------- #


def get_placement(conn: sqlite3.Connection, placement_id: int) -> models.Placement:
    """One placement, or `NotFoundError`."""
    row = conn.execute("SELECT * FROM placement WHERE id = ?", (placement_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"no placement {placement_id}")
    return _placement(row)


def _refuse_conflicting_residency(
    conn: sqlite3.Connection, note_id: int, group_id: int | None, *, exclude: int | None = None
) -> None:
    """A note holds either a roll placement or group placements, never both."""
    rows = conn.execute(
        "SELECT id, group_id FROM placement WHERE note_id = ? AND id IS NOT ?",
        (note_id, exclude),
    ).fetchall()
    if group_id is None:
        if any(row["group_id"] is not None for row in rows):
            raise RefusedError(
                f"note {note_id} has a group placement, so it may not sit on the roll "
                "— design/Data.md#decisions"
            )
    else:
        if any(row["group_id"] is None for row in rows):
            raise RefusedError(
                f"note {note_id} sits on the roll; promotion is a move, not a second "
                "placement — design/Data.md#decisions"
            )
        if any(row["group_id"] == group_id for row in rows):
            raise RefusedError(
                f"note {note_id} is already placed in group {group_id} — UNIQUE (note_id, group_id)"
            )


def place_notes(
    conn: sqlite3.Connection, requests: Sequence[models.PlacementRequest]
) -> list[models.Placement]:
    """Place notes in a batch. Every residency lands with no pairs.

    Args:
        conn: The connection.
        requests: One residency each. A `group_id` of `None` is the roll.

    Returns:
        The placements created, in the order asked for.

    Raises:
        RefusedError: If any residency breaks a rule. The batch is all or nothing.
    """
    made: list[models.Placement] = []
    with transaction(conn):
        for req in requests:
            get_note(conn, req.note_id)
            if req.group_id is not None:
                get_group(conn, req.group_id)
            _refuse_conflicting_residency(conn, req.note_id, req.group_id)
            cur = conn.execute(
                "INSERT INTO placement (note_id, group_id) VALUES (?, ?)",
                (req.note_id, req.group_id),
            )
            made.append(get_placement(conn, int(cur.lastrowid or 0)))
    return made


def _delete_group_if_empty(conn: sqlite3.Connection, group_id: int | None) -> None:
    if group_id is None:
        return
    left = conn.execute("SELECT 1 FROM placement WHERE group_id = ?", (group_id,)).fetchone()
    if left is None:
        conn.execute("DELETE FROM groups WHERE id = ?", (group_id,))


def move_placement(
    conn: sqlite3.Connection, placement_id: int, payload: models.PlacementMove
) -> models.Placement:
    """Move a placement to another group, or to the roll.

    The pairs travel with it, keeping `sessions_correct`, and are flagged stale
    because they were worded for the old siblings. A group the move empties is
    deleted — design/flows/Regrouping.md#moving-placements.
    """
    placement = get_placement(conn, placement_id)
    if placement.group_id == payload.group_id:
        # Not a move. Flagging its pairs stale would dump a good placement back
        # into the wordsmithing queue for nothing.
        return placement
    if payload.group_id is not None:
        get_group(conn, payload.group_id)
    _refuse_conflicting_residency(conn, placement.note_id, payload.group_id, exclude=placement_id)
    with transaction(conn):
        conn.execute(
            "UPDATE placement SET group_id = ?, pairs_stale = 1 WHERE id = ?",
            (payload.group_id, placement_id),
        )
        _delete_group_if_empty(conn, placement.group_id)
    return get_placement(conn, placement_id)


def list_pending_placements(conn: sqlite3.Connection) -> list[models.PendingPlacement]:
    """The wordsmithing queue: placements with no live pairs, or flagged stale.

    Each carries everything design/flows/Wordsmithing.md#what-claude-reads asks
    for: the note, the group, the group's other notes, and the group's pairs.
    """
    rows = conn.execute(
        """
        SELECT * FROM placement p
        WHERE p.pairs_stale = 1
           OR NOT EXISTS (
               SELECT 1 FROM recall_pair r WHERE r.placement_id = p.id AND r.retired = 0
           )
        ORDER BY p.id
        """
    ).fetchall()
    pending: list[models.PendingPlacement] = []
    for row in rows:
        placement = _placement(row)
        group = get_group(conn, placement.group_id) if placement.group_id is not None else None
        own = conn.execute(
            f"{_PAIR_SELECT} AND r.placement_id = ? ORDER BY r.id",
            (placement.id,),
        ).fetchall()
        if group is None:
            group_notes: list[models.Note] = []
            group_pairs: list[models.Pair] = []
        else:
            group_notes = [
                n for n in list_notes(conn, group_id=group.id) if n.id != placement.note_id
            ]
            others = conn.execute(
                f"{_PAIR_SELECT} AND p.group_id = ? AND r.placement_id != ? ORDER BY r.id",
                (group.id, placement.id),
            ).fetchall()
            group_pairs = [_pair(r) for r in others]
        pending.append(
            models.PendingPlacement(
                placement=placement,
                note=get_note(conn, placement.note_id),
                group=group,
                pairs=[_pair(r) for r in own],
                group_notes=group_notes,
                group_pairs=group_pairs,
            )
        )
    return pending


# --------------------------------------------------------------------------- #
# Writing a pair set — design/api/API.md#writing-a-pair-set
# --------------------------------------------------------------------------- #


def write_pairs(
    conn: sqlite3.Connection, placement_id: int, entries: Sequence[models.PairWrite]
) -> list[models.Pair]:
    """Write a placement's whole pair set at once.

    One shape covers first write, reword, split, combine and drop. The
    inheritance rule lives here rather than in every caller.

    Args:
        conn: The connection.
        placement_id: The placement whose set this is.
        entries: The set. See `models.PairWrite`.

    Returns:
        The placement's live pairs after the write.

    Raises:
        RefusedError: If the set is empty, names a pair that is not a live pair
            of this placement, or would retire every pair the placement has.
    """
    get_placement(conn, placement_id)
    if not entries:
        raise RefusedError(
            f"placement {placement_id} would be left with no live pair, and would "
            "re-enter the wordsmithing queue forever — design/api/API.md#errors"
        )

    live: dict[int, int] = {
        int(row["id"]): int(row["sessions_correct"])
        for row in conn.execute(
            "SELECT id, sessions_correct FROM recall_pair WHERE placement_id = ? AND retired = 0",
            (placement_id,),
        ).fetchall()
    }

    def _own(pair_id: int) -> int:
        if pair_id not in live:
            raise RefusedError(f"pair {pair_id} is not a live pair of placement {placement_id}")
        return live[pair_id]

    kept: set[int] = set()
    for entry in entries:
        if entry.id is not None:
            _own(entry.id)
            kept.add(entry.id)
        for source_id in entry.inherit_from:
            _own(source_id)

    with transaction(conn):
        for entry in entries:
            if entry.id is not None:
                conn.execute(
                    "UPDATE recall_pair SET question = ?, answer = ? WHERE id = ?",
                    (entry.question, entry.answer, entry.id),
                )
                continue
            inherited = min((live[i] for i in entry.inherit_from), default=0)
            conn.execute(
                """
                INSERT INTO recall_pair (placement_id, question, answer, sessions_correct)
                VALUES (?, ?, ?, ?)
                """,
                (placement_id, entry.question, entry.answer, inherited),
            )
        for pair_id in live:
            if pair_id in kept:
                continue
            conn.execute("UPDATE recall_pair SET retired = 1 WHERE id = ?", (pair_id,))
            conn.execute("DELETE FROM draw WHERE recall_pair_id = ?", (pair_id,))
        conn.execute("UPDATE placement SET pairs_stale = 0 WHERE id = ?", (placement_id,))

    rows = conn.execute(
        f"{_PAIR_SELECT} AND r.placement_id = ? ORDER BY r.id",
        (placement_id,),
    ).fetchall()
    return [_pair(row) for row in rows]


# --------------------------------------------------------------------------- #
# The draw — design/flows/Drilling.md#building-the-draw
# --------------------------------------------------------------------------- #


def draw_summary(conn: sqlite3.Connection, day: str | None = None) -> models.DrawSummary | None:
    """The day's draw as numbers — today's unless another date is named.

    A day with no marker has no draw, however recently the last one was built:
    the draw is today's, and an earlier one is never presented as the day's work.
    See design/Data.md#the-draw.

    Args:
        conn: The connection.
        day: A specific date. Defaults to today.

    Returns:
        The numbers, or `None` if that day was never built. A day worked to the
        end returns its `drawn` with zeros beside it, never `None` — otherwise a
        finished morning reads as an unbuilt one and offers to draw itself again.
    """
    target = day or today()
    marker = conn.execute(
        "SELECT drawn, expected FROM draw_day WHERE day = ?", (target,)
    ).fetchone()
    if marker is None:
        return None
    row = conn.execute(
        """
        SELECT COUNT(*) AS due,
               COUNT(DISTINCT p.group_id) AS boards,
               SUM(CASE WHEN p.group_id IS NULL THEN 1 ELSE 0 END) AS roll
        FROM draw d
        JOIN recall_pair r ON r.id = d.recall_pair_id
        JOIN placement p ON p.id = r.placement_id
        WHERE d.day = ?
        """,
        (target,),
    ).fetchone()
    return models.DrawSummary(
        day=target,
        drawn=marker["drawn"],
        expected=marker["expected"],
        due=row["due"],
        boards=row["boards"],
        roll=row["roll"] or 0,
    )


def build_draw(
    conn: sqlite3.Connection,
    day: str | None = None,
    rng: Callable[[], float] = random.random,
) -> models.DrawSummary:
    """Build a date's draw, once for that date.

    Every live pair flips its own coin at `e^(-alpha * sessions_correct)`. There
    is no cap. The stranded rows of every earlier draw are swept first: an
    undrilled pair had no session, so nothing is owed to it and it flips again at
    exactly the same odds. The marker records what the draw was expected to come
    out at alongside what it did.

    Args:
        conn: The connection.
        day: The date to build. Defaults to today.
        rng: A source of uniform randomness in [0, 1). Injectable for tests.

    Returns:
        That date's numbers. Idempotent **on the marker**, not on the rows: a
        date that already has a `draw_day` is reported, never redrawn, however
        many of its pairs have since been drilled away.
    """
    target = day or today()
    with transaction(conn):
        conn.execute("DELETE FROM draw WHERE day < ?", (target,))
        built = conn.execute("SELECT 1 FROM draw_day WHERE day = ?", (target,)).fetchone()
        if built is None:
            # Frozen before a single coin is flipped: drilling moves every term
            # in the sum, so a later one would not be about this draw at all.
            _, expected = corpus(conn)
            drawn = 0
            pairs = conn.execute(
                "SELECT id, sessions_correct FROM recall_pair WHERE retired = 0"
            ).fetchall()
            for pair in pairs:
                if rng() < draw_probability(pair["sessions_correct"]):
                    conn.execute(
                        "INSERT INTO draw (recall_pair_id, day) VALUES (?, ?)",
                        (pair["id"], target),
                    )
                    drawn += 1
            conn.execute(
                "INSERT INTO draw_day (day, drawn, expected) VALUES (?, ?, ?)",
                (target, drawn, expected),
            )
    summary = draw_summary(conn, target)
    if summary is None:  # pragma: no cover — the marker was written a line ago
        raise StoreError(f"the draw marker for {target} went missing")
    return summary


def boards(conn: sqlite3.Connection, n: int) -> list[models.Board]:
    """The next `n` boards of today's draw.

    A group, its due pairs, and its context pairs. Empty when today has no draw
    — an earlier draw's rows are stranded and never handed out.
    """
    day = today()
    group_rows = conn.execute(
        """
        SELECT DISTINCT p.group_id AS group_id
        FROM draw d
        JOIN recall_pair r ON r.id = d.recall_pair_id
        JOIN placement p ON p.id = r.placement_id
        WHERE d.day = ? AND p.group_id IS NOT NULL AND r.retired = 0
        ORDER BY p.group_id
        LIMIT ?
        """,
        (day, n),
    ).fetchall()
    out: list[models.Board] = []
    for group_row in group_rows:
        group = get_group(conn, group_row["group_id"])
        rows = conn.execute(
            f"""
            {_PAIR_SELECT}
            AND p.group_id = ?
            ORDER BY r.id
            """,
            (group.id,),
        ).fetchall()
        due_ids = {
            row["recall_pair_id"]
            for row in conn.execute(
                """
                SELECT d.recall_pair_id FROM draw d
                JOIN recall_pair r ON r.id = d.recall_pair_id
                JOIN placement p ON p.id = r.placement_id
                WHERE d.day = ? AND p.group_id = ?
                """,
                (day, group.id),
            ).fetchall()
        }
        due = [
            models.DuePair(id=r["id"], question=r["question"]) for r in rows if r["id"] in due_ids
        ]
        context = [
            models.ContextPair(
                id=r["id"], question=r["question"], answer=r["answer"], source=_source(r)
            )
            for r in rows
            if r["id"] not in due_ids
        ]
        out.append(
            models.Board(
                group_id=group.id,
                group_name=group.name,
                pair_count=group.pair_count,
                due=due,
                context=context,
            )
        )
    return out


def roll_batch(conn: sqlite3.Connection, n: int) -> models.RollBatch:
    """`n` due roll pairs of today's draw. A board without context."""
    day = today()
    rows = conn.execute(
        """
        SELECT r.id, r.question FROM draw d
        JOIN recall_pair r ON r.id = d.recall_pair_id
        JOIN placement p ON p.id = r.placement_id
        WHERE d.day = ? AND p.group_id IS NULL AND r.retired = 0
        ORDER BY r.id LIMIT ?
        """,
        (day, n),
    ).fetchall()
    return models.RollBatch(due=[models.DuePair(id=r["id"], question=r["question"]) for r in rows])


def grade_inputs(
    conn: sqlite3.Connection, answers: Sequence[models.Answer]
) -> list[dict[str, object]]:
    """The ground truth for a board's answers, ready for the grade call.

    The note is deliberately not included — see design/Claude.md#decisions.
    """
    items: list[dict[str, object]] = []
    for answer in answers:
        row = conn.execute(f"{_PAIR_SELECT} AND r.id = ?", (answer.recall_pair_id,)).fetchone()
        if row is None:
            raise NotFoundError(f"no recall pair {answer.recall_pair_id}")
        items.append(
            {
                "recall_pair_id": row["id"],
                "question": row["question"],
                "answer": row["answer"],
                "source": f"{row['author']} {row['year']}",
                "user_answer": answer.user_answer,
                "user_source": answer.user_source,
            }
        )
    return items


def confirm(conn: sqlite3.Connection, results: Sequence[models.ConfirmResult]) -> None:
    """Commit a board or roll batch, in one transaction.

    The one operation that does not ask what day it is. Each pair's own `draw`
    row says which draw it belongs to, so a board started at 23:58 and answered
    at 00:01 writes against the evening's date: its rows are **stranded** — no
    longer offered anywhere, still writable — and that is the whole of what
    surviving midnight needs. The row is an unambiguous answer because
    `recall_pair_id` is the table's key.

    A correct or contested pair advances by one; a missed pair resets to zero and
    writes a miss row dated by **that row's day, not the wall clock** — one
    clock, so a Tuesday board confirmed on Wednesday records Tuesday. Every
    pair's draw row is deleted — see design/flows/Drilling.md#writes.

    Raises:
        RefusedError: If any pair has no `draw` row. That means the board was
            already confirmed, or a build has since swept it.
    """
    days: dict[int, str] = {}
    for result in results:
        row = conn.execute(
            "SELECT day FROM draw WHERE recall_pair_id = ?", (result.recall_pair_id,)
        ).fetchone()
        if row is None:
            raise RefusedError(
                f"pair {result.recall_pair_id} has no draw row; this board was already "
                "confirmed, or a build has since swept it — design/api/API.md#errors"
            )
        days[result.recall_pair_id] = str(row["day"])
    with transaction(conn):
        for result in results:
            if result.correct:
                conn.execute(
                    "UPDATE recall_pair SET sessions_correct = sessions_correct + 1 WHERE id = ?",
                    (result.recall_pair_id,),
                )
            else:
                conn.execute(
                    "UPDATE recall_pair SET sessions_correct = 0 WHERE id = ?",
                    (result.recall_pair_id,),
                )
                conn.execute(
                    """
                    INSERT INTO miss (recall_pair_id, day, user_answer, user_source)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        result.recall_pair_id,
                        days[result.recall_pair_id],
                        result.user_answer,
                        result.user_source,
                    ),
                )
            conn.execute("DELETE FROM draw WHERE recall_pair_id = ?", (result.recall_pair_id,))


# --------------------------------------------------------------------------- #
# Misses and Home
# --------------------------------------------------------------------------- #


def list_misses(
    conn: sqlite3.Connection,
    *,
    group_id: int | None = None,
    placement_id: int | None = None,
    since: str | None = None,
) -> list[models.Miss]:
    """The drill record, newest first."""
    clauses: list[str] = []
    args: list[object] = []
    if group_id is not None:
        clauses.append("p.group_id = ?")
        args.append(group_id)
    if placement_id is not None:
        clauses.append("p.id = ?")
        args.append(placement_id)
    if since is not None:
        clauses.append("m.day >= ?")
        args.append(since)
    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    rows = conn.execute(
        f"""
        SELECT m.id, m.recall_pair_id, m.day, m.user_answer, m.user_source,
               r.question, r.answer, p.group_id, g.name AS group_name
        FROM miss m
        JOIN recall_pair r ON r.id = m.recall_pair_id
        JOIN placement p ON p.id = r.placement_id
        LEFT JOIN groups g ON g.id = p.group_id
        {where}
        ORDER BY m.day DESC, m.id DESC
        """,
        tuple(args),
    ).fetchall()
    return [
        models.Miss(
            id=r["id"],
            recall_pair_id=r["recall_pair_id"],
            day=r["day"],
            user_answer=r["user_answer"],
            user_source=r["user_source"],
            question=r["question"],
            answer=r["answer"],
            group_id=r["group_id"],
            group_name=r["group_name"],
        )
        for r in rows
    ]


def home(conn: sqlite3.Connection) -> models.Home:
    """The three backlog counts, the live corpus, and today's draw."""
    ungrouped = int(
        conn.execute(
            "SELECT COUNT(*) AS c FROM note n"
            " WHERE NOT EXISTS (SELECT 1 FROM placement p WHERE p.note_id = n.id)"
        ).fetchone()["c"]
    )
    pairless = int(
        conn.execute(
            "SELECT COUNT(*) AS c FROM placement p WHERE NOT EXISTS ("
            " SELECT 1 FROM recall_pair r WHERE r.placement_id = p.id AND r.retired = 0)"
        ).fetchone()["c"]
    )
    stale = int(
        conn.execute("SELECT COUNT(*) AS c FROM placement WHERE pairs_stale = 1").fetchone()["c"]
    )
    pairs, expected = corpus(conn)
    draw = draw_summary(conn)
    return models.Home(
        ungrouped_notes=ungrouped,
        placements_without_pairs=pairless,
        placements_stale=stale,
        pairs=pairs,
        # Only a prediction of the build about to happen, and it moves as pairs
        # are written. Once today is built the number that matters is that
        # draw's own, frozen — design/api/API.md.
        expected=None if draw is not None else expected,
        draw=draw,
    )
