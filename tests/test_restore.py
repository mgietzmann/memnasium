"""A fresh clone must be able to work — design/Stack.md#backup."""

import sqlite3
from pathlib import Path

import pytest

from api.db import connect
from scripts import db as script


def test_the_committed_dump_restores(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """`make restore` on a fresh clone, against the dump that is actually committed.

    `iterdump` writes the tables in name order, so every reference in the dump is
    forward at the moment it is made — with foreign keys on, `note` fails on a
    `source` table that does not exist yet.
    """
    target = tmp_path / "memnasium.db"
    monkeypatch.setattr(script, "db_path", lambda: target)
    script.restore()

    conn = connect(target)
    try:
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        # The schema is whole and the rows came with it.
        assert conn.execute("SELECT COUNT(*) AS n FROM source").fetchone()["n"] > 0
        assert conn.execute("SELECT COUNT(*) AS n FROM recall_pair").fetchone()["n"] > 0
        # And it is the rekeyed draw table — design/Data.md#the-draw.
        sql = conn.execute("SELECT sql FROM sqlite_master WHERE name = 'draw'").fetchone()["sql"]
        assert "recall_pair_id INTEGER PRIMARY KEY" in sql
    finally:
        conn.close()


def test_restore_leaves_no_database_behind_when_the_dump_is_broken(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Or the next `make restore` would be a silent no-op on a half-built file."""
    dump = tmp_path / "broken.sql"
    dump.write_text(
        "CREATE TABLE source (id INTEGER PRIMARY KEY);\n"
        "CREATE TABLE note (id INTEGER PRIMARY KEY,"
        " source_id INTEGER NOT NULL REFERENCES source(id));\n"
        "INSERT INTO note VALUES (1, 99);\n"
    )
    target = tmp_path / "memnasium.db"
    monkeypatch.setattr(script, "db_path", lambda: target)
    monkeypatch.setattr(script, "DUMP", dump)
    with pytest.raises(SystemExit):
        script.restore()
    assert not target.exists()


def test_restore_does_nothing_when_the_database_is_already_there(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The live database is never overwritten by a restore."""
    target = tmp_path / "memnasium.db"
    conn = sqlite3.connect(target)
    conn.execute("CREATE TABLE mine (x INTEGER)")
    conn.close()
    monkeypatch.setattr(script, "db_path", lambda: target)
    script.restore()
    conn = connect(target)
    try:
        assert conn.execute("SELECT name FROM sqlite_master WHERE name = 'mine'").fetchone()
    finally:
        conn.close()
