"""Where memnasium keeps things on disk.

The layout is design/Project.md's; what is committed and what is rebuilt is design/Stack.md's.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "memnasium.db"
DUMP_PATH = DATA_DIR / "memnasium.sql"
IMAGES_DIR = DATA_DIR / "images"

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"
DIST_DIR = ROOT / "app" / "dist"


def image_path(img_id: str) -> Path:
    """Absolute path of a stored image.

    Args:
        img_id: The image's id, which is also its filename stem.
    """
    return IMAGES_DIR / f"{img_id}.webp"
