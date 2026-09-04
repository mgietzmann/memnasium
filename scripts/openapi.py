"""Dump the OpenAPI schema the app's TypeScript types are generated from.

design/standards/Code.md#one-definition-of-a-payload: a payload is written once,
as a Pydantic model, and the client's types come from the schema it produces.
"""

import json
import sys
from pathlib import Path

from api.main import app


def main() -> None:
    """Write `openapi.json` to the path given, or to stdout."""
    schema = json.dumps(app.openapi(), indent=2, sort_keys=True)
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(schema + "\n")
    else:
        sys.stdout.write(schema)


if __name__ == "__main__":
    main()
