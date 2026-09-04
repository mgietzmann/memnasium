"""The draw, boards, and confirm — design/flows/Drilling.md, design/Data.md."""

import math
import sqlite3

import pytest

from api import models, store
from api.config import ALPHA
from tests.conftest import Corpus, draw_all

DAY = "2026-09-03"


def test_a_new_pair_is_certain_to_be_drawn(db: sqlite3.Connection, corpus: Corpus) -> None:
    # Data.md#background — at sessions_correct 0, p = 1
    assert store.draw_probability(0) == 1.0
    summary = store.build_draw(db, DAY, rng=lambda: 0.999999)
    assert summary.due == 6


def test_the_draw_rate_approaches_the_probability(db: sqlite3.Connection, corpus: Corpus) -> None:
    # Tests.md#randomness — a distribution over many days, not one trial
    db.execute("UPDATE recall_pair SET sessions_correct = 4")
    import random

    rng = random.Random(1)
    hits = 0
    trials = 2000
    for _ in range(trials):
        if rng.random() < store.draw_probability(4):
            hits += 1
    assert abs(hits / trials - math.exp(-ALPHA * 4)) < 0.03


def test_building_the_draw_is_idempotent(db: sqlite3.Connection, corpus: Corpus) -> None:
    # flows/Drilling.md#building-the-draw
    first = store.build_draw(db, DAY, rng=lambda: 0.0)
    second = store.build_draw(db, DAY, rng=lambda: 1.0)
    assert first == second


def test_undrilled_draw_rows_are_swept_not_carried(db: sqlite3.Connection, corpus: Corpus) -> None:
    # Data.md#decisions — they were never sessions, so nothing is owed to them
    draw_all(db, "2026-09-02")
    store.build_draw(db, DAY, rng=lambda: 1.0)
    left = db.execute("SELECT COUNT(*) AS c FROM draw").fetchone()["c"]
    assert left == 0
    row = db.execute(
        "SELECT sessions_correct FROM recall_pair WHERE id = ?", (corpus.pair_a,)
    ).fetchone()
    assert row["sessions_correct"] == 0


def test_a_board_holds_every_pair_of_its_group_exactly_once(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    # flows/Drilling.md#a-board — partitioned into due and context
    db.execute("DELETE FROM draw")
    db.execute("INSERT INTO draw_day (day, drawn) VALUES (?, 1)", (DAY,))
    db.execute("INSERT INTO draw (day, recall_pair_id) VALUES (?, ?)", (DAY, corpus.pair_b))
    (board,) = store.boards(db, 5)
    assert board.group_id == corpus.piscivory
    assert [p.id for p in board.due] == [corpus.pair_b]
    assert {p.id for p in board.context} == {corpus.pair_a, corpus.pair_c}
    assert board.pair_count == 3


def test_no_pair_appears_on_two_boards_in_one_day(db: sqlite3.Connection, corpus: Corpus) -> None:
    draw_all(db, DAY)
    seen: list[int] = []
    for board in store.boards(db, 10):
        seen += [p.id for p in board.due]
    assert len(seen) == len(set(seen))


def test_a_due_pair_does_not_leak_its_answer(db: sqlite3.Connection, corpus: Corpus) -> None:
    # Claude.md — the answer is ground truth and stays on the server
    draw_all(db, DAY)
    (board,) = [b for b in store.boards(db, 5) if b.group_id == corpus.piscivory]
    assert not any(hasattr(p, "answer") for p in board.due)


def test_a_roll_batch_has_no_context(db: sqlite3.Connection, corpus: Corpus) -> None:
    # flows/Drilling.md#a-roll-batch
    draw_all(db, DAY)
    batch = store.roll_batch(db, 10)
    assert [p.id for p in batch.due] == [corpus.pair_f]


def test_a_missed_pair_resets_to_zero_and_writes_a_miss(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    # flows/Drilling.md#writes
    db.execute("UPDATE recall_pair SET sessions_correct = 4 WHERE id = ?", (corpus.pair_b,))
    draw_all(db, DAY)
    store.confirm(
        db,
        [
            models.ConfirmResult(
                recall_pair_id=corpus.pair_b,
                correct=False,
                user_answer="130 mm",
                user_source="Duffy 2012",
            )
        ],
    )
    row = db.execute(
        "SELECT sessions_correct FROM recall_pair WHERE id = ?", (corpus.pair_b,)
    ).fetchone()
    assert row["sessions_correct"] == 0
    (miss,) = store.list_misses(db)
    assert (miss.user_answer, miss.user_source) == ("130 mm", "Duffy 2012")


def test_a_contested_miss_writes_no_row(db: sqlite3.Connection, corpus: Corpus) -> None:
    # flows/Drilling.md#contest-and-confirm — contesting counts as correct
    draw_all(db, DAY)
    store.confirm(
        db,
        [
            models.ConfirmResult(
                recall_pair_id=corpus.pair_b, correct=True, user_answer="70mm", user_source="Duffy"
            )
        ],
    )
    assert store.list_misses(db) == []
    row = db.execute(
        "SELECT sessions_correct FROM recall_pair WHERE id = ?", (corpus.pair_b,)
    ).fetchone()
    assert row["sessions_correct"] == 1


def test_confirming_a_board_deletes_exactly_its_draw_rows(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    draw_all(db, DAY)
    store.confirm(
        db,
        [
            models.ConfirmResult(recall_pair_id=pid, correct=True, user_answer="", user_source="")
            for pid in (corpus.pair_a, corpus.pair_b, corpus.pair_c)
        ],
    )
    left = {r["recall_pair_id"] for r in db.execute("SELECT recall_pair_id FROM draw").fetchall()}
    assert left == {corpus.pair_d, corpus.pair_e, corpus.pair_f}


def test_confirming_a_board_twice_is_refused(db: sqlite3.Connection, corpus: Corpus) -> None:
    # api/API.md#errors
    draw_all(db, DAY)
    result = models.ConfirmResult(
        recall_pair_id=corpus.pair_a, correct=True, user_answer="", user_source=""
    )
    store.confirm(db, [result])
    with pytest.raises(store.RefusedError):
        store.confirm(db, [result])


def test_confirm_writes_nothing_when_one_pair_is_not_in_the_draw(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    draw_all(db, DAY)
    db.execute("DELETE FROM draw WHERE recall_pair_id = ?", (corpus.pair_b,))
    with pytest.raises(store.RefusedError):
        store.confirm(
            db,
            [
                models.ConfirmResult(
                    recall_pair_id=corpus.pair_a, correct=True, user_answer="", user_source=""
                ),
                models.ConfirmResult(
                    recall_pair_id=corpus.pair_b, correct=True, user_answer="", user_source=""
                ),
            ],
        )
    row = db.execute(
        "SELECT sessions_correct FROM recall_pair WHERE id = ?", (corpus.pair_a,)
    ).fetchone()
    assert row["sessions_correct"] == 0


def test_stopping_early_leaves_the_draw_rows_untouched(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    # flows/Drilling.md#stopping-early
    draw_all(db, DAY)
    before = db.execute("SELECT COUNT(*) AS c FROM draw").fetchone()["c"]
    assert before == 6
    assert store.list_misses(db) == []


def test_sessions_correct_rises_by_at_most_one_per_confirm(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    for expected, day in enumerate(("2026-09-03", "2026-09-04", "2026-09-05"), start=1):
        draw_all(db, day)
        store.confirm(
            db,
            [
                models.ConfirmResult(
                    recall_pair_id=corpus.pair_a, correct=True, user_answer="", user_source=""
                )
            ],
        )
        row = db.execute(
            "SELECT sessions_correct FROM recall_pair WHERE id = ?", (corpus.pair_a,)
        ).fetchone()
        assert row["sessions_correct"] == expected


def test_stale_pairs_are_still_drilled(db: sqlite3.Connection, corpus: Corpus) -> None:
    # flows/Drilling.md#decisions
    store.move_placement(db, corpus.p1, models.PlacementMove(group_id=corpus.nearshore))
    summary = store.build_draw(db, DAY, rng=lambda: 0.0)
    assert summary.due == 6


def test_home_counts_are_the_three_backlogs(db: sqlite3.Connection, corpus: Corpus) -> None:
    # app/Home.md#the-counts
    home = store.home(db)
    assert home.ungrouped_notes == 1
    assert home.placements_without_pairs == 0
    assert home.placements_stale == 0
    assert home.draw is None
    draw_all(db, DAY)
    assert store.home(db).draw == models.DrawSummary(day=DAY, drawn=6, due=6, boards=2, roll=1)


def test_a_finished_draw_still_reads_as_built(db: sqlite3.Connection, corpus: Corpus) -> None:
    """Data.md#the-draw — the pathological case the marker exists to close."""
    draw_all(db, DAY)
    store.confirm(
        db,
        [
            models.ConfirmResult(recall_pair_id=pid, correct=True, user_answer="a", user_source="b")
            for pid in (
                corpus.pair_a,
                corpus.pair_b,
                corpus.pair_c,
                corpus.pair_d,
                corpus.pair_e,
                corpus.pair_f,
            )
        ],
    )
    summary = store.draw_summary(db)
    assert summary is not None
    assert (summary.drawn, summary.due, summary.boards, summary.roll) == (6, 0, 0, 0)


def test_building_after_finishing_the_same_day_moves_no_counter(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    """Data.md#the-draw — idempotent on the marker, not on the rows."""
    draw_all(db, DAY)
    store.confirm(
        db,
        [
            models.ConfirmResult(
                recall_pair_id=corpus.pair_a, correct=True, user_answer="a", user_source="b"
            )
        ],
    )
    again = store.build_draw(db, DAY, rng=lambda: 0.0)
    assert again.drawn == 6
    assert corpus.pair_a not in {
        r["recall_pair_id"] for r in db.execute("SELECT recall_pair_id FROM draw").fetchall()
    }
    row = db.execute(
        "SELECT sessions_correct FROM recall_pair WHERE id = ?", (corpus.pair_a,)
    ).fetchone()
    assert row["sessions_correct"] == 1


def test_the_current_draw_is_the_latest_built_not_todays(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    """Data.md#the-draw — nothing expires at midnight."""
    draw_all(db, "2026-09-01")
    assert store.current_day(db) == "2026-09-01"
    summary = store.draw_summary(db)
    assert summary is not None and summary.day == "2026-09-01"
    assert store.boards(db, 5)


def test_a_board_from_an_earlier_draw_still_confirms(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    """flows/Drilling.md — the 23:58 board answered at 00:01 commits normally."""
    draw_all(db, "2026-09-01")
    store.confirm(
        db,
        [
            models.ConfirmResult(
                recall_pair_id=corpus.pair_a, correct=False, user_answer="wrong", user_source="who"
            )
        ],
    )
    (miss,) = store.list_misses(db)
    # One clock: the miss is dated by its draw, not by the wall.
    assert miss.day == "2026-09-01"


def test_building_replaces_the_current_draw_and_sweeps_the_old_rows(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    """Data.md#the-draw — what ends a draw is the next one being built."""
    draw_all(db, "2026-09-01")
    store.build_draw(db, DAY, rng=lambda: 1.0)
    assert store.current_day(db) == DAY
    left = db.execute("SELECT COUNT(*) AS c FROM draw").fetchone()["c"]
    assert left == 0
    summary = store.draw_summary(db)
    assert summary is not None and (summary.day, summary.drawn) == (DAY, 0)


def test_confirming_with_no_draw_is_refused(db: sqlite3.Connection, corpus: Corpus) -> None:
    with pytest.raises(store.RefusedError):
        store.confirm(
            db,
            [
                models.ConfirmResult(
                    recall_pair_id=corpus.pair_a, correct=True, user_answer="", user_source=""
                )
            ],
        )
