"""The payloads of design/api/Kin.md, defined once.

Play `edge_id`s are unique only within their own table, so a slot travels as a **handle** built
from the kind and the id — `ci-41`, `cc-7`, `is-19`, `cs-88`. Derived, never stored, and
identical across requests and restarts, so a resumed board hands back the same handles.
"""

from typing import Literal

from pydantic import BaseModel

SlotState = Literal["due", "locked"]
Result = Literal["correct", "wrong"]


class KinState(BaseModel):
    """What the games-list card shows.

    `generated_on` is null when no set exists. Together with `anchors_left` it is everything the
    card needs: a spent set drawn today reads *done for today*, the same set read tomorrow reads
    *not generated*.
    """

    generated_on: str | None
    anchors_total: int
    anchors_left: int
    open_board: bool


class Slot(BaseModel):
    """One blank on a card.

    `due` is blank and the player fills it; `locked` is shown filled and is not editable.
    `value` is a clade name on a clade slot and a `src` on a source slot, and is null while the
    slot is live — the right answer is never returned to a board still being played.
    """

    slot: str
    state: SlotState
    value: str | int | None


class Card(BaseModel):
    """One image or one character, with a clade slot above it and a source slot below."""

    kind: Literal["image", "character"]
    img_id: str | None = None
    text: str | None = None
    clade: Slot
    src: Slot


class PaletteClade(BaseModel):
    """A chip in the clade palette: the group's anchors, and nothing else."""

    name: str
    common_name: str | None


class Citation(BaseModel):
    """A chip in the citation pool, holding only the sources behind due `src` slots."""

    src: int
    label: str


class Board(BaseModel):
    """One round: a group, its cards, and the two palettes.

    Every card of every anchor comes down, prefilled where the edge was not drawn — most of a
    board is `locked`.
    """

    board_id: int
    level: str
    ended: bool
    scored: bool
    clades: list[PaletteClade]
    citations: list[Citation]
    cards: list[Card]
    labels: dict[int, str]
    """Every source shown on the board, by `src`.

    `citations` is the pool and holds only the sources behind due slots, but a *prefilled* source
    slot shows its true value too — and a `src` is a number, not something a player can read. This
    is what lets a locked slot render `Brown, 2014`. It is not the pool and must never be drawn
    as chips.
    """


class DealRequest(BaseModel):
    """`size` is a maximum. A short group comes back short."""

    size: int


class SubmitRequest(BaseModel):
    """Every due slot at once — a slot only becomes an answer at submission."""

    slots: dict[str, str | int]


class SubmitResponse(BaseModel):
    """What one submission did.

    `scored` is true only on the first submission, the one that moves
    `sessions_since_last_failed`. `complete` true means every slot is locked and the board is
    finished.
    """

    results: dict[str, Result]
    complete: bool
    scored: bool
