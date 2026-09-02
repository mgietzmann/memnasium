"""Opening the database.

SQLite is a file, so there is one connection factory and no pool. Every test gets a real
temporary file built from the same `schema.sql` the app uses — see design/standards/Tests.md.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from api.paths import DB_PATH, SCHEMA_PATH


def create_schema(connection: sqlite3.Connection) -> None:
    """Build every table and index from `schema.sql` into an empty database."""
    connection.executescript(SCHEMA_PATH.read_text())


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    """Open a connection with foreign keys on and rows that behave like mappings.

    Args:
        path: The database file. Created empty if it does not exist, without a schema —
            `api.restore` is what builds one.
    """
    # FastAPI runs sync routes on a threadpool, so the connection a request opens is used
    # off the thread that made it. One connection per request means nothing is shared.
    connection = sqlite3.connect(path, isolation_level=None, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def transaction(connection: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Run a block as one unit, so a failure half way leaves nothing behind.

    An entry writes a clade chain, a source, a node and two edges together — see
    design/api/Fish.md.
    """
    connection.execute("BEGIN")
    try:
        yield connection
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    connection.execute("COMMIT")
