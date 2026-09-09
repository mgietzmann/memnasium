"""The drill record — design/api/API.md#the-record, design/app/Review.md."""

import sqlite3

from fastapi.testclient import TestClient

from api import models, store
from tests.conftest import Corpus, days_ago, draw_all

DAY = store.today()


def blow(db: sqlite3.Connection, *pair_ids: int) -> None:
    """Confirm each pair as missed, in the order given."""
    for pair_id in pair_ids:
        store.confirm(
            db,
            [
                models.ConfirmResult(
                    recall_pair_id=pair_id,
                    correct=False,
                    user_answer="130 mm",
                    user_source="Duffy 2012",
                )
            ],
        )


def test_last_drill_is_the_last_draw_built(db: sqlite3.Connection, corpus: Corpus) -> None:
    """app/Review.md#which-misses — the window is the last draw, not the last miss."""
    draw_all(db, days_ago(1))
    blow(db, corpus.pair_a, corpus.pair_b)
    draw_all(db)
    blow(db, corpus.pair_c)
    misses = store.list_misses(db, since=store.LAST_DRILL)
    assert [m.recall_pair_id for m in misses] == [corpus.pair_c]


def test_a_clean_morning_hides_yesterday(db: sqlite3.Connection, corpus: Corpus) -> None:
    """app/Review.md#which-misses — anchoring on the last day that has misses would not."""
    draw_all(db, days_ago(1))
    blow(db, corpus.pair_a)
    draw_all(db)
    assert store.list_misses(db, since=store.LAST_DRILL) == []


def test_a_drill_in_progress_is_reviewable(db: sqlite3.Connection, corpus: Corpus) -> None:
    """app/Review.md#which-misses — today built and half worked reviews today."""
    draw_all(db)
    blow(db, corpus.pair_a)
    misses = store.list_misses(db, since=store.LAST_DRILL)
    assert [m.recall_pair_id for m in misses] == [corpus.pair_a]
    assert db.execute("SELECT COUNT(*) AS c FROM draw").fetchone()["c"] > 0


def test_last_drill_on_an_install_that_never_drilled(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    """app/Review.md#nothing-missed — no draw_day row means no day to be since."""
    assert store.list_misses(db, since=store.LAST_DRILL) == []


def test_an_omitted_since_still_means_everything(db: sqlite3.Connection, corpus: Corpus) -> None:
    """api/API.md#decisions — the app names its window; a skill's record is unchanged."""
    draw_all(db, days_ago(1))
    blow(db, corpus.pair_a)
    draw_all(db)
    blow(db, corpus.pair_b)
    assert len(store.list_misses(db)) == 2


def test_the_record_is_newest_first(db: sqlite3.Connection, corpus: Corpus) -> None:
    """api/API.md#the-record — day descending, then id descending, as a guarantee."""
    draw_all(db, days_ago(1))
    blow(db, corpus.pair_a)
    draw_all(db)
    blow(db, corpus.pair_b, corpus.pair_c)
    misses = store.list_misses(db)
    assert [m.recall_pair_id for m in misses] == [corpus.pair_c, corpus.pair_b, corpus.pair_a]
    assert [m.day for m in misses] == [DAY, DAY, days_ago(1)]


def test_a_miss_carries_the_pair_its_source_and_its_group(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    """api/API.md#the-record — everything either reader needs without a second call."""
    draw_all(db)
    blow(db, corpus.pair_b)
    (miss,) = store.list_misses(db, since=store.LAST_DRILL)
    assert miss.question == "Puget Sound, inshore?"
    assert miss.answer == "70 mm"
    assert (miss.source.author, miss.source.year) == ("Duffy", 2010)
    assert (miss.group_id, miss.group_name) == (corpus.piscivory, "Onset of piscivory")


def test_a_roll_pairs_miss_has_no_group(db: sqlite3.Connection, corpus: Corpus) -> None:
    """app/Review.md#layout — pairs on the roll sit under a final rule, not a group."""
    draw_all(db)
    blow(db, corpus.pair_f)
    (miss,) = store.list_misses(db, since=store.LAST_DRILL)
    assert (miss.group_id, miss.group_name) == (None, None)


def test_a_retired_pairs_misses_are_still_returned(db: sqlite3.Connection, corpus: Corpus) -> None:
    """api/API.md#the-record — retiring is not a deletion, and the record is of what was drilled."""
    draw_all(db)
    blow(db, corpus.pair_b)
    # Rewriting the set without pair B retires it.
    store.write_pairs(db, corpus.p2, [models.PairWrite(question="Offshore?", answer="130 mm")])
    assert (
        db.execute("SELECT retired FROM recall_pair WHERE id = ?", (corpus.pair_b,)).fetchone()[
            "retired"
        ]
        == 1
    )
    (miss,) = store.list_misses(db, since=store.LAST_DRILL)
    assert miss.recall_pair_id == corpus.pair_b


def test_the_route_takes_last_drill(
    client: TestClient, db: sqlite3.Connection, corpus: Corpus
) -> None:
    """api/API.md#the-record — `last-drill` is resolved in the store, not by the caller."""
    draw_all(db, days_ago(1))
    blow(db, corpus.pair_a)
    draw_all(db)
    blow(db, corpus.pair_b)
    response = client.get("/api/misses?since=last-drill")
    assert response.status_code == 200
    assert [m["recall_pair_id"] for m in response.json()] == [corpus.pair_b]
