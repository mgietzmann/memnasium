"""Rebuild `data/memnasium.db`.

Git holds the dump and the images, never the database file (design/Stack.md). This restores
from the dump when there is one and from `schema.sql` when there is not — a fresh clone of a
repository nobody has played yet has no dump.
"""

import sqlite3
import subprocess

from api.db import create_schema
from api.paths import DB_PATH, DUMP_PATH, IMAGES_DIR


def restore() -> None:
    """Create the database file if it is missing, from the dump or from the schema."""
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        return
    if DUMP_PATH.exists():
        subprocess.run(
            ["sqlite3", str(DB_PATH)],
            input=DUMP_PATH.read_text(),
            text=True,
            check=True,
        )
        return
    connection = sqlite3.connect(DB_PATH)
    try:
        create_schema(connection)
        connection.commit()
    finally:
        connection.close()


if __name__ == "__main__":
    restore()
