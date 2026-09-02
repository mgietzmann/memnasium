"""The errors the API answers with.

Each status is one of the cases tabled in design/api/Fish.md and design/api/Kin.md; the message
is for the developer, since the app never shows a raw error to the player.
"""

from fastapi import HTTPException


class ApiError(HTTPException):
    """A refusal with a status the design docs name."""


def not_found(detail: str) -> ApiError:
    """The resource is not there — which is also the walk's signal that a clade is new."""
    return ApiError(status_code=404, detail=detail)


def conflict(detail: str) -> ApiError:
    """The request contradicts what is already recorded."""
    return ApiError(status_code=409, detail=detail)


def bad_request(detail: str) -> ApiError:
    """The request is malformed or refers to something that does not exist."""
    return ApiError(status_code=400, detail=detail)


def inconsistent_data(detail: str) -> ApiError:
    """What is stored contradicts the model, so no correct answer can be given.

    Corrections are made against the database by hand (design/app/Fish.md), which is exactly how
    a fact can end up without the source design/data/Fish.md says every fact carries. Saying so
    beats quietly serving a board with the card missing.
    """
    return ApiError(status_code=500, detail=detail)
