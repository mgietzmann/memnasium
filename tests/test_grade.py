"""The app's side of the grading contract — design/Claude.md#enforcing-the-contract."""

import json

import pytest

from api import claude


def items(*ids: int) -> list[dict[str, object]]:
    return [
        {
            "recall_pair_id": i,
            "question": "q",
            "answer": "70 mm",
            "source": "Duffy 2010",
            "user_answer": "70 mm",
            "user_source": "Duffy 2010",
        }
        for i in ids
    ]


def replies(*texts: str) -> tuple[claude.Caller, list[int]]:
    calls: list[int] = []

    def caller(messages: list[dict[str, str]], max_tokens: int) -> str:
        calls.append(max_tokens)
        return texts[min(len(calls) - 1, len(texts) - 1)]

    return caller, calls


def result(pair_id: int, **over: object) -> dict[str, object]:
    base: dict[str, object] = {
        "recall_pair_id": pair_id,
        "answer_correct": True,
        "source_correct": True,
        "right_answer": None,
        "right_source": None,
    }
    base.update(over)
    return base


def test_a_well_formed_response_is_accepted() -> None:
    caller, _ = replies(json.dumps({"results": [result(1), result(2)]}))
    verdicts = claude.grade(items(1, 2), caller)
    assert [v.recall_pair_id for v in verdicts] == [1, 2]


def test_a_reordered_response_is_accepted() -> None:
    # Claude.md — keyed by recall_pair_id, order irrelevant
    caller, _ = replies(json.dumps({"results": [result(2), result(1)]}))
    assert {v.recall_pair_id for v in claude.grade(items(1, 2), caller)} == {1, 2}


def test_a_response_missing_an_id_is_rejected() -> None:
    caller, calls = replies(json.dumps({"results": [result(1)]}))
    with pytest.raises(claude.GradeError):
        claude.grade(items(1, 2), caller)
    assert len(calls) == 2


def test_a_response_with_an_extra_id_is_rejected() -> None:
    caller, _ = replies(json.dumps({"results": [result(1), result(2), result(3)]}))
    with pytest.raises(claude.GradeError):
        claude.grade(items(1, 2), caller)


def test_a_right_answer_on_a_correct_box_is_rejected() -> None:
    caller, _ = replies(json.dumps({"results": [result(1, right_answer="70 mm")]}))
    with pytest.raises(claude.GradeError):
        claude.grade(items(1), caller)


def test_a_missing_right_answer_on_a_failed_box_is_rejected() -> None:
    caller, _ = replies(json.dumps({"results": [result(1, answer_correct=False)]}))
    with pytest.raises(claude.GradeError):
        claude.grade(items(1), caller)


def test_a_non_boolean_verdict_is_rejected() -> None:
    caller, _ = replies(json.dumps({"results": [result(1, answer_correct="yes")]}))
    with pytest.raises(claude.GradeError):
        claude.grade(items(1), caller)


def test_one_retry_happens_with_the_specific_error() -> None:
    seen: list[str] = []

    def caller(messages: list[dict[str, str]], max_tokens: int) -> str:
        seen.append(messages[-1]["content"])
        if len(seen) == 1:
            return "not json at all"
        return json.dumps({"results": [result(1)]})

    verdicts = claude.grade(items(1), caller)
    assert [v.recall_pair_id for v in verdicts] == [1]
    assert "was rejected" in seen[1]
    assert "not JSON" in seen[1]


def test_a_second_failure_raises_and_nothing_is_guessed() -> None:
    caller, calls = replies("nonsense")
    with pytest.raises(claude.GradeError) as exc:
        claude.grade(items(1), caller)
    assert "twice" in str(exc.value)
    assert len(calls) == 2


def test_the_token_budget_is_sized_from_the_batch() -> None:
    # Claude.md#stack — 1024 + 400 * N, thinking included
    caller, calls = replies(json.dumps({"results": [result(1), result(2), result(3)]}))
    claude.grade(items(1, 2, 3), caller)
    assert calls[0] == 1024 + 400 * 3


def test_a_duplicated_id_is_rejected() -> None:
    # Claude.md#enforcing-the-contract — no extras, and a duplicate is an extra
    caller, calls = replies(json.dumps({"results": [result(1), result(1, answer_correct=False)]}))
    with pytest.raises(claude.GradeError):
        claude.grade(items(1), caller)
    assert len(calls) == 2


def test_the_retry_shows_claude_what_it_produced() -> None:
    # Claude.md — the specific error goes back, and so does the output it is about
    seen: list[list[dict[str, str]]] = []

    def caller(messages: list[dict[str, str]], max_tokens: int) -> str:
        seen.append(list(messages))
        if len(seen) == 1:
            return "not json at all"
        return json.dumps({"results": [result(1)]})

    claude.grade(items(1), caller)
    retry = seen[1]
    assert [m["role"] for m in retry] == ["user", "assistant", "user"]
    assert retry[1]["content"] == "not json at all"
