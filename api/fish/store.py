"""Reading and writing the knowledge graph — the tables of design/data/Fish.md.

One submission is one transaction: a submission that fails half way cannot leave orphan clades
behind (design/api/Fish.md).
"""

import sqlite3
from itertools import pairwise

from api.errors import bad_request, conflict, not_found
from api.fish.models import (
    Ancestor,
    CharacterCreated,
    CharacterEntry,
    CladeDetail,
    ImageCreated,
    ImageEntryBody,
    NewClade,
    NewSource,
)
from api.fish.search import CladeRow, SourceRow
from api.levels import Level

MAX_CHAIN = len(Level)
"""A parent chain cannot be longer than the level enum, which is what bounds every walk."""


def all_clades(connection: sqlite3.Connection) -> list[CladeRow]:
    """Every clade, for search to scan."""
    rows = connection.execute(
        "SELECT name, common_name, level FROM clades ORDER BY name"
    ).fetchall()
    return [CladeRow(r["name"], r["common_name"], r["level"]) for r in rows]


def all_sources(connection: sqlite3.Connection) -> list[SourceRow]:
    """Every source, for search to scan."""
    rows = connection.execute(
        "SELECT src, author, year, title FROM sources ORDER BY author, year"
    ).fetchall()
    return [SourceRow(r["src"], r["author"], r["year"], r["title"]) for r in rows]


def chain(connection: sqlite3.Connection, name: str) -> list[str]:
    """A clade, its parent, its grandparent, and so on to a root.

    The level enum caps this at seven entries, so the walk is bounded (design/algorithms/Kin.md).

    Args:
        connection: An open database connection.
        name: Scientific name of the clade to start from.

    Returns:
        Names from `name` outward, `name` first.
    """
    walked = [name]
    seen = {name}
    for _ in range(MAX_CHAIN):
        row = connection.execute(
            "SELECT parent FROM clade_parent_edges WHERE name = ?", (walked[-1],)
        ).fetchone()
        if row is None or row["parent"] in seen:
            break
        walked.append(row["parent"])
        seen.add(row["parent"])
    return walked


def clade_detail(connection: sqlite3.Connection, name: str) -> CladeDetail:
    """One clade and its ancestors, narrowest to broadest.

    Raises:
        ApiError: 404 when the clade is not recorded, which is the walk's signal that it is new.
    """
    row = connection.execute(
        "SELECT name, common_name, level FROM clades WHERE name = ?", (name,)
    ).fetchone()
    if row is None:
        raise not_found(f"no clade named {name!r}")
    ancestors = []
    for ancestor in chain(connection, name)[1:]:
        level = connection.execute(
            "SELECT level FROM clades WHERE name = ?", (ancestor,)
        ).fetchone()["level"]
        ancestors.append(Ancestor(name=ancestor, level=Level(level)))
    return CladeDetail(
        name=row["name"],
        common_name=row["common_name"],
        level=Level(row["level"]),
        ancestors=ancestors,
    )


def _level_of(connection: sqlite3.Connection, name: str) -> Level | None:
    """The level a recorded clade sits at, or None when it is not recorded."""
    row = connection.execute("SELECT level FROM clades WHERE name = ?", (name,)).fetchone()
    return None if row is None else Level(row["level"])


def _exists(connection: sqlite3.Connection, name: str) -> bool:
    """Whether a clade is already recorded."""
    return connection.execute("SELECT 1 FROM clades WHERE name = ?", (name,)).fetchone() is not None


def _check_chain(connection: sqlite3.Connection, new: NewClade) -> Level | None:
    """Check the two things the server does not trust the client about.

    Every step of the chain must go to a strictly broader level — levels may be skipped but never
    repeat or invert — and `parent` must already exist. A `parent` that does not means the client
    stopped walking early.

    Returns:
        The parent's level, or None when the chain tops out at a root.

    Raises:
        ApiError: 400 when a step is not strictly broader, or `parent` is not recorded.
    """
    parent_level: Level | None = None
    if new.parent is not None:
        parent_level = _level_of(connection, new.parent)
        if parent_level is None:
            raise bad_request(f"parent {new.parent!r} does not exist")

    steps: list[tuple[str, Level]] = [(new.name, new.level)]
    steps += [(a.name, a.level) for a in new.new_ancestors]
    if new.parent is not None and parent_level is not None:
        steps.append((new.parent, parent_level))

    for (child_name, child_level), (parent_name, level) in pairwise(steps):
        if not level.is_broader_than(child_level):
            raise bad_request(
                f"{parent_name!r} ({level}) is not strictly broader than "
                f"{child_name!r} ({child_level})"
            )
    return parent_level


def _insert_clade(
    connection: sqlite3.Connection, name: str, level: Level, common_name: str | None
) -> None:
    """Write one `clades` row, refusing to mint a clade that is already there."""
    if _exists(connection, name):
        raise conflict(f"clade {name!r} already exists")
    connection.execute(
        "INSERT INTO clades (name, common_name, level) VALUES (?, ?, ?)",
        (name, common_name, str(level)),
    )


def resolve_clade(connection: sqlite3.Connection, ref: str | NewClade) -> str:
    """Turn a reference-or-object into the name of a recorded clade.

    A bare name means reuse and must already exist; an object means create, along with every
    ancestor the walk found missing and the parent edges joining them.

    Raises:
        ApiError: 400 for a bare name that is not recorded or a chain that is not strictly
            broadening, 409 for creating a clade that already exists.
    """
    if isinstance(ref, str):
        if not _exists(connection, ref):
            raise bad_request(f"clade {ref!r} does not exist")
        return ref

    _check_chain(connection, ref)

    _insert_clade(connection, ref.name, ref.level, ref.common_name)
    for ancestor in ref.new_ancestors:
        _insert_clade(connection, ancestor.name, ancestor.level, None)

    links = [ref.name, *[a.name for a in ref.new_ancestors]]
    if ref.parent is not None:
        links.append(ref.parent)
    for child, parent in pairwise(links):
        connection.execute(
            "INSERT INTO clade_parent_edges (name, parent) VALUES (?, ?)", (child, parent)
        )
    return ref.name


def resolve_source(connection: sqlite3.Connection, ref: int | NewSource) -> int:
    """Turn a reference-or-object into the `src` of a recorded source.

    Raises:
        ApiError: 400 when a bare `src` is not recorded.
    """
    if isinstance(ref, int):
        row = connection.execute("SELECT 1 FROM sources WHERE src = ?", (ref,)).fetchone()
        if row is None:
            raise bad_request(f"source {ref} does not exist")
        return ref
    cursor = connection.execute(
        "INSERT INTO sources (author, year, title) VALUES (?, ?, ?)",
        (ref.author, ref.year, ref.title),
    )
    assert cursor.lastrowid is not None
    return cursor.lastrowid


def enter_character(connection: sqlite3.Connection, entry: CharacterEntry) -> CharacterCreated:
    """Write a character, its clade and source if new, and both of its edges.

    New edges start at `sessions_since_last_failed = 0`, so each is certain to be drawn the next
    time its game is generated.
    """
    name = resolve_clade(connection, entry.clade)
    src = resolve_source(connection, entry.source)
    cursor = connection.execute("INSERT INTO characters (text) VALUES (?)", (entry.text,))
    assert cursor.lastrowid is not None
    char_id = cursor.lastrowid
    connection.execute(
        "INSERT INTO clade_character_edges (name, char_id) VALUES (?, ?)", (name, char_id)
    )
    connection.execute(
        "INSERT INTO character_src_edges (char_id, src) VALUES (?, ?)", (char_id, src)
    )
    return CharacterCreated(clade=name, source=src, char_id=char_id)


def enter_image(connection: sqlite3.Connection, body: ImageEntryBody, img_id: str) -> ImageCreated:
    """Write an image, its clade and source if new, and both of its edges.

    The bytes are already normalised to WebP and on disk under `img_id` — see api.fish.images.
    """
    name = resolve_clade(connection, body.clade)
    src = resolve_source(connection, body.source)
    connection.execute("INSERT INTO images (img_id, img) VALUES (?, ?)", (img_id, f"{img_id}.webp"))
    connection.execute("INSERT INTO clade_image_edges (name, img_id) VALUES (?, ?)", (name, img_id))
    connection.execute("INSERT INTO image_src_edges (img_id, src) VALUES (?, ?)", (img_id, src))
    return ImageCreated(clade=name, source=src, img_id=img_id)
