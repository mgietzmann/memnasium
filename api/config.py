"""Settings with exactly one home each.

Everything tunable lives here so that changing a model or the scheduling
constant is a one-line edit rather than a search.
"""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: The scheduling constant from design/Data.md#background: `p = e^(-alpha * n)`.
ALPHA = 0.5

#: The grading model — design/Claude.md#stack.
MODEL_ID = "claude-opus-5"

#: `max_tokens` for one grade call is `GRADE_BASE + GRADE_PER_PAIR * n`, sized to
#: carry the thinking tokens as well as the visible result.
GRADE_BASE = 1024
GRADE_PER_PAIR = 400


def db_path() -> Path:
    """Where the live database sits.

    Returns:
        `data/memnasium.db` under the repository root, unless `MEMNASIUM_DB`
        overrides it — which is what the tests use.
    """
    override = os.environ.get("MEMNASIUM_DB")
    return Path(override) if override else ROOT / "data" / "memnasium.db"


def app_dist() -> Path:
    """Where the built app is served from."""
    return ROOT / "app" / "dist"
