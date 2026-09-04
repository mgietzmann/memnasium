"""The eleven MCP tools.

Curated by hand, never generated from the routes. Nothing that *writes* in the
drill loop is here: if `POST /confirm` were reachable from a Claude Code session
an agent could mark pairs correct, silently editing the record of what was
actually recalled — see design/api/API.md#decisions.

Each tool is a thin adapter over the same store function the matching route
calls. No rule lives in this module.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from mcp.server.mcpserver import MCPServer

from api import models, store
from api.db import connect

#: The roster, as a doc-checkable fact. Tested against the drill loop.
TOOL_NAMES = (
    "list_ungrouped_notes",
    "list_groups",
    "get_group",
    "search_notes",
    "place_notes",
    "create_group",
    "update_group",
    "move_placement",
    "list_pending_placements",
    "write_pairs",
    "list_misses",
)

server = MCPServer("memnasium")


@contextmanager
def _conn() -> Iterator[sqlite3.Connection]:
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


@server.tool()
def list_ungrouped_notes() -> list[models.Note]:
    """Notes that have been entered but never triaged. The grouping queue."""
    with _conn() as conn:
        return store.list_notes(conn, ungrouped=True)


@server.tool()
def list_groups() -> list[models.Group]:
    """Every group with its description, note count and live pair count."""
    with _conn() as conn:
        return store.list_groups(conn)


@server.tool()
def get_group(group_id: int) -> models.GroupDetail:
    """One group's notes and its live pairs."""
    with _conn() as conn:
        return store.get_group_detail(conn, group_id)


@server.tool()
def search_notes(
    ungrouped: bool = False,
    roll: bool = False,
    group_id: int | None = None,
    source_id: int | None = None,
    q: str | None = None,
) -> list[models.Note]:
    """Notes by group, by the roll, by source, by text, or any combination."""
    with _conn() as conn:
        return store.list_notes(
            conn, ungrouped=ungrouped, roll=roll, group_id=group_id, source_id=source_id, q=q
        )


@server.tool()
def place_notes(placements: list[models.PlacementRequest]) -> list[models.Placement]:
    """Place notes in a batch. A `group_id` of null is the roll."""
    with _conn() as conn:
        return store.place_notes(conn, placements)


@server.tool()
def create_group(name: str, description: str) -> models.Group:
    """Coin a group. Only ever because the user asked for one."""
    with _conn() as conn:
        return store.create_group(conn, models.GroupCreate(name=name, description=description))


@server.tool()
def update_group(
    group_id: int, name: str | None = None, description: str | None = None
) -> models.Group:
    """Reword a group's name or description."""
    with _conn() as conn:
        return store.update_group(
            conn, group_id, models.GroupEdit(name=name, description=description)
        )


@server.tool()
def move_placement(placement_id: int, group_id: int | None = None) -> models.Placement:
    """Move a placement to another group, or to the roll.

    Flags its pairs stale and deletes a group the move empties.
    """
    with _conn() as conn:
        return store.move_placement(conn, placement_id, models.PlacementMove(group_id=group_id))


@server.tool()
def list_pending_placements() -> list[models.PendingPlacement]:
    """The wordsmithing queue: placements with no live pairs, or flagged stale."""
    with _conn() as conn:
        return store.list_pending_placements(conn)


@server.tool()
def write_pairs(placement_id: int, pairs: list[models.PairWrite]) -> list[models.Pair]:
    """Write a placement's whole pair set at once; clears the stale flag.

    An entry with an `id` rewords that pair. An entry with neither `id` nor
    `inherit_from` is new at zero. An entry with `inherit_from` is new, taking
    the lower `sessions_correct` of the pairs it names. A live pair left out of
    the set is retired.
    """
    with _conn() as conn:
        return store.write_pairs(conn, placement_id, pairs)


@server.tool()
def list_misses(
    group_id: int | None = None, placement_id: int | None = None, since: str | None = None
) -> list[models.Miss]:
    """The drill record, newest first. Reads it; cannot touch it."""
    with _conn() as conn:
        return store.list_misses(conn, group_id=group_id, placement_id=placement_id, since=since)
