"""Placements, the roll, and moves — design/Data.md, design/flows/Regrouping.md."""

import sqlite3

import pytest

from api import models, store
from tests.conftest import Corpus


def test_a_note_with_a_group_never_holds_a_roll_placement(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    # Data.md#decisions
    with pytest.raises(store.RefusedError):
        store.place_notes(db, [models.PlacementRequest(note_id=corpus.note1, group_id=None)])


def test_a_roll_note_is_promoted_by_a_move_not_a_second_placement(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    # Data.md#decisions
    with pytest.raises(store.RefusedError):
        store.place_notes(
            db, [models.PlacementRequest(note_id=corpus.note4, group_id=corpus.piscivory)]
        )
    moved = store.move_placement(db, corpus.p5, models.PlacementMove(group_id=corpus.piscivory))
    assert moved.group_id == corpus.piscivory


def test_a_second_placement_into_the_same_group_is_refused(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    # api/API.md#errors — UNIQUE (note_id, group_id), on POST and on a move
    with pytest.raises(store.RefusedError):
        store.place_notes(
            db, [models.PlacementRequest(note_id=corpus.note1, group_id=corpus.piscivory)]
        )
    with pytest.raises(store.RefusedError):
        store.move_placement(db, corpus.p3, models.PlacementMove(group_id=corpus.piscivory))


def test_a_batch_of_placements_is_all_or_nothing(db: sqlite3.Connection, corpus: Corpus) -> None:
    before = len(store.list_notes(db, group_id=corpus.piscivory))
    with pytest.raises(store.RefusedError):
        store.place_notes(
            db,
            [
                models.PlacementRequest(note_id=corpus.note5, group_id=corpus.piscivory),
                models.PlacementRequest(note_id=corpus.note1, group_id=corpus.piscivory),
            ],
        )
    assert len(store.list_notes(db, group_id=corpus.piscivory)) == before


def test_a_moved_placement_flags_its_pairs_stale(db: sqlite3.Connection, corpus: Corpus) -> None:
    # flows/Regrouping.md#moving-placements
    moved = store.move_placement(db, corpus.p1, models.PlacementMove(group_id=corpus.nearshore))
    assert moved.pairs_stale is True


def test_a_moved_placement_keeps_its_sessions_correct(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    # flows/Regrouping.md — the memory was real even if the wording needs redoing
    db.execute("UPDATE recall_pair SET sessions_correct = 4 WHERE id = ?", (corpus.pair_a,))
    store.move_placement(db, corpus.p1, models.PlacementMove(group_id=corpus.nearshore))
    row = db.execute(
        "SELECT sessions_correct FROM recall_pair WHERE id = ?", (corpus.pair_a,)
    ).fetchone()
    assert row["sessions_correct"] == 4


def test_a_group_emptied_by_a_move_is_deleted(db: sqlite3.Connection, corpus: Corpus) -> None:
    # Data.md#decisions — the one thing in the schema that goes away
    thresholds = store.create_group(
        db, models.GroupCreate(name="Thresholds", description="Every length threshold")
    ).id
    store.move_placement(db, corpus.p1, models.PlacementMove(group_id=thresholds))
    assert store.get_group(db, corpus.piscivory).note_count == 1
    store.move_placement(db, corpus.p2, models.PlacementMove(group_id=thresholds))
    with pytest.raises(store.NotFoundError):
        store.get_group(db, corpus.piscivory)


def test_the_wordsmithing_queue_is_pairless_or_stale_placements(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    # flows/Wordsmithing.md#the-queue
    assert store.list_pending_placements(db) == []
    store.place_notes(
        db, [models.PlacementRequest(note_id=corpus.note5, group_id=corpus.piscivory)]
    )
    store.move_placement(db, corpus.p1, models.PlacementMove(group_id=corpus.nearshore))
    pending = {p.placement.id for p in store.list_pending_placements(db)}
    assert corpus.p1 in pending
    assert len(pending) == 2


def test_a_pending_placement_carries_what_claude_reads(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    # flows/Wordsmithing.md#what-claude-reads
    store.place_notes(
        db, [models.PlacementRequest(note_id=corpus.note5, group_id=corpus.piscivory)]
    )
    (pending,) = [p for p in store.list_pending_placements(db) if p.note.id == corpus.note5]
    assert pending.group is not None and pending.group.id == corpus.piscivory
    assert {n.id for n in pending.group_notes} == {corpus.note1, corpus.note2}
    assert {p.id for p in pending.group_pairs} == {corpus.pair_a, corpus.pair_b, corpus.pair_c}


def test_a_move_into_the_group_it_already_sits_in_changes_nothing(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    # flows/Regrouping.md — a move flags pairs stale; this is not a move
    before = store.get_placement(db, corpus.p1)
    after = store.move_placement(db, corpus.p1, models.PlacementMove(group_id=corpus.piscivory))
    assert after == before
    assert after.pairs_stale is False
    assert store.list_pending_placements(db) == []
