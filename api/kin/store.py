"""Kin's play state: generating a set, dealing a board, submitting it, giving it up.

The tables are design/data/Kin.md's, the rules design/games/Kin.md's, and the procedures
design/algorithms/Kin.md's. Everything here is disposable — it exists so a half-finished day
survives closing the app.
"""

import random
import sqlite3
from datetime import date, datetime
from typing import Any

from api.errors import bad_request, conflict, inconsistent_data, not_found
from api.fish.search import citation
from api.kin.draw import Anchor, build_group, is_due
from api.kin.kinds import CLADE_CHARACTER, CLADE_IMAGE, KINDS, EdgeKind, handle, parse_handle
from api.kin.models import (
    Board,
    Card,
    Citation,
    KinState,
    PaletteClade,
    Result,
    Slot,
    SubmitResponse,
)


def _today() -> str:
    """The date a set is stamped with. Played days, not calendar days, drive Δt."""
    return date.today().isoformat()


def _now() -> str:
    """A timestamp for `first_submitted` and `ended`."""
    return datetime.now().isoformat(timespec="seconds")


def _placeholders(values: list[Any]) -> str:
    """`?, ?, ?` for an IN clause of the given length."""
    return ", ".join("?" for _ in values)


# ───────────────────────────────────────────────────────────────────────── the set


def _current_set(connection: sqlite3.Connection) -> sqlite3.Row | None:
    """The one set, or None. At most one exists at a time."""
    row: sqlite3.Row | None = connection.execute(
        "SELECT set_id, generated_on FROM kin_sets ORDER BY set_id DESC LIMIT 1"
    ).fetchone()
    return row


def state(connection: sqlite3.Connection) -> KinState:
    """What the games-list card shows — design/app/Navigation.md's table reads off this."""
    current = _current_set(connection)
    if current is None:
        return KinState(generated_on=None, anchors_total=0, anchors_left=0, open_board=False)
    counts = connection.execute(
        "SELECT count(*) AS total, sum(board_id IS NULL) AS left_ "
        "FROM kin_set_anchors WHERE set_id = ?",
        (current["set_id"],),
    ).fetchone()
    return KinState(
        generated_on=current["generated_on"],
        anchors_total=counts["total"],
        anchors_left=counts["left_"] or 0,
        open_board=_open_board(connection) is not None,
    )


def _is_spent(connection: sqlite3.Connection) -> bool:
    """Whether the current set is finished with: every anchor dealt, *and* no board open.

    The glossary calls a set spent when its anchors have all been "dealt and played" — an open
    board is the second half. It holds the set open however the anchor count reads, because every
    anchor can be dealt and the last board still be half-played, and redrawing would throw away a
    board the player is in the middle of (design/api/Kin.md, design/app/Kin.md).
    """
    return state(connection).anchors_left == 0 and _open_board(connection) is None


def _anchors_of_due_edges(
    connection: sqlite3.Connection, kind: EdgeKind, due: list[sqlite3.Row]
) -> set[str]:
    """Which clades a set of drawn edges belongs to.

    A `clade_image` or `clade_character` edge names its clade directly. A drawn `src` edge makes
    an anchor of **every** clade its image or character hangs off, which is what lets a shared
    image's card appear on both their boards.
    """
    if kind in (CLADE_IMAGE, CLADE_CHARACTER):
        return {row["name"] for row in due}
    card_column = kind.other  # img_id or char_id
    table = "clade_image_edges" if card_column == "img_id" else "clade_character_edges"
    cards = [row[card_column] for row in due]
    if not cards:
        return set()
    rows = connection.execute(
        f"SELECT name FROM {table} WHERE {card_column} IN ({_placeholders(cards)})",
        cards,
    ).fetchall()
    return {row["name"] for row in rows}


def _edges_of_anchors(
    connection: sqlite3.Connection, kind: EdgeKind, anchors: list[str]
) -> list[sqlite3.Row]:
    """Every edge of the given clades, of one kind.

    A `src` edge reaches its clade through the image or character it hangs off.
    """
    holes = _placeholders(anchors)
    if kind in (CLADE_IMAGE, CLADE_CHARACTER):
        return connection.execute(
            f"SELECT * FROM {kind.knowledge_table} WHERE name IN ({holes})",
            anchors,
        ).fetchall()
    card_column = kind.other
    via = "clade_image_edges" if card_column == "img_id" else "clade_character_edges"
    return connection.execute(
        f"SELECT * FROM {kind.knowledge_table} WHERE {card_column} IN "
        f"(SELECT {card_column} FROM {via} WHERE name IN ({holes}))",
        anchors,
    ).fetchall()


def generate(connection: sqlite3.Connection, rng: random.Random | None = None) -> KinState:
    """Generate the day's draw, honouring carry-over.

    Called twice in a day this returns the existing set, and called on a day whose previous set
    still has anchors left it returns that one rather than drawing a new one. A new set is drawn
    only when there is no set at all, or the one there is was spent on an earlier day — and
    drawing it drops the old set and its boards.

    A set with an open board is never spent, so this never draws over a board the player is in
    the middle of. It stays idempotent and always answers `200`.
    """
    rng = rng or random.Random()
    current = _current_set(connection)
    if current is not None:
        # Carry-over: an unspent set is played to the end before another is drawn, and a set
        # spent today is still the answer to "is the player done for today".
        if not _is_spent(connection) or current["generated_on"] == _today():
            return state(connection)

    connection.execute("DELETE FROM kin_sets")
    cursor = connection.execute("INSERT INTO kin_sets (generated_on) VALUES (?)", (_today(),))
    assert cursor.lastrowid is not None
    set_id = cursor.lastrowid

    # 1. draw each candidate edge with p = e^(−α·Δt)
    drawn: dict[str, list[sqlite3.Row]] = {}
    anchors: set[str] = set()
    for kind in KINDS:
        rows = connection.execute(f"SELECT * FROM {kind.knowledge_table}").fetchall()
        due = [r for r in rows if is_due(r["sessions_since_last_failed"], rng)]
        drawn[kind.prefix] = due
        # 2. anchors := the clades those drawn edges belong to
        anchors |= _anchors_of_due_edges(connection, kind, due)

    if anchors:
        names = sorted(anchors)
        levels = dict(
            connection.execute(
                f"SELECT name, level FROM clades WHERE name IN ({_placeholders(names)})",
                names,
            ).fetchall()
        )
        connection.executemany(
            "INSERT INTO kin_set_anchors (set_id, name, level) VALUES (?, ?, ?)",
            [(set_id, name, levels[name]) for name in names],
        )

        # 3. set rows := every edge of every anchor, `due` marking those drawn in step 1
        for kind in KINDS:
            due_keys = {(r[kind.keys[0]], r[kind.keys[1]]) for r in drawn[kind.prefix]}
            rows = _edges_of_anchors(connection, kind, names)
            connection.executemany(
                f"INSERT INTO {kind.set_table} "
                f"(set_id, {kind.keys[0]}, {kind.keys[1]}, due, locked) VALUES (?, ?, ?, ?, ?)",
                [
                    (
                        set_id,
                        row[kind.keys[0]],
                        row[kind.keys[1]],
                        int((row[kind.keys[0]], row[kind.keys[1]]) in due_keys),
                        int((row[kind.keys[0]], row[kind.keys[1]]) not in due_keys),
                    )
                    for row in rows
                ],
            )
    return state(connection)


# ─────────────────────────────────────────────────────────────────────── the board


def _open_board(connection: sqlite3.Connection) -> sqlite3.Row | None:
    """The one board with `ended` null, or None."""
    row: sqlite3.Row | None = connection.execute(
        "SELECT * FROM kin_boards WHERE ended IS NULL ORDER BY board_id DESC LIMIT 1"
    ).fetchone()
    return row


def _parents(connection: sqlite3.Connection) -> dict[str, str]:
    """Every parent edge as a map, for distance to walk."""
    return dict(connection.execute("SELECT name, parent FROM clade_parent_edges").fetchall())


def deal(connection: sqlite3.Connection, size: int, rng: random.Random | None = None) -> Board:
    """Deal a group onto a new board.

    Takes **all** of each chosen anchor's set edges, so no anchor is ever split across two
    boards and every card is complete.

    Raises:
        ApiError: 409 when no set is generated, a board is already open, or nothing is left
            to deal.
    """
    rng = rng or random.Random()
    current = _current_set(connection)
    if current is None:
        raise conflict("no set generated yet")
    if _open_board(connection) is not None:
        raise conflict("a board is already open")
    set_id = current["set_id"]

    undealt = connection.execute(
        "SELECT name, level FROM kin_set_anchors WHERE set_id = ? AND board_id IS NULL",
        (set_id,),
    ).fetchall()
    if not undealt:
        raise conflict("no anchors left to deal")

    group = build_group(
        _parents(connection), [Anchor(r["name"], r["level"]) for r in undealt], size, rng
    )
    level = next(r["level"] for r in undealt if r["name"] == group[0])

    cursor = connection.execute(
        "INSERT INTO kin_boards (set_id, level) VALUES (?, ?)", (set_id, level)
    )
    assert cursor.lastrowid is not None
    board_id = cursor.lastrowid
    connection.execute(
        f"UPDATE kin_set_anchors SET board_id = ? "
        f"WHERE set_id = ? AND name IN ({_placeholders(group)})",
        (board_id, set_id, *group),
    )

    for kind in KINDS:
        if kind in (CLADE_IMAGE, CLADE_CHARACTER):
            select = (
                f"SELECT edge_id FROM {kind.set_table} "
                f"WHERE set_id = ? AND name IN ({_placeholders(group)})"
            )
            params = [set_id, *group]
        else:
            card_column = kind.other
            via = CLADE_IMAGE if card_column == "img_id" else CLADE_CHARACTER
            select = (
                f"SELECT edge_id FROM {kind.set_table} WHERE set_id = ? AND "
                f"{card_column} IN (SELECT {card_column} FROM {via.set_table} "
                f"WHERE set_id = ? AND name IN ({_placeholders(group)}))"
            )
            params = [set_id, set_id, *group]
        edge_ids = [r["edge_id"] for r in connection.execute(select, params).fetchall()]
        connection.executemany(
            f"INSERT INTO {kind.board_table} (board_id, edge_id) VALUES (?, ?)",
            [(board_id, edge_id) for edge_id in edge_ids],
        )

    board = _open_board(connection)
    assert board is not None
    return board_body(connection, board, scored=False)


def _slot(kind: EdgeKind, row: sqlite3.Row) -> Slot:
    """One slot as the client sees it.

    A locked slot shows the true value out of its set row; a live one shows nothing, because the
    right answer is never returned to a board still being played.
    """
    locked = bool(row["locked"])
    return Slot(
        slot=handle(kind, row["edge_id"]),
        state="locked" if locked else "due",
        value=row[kind.truth] if locked else None,
    )


def _board_rows(connection: sqlite3.Connection, kind: EdgeKind, board_id: int) -> list[sqlite3.Row]:
    """Every set row of one kind dealt onto a board."""
    return connection.execute(
        f"SELECT e.* FROM {kind.set_table} e "
        f"JOIN {kind.board_table} b ON b.edge_id = e.edge_id "
        "WHERE b.board_id = ? ORDER BY e.edge_id",
        (board_id,),
    ).fetchall()


def board_body(connection: sqlite3.Connection, board: sqlite3.Row, *, scored: bool) -> Board:
    """Assemble a board: its palette, its pool, and a card per image and character."""
    board_id = board["board_id"]
    set_id = board["set_id"]

    palette = [
        PaletteClade(name=r["name"], common_name=r["common_name"])
        for r in connection.execute(
            "SELECT a.name, c.common_name FROM kin_set_anchors a "
            "JOIN clades c ON c.name = a.name WHERE a.board_id = ? ORDER BY a.name",
            (board_id,),
        ).fetchall()
    ]

    src_by_card: dict[str, dict[Any, sqlite3.Row]] = {}
    for kind in (KINDS[2], KINDS[3]):
        src_by_card[kind.prefix] = {
            r[kind.other]: r
            for r in connection.execute(
                f"SELECT * FROM {kind.set_table} WHERE set_id = ?", (set_id,)
            ).fetchall()
        }

    cards: list[tuple[str, int, Card]] = []
    for row in _board_rows(connection, CLADE_IMAGE, board_id):
        src_row = src_by_card["is"].get(row["img_id"])
        if src_row is None:
            # Every card of every anchor is on the board (design/games/Kin.md), and every card
            # has both of its edges — so a missing source is bad data, not a card to drop.
            raise inconsistent_data(
                f"image {row['img_id']!r} has no source edge, so its card cannot be built"
            )
        cards.append(
            (
                row["name"],
                row["edge_id"],
                Card(
                    kind="image",
                    img_id=row["img_id"],
                    clade=_slot(CLADE_IMAGE, row),
                    src=_slot(KINDS[2], src_row),
                ),
            )
        )
    for row in _board_rows(connection, CLADE_CHARACTER, board_id):
        src_row = src_by_card["cs"].get(row["char_id"])
        if src_row is None:
            raise inconsistent_data(
                f"character {row['char_id']} has no source edge, so its card cannot be built"
            )
        text = connection.execute(
            "SELECT text FROM characters WHERE char_id = ?", (row["char_id"],)
        ).fetchone()["text"]
        cards.append(
            (
                row["name"],
                row["edge_id"],
                Card(
                    kind="character",
                    text=text,
                    clade=_slot(CLADE_CHARACTER, row),
                    src=_slot(KINDS[3], src_row),
                ),
            )
        )
    cards.sort(key=lambda c: (c[0], c[2].kind, c[1]))

    # The pool holds the sources behind the board's due `src` slots, and nothing else. It is
    # computed from `due` rather than from what is still blank, so nothing is consumed.
    due_srcs: set[int] = set()
    shown_srcs: set[int] = set()
    for kind in (KINDS[2], KINDS[3]):
        for row in _board_rows(connection, kind, board_id):
            shown_srcs.add(row["src"])
            if row["due"]:
                due_srcs.add(row["src"])

    labels: dict[int, str] = {}
    if shown_srcs:
        srcs = sorted(shown_srcs)
        labels = {
            r["src"]: citation(r["author"], r["year"])
            for r in connection.execute(
                f"SELECT src, author, year FROM sources WHERE src IN ({_placeholders(srcs)}) "
                "ORDER BY author, year",
                srcs,
            ).fetchall()
        }
    citations = [Citation(src=src, label=labels[src]) for src in labels if src in due_srcs]

    return Board(
        board_id=board_id,
        level=board["level"],
        ended=board["ended"] is not None,
        scored=scored,
        clades=palette,
        citations=citations,
        cards=[card for _, _, card in cards],
        labels=labels,
    )


def current_board(connection: sqlite3.Connection) -> Board:
    """The open board, which is how a board resumes after the app is closed.

    Raises:
        ApiError: 404 when there is none.
    """
    board = _open_board(connection)
    if board is None:
        raise not_found("no open board")
    return board_body(connection, board, scored=False)


# ─────────────────────────────────────────────────────────────────── playing it


def _live_slots(
    connection: sqlite3.Connection, board_id: int
) -> dict[str, tuple[EdgeKind, sqlite3.Row]]:
    """Every slot on the board still waiting for an answer: due, and not yet locked."""
    live: dict[str, tuple[EdgeKind, sqlite3.Row]] = {}
    for kind in KINDS:
        for row in _board_rows(connection, kind, board_id):
            if row["due"] and not row["locked"]:
                live[handle(kind, row["edge_id"])] = (kind, row)
    return live


def _all_handles(connection: sqlite3.Connection, board_id: int) -> set[str]:
    """Every slot handle on the board, live or locked."""
    return {
        handle(kind, row["edge_id"])
        for kind in KINDS
        for row in _board_rows(connection, kind, board_id)
    }


def _score_back(
    connection: sqlite3.Connection, kind: EdgeKind, row: sqlite3.Row, *, correct: bool
) -> None:
    """Move the knowledge edge's counter: `+= 1` when right, `→ 0` when not.

    Only `due` rows reach here; prefill never moves a counter.
    """
    value = "sessions_since_last_failed + 1" if correct else "0"
    connection.execute(
        f"UPDATE {kind.knowledge_table} SET sessions_since_last_failed = {value} "
        f"WHERE {kind.keys[0]} = ? AND {kind.keys[1]} = ?",
        (row[kind.keys[0]], row[kind.keys[1]]),
    )


def _is_a_node(connection: sqlite3.Connection, kind: EdgeKind, given: str | int) -> bool:
    """Whether an answer names something real.

    `answered_name` and `answered_src` are real foreign keys (design/data/Kin.md), and the client
    can only ever send a chip, so anything else is a malformed request rather than a wrong guess.
    """
    if kind.truth == "src":
        try:
            src = int(given)
        except (TypeError, ValueError):
            return False
        return (
            connection.execute("SELECT 1 FROM sources WHERE src = ?", (src,)).fetchone() is not None
        )
    return (
        connection.execute("SELECT 1 FROM clades WHERE name = ?", (str(given),)).fetchone()
        is not None
    )


def _matches(kind: EdgeKind, given: str | int, truth: str | int) -> bool:
    """Whether an answer is the right one, tolerating a `src` arriving as a string."""
    if kind.truth == "src":
        try:
            return int(given) == int(truth)
        except (TypeError, ValueError):
            return False
    return str(given) == str(truth)


def submit(connection: sqlite3.Connection, slots: dict[str, str | int]) -> SubmitResponse:
    """Answer the open board.

    Every due slot must be present. Correct slots lock; incorrect ones stay live for the player
    to fill again. Scoring happens on the first submission only — later ones re-lock and report,
    and change no counters.

    Raises:
        ApiError: 404 when no board is open, 400 when a due slot is missing or a handle is not
            one of this board's.
    """
    board = _open_board(connection)
    if board is None:
        raise not_found("no open board")
    board_id = board["board_id"]

    live = _live_slots(connection, board_id)
    known = _all_handles(connection, board_id)
    for slot in slots:
        if parse_handle(slot) is None or slot not in known:
            raise bad_request(f"unknown slot handle {slot!r}")
    missing = sorted(set(live) - set(slots))
    if missing:
        raise bad_request(f"every due slot must be present; missing {missing}")

    scored = board["first_submitted"] is None
    results: dict[str, Result] = {}
    for slot, (kind, row) in live.items():
        given = slots[slot]
        if not _is_a_node(connection, kind, given):
            raise bad_request(f"slot {slot!r} was answered with {given!r}, which is not a chip")
        correct = _matches(kind, given, row[kind.truth])
        results[slot] = "correct" if correct else "wrong"
        if scored:
            connection.execute(
                f"UPDATE {kind.set_table} SET {kind.answer} = ? WHERE edge_id = ?",
                (given, row["edge_id"]),
            )
            _score_back(connection, kind, row, correct=correct)
        if correct:
            connection.execute(
                f"UPDATE {kind.set_table} SET locked = 1 WHERE edge_id = ?",
                (row["edge_id"],),
            )
    if scored:
        connection.execute(
            "UPDATE kin_boards SET first_submitted = ? WHERE board_id = ?", (_now(), board_id)
        )

    complete = not _live_slots(connection, board_id)
    if complete:
        connection.execute("UPDATE kin_boards SET ended = ? WHERE board_id = ?", (_now(), board_id))
    return SubmitResponse(results=results, complete=complete, scored=scored)


def move_on(connection: sqlite3.Connection) -> Board:
    """Give the open board up.

    Everything not already locked scores as a miss, every slot locks, and the anchors are spent.
    The completed board comes back with every value showing, because a player who has given up
    has to be told what it was.

    Raises:
        ApiError: 404 when no board is open.
    """
    board = _open_board(connection)
    if board is None:
        raise not_found("no open board")
    board_id = board["board_id"]
    scored = board["first_submitted"] is None

    for slot_kind, row in _live_slots(connection, board_id).values():
        if scored:
            _score_back(connection, slot_kind, row, correct=False)
        connection.execute(
            f"UPDATE {slot_kind.set_table} SET locked = 1 WHERE edge_id = ?",
            (row["edge_id"],),
        )
    if scored:
        connection.execute(
            "UPDATE kin_boards SET first_submitted = ? WHERE board_id = ?", (_now(), board_id)
        )
    connection.execute("UPDATE kin_boards SET ended = ? WHERE board_id = ?", (_now(), board_id))

    ended = connection.execute(
        "SELECT * FROM kin_boards WHERE board_id = ?", (board_id,)
    ).fetchone()
    return board_body(connection, ended, scored=scored)
