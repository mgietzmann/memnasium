"""One process: the API, the MCP endpoint, and the built app.

No CORS, no second port — see design/Stack.md#the-mcp-server.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from api import mcp, routes, store
from api.config import app_dist
from api.db import connect, create_schema

#: The MCP endpoint, over HTTP, in this same process — design/Stack.md#the-mcp-server.
mcp_app = mcp.server.streamable_http_app(streamable_http_path="/")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Make sure the schema exists, and run the MCP session manager.

    A mounted sub-app's lifespan is not run by the parent, so the MCP app's is
    entered here by hand.
    """
    conn = connect()
    try:
        create_schema(conn)
    finally:
        conn.close()
    async with mcp_app.router.lifespan_context(mcp_app):
        yield


app = FastAPI(title="memnasium", lifespan=lifespan)
app.include_router(routes.router)
app.mount("/mcp", mcp_app)


@app.exception_handler(store.StoreError)
async def store_error(request: Request, exc: Exception) -> JSONResponse:
    """Every refusal is a typed error with a reason, never a silent no-op."""
    status = 404 if isinstance(exc, store.NotFoundError) else 409
    code = exc.code if isinstance(exc, store.StoreError) else "refused"
    return JSONResponse(status_code=status, content={"code": code, "detail": str(exc)})


def mount_app() -> None:
    """Serve the built app from the same origin, if it has been built."""
    dist = app_dist()
    if dist.is_dir():
        app.mount("/", StaticFiles(directory=dist, html=True), name="app")


mount_app()
