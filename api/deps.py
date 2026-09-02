"""The one dependency every route has: an open database connection.

SQLite is a file, so there is no pool — a connection per request, closed after it. Tests swap
this for one pointing at a temporary file (design/standards/Tests.md).
"""

import sqlite3
from collections.abc import Iterator

from api.db import connect


def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a connection to the live database, closed when the request ends."""
    connection = connect()
    try:
        yield connection
    finally:
        connection.close()
