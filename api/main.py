"""The one process. It serves `/api` and the built app off the same origin.

No CORS, no second port — design/Stack.md.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api.fish.routes import router as fish_router
from api.kin.routes import router as kin_router
from api.paths import DIST_DIR

app = FastAPI(title="memnasium", version="0.1.0")


@app.exception_handler(RequestValidationError)
async def malformed_request(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Answer a malformed body with `400`, the status the design docs table.

    A level outside the enum and a submission with slots missing are both listed as `400`, so
    FastAPI's default `422` is replaced wholesale rather than in two places.
    """
    return JSONResponse(status_code=400, content={"detail": jsonable(exc.errors())})


def jsonable(errors: Any) -> Any:
    """Strip the exception objects Pydantic puts in `ctx`, which do not serialise."""
    if isinstance(errors, list):
        return [jsonable(e) for e in errors]
    if isinstance(errors, dict):
        return {k: jsonable(v) for k, v in errors.items() if k != "ctx"}
    if isinstance(errors, (str, int, float, bool)) or errors is None:
        return errors
    return str(errors)


app.include_router(fish_router)
app.include_router(kin_router)

if DIST_DIR.is_dir():
    app.mount("/", StaticFiles(directory=DIST_DIR, html=True), name="app")
