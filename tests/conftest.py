"""Fixtures every test shares — design/standards/Tests.md.

The database is always a real temporary file built from the same `schema.sql` the app uses.
No mocks, no fakes, no in-memory substitute: the queries *are* the logic.
"""

import sqlite3
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api import paths
from api.db import connect, create_schema
from api.deps import get_connection
from api.main import app


@pytest.fixture
def db(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """A real file, real schema, real transactions."""
    connection = connect(tmp_path / "test.db")
    create_schema(connection)
    try:
        yield connection
    finally:
        connection.close()


@pytest.fixture
def images_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Stored images go under the test's own directory, never `data/images`."""
    directory = tmp_path / "images"
    directory.mkdir()
    monkeypatch.setattr(paths, "IMAGES_DIR", directory)
    return directory


@pytest.fixture
def client(db: sqlite3.Connection, images_dir: Path) -> Iterator[TestClient]:
    """A TestClient talking to the temporary database."""
    _ = images_dir
    app.dependency_overrides[get_connection] = lambda: db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


# ─────────────────────────────────────────────────────── the shared taxonomy fixture

CLADES: tuple[tuple[str, str | None, str], ...] = (
    ("Perciformes", None, "order"),
    ("Artificialidae", None, "family"),
    ("Artificialus", None, "genus"),
    ("Artificialus claudus", "spotted claudfish", "species"),
    ("Artificialus opus", None, "species"),
    ("Artificialus borealis", None, "species"),
    ("Artificialoides", None, "genus"),
    ("Artificialoides minor", "spotted claudperch", "species"),
    ("Miniformes", None, "order"),
    ("Minimidae", None, "family"),
    ("Minimus parvus", None, "species"),
)

PARENTS: tuple[tuple[str, str], ...] = (
    ("Artificialidae", "Perciformes"),
    ("Artificialus", "Artificialidae"),
    ("Artificialus claudus", "Artificialus"),
    ("Artificialus opus", "Artificialus"),
    ("Artificialus borealis", "Artificialidae"),  # the genus is skipped
    ("Artificialoides", "Artificialidae"),
    ("Artificialoides minor", "Artificialoides"),
    ("Minimidae", "Miniformes"),  # a second root: nothing here reaches Perciformes
    ("Minimus parvus", "Minimidae"),
)

SOURCES: tuple[tuple[int, str, int, str], ...] = (
    (17, "Brown", 2014, "Spines of the Artificialidae"),
    (22, "Okafor", 2021, "A revision of Artificialus"),
    (31, "Miller", 2019, "Caudal blotches in reef fishes"),
)


@pytest.fixture
def taxonomy(db: sqlite3.Connection) -> sqlite3.Connection:
    """One small tree with the awkward cases baked in, so they are always in play.

    A skipped genus and a second root are always present, so a test never has to remember to
    include them. Distances match the worked example in design/games/Kin.md.
    """
    db.executemany("INSERT INTO clades (name, common_name, level) VALUES (?, ?, ?)", CLADES)
    db.executemany("INSERT INTO clade_parent_edges (name, parent) VALUES (?, ?)", PARENTS)
    db.executemany("INSERT INTO sources (src, author, year, title) VALUES (?, ?, ?, ?)", SOURCES)
    return db


IMAGES: tuple[tuple[str, str, int], ...] = (
    # img_id, the clade it pictures, its source
    ("img_claudus", "Artificialus claudus", 17),
    ("img_opus", "Artificialus opus", 22),
    ("img_borealis", "Artificialus borealis", 31),
    ("img_minor", "Artificialoides minor", 17),
    ("img_shared", "Artificialus", 31),  # also edged to a species below
)

CHARACTERS: tuple[tuple[int, str, str, int], ...] = (
    # char_id, text, the clade it tells, its source
    (1, "three dorsal spines", "Artificialus claudus", 17),
    (2, "black caudal blotch", "Artificialus opus", 31),
    (3, "pale flank", "Artificialus borealis", 22),
    (4, "forked caudal fin", "Artificialoides minor", 17),
    (5, "one dorsal spine", "Minimus parvus", 22),
)


@pytest.fixture
def stocked(taxonomy: sqlite3.Connection) -> sqlite3.Connection:
    """The taxonomy with images and characters hung off it, so Kin has something to draw.

    `img_shared` pictures both a genus and a species, which is the case design/data/Kin.md
    exists to handle: one `image_src` edge turning up on two boards.
    """
    db = taxonomy
    for img_id, name, src in IMAGES:
        db.execute("INSERT INTO images (img_id, img) VALUES (?, ?)", (img_id, f"{img_id}.webp"))
        db.execute("INSERT INTO clade_image_edges (name, img_id) VALUES (?, ?)", (name, img_id))
        db.execute("INSERT INTO image_src_edges (img_id, src) VALUES (?, ?)", (img_id, src))
    db.execute(
        "INSERT INTO clade_image_edges (name, img_id) VALUES ('Artificialus claudus', 'img_shared')"
    )
    for char_id, text, name, src in CHARACTERS:
        db.execute("INSERT INTO characters (char_id, text) VALUES (?, ?)", (char_id, text))
        db.execute(
            "INSERT INTO clade_character_edges (name, char_id) VALUES (?, ?)", (name, char_id)
        )
        db.execute("INSERT INTO character_src_edges (char_id, src) VALUES (?, ?)", (char_id, src))
    return db


def never_drawn(db: sqlite3.Connection, table: str, **where: object) -> None:
    """Push an edge's counter far enough out that its draw is a certainty against."""
    clause = " AND ".join(f"{k} = ?" for k in where)
    db.execute(
        f"UPDATE {table} SET sessions_since_last_failed = 100 WHERE {clause}",
        tuple(where.values()),
    )
