"""The one call out: grading a board.

Design/Claude.md is the specification. The real call sits behind an injectable
function so tests never touch the API.
"""

import json
from collections.abc import Callable, Sequence
from typing import Any

from api.config import GRADE_BASE, GRADE_PER_PAIR, MODEL_ID
from api.models import Verdict

#: A call out: messages and a token budget in, the model's text out.
Caller = Callable[[list[dict[str, str]], int], str]


class GradeError(Exception):
    """A grade response that could not be trusted, after one retry."""


RESULT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "recall_pair_id": {"type": "integer"},
                    "answer_correct": {"type": "boolean"},
                    "source_correct": {"type": "boolean"},
                    "right_answer": {"type": ["string", "null"]},
                    "right_source": {"type": ["string", "null"]},
                },
                "required": [
                    "recall_pair_id",
                    "answer_correct",
                    "source_correct",
                    "right_answer",
                    "right_source",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["results"],
    "additionalProperties": False,
}

SYSTEM = """\
You grade recall answers for a spaced-repetition trainer. Each item gives you a
question, the ground-truth answer, the ground-truth source, and what the user
typed into two boxes: an answer box and a source box.

Judge each answer against the given `answer` and each source against the given
`source`. Be fair to paraphrase, to equivalent maths, and to units expressed
differently. The source must name the right author and the right year; the
publication is not asked for. Do not reward an answer that is merely adjacent to
the truth, and do not penalise one that is right but differently put.

Statements may contain LaTeX. Judge equivalence, not formatting.

Return one result per item, keyed by `recall_pair_id`. Set `right_answer` only
when `answer_correct` is false, and `right_source` only when `source_correct` is
false; the other must be null. The value is the ground truth restated for
display. No commentary of any kind.

Worked example. Given the item

  {"recall_pair_id": 812,
   "question": "At what length do Puget Sound Chinook turn piscivorous inshore?",
   "answer": "70 mm", "source": "Duffy 2010",
   "user_answer": "130 mm", "user_source": "Duffy, 2010"}

return

  {"results": [{"recall_pair_id": 812, "answer_correct": false,
                "source_correct": true, "right_answer": "70 mm",
                "right_source": null}]}\
"""


def _validate(text: str, expected: set[int]) -> list[Verdict]:
    """Turn a response into verdicts, or say precisely what is wrong with it.

    Args:
        text: The model's reply.
        expected: The `recall_pair_id`s that were asked about.

    Returns:
        One verdict per expected id.

    Raises:
        GradeError: With a message specific enough to send back to Claude.
    """
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise GradeError(f"the response was not JSON: {exc}") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
        raise GradeError("the response must be an object with a `results` array")

    verdicts: list[Verdict] = []
    seen: set[int] = set()
    for item in payload["results"]:
        if not isinstance(item, dict):
            raise GradeError("every entry in `results` must be an object")
        for key in ("recall_pair_id", "answer_correct", "source_correct"):
            if key not in item:
                raise GradeError(f"an entry is missing `{key}`")
        pair_id = item["recall_pair_id"]
        answer_ok = item["answer_correct"]
        source_ok = item["source_correct"]
        if not isinstance(pair_id, int) or isinstance(pair_id, bool):
            raise GradeError("`recall_pair_id` must be an integer")
        if not isinstance(answer_ok, bool) or not isinstance(source_ok, bool):
            raise GradeError(f"the verdicts for pair {pair_id} must be booleans")
        right_answer = item.get("right_answer")
        right_source = item.get("right_source")
        if answer_ok and right_answer is not None:
            raise GradeError(f"pair {pair_id} is answer_correct, so `right_answer` must be null")
        if not answer_ok and not right_answer:
            raise GradeError(f"pair {pair_id} failed the answer, so `right_answer` is required")
        if source_ok and right_source is not None:
            raise GradeError(f"pair {pair_id} is source_correct, so `right_source` must be null")
        if not source_ok and not right_source:
            raise GradeError(f"pair {pair_id} failed the source, so `right_source` is required")
        if pair_id in seen:
            raise GradeError(f"pair {pair_id} was returned more than once")
        seen.add(pair_id)
        verdicts.append(
            Verdict(
                recall_pair_id=pair_id,
                answer_correct=answer_ok,
                source_correct=source_ok,
                right_answer=right_answer,
                right_source=right_source,
            )
        )
    if seen != expected:
        raise GradeError(
            "the returned ids must match the ids asked about exactly: "
            f"missing {sorted(expected - seen)}, unexpected {sorted(seen - expected)}"
        )
    return verdicts


def grade(items: Sequence[dict[str, object]], caller: Caller | None = None) -> list[Verdict]:
    """Grade one board's answers in a single call.

    Args:
        items: One entry per due pair, as built by `store.grade_inputs`.
        caller: The call out. Defaults to the real Claude API.

    Returns:
        One verdict per item.

    Raises:
        GradeError: If the response fails validation twice. Nothing is guessed.
    """
    call = caller or live_caller
    expected = {int(str(item["recall_pair_id"])) for item in items}
    budget = GRADE_BASE + GRADE_PER_PAIR * len(items)
    messages = [{"role": "user", "content": json.dumps(list(items))}]

    rejected = call(messages, budget)
    try:
        return _validate(rejected, expected)
    except GradeError as first:
        # The rejected output goes back as the assistant turn it was, or the
        # model is being told about something it cannot see.
        retry = [
            *messages,
            {"role": "assistant", "content": rejected},
            {
                "role": "user",
                "content": (
                    f"That result was rejected: {first}. Return a corrected result for "
                    "the same items, and nothing else."
                ),
            },
        ]
        try:
            return _validate(call(retry, budget), expected)
        except GradeError as second:
            raise GradeError(
                f"grading failed validation twice; first: {first}; second: {second}"
            ) from second


def live_caller(messages: list[dict[str, str]], max_tokens: int) -> str:
    """The real Claude call. Adaptive thinking at low effort, no streaming."""
    import anthropic
    from anthropic.types import MessageParam, OutputConfigParam

    client = anthropic.Anthropic()
    payload: list[MessageParam] = [
        MessageParam(role="assistant" if m["role"] == "assistant" else "user", content=m["content"])
        for m in messages
    ]
    output_config: OutputConfigParam = {
        "effort": "low",
        "format": {"type": "json_schema", "schema": RESULT_SCHEMA},
    }
    response = client.messages.create(
        model=MODEL_ID,
        max_tokens=max_tokens,
        system=SYSTEM,
        messages=payload,
        output_config=output_config,
    )
    for block in response.content:
        if block.type == "text":
            return str(block.text)
    raise GradeError("the response carried no text block")
