"""The endpoints of design/api/Fish.md: finding what is recorded, and adding what was read."""

import json
import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from fastapi.responses import FileResponse
from pydantic import ValidationError

from api import paths
from api.db import transaction
from api.deps import get_connection
from api.errors import bad_request, not_found
from api.fish import store
from api.fish.images import store_image
from api.fish.models import (
    CharacterCreated,
    CharacterEntry,
    CladeDetail,
    CladeResult,
    ImageCreated,
    ImageEntryBody,
    SourceResult,
)
from api.fish.search import citation, search_clades, search_sources
from api.levels import Level

router = APIRouter(prefix="/api/fish", tags=["fish"])

Connection = Annotated[sqlite3.Connection, Depends(get_connection)]


@router.get("/clades")
def get_clades(
    connection: Connection,
    q: Annotated[str, Query()] = "",
    level: Annotated[Level | None, Query()] = None,
) -> list[CladeResult]:
    """Search clades by scientific and common name, optionally at one level."""
    matched = search_clades(store.all_clades(connection), q, None if level is None else str(level))
    return [
        CladeResult(name=row.name, common_name=row.common_name, level=Level(row.level))
        for row in matched
    ]


@router.get("/clades/{name}")
def get_clade(connection: Connection, name: str) -> CladeDetail:
    """One clade and its ancestors. A `404` is the walk's signal that the clade is new."""
    return store.clade_detail(connection, name)


@router.get("/sources")
def get_sources(connection: Connection, q: Annotated[str, Query()] = "") -> list[SourceResult]:
    """Search sources by author prefix, year, or a substring of the title."""
    return [
        SourceResult(
            src=row.src,
            author=row.author,
            year=row.year,
            title=row.title,
            label=citation(row.author, row.year),
        )
        for row in search_sources(store.all_sources(connection), q)
    ]


@router.post("/characters", status_code=201)
def post_character(connection: Connection, entry: CharacterEntry) -> CharacterCreated:
    """Enter a character: one transaction writing the clade chain, the source, and both edges.

    The response is what the next submission should send, which is how the sticky form stops
    creating and starts referring.
    """
    with transaction(connection):
        return store.enter_character(connection, entry)


@router.post("/images", status_code=201)
async def post_image(
    connection: Connection,
    json_part: Annotated[str, Form(alias="json")],
    image: Annotated[UploadFile, File()],
) -> ImageCreated:
    """Enter an image: the same body as a character, with the file in place of the text.

    Any common format is accepted; the server scales it and stores WebP.
    """
    try:
        body = ImageEntryBody.model_validate(json.loads(json_part))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise bad_request(f"malformed json part: {exc}") from exc

    img_id = store_image(await image.read())
    with transaction(connection):
        return store.enter_image(connection, body, img_id)


@router.get("/images/{img_id}", response_class=FileResponse)
def get_image(img_id: str) -> FileResponse:
    """Serve a stored image. This is what a Kin board's image cards point at."""
    path = paths.image_path(img_id)
    if not path.is_file():
        raise not_found(f"no image {img_id!r}")
    return FileResponse(path, media_type="image/webp")
