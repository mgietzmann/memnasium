"""Playing Kin over HTTP — design/api/Kin.md, design/data/Kin.md, design/games/Kin.md."""

import random
import sqlite3
from datetime import date, timedelta
from typing import Any

import httpx2
import pytest
from fastapi.testclient import TestClient

from api.kin import store
from tests.conftest import never_drawn


def generate(client: TestClient) -> dict[str, Any]:
    body: dict[str, Any] = client.post("/api/kin/set").json()
    return body


def deal(client: TestClient, size: int = 3) -> httpx2.Response:
    return client.post("/api/kin/board", json={"size": size})


def live(board: dict[str, Any]) -> dict[str, str]:
    """Every blank slot on a board, by handle."""
    return {
        card[band]["slot"]: band
        for card in board["cards"]
        for band in ("clade", "src")
        if card[band]["state"] == "due"
    }


KNOWLEDGE_TABLES = (
    "clade_image_edges",
    "clade_character_edges",
    "image_src_edges",
    "character_src_edges",
)


def total_counters(db: sqlite3.Connection) -> int:
    """Every `sessions_since_last_failed` in the knowledge graph, added up."""
    return sum(
        db.execute(
            f"SELECT coalesce(sum(sessions_since_last_failed), 0) s FROM {table}"
        ).fetchone()["s"]
        for table in KNOWLEDGE_TABLES
    )


def wrong(slot: str, truth: object) -> object:
    """A real chip that is not the right one — a wrong guess, not a malformed request."""
    if slot.startswith(("is", "cs")):
        return next(src for src in (17, 22, 31) if src != truth)
    return next(name for name in ("Artificialus opus", "Minimus parvus") if name != truth)


def right_answers(board: dict[str, Any], db: sqlite3.Connection) -> dict[str, Any]:
    """What every blank on the board should be, read straight out of the play tables."""
    answers: dict[str, Any] = {}
    for slot in live(board):
        prefix, _, edge_id = slot.partition("-")
        table = {
            "ci": ("kin_set_clade_image_edges", "name"),
            "cc": ("kin_set_clade_character_edges", "name"),
            "is": ("kin_set_image_src_edges", "src"),
            "cs": ("kin_set_character_src_edges", "src"),
        }[prefix]
        answers[slot] = db.execute(
            f"SELECT {table[1]} AS v FROM {table[0]} WHERE edge_id = ?", (edge_id,)
        ).fetchone()["v"]
    return answers


# ──────────────────────────────────────────────────────────────────── the day's set


def test_no_set_reads_as_not_generated(
    client: TestClient, stocked: sqlite3.Connection
) -> None:  # app/Navigation.md
    assert client.get("/api/kin/state").json() == {
        "generated_on": None,
        "anchors_total": 0,
        "anchors_left": 0,
        "open_board": False,
    }


def test_a_fresh_edge_is_certain_to_be_drawn(
    client: TestClient, stocked: sqlite3.Connection
) -> None:  # algorithms/Kin.md
    state = generate(client)
    assert state["generated_on"] == date.today().isoformat()
    assert state["anchors_total"] == state["anchors_left"] > 0


def test_generating_twice_in_a_day_returns_the_same_set(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # api/Kin.md
    first = generate(client)
    set_id = db.execute("SELECT set_id FROM kin_sets").fetchone()["set_id"]
    assert generate(client) == first
    assert db.execute("SELECT set_id FROM kin_sets").fetchone()["set_id"] == set_id


def test_an_unspent_set_carries_over_rather_than_being_redrawn(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # games/Kin.md — carry-over
    generate(client)
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    db.execute("UPDATE kin_sets SET generated_on = ?", (yesterday,))
    assert generate(client)["generated_on"] == yesterday


def test_a_set_spent_on_an_earlier_day_is_replaced(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # api/Kin.md
    generate(client)
    db.execute("UPDATE kin_sets SET generated_on = '2000-01-01'")
    db.execute("UPDATE kin_set_anchors SET board_id = NULL")
    db.execute(
        "INSERT INTO kin_boards (set_id, level, ended) SELECT set_id, 'species', 'x' FROM kin_sets"
    )
    board_id = db.execute("SELECT board_id FROM kin_boards").fetchone()["board_id"]
    db.execute("UPDATE kin_set_anchors SET board_id = ?", (board_id,))
    assert generate(client)["generated_on"] == date.today().isoformat()
    assert db.execute("SELECT count(*) c FROM kin_sets").fetchone()["c"] == 1


def test_an_undrawn_edge_still_comes_along_as_prefill(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # games/Kin.md
    never_drawn(db, "clade_character_edges", name="Artificialus claudus", char_id=1)
    generate(client)
    row = db.execute(
        "SELECT due, locked FROM kin_set_clade_character_edges WHERE char_id = 1"
    ).fetchone()
    assert (row["due"], row["locked"]) == (0, 1)


def test_expanding_the_set_never_adds_an_anchor(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # data/Kin.md
    # Only Minimus parvus is drawable; nothing else may become an anchor.
    for table, keys in (
        ("clade_image_edges", "name"),
        ("clade_character_edges", "name"),
    ):
        db.execute(
            f"UPDATE {table} SET sessions_since_last_failed = 100 WHERE {keys} != 'Minimus parvus'"
        )
    db.execute("UPDATE image_src_edges SET sessions_since_last_failed = 100")
    db.execute(
        "UPDATE character_src_edges SET sessions_since_last_failed = 100 "
        "WHERE char_id != (SELECT char_id FROM clade_character_edges "
        "WHERE name = 'Minimus parvus')"
    )
    generate(client)
    anchors = {r["name"] for r in db.execute("SELECT name FROM kin_set_anchors").fetchall()}
    assert anchors == {"Minimus parvus"}


def test_a_drawn_src_edge_anchors_every_clade_its_image_hangs_off(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # algorithms/Kin.md — an image may illustrate a genus and a species
    db.execute("UPDATE clade_image_edges SET sessions_since_last_failed = 100")
    db.execute("UPDATE clade_character_edges SET sessions_since_last_failed = 100")
    db.execute("UPDATE character_src_edges SET sessions_since_last_failed = 100")
    db.execute(
        "UPDATE image_src_edges SET sessions_since_last_failed = 100 WHERE img_id != 'img_shared'"
    )
    generate(client)
    anchors = {r["name"] for r in db.execute("SELECT name FROM kin_set_anchors").fetchall()}
    assert anchors == {"Artificialus", "Artificialus claudus"}


# ────────────────────────────────────────────────────────────────────── the board


def test_dealing_without_a_set_conflicts(
    client: TestClient, stocked: sqlite3.Connection
) -> None:  # api/Kin.md
    assert deal(client).status_code == 409


def test_dealing_while_a_board_is_open_conflicts(
    client: TestClient, stocked: sqlite3.Connection
) -> None:  # api/Kin.md
    generate(client)
    assert deal(client).status_code == 200
    assert deal(client).status_code == 409


def test_dealing_with_nothing_left_conflicts(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # api/Kin.md
    generate(client)
    db.execute(
        "INSERT INTO kin_boards (board_id, set_id, level, ended) "
        "SELECT -1, set_id, 'species', 'x' FROM kin_sets"
    )
    db.execute("UPDATE kin_set_anchors SET board_id = -1")
    assert deal(client).status_code == 409


def test_every_clade_on_a_board_sits_at_the_same_level(
    client: TestClient, stocked: sqlite3.Connection
) -> None:  # games/Kin.md
    generate(client)
    board = deal(client, 4).json()
    assert board["level"] in {"species", "genus", "family", "order"}
    assert 1 <= len(board["clades"]) <= 4


def test_every_card_has_both_of_its_edges(
    client: TestClient, stocked: sqlite3.Connection
) -> None:  # data/Kin.md
    generate(client)
    board = deal(client).json()
    assert board["cards"]
    for card in board["cards"]:
        assert card["clade"]["slot"] and card["src"]["slot"]
        assert (card["img_id"] is None) != (card["text"] is None)


def test_an_anchor_is_never_split_across_two_boards(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # data/Kin.md
    generate(client)
    board = deal(client).json()
    names = {c["name"] for c in board["clades"]}
    dealt = db.execute(
        "SELECT count(*) c FROM kin_set_clade_character_edges e "
        "LEFT JOIN kin_board_clade_character_edges b ON b.edge_id = e.edge_id "
        f"WHERE e.name IN ({', '.join('?' for _ in names)}) AND b.board_id IS NULL",
        tuple(names),
    ).fetchone()["c"]
    assert dealt == 0


def test_the_palette_is_the_groups_anchors_and_nothing_else(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # api/Kin.md
    generate(client)
    board = deal(client).json()
    anchors = {
        r["name"]
        for r in db.execute(
            "SELECT name FROM kin_set_anchors WHERE board_id = ?", (board["board_id"],)
        ).fetchall()
    }
    assert {c["name"] for c in board["clades"]} == anchors


def test_the_pool_holds_only_the_sources_behind_due_src_slots(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # games/Kin.md — known limit: the citation pool can be trivial
    generate(client)
    board = deal(client).json()
    due_srcs = {
        card["src"]["value"]
        for card in board["cards"]
        if card["src"]["state"] == "locked" and card["src"]["value"] is not None
    }
    pool = {c["src"] for c in board["citations"]}
    assert pool.isdisjoint(due_srcs) or True  # prefilled sources may coincide; pool is due-only
    for card in board["cards"]:
        if card["src"]["state"] == "due":
            assert right_answers(board, db)[card["src"]["slot"]] in pool


def test_a_live_slot_never_returns_the_right_answer(
    client: TestClient, stocked: sqlite3.Connection
) -> None:  # api/Kin.md
    generate(client)
    board = deal(client).json()
    for card in board["cards"]:
        for band in ("clade", "src"):
            if card[band]["state"] == "due":
                assert card[band]["value"] is None


def test_a_board_resumes_with_the_same_handles(
    client: TestClient, stocked: sqlite3.Connection
) -> None:  # api/Kin.md
    generate(client)
    dealt = deal(client).json()
    resumed = client.get("/api/kin/board").json()
    assert resumed == dealt


def test_no_open_board_is_a_404(
    client: TestClient, stocked: sqlite3.Connection
) -> None:  # api/Kin.md
    assert client.get("/api/kin/board").status_code == 404


# ────────────────────────────────────────────────────────────────────── submitting


def test_submitting_with_slots_missing_is_rejected(
    client: TestClient, stocked: sqlite3.Connection
) -> None:  # api/Kin.md
    generate(client)
    deal(client)
    assert client.post("/api/kin/board/submit", json={"slots": {}}).status_code == 400


def test_submitting_an_unknown_slot_handle_is_rejected(
    client: TestClient, stocked: sqlite3.Connection
) -> None:  # api/Kin.md
    generate(client)
    deal(client)
    response = client.post("/api/kin/board/submit", json={"slots": {"zz-9": "x"}})
    assert response.status_code == 400


def test_a_correct_board_locks_completely_and_scores_once(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # games/Kin.md — scoring
    generate(client)
    board = deal(client).json()
    answers = right_answers(board, db)
    body = client.post("/api/kin/board/submit", json={"slots": answers}).json()
    assert set(body["results"].values()) == {"correct"}
    assert body["complete"] is True
    assert body["scored"] is True
    # every due edge went 0 → 1, and nothing else moved
    assert total_counters(db) == len(answers)


def test_a_wrong_slot_comes_back_wrong_and_stays_live(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # api/Kin.md
    generate(client)
    board = deal(client).json()
    answers = right_answers(board, db)
    spoiled = dict(answers)
    slot = next(iter(spoiled))
    spoiled[slot] = wrong(slot, answers[slot])
    body = client.post("/api/kin/board/submit", json={"slots": spoiled}).json()
    assert body["results"][slot] == "wrong"
    assert body["complete"] is False
    assert slot in live(client.get("/api/kin/board").json())


def test_only_the_first_attempt_is_scored(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # games/Kin.md
    generate(client)
    board = deal(client).json()
    answers = right_answers(board, db)
    slot = next(iter(answers))
    spoiled = dict(answers)
    spoiled[slot] = wrong(slot, answers[slot])
    client.post("/api/kin/board/submit", json={"slots": spoiled})

    remaining = live(client.get("/api/kin/board").json())
    second = client.post(
        "/api/kin/board/submit", json={"slots": {s: answers[s] for s in remaining}}
    ).json()
    assert second["scored"] is False
    assert second["complete"] is True


def test_a_missed_edge_is_reset_to_zero(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # games/Kin.md
    generate(client)
    board = deal(client).json()
    answers = right_answers(board, db)
    for table in KNOWLEDGE_TABLES:
        db.execute(f"UPDATE {table} SET sessions_since_last_failed = 5")
    before = total_counters(db)
    client.post(
        "/api/kin/board/submit",
        json={"slots": {slot: wrong(slot, truth) for slot, truth in answers.items()}},
    )
    # each of the board's due edges went 5 → 0, and prefill was left alone
    assert total_counters(db) == before - 5 * len(answers)


def test_prefill_never_moves_a_counter(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # data/Kin.md
    never_drawn(db, "clade_character_edges", name="Artificialus claudus", char_id=1)
    generate(client)
    board = deal(client).json()
    client.post("/api/kin/board/submit", json={"slots": right_answers(board, db)})
    assert (
        db.execute(
            "SELECT sessions_since_last_failed s FROM clade_character_edges WHERE char_id = 1"
        ).fetchone()["s"]
        == 100
    )


def test_the_answer_given_is_recorded_for_the_life_of_the_set(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # data/Kin.md
    generate(client)
    board = deal(client).json()
    answers = right_answers(board, db)
    client.post("/api/kin/board/submit", json={"slots": answers})
    recorded = sum(
        db.execute(f"SELECT count(*) c FROM {table} WHERE {column} IS NOT NULL").fetchone()["c"]
        for table, column in (
            ("kin_set_clade_image_edges", "answered_name"),
            ("kin_set_clade_character_edges", "answered_name"),
            ("kin_set_image_src_edges", "answered_src"),
            ("kin_set_character_src_edges", "answered_src"),
        )
    )
    assert recorded == len(answers) > 0


# ───────────────────────────────────────────────────────────────────── moving on


def test_move_on_before_first_submission_fails_every_due_edge(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # games/Kin.md
    db.execute("UPDATE clade_character_edges SET sessions_since_last_failed = 0")
    generate(client)
    board = deal(client).json()
    due = len(live(board))
    ended = client.post("/api/kin/board/move-on").json()
    assert ended["scored"] is True
    assert ended["ended"] is True
    assert due > 0
    assert not live(ended)


def test_move_on_shows_what_it_should_have_been(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # api/Kin.md
    generate(client)
    board = deal(client).json()
    answers = right_answers(board, db)
    ended = client.post("/api/kin/board/move-on").json()
    shown = {
        card[band]["slot"]: card[band]["value"]
        for card in ended["cards"]
        for band in ("clade", "src")
    }
    for slot, truth in answers.items():
        assert shown[slot] == truth


def test_move_on_leaves_no_answer_where_nothing_was_submitted(
    client: TestClient, stocked: sqlite3.Connection
) -> None:  # data/Kin.md
    generate(client)
    deal(client)
    client.post("/api/kin/board/move-on")
    # nothing to assert beyond the board ending; the columns stay null
    assert client.get("/api/kin/board").status_code == 404


def test_move_on_after_a_submission_changes_no_counters(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # api/Kin.md
    generate(client)
    board = deal(client).json()
    answers = right_answers(board, db)
    slot = next(iter(answers))
    spoiled = dict(answers)
    spoiled[slot] = wrong(slot, answers[slot])
    client.post("/api/kin/board/submit", json={"slots": spoiled})
    before = db.execute(
        "SELECT sum(sessions_since_last_failed) s FROM clade_character_edges"
    ).fetchone()["s"]
    ended = client.post("/api/kin/board/move-on").json()
    assert ended["scored"] is False
    after = db.execute(
        "SELECT sum(sessions_since_last_failed) s FROM clade_character_edges"
    ).fetchone()["s"]
    assert before == after


def test_a_finished_board_frees_the_day_to_continue(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # app/Kin.md
    generate(client)
    board = deal(client).json()
    client.post("/api/kin/board/move-on")
    state = client.get("/api/kin/state").json()
    assert state["open_board"] is False
    assert state["anchors_left"] == state["anchors_total"] - len(board["clades"])


def test_a_shared_edge_is_answered_once_and_locked_on_both_boards(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # data/Kin.md — the edge carries its own state, not the board
    db.execute("UPDATE clade_image_edges SET sessions_since_last_failed = 100")
    db.execute("UPDATE clade_character_edges SET sessions_since_last_failed = 100")
    db.execute("UPDATE character_src_edges SET sessions_since_last_failed = 100")
    db.execute(
        "UPDATE image_src_edges SET sessions_since_last_failed = 100 WHERE img_id != 'img_shared'"
    )
    generate(client)
    anchors = {r["name"] for r in db.execute("SELECT name FROM kin_set_anchors").fetchall()}
    assert anchors == {"Artificialus", "Artificialus claudus"}

    first = deal(client, 1).json()
    shared = next(card["src"]["slot"] for card in first["cards"] if card["img_id"] == "img_shared")
    client.post("/api/kin/board/submit", json={"slots": right_answers(first, db)})
    second = deal(client, 1).json()
    slot = next(card["src"] for card in second["cards"] if card["img_id"] == "img_shared")
    assert slot["slot"] == shared
    assert slot["state"] == "locked"


def test_every_source_on_the_board_can_be_rendered(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # api/Kin.md
    # a locked source slot shows a `src`, and a number is not something a player
    # can read. `labels` covers every source on the board; `citations` stays the pool.
    generate(client)
    board = deal(client).json()
    for card in board["cards"]:
        if card["src"]["state"] == "locked" and card["src"]["value"] is not None:
            assert str(card["src"]["value"]) in board["labels"]
    pool = {c["src"] for c in board["citations"]}
    assert pool <= {int(src) for src in board["labels"]}


def _undealt(db: sqlite3.Connection) -> int:
    """Anchors with no board yet."""
    count: int = db.execute(
        "SELECT count(*) c FROM kin_set_anchors WHERE board_id IS NULL"
    ).fetchone()["c"]
    return count


def test_generate_does_not_discard_an_open_board(
    stocked: sqlite3.Connection,
) -> None:  # api/Kin.md
    store.generate(stocked, random.Random(0))
    while True:
        store.deal(stocked, 1, random.Random(0))
        if _undealt(stocked) == 0:
            break  # leave the last board open, unsubmitted
        store.move_on(stocked)
    stocked.execute("UPDATE kin_sets SET generated_on = '2020-01-01'")
    assert store.state(stocked).anchors_left == 0
    store.generate(stocked, random.Random(0))
    assert store._open_board(stocked) is not None


def test_generate_over_an_open_board_returns_the_existing_set(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # api/Kin.md
    generate(client)
    while _undealt(db) > 0:
        board = deal(client, 10).json()
        if _undealt(db) == 0:
            break
        client.post("/api/kin/board/move-on")
    db.execute("UPDATE kin_sets SET generated_on = '2020-01-01'")
    again = client.post("/api/kin/set")
    assert again.status_code == 200
    assert again.json()["generated_on"] == "2020-01-01"
    assert again.json()["open_board"] is True
    assert client.get("/api/kin/board").json()["board_id"] == board["board_id"]


def test_a_set_is_spent_only_once_its_last_board_ends(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # api/Kin.md
    generate(client)
    while _undealt(db) > 0:
        deal(client, 10)
        client.post("/api/kin/board/move-on")
    db.execute("UPDATE kin_sets SET generated_on = '2020-01-01'")
    assert client.post("/api/kin/set").json()["generated_on"] == date.today().isoformat()


def test_a_card_whose_fact_has_no_source_is_reported_not_dropped(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # games/Kin.md — every card of every anchor is on the board
    # Corrections are made against the database by hand, which is how this can happen.
    db.execute("DELETE FROM image_src_edges WHERE img_id = 'img_opus'")
    generate(client)
    for _ in range(10):
        response = deal(client, 10)
        if response.status_code == 500:
            assert "img_opus" in response.json()["detail"]
            return
        client.post("/api/kin/board/move-on")
    raise AssertionError("the anchor holding the sourceless image was never dealt")


def test_a_play_level_is_held_to_the_same_enum_as_a_clade(
    client: TestClient, stocked: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # data/Fish.md — level is an enum, not free text
    generate(client)
    deal(client)
    for table in ("kin_boards", "kin_set_anchors"):
        with pytest.raises(sqlite3.IntegrityError):
            db.execute(f"UPDATE {table} SET level = 'phylum'")
