"""The endpoints of design/api/Kin.md: the day's set, a board, and the two ways it ends."""

import sqlite3
from typing import Annotated

from fastapi import APIRouter, Depends

from api.db import transaction
from api.deps import get_connection
from api.kin import store
from api.kin.models import Board, DealRequest, KinState, SubmitRequest, SubmitResponse

router = APIRouter(prefix="/api/kin", tags=["kin"])

Connection = Annotated[sqlite3.Connection, Depends(get_connection)]


@router.get("/state")
def get_state(connection: Connection) -> KinState:
    """What the games-list card shows."""
    return store.state(connection)


@router.post("/set")
def post_set(connection: Connection) -> KinState:
    """Generate the day's draw. Idempotent, and it honours carry-over."""
    with transaction(connection):
        return store.generate(connection)


@router.post("/board")
def post_board(connection: Connection, request: DealRequest) -> Board:
    """Deal a group. `size` is a maximum; a short group comes back short."""
    with transaction(connection):
        return store.deal(connection, request.size)


@router.get("/board")
def get_board(connection: Connection) -> Board:
    """The open board, which is how a board resumes after the app is closed."""
    return store.current_board(connection)


@router.post("/board/submit")
def post_submit(connection: Connection, request: SubmitRequest) -> SubmitResponse:
    """Answer the board. Correct slots lock; incorrect ones clear for another try."""
    with transaction(connection):
        return store.submit(connection, request.slots)


@router.post("/board/move-on")
def post_move_on(connection: Connection) -> Board:
    """Give the board up, and return it filled in — so giving up teaches the answer."""
    with transaction(connection):
        return store.move_on(connection)
