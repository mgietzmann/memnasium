# Claude

**Status:** drafted

## Table of Contents

- [Claude](#claude)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [One call](#one-call)
    - [Grade](#grade)
    - [Enforcing the contract](#enforcing-the-contract)
    - [Stack](#stack)
    - [Cost](#cost)

## Purpose

Defines the app's use of the Claude API: grading a board's answers. One call, at
one moment, with a shape the app can parse without worrying.

## Scope

Covers the grade call — its inputs, outputs, prompt at design altitude, and the
rails that make a malformed response an error rather than bad data.

Does **not** cover the skills ([Grouping](flows/Grouping.md),
[Wordsmithing](flows/Wordsmithing.md), [Regrouping](flows/Regrouping.md)) — those
run inside a Claude Code session and make no API call from the app. Does not cover
the contest override (a local control, no round trip — see
[flows/Drilling.md](flows/Drilling.md#contest-and-confirm)) or where results are
written (see [Data.md](Data.md)).

## Decisions

- **One call, and only grading.** The questions are written ahead of time by
  [wordsmithing](flows/Wordsmithing.md), so there is no build-sheet call at drill
  time. This is the whole reason pairs exist rather than raw notes.
- **The pair's `answer` is the only ground truth.** The note it came from is *not*
  sent — a longer, richer statement invites grading against the note instead of
  the question that was actually asked.
- **Two judgements, one outcome.** The answer box and the source box are graded
  separately, so a miss can say which failed and show what was right; the pair is
  correct only if both are.
- **One call per board, batched.** A six-pair board is one round trip, not six.
- **Keyed by `recall_pair_id`, never by position.** A dropped or reordered item
  fails an id-set check instead of silently pairing an answer with the wrong pair.
- **Structured outputs, then validated.** `output_config.format` constrains the
  response shape directly; it is validated anyway. Forcing a shape makes malformed
  output unlikely, validation makes it always detected.
- **Retry once, then fail loud.** A validation failure goes back to Claude with the
  specific error. A second failure is a surfaced error, never a guess.
- **No commentary.** A verdict and, on a miss, the right value. That is everything
  needed to decide whether to contest.
- **No caching.** Every board is different and the stable prefix is below the
  minimum cacheable size.
- **Low effort, and `max_tokens` budgeted for thinking.** Thinking tokens are
  output tokens: they count against `max_tokens` and they are billed. Grading a
  handful of short answers against a given key is bounded work, so effort is set
  low and the budget carries headroom for the reasoning as well as the visible
  result. Sizing for the visible output alone would truncate every board.
- **`claude-opus-5`, in config.** Judging paraphrases and near-miss numbers is the
  judgment-heavy part, and it is the thing the whole app hinges on. See
  [Cost](#cost).
- **Injectable client.** The real call sits behind a swappable function so tests
  never touch the API.

## Design

### One call

```
board submitted ──▶ [ Grade ] ──▶ verdicts ──▶ user contests ──▶ confirm
                  (1 Claude call)              (no call)        (no call)
```

Context pairs are never sent. They are already answered on screen and have
nothing to grade.

### Grade

**In:** for each **due** pair on the board —

| Field | Is |
|---|---|
| `recall_pair_id` | the key |
| `question` | what was asked |
| `answer` | the ground truth for the answer box |
| `source` | the ground truth for the source box: author and year |
| `user_answer` | what was typed in the answer box |
| `user_source` | what was typed in the source box |

**Out:** one result per input id —

```json
[
  {
    "recall_pair_id": 812,
    "answer_correct": false,
    "source_correct": true,
    "right_answer": "70 mm",
    "right_source": null
  }
]
```

`right_answer` and `right_source` are populated only for the box that failed, and
are the ground truth restated for display. The pair is **missed** unless both
`answer_correct` and `source_correct` are true — see
[flows/Drilling.md](flows/Drilling.md#grading).

Claude is told: judge each answer against the given `answer` and each source
against the given `source`. Be fair to paraphrase, to equivalent maths, and to
units expressed differently. The source must name the right author and the right
year; the publication is not asked for. Do not reward an answer that is merely
adjacent to the truth, and do not penalise one that is right but differently put.

Statements may contain LaTeX. Judge equivalence, not formatting.

### Enforcing the contract

Four layers, the last of which turns any non-conforming response into a surfaced
error rather than silent bad data.

1. **Constrain the shape** with `output_config.format` set to the result schema.
2. **Validate it anyway** — one result per input id, all keys present, booleans
   are booleans, `right_answer` present exactly when `answer_correct` is false
   (and likewise for the source).
3. **Match by id.** The returned id set must equal the input id set exactly — no
   extras, none missing, order irrelevant.
4. **Retry once, then fail.** The specific validation error goes back with a
   request for a corrected result. A second failure raises a typed error and the
   board reports it; nothing is written and nothing is guessed.

### Stack

- `anthropic` SDK, one `messages` call. Adaptive thinking at
  `output_config: {effort: "low"}`; no streaming — a board's output is small and
  bounded.
- `MODEL_ID = claude-opus-5` in config, swappable in one place.
- The real call sits behind an injectable function; tests pass a stub.
- **`max_tokens` sized from the batch, thinking included.** The visible result is
  a small object per pair plus the restated truth on a miss, but the thinking that
  precedes it is charged to the same budget. Roughly `1024 + 400·N`, so a ten-pair
  board budgets about 5k rather than the ~1.5k the visible output alone suggests.
  Tune the per-item constant once real boards have been graded.
- The system prompt carries the rules and a worked example; the board's pairs are
  the user message.

### Cost

A six-pair board is roughly 1,400 input tokens and, counting the thinking that is
billed with it, on the order of 1,000 output. At `claude-opus-5` rates
($5 / $25 per Mtok) that is about **3¢ a board** — a heavy morning of fifteen
boards and a roll batch runs near 55¢, so something like $15 a month.

The thinking is the larger half of that and the least predictable; the figure is
an estimate until real boards have been graded.

The build-sheet call that a raw-note design would need at drill time does not
exist here, because the questions were written once, in advance, by
[wordsmithing](flows/Wordsmithing.md).
