"""Backup and restore, with no prerequisite beyond uv.

Git is the backup, so nothing binary that changes may be committed: the dump is
what is versioned and `data/memnasium.db` is rebuilt from it — see
design/Stack.md#backup.
"""

import sys

from api.config import ROOT, db_path
from api.db import connect, create_schema

DUMP = ROOT / "data" / "memnasium.sql"


def backup() -> None:
    """Dump the live database to `data/memnasium.sql`, ready to commit."""
    conn = connect()
    try:
        DUMP.parent.mkdir(parents=True, exist_ok=True)
        DUMP.write_text("\n".join(conn.iterdump()) + "\n")
    finally:
        conn.close()


def restore() -> None:
    """Rebuild `data/memnasium.db` from the dump, or from the schema if there is none."""
    target = db_path()
    if target.exists():
        return
    conn = connect(target)
    try:
        if DUMP.exists():
            conn.executescript(DUMP.read_text())
        create_schema(conn)
    finally:
        conn.close()


def main() -> None:
    """Run `backup` or `restore`, named by the first argument."""
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action == "backup":
        backup()
    elif action == "restore":
        restore()
    else:
        raise SystemExit("usage: db.py [backup|restore]")


if __name__ == "__main__":
    main()
