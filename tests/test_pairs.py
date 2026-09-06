"""Writing a pair set — design/api/API.md#writing-a-pair-set."""

import sqlite3

import pytest

from api import models, store
from tests.conftest import Corpus, draw_all


def counts(db: sqlite3.Connection, placement_id: int) -> dict[int, int]:
    rows = db.execute(
        "SELECT id, sessions_correct FROM recall_pair WHERE placement_id = ? AND retired = 0",
        (placement_id,),
    ).fetchall()
    return {r["id"]: r["sessions_correct"] for r in rows}


def test_a_first_write_starts_every_pair_at_zero(db: sqlite3.Connection, corpus: Corpus) -> None:
    # flows/Wordsmithing.md#writes
    assert set(counts(db, corpus.p2).values()) == {0}


def test_a_reword_leaves_sessions_correct_alone(db: sqlite3.Connection, corpus: Corpus) -> None:
    db.execute("UPDATE recall_pair SET sessions_correct = 3 WHERE id = ?", (corpus.pair_b,))
    store.write_pairs(
        db,
        corpus.p2,
        [
            models.PairWrite(id=corpus.pair_b, question="reworded?", answer="70 mm"),
            models.PairWrite(id=corpus.pair_c, question="Puget Sound, offshore?", answer="130 mm"),
        ],
    )
    assert counts(db, corpus.p2)[corpus.pair_b] == 3


def test_a_split_pair_inherits_the_originals_count(db: sqlite3.Connection, corpus: Corpus) -> None:
    # flows/Wordsmithing.md#rewriting
    db.execute("UPDATE recall_pair SET sessions_correct = 5 WHERE id = ?", (corpus.pair_a,))
    written = store.write_pairs(
        db,
        corpus.p1,
        [
            models.PairWrite(id=corpus.pair_a, question="Yukon, freshwater?", answer="85-90 mm"),
            models.PairWrite(
                question="Yukon, where?", answer="freshwater", inherit_from=[corpus.pair_a]
            ),
        ],
    )
    assert [p.sessions_correct for p in written] == [5, 5]


def test_a_combined_pair_inherits_the_lower_count(db: sqlite3.Connection, corpus: Corpus) -> None:
    # flows/Wordsmithing.md#rewriting — the weaker memory is the honest description
    db.execute("UPDATE recall_pair SET sessions_correct = 6 WHERE id = ?", (corpus.pair_b,))
    db.execute("UPDATE recall_pair SET sessions_correct = 2 WHERE id = ?", (corpus.pair_c,))
    written = store.write_pairs(
        db,
        corpus.p2,
        [
            models.PairWrite(
                question="Puget Sound, inshore and offshore?",
                answer="70 mm and 130 mm",
                inherit_from=[corpus.pair_b, corpus.pair_c],
            )
        ],
    )
    assert [p.sessions_correct for p in written] == [2]
    assert {corpus.pair_b, corpus.pair_c}.isdisjoint({p.id for p in written})


def test_a_pair_dropped_from_the_set_is_retired_not_deleted(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    # Data.md#decisions — miss rows point at pairs forever
    store.write_pairs(
        db,
        corpus.p2,
        [models.PairWrite(id=corpus.pair_b, question="Puget Sound, inshore?", answer="70 mm")],
    )
    row = db.execute("SELECT retired FROM recall_pair WHERE id = ?", (corpus.pair_c,)).fetchone()
    assert row["retired"] == 1


def test_retiring_a_pair_drops_its_draw_row(db: sqlite3.Connection, corpus: Corpus) -> None:
    draw_all(db)
    store.write_pairs(
        db,
        corpus.p2,
        [models.PairWrite(id=corpus.pair_b, question="Puget Sound, inshore?", answer="70 mm")],
    )
    left = db.execute("SELECT 1 FROM draw WHERE recall_pair_id = ?", (corpus.pair_c,)).fetchone()
    assert left is None


def test_retiring_the_last_live_pair_is_refused(db: sqlite3.Connection, corpus: Corpus) -> None:
    # api/API.md#errors — it would re-enter the wordsmithing queue forever
    with pytest.raises(store.RefusedError):
        store.write_pairs(db, corpus.p1, [])


def test_a_pair_of_another_placement_cannot_be_named(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    with pytest.raises(store.RefusedError):
        store.write_pairs(
            db, corpus.p1, [models.PairWrite(id=corpus.pair_b, question="q", answer="a")]
        )


def test_a_retired_pair_is_absent_from_every_read(db: sqlite3.Connection, corpus: Corpus) -> None:
    # Data.md#recall-pairs
    store.write_pairs(
        db,
        corpus.p2,
        [models.PairWrite(id=corpus.pair_b, question="Puget Sound, inshore?", answer="70 mm")],
    )
    detail = store.get_group_detail(db, corpus.piscivory)
    assert corpus.pair_c not in {p.id for p in detail.pairs}
    assert detail.group.pair_count == 2
    draw_all(db)
    (board,) = [b for b in store.boards(db, 5) if b.group_id == corpus.piscivory]
    seen = {p.id for p in board.due} | {p.id for p in board.context}
    assert corpus.pair_c not in seen


def test_writing_a_pair_set_clears_the_stale_flag(db: sqlite3.Connection, corpus: Corpus) -> None:
    # flows/Wordsmithing.md#writes
    store.move_placement(db, corpus.p1, models.PlacementMove(group_id=corpus.nearshore))
    store.write_pairs(db, corpus.p1, [models.PairWrite(id=corpus.pair_a, question="q", answer="a")])
    assert store.get_placement(db, corpus.p1).pairs_stale is False


def test_a_pair_set_write_leaves_exactly_the_pairs_it_was_given(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    written = store.write_pairs(
        db,
        corpus.p2,
        [
            models.PairWrite(id=corpus.pair_c, question="offshore?", answer="130 mm"),
            models.PairWrite(question="new one?", answer="x"),
        ],
    )
    assert {p.question for p in written} == {"offshore?", "new one?"}
    assert set(counts(db, corpus.p2)) == {p.id for p in written}


def test_a_retired_pair_is_never_graded(db: sqlite3.Connection, corpus: Corpus) -> None:
    # Data.md#recall-pairs — retired is filtered by the pair select itself
    store.write_pairs(
        db,
        corpus.p2,
        [models.PairWrite(id=corpus.pair_b, question="Puget Sound, inshore?", answer="70 mm")],
    )
    with pytest.raises(store.NotFoundError):
        store.grade_inputs(
            db,
            [models.Answer(recall_pair_id=corpus.pair_c, user_answer="a", user_source="b")],
        )
