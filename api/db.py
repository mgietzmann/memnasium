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
    _rekey_draw(conn)
    conn.executescript(SCHEMA.read_text())


def _rekey_draw(conn: sqlite3.Connection) -> None:
    """Drop a `draw` table still keyed on `(day, recall_pair_id)`.

    The table is rekeyed on `recall_pair_id` rather than migrated: its rows are
    stranded at worst and swept by the next build, so there is nothing to carry
    across — see design/Data.md#the-expectation. `CREATE TABLE IF NOT EXISTS`
    would leave the old shape in place forever, and `confirm` rests on the new
    key, so the old one is dropped here first.
    """
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'draw'"
    ).fetchone()
    if row is not None and "recall_pair_id INTEGER PRIMARY KEY" not in row["sql"]:
        conn.execute("DROP TABLE draw")


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
