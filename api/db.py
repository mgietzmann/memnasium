"""Connections to the SQLite file, and the schema that shapes it."""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from api import config

SCHEMA = Path(__file__).resolve().parent / "schema.sql"


def connect(path: Path | None = None) -> sqlite3.Connection:
    """Open a connection with the settings every caller needs.

    Args:
        path: The database file. Defaults to `config.db_path()`.

    Returns:
        A connection with row access by name and foreign keys enforced.
    """
    target = path or config.db_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(target, isolation_level=None, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    """Apply `schema.sql` to a connection. Idempotent."""
    conn.executescript(SCHEMA.read_text())


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run a block as one unit, rolled back entirely if anything raises."""
    conn.execute("BEGIN")
    try:
        yield conn
    except BaseException:
        conn.execute("ROLLBACK")
        raise
    conn.execute("COMMIT")
