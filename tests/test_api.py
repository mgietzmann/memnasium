"""The routes, through a real client — design/api/API.md, design/standards/Tests.md."""

import sqlite3

from fastapi.testclient import TestClient

from api import claude, mcp, routes
from api.main import app
from tests.conftest import Corpus


def test_the_mcp_roster_excludes_the_drill_loop() -> None:
    # api/API.md#the-mcp-tools — nothing that writes in the drill loop is a tool
    assert len(mcp.TOOL_NAMES) == 11
    forbidden = {"build_draw", "post_draw", "grade", "confirm", "get_boards", "get_roll", "home"}
    assert forbidden.isdisjoint(mcp.TOOL_NAMES)
    assert not any(
        "confirm" in name or "grade" in name or "draw" in name for name in mcp.TOOL_NAMES
    )


def test_every_mcp_tool_is_registered() -> None:
    import asyncio

    registered = {t.name for t in asyncio.run(mcp.server.list_tools())}
    assert registered == set(mcp.TOOL_NAMES)


def test_home_is_one_call(client: TestClient, corpus: Corpus) -> None:
    # api/API.md#decisions — GET /home is coarse
    body = client.get("/api/home").json()
    assert set(body) == {
        "ungrouped_notes",
        "placements_without_pairs",
        "placements_stale",
        "draw",
    }
    assert body["draw"] is None


def test_the_drill_loop_round_trips(
    client: TestClient, db: sqlite3.Connection, corpus: Corpus
) -> None:
    day = client.post("/api/draw").json()
    assert day["due"] >= 1

    boards = client.get("/api/draw/boards", params={"n": 1}).json()
    assert len(boards) == 1
    board = boards[0]
    assert board["due"]

    def stub(messages: list[dict[str, str]], max_tokens: int) -> str:
        import json

        return json.dumps(
            {
                "results": [
                    {
                        "recall_pair_id": p["id"],
                        "answer_correct": True,
                        "source_correct": True,
                        "right_answer": None,
                        "right_source": None,
                    }
                    for p in board["due"]
                ]
            }
        )

    app.dependency_overrides[routes.get_caller] = lambda: stub
    graded = client.post(
        "/api/grade",
        json={
            "answers": [
                {"recall_pair_id": p["id"], "user_answer": "x", "user_source": "y"}
                for p in board["due"]
            ]
        },
    ).json()
    assert all(v["answer_correct"] for v in graded["verdicts"])

    confirmed = client.post(
        "/api/confirm",
        json={
            "results": [
                {
                    "recall_pair_id": p["id"],
                    "correct": True,
                    "user_answer": "x",
                    "user_source": "y",
                }
                for p in board["due"]
            ]
        },
    )
    assert confirmed.status_code == 204

    again = client.post(
        "/api/confirm",
        json={
            "results": [
                {
                    "recall_pair_id": p["id"],
                    "correct": True,
                    "user_answer": "x",
                    "user_source": "y",
                }
                for p in board["due"]
            ]
        },
    )
    assert again.status_code == 409
    assert again.json()["code"] == "refused"


def test_a_refusal_is_a_typed_error_with_a_reason(client: TestClient, corpus: Corpus) -> None:
    # api/API.md#errors — never a silent no-op
    response = client.patch(f"/api/notes/{corpus.note1}", json={"statement": "nope"})
    assert response.status_code == 409
    assert response.json()["code"] == "refused"
    assert "frozen" in response.json()["detail"]


def test_a_missing_row_is_a_404(client: TestClient, corpus: Corpus) -> None:
    response = client.get("/api/groups/9999")
    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


def test_a_grade_failure_is_surfaced_not_written(client: TestClient, corpus: Corpus) -> None:
    # Claude.md#enforcing-the-contract
    app.dependency_overrides[routes.get_caller] = lambda: lambda m, t: "nonsense"
    response = client.post(
        "/api/grade",
        json={
            "answers": [{"recall_pair_id": corpus.pair_a, "user_answer": "a", "user_source": "b"}]
        },
    )
    assert response.status_code == 502


def test_note_filters_compose(client: TestClient, corpus: Corpus) -> None:
    # api/API.md#entry-and-lookup
    body = client.get("/api/notes", params={"source_id": corpus.duffy, "q": "piscivor"}).json()
    assert [n["id"] for n in body] == [corpus.note2]


def test_the_grade_call_is_never_reached_without_a_stub() -> None:
    # Tests.md — Claude is always stubbed; the real caller is the default only
    assert routes.get_caller() is claude.live_caller
