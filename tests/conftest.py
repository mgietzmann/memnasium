"""The corpus fixture, and a real database for every test.

design/standards/Tests.md: never mock the database, always stub Claude.
"""

import sqlite3
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api import models, routes, store
from api.db import connect, create_schema
from api.main import app


@dataclass
class Corpus:
    """The ids of the fixture corpus in design/standards/Tests.md."""

    riddell: int
    duffy: int
    piscivory: int
    nearshore: int
    note1: int
    note2: int
    note3: int
    note4: int
    note5: int
    p1: int  # note1 in piscivory
    p2: int  # note2 in piscivory  — two pairs
    p3: int  # note2 in nearshore  — the same note, a second placement
    p4: int  # note3 in nearshore
    p5: int  # note4 on the roll
    pair_a: int
    pair_b: int
    pair_c: int
    pair_d: int
    pair_e: int
    pair_f: int


@pytest.fixture
def db(tmp_path: Path) -> Iterator[sqlite3.Connection]:
    """A real file, real schema, real transactions."""
    conn = connect(tmp_path / "memnasium.db")
    create_schema(conn)
    try:
        yield conn
    finally:
        conn.close()


@pytest.fixture
def corpus(db: sqlite3.Connection) -> Corpus:
    """One small corpus with the awkward cases baked in."""
    riddell = store.create_source(
        db, models.SourceCreate(author="Riddell", year=2018, publication="Chinook in SE Alaska")
    ).id
    duffy = store.create_source(db, models.SourceCreate(author="Duffy", year=2010)).id

    def note(source_id: int, statement: str) -> int:
        return store.create_note(db, models.NoteCreate(source_id=source_id, statement=statement)).id

    note1 = note(riddell, "Yukon Chinook transition in freshwater at 85-90 mm")
    note2 = note(duffy, "Puget Sound: piscivory at $70$ mm inshore, 130 mm offshore")
    note3 = note(riddell, "Nearshore residence lasts 30-60 d")
    note4 = note(duffy, "Trawl surveys underestimate juvenile abundance nearshore")
    note5 = note(riddell, "River outflow reverses under wind stress")

    piscivory = store.create_group(
        db,
        models.GroupCreate(
            name="Onset of piscivory", description="Regional length thresholds for piscivory"
        ),
    ).id
    nearshore = store.create_group(
        db,
        models.GroupCreate(
            name="Nearshore residence", description="How long juveniles hold in the nearshore"
        ),
    ).id

    placements = store.place_notes(
        db,
        [
            models.PlacementRequest(note_id=note1, group_id=piscivory),
            models.PlacementRequest(note_id=note2, group_id=piscivory),
            models.PlacementRequest(note_id=note2, group_id=nearshore),
            models.PlacementRequest(note_id=note3, group_id=nearshore),
            models.PlacementRequest(note_id=note4, group_id=None),
        ],
    )
    p1, p2, p3, p4, p5 = (p.id for p in placements)

    def pairs(placement_id: int, *qa: tuple[str, str]) -> list[int]:
        written = store.write_pairs(
            db,
            placement_id,
            [models.PairWrite(question=q, answer=a) for q, a in qa],
        )
        return [p.id for p in written]

    (pair_a,) = pairs(p1, ("Yukon, freshwater?", "85-90 mm"))
    pair_b, pair_c = pairs(
        p2, ("Puget Sound, inshore?", "70 mm"), ("Puget Sound, offshore?", "130 mm")
    )
    (pair_d,) = pairs(p3, ("Puget Sound, how long inshore?", "weeks"))
    (pair_e,) = pairs(p4, ("Nearshore residence, how long?", "30-60 d"))
    (pair_f,) = pairs(p5, ("What do trawl surveys miss?", "Juveniles nearshore"))

    return Corpus(
        riddell=riddell,
        duffy=duffy,
        piscivory=piscivory,
        nearshore=nearshore,
        note1=note1,
        note2=note2,
        note3=note3,
        note4=note4,
        note5=note5,
        p1=p1,
        p2=p2,
        p3=p3,
        p4=p4,
        p5=p5,
        pair_a=pair_a,
        pair_b=pair_b,
        pair_c=pair_c,
        pair_d=pair_d,
        pair_e=pair_e,
        pair_f=pair_f,
    )


@pytest.fixture
def client(db: sqlite3.Connection) -> Iterator[TestClient]:
    """A `TestClient` wired to the test database. Claude is never reached."""
    app.dependency_overrides[routes.get_conn] = lambda: db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def draw_all(db: sqlite3.Connection, day: str | None = None) -> None:
    """Build a draw that certainly includes every live pair. Today's by default.

    The dates are relative to the clock rather than fixed, because everything but
    `confirm` reads today — see design/Data.md#the-draw.
    """
    store.build_draw(db, day or store.today(), rng=lambda: 0.0)


def days_ago(n: int) -> str:
    """An ISO date `n` days before today."""
    return (date.fromisoformat(store.today()) - timedelta(days=n)).isoformat()
