"""The HTTP routes. Thin adapters over `store` — no rule lives here."""

import sqlite3
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Query

from api import claude, models, store
from api.db import connect

router = APIRouter(prefix="/api")


def get_conn() -> Iterator[sqlite3.Connection]:
    """One connection per request."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def get_caller() -> claude.Caller:
    """The grade call. Overridden in tests so the API is never touched."""
    return claude.live_caller


Conn = Annotated[sqlite3.Connection, Depends(get_conn)]
Caller = Annotated[claude.Caller, Depends(get_caller)]


# --------------------------------------------------------------------------- #
# The drill loop — app only. None of these is an MCP tool.
# --------------------------------------------------------------------------- #


@router.get("/home")
def read_home(conn: Conn) -> models.Home:
    """The three backlog counts and today's draw status."""
    return store.home(conn)


@router.post("/draw")
def post_draw(conn: Conn) -> models.DrawSummary:
    """Build today's draw. Idempotent on the `draw_day` marker.

    The only route in the drill loop that reads the calendar.
    """
    return store.build_draw(conn)


@router.get("/draw")
def read_draw(conn: Conn) -> models.DrawSummary | None:
    """The current draw — the one most recently built — or `null` if there is none."""
    return store.draw_summary(conn)


@router.get("/draw/boards")
def read_boards(conn: Conn, n: Annotated[int, Query(ge=1)] = 1) -> list[models.Board]:
    """The next `n` boards of the current draw."""
    return store.boards(conn, n)


@router.get("/draw/roll")
def read_roll(conn: Conn, n: Annotated[int, Query(ge=1)] = 1) -> models.RollBatch:
    """`n` due roll pairs of the current draw."""
    return store.roll_batch(conn, n)


@router.post("/grade")
def post_grade(conn: Conn, caller: Caller, payload: models.GradeRequest) -> models.GradeResponse:
    """Grade a board's typed answers. The only Claude call; writes nothing."""
    items = store.grade_inputs(conn, payload.answers)
    try:
        return models.GradeResponse(verdicts=claude.grade(items, caller))
    except claude.GradeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/confirm", status_code=204)
def post_confirm(conn: Conn, payload: models.ConfirmRequest) -> None:
    """Commit a board or roll batch against the current draw, in one transaction."""
    store.confirm(conn, payload.results)


# --------------------------------------------------------------------------- #
# Entry and lookup — called by both front doors
# --------------------------------------------------------------------------- #


@router.get("/sources")
def read_sources(conn: Conn, q: str = "") -> list[models.Source]:
    """Search author, year and publication."""
    return store.search_sources(conn, q)


@router.post("/sources", status_code=201)
def post_source(conn: Conn, payload: models.SourceCreate) -> models.Source:
    """Create a source."""
    return store.create_source(conn, payload)


@router.post("/notes", status_code=201)
def post_note(conn: Conn, payload: models.NoteCreate) -> models.Note:
    """Create a note against a source."""
    return store.create_note(conn, payload)


@router.patch("/notes/{note_id}")
def patch_note(conn: Conn, note_id: int, payload: models.NoteEdit) -> models.Note:
    """Edit a statement. Refused once the note has a placement."""
    return store.edit_note(conn, note_id, payload)


@router.delete("/notes/{note_id}", status_code=204)
def delete_note(conn: Conn, note_id: int) -> None:
    """Delete a note. Refused once the note has a placement."""
    store.delete_note(conn, note_id)


@router.get("/notes")
def read_notes(
    conn: Conn,
    ungrouped: bool = False,
    roll: bool = False,
    group_id: int | None = None,
    source_id: int | None = None,
    q: str | None = None,
) -> list[models.Note]:
    """Notes by any combination of the filters."""
    return store.list_notes(
        conn, ungrouped=ungrouped, roll=roll, group_id=group_id, source_id=source_id, q=q
    )


@router.get("/groups")
def read_groups(conn: Conn) -> list[models.Group]:
    """Every group with its description, note count and live pair count."""
    return store.list_groups(conn)


@router.get("/groups/{group_id}")
def read_group(conn: Conn, group_id: int) -> models.GroupDetail:
    """One group's notes and pairs."""
    return store.get_group_detail(conn, group_id)


# --------------------------------------------------------------------------- #
# Reshaping — skills only
# --------------------------------------------------------------------------- #


@router.post("/groups", status_code=201)
def post_group(conn: Conn, payload: models.GroupCreate) -> models.Group:
    """Create a group from a name and description the user approved."""
    return store.create_group(conn, payload)


@router.patch("/groups/{group_id}")
def patch_group(conn: Conn, group_id: int, payload: models.GroupEdit) -> models.Group:
    """Reword a name or description."""
    return store.update_group(conn, group_id, payload)


@router.post("/placements", status_code=201)
def post_placements(
    conn: Conn, payload: Annotated[list[models.PlacementRequest], Body()]
) -> list[models.Placement]:
    """Batch place notes."""
    return store.place_notes(conn, payload)


@router.patch("/placements/{placement_id}")
def patch_placement(
    conn: Conn, placement_id: int, payload: models.PlacementMove
) -> models.Placement:
    """Move a placement. Sets `pairs_stale`; deletes a group the move empties."""
    return store.move_placement(conn, placement_id, payload)


@router.get("/placements")
def read_placements(conn: Conn, pending: bool = False) -> list[models.PendingPlacement]:
    """The wordsmithing queue."""
    if not pending:
        raise HTTPException(status_code=400, detail="only `?pending` is served")
    return store.list_pending_placements(conn)


@router.put("/placements/{placement_id}/pairs")
def put_pairs(
    conn: Conn, placement_id: int, payload: Annotated[list[models.PairWrite], Body()]
) -> list[models.Pair]:
    """Write the pair set whole; clears `pairs_stale`."""
    return store.write_pairs(conn, placement_id, payload)


@router.get("/misses")
def read_misses(
    conn: Conn,
    group_id: int | None = None,
    placement_id: int | None = None,
    since: str | None = None,
) -> list[models.Miss]:
    """The drill record, newest first."""
    return store.list_misses(conn, group_id=group_id, placement_id=placement_id, since=since)
