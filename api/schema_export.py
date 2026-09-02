"""`make types`: print the OpenAPI schema the app's TypeScript types are generated from.

A payload is defined once, as a Pydantic model — design/standards/Code.md.
"""

import json

from api.main import app


def main() -> None:
    """Write the schema to stdout."""
    print(json.dumps(app.openapi(), indent=2))


if __name__ == "__main__":
    main()
