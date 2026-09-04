# Drilling

**Status:** changed

## Table of Contents

- [Drilling](#drilling)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [The flow](#the-flow)
    - [Building the draw](#building-the-draw)
    - [The fork](#the-fork)
    - [A board](#a-board)
    - [A roll batch](#a-roll-batch)
    - [Answering](#answering)
    - [Grading](#grading)
    - [Contest and confirm](#contest-and-confirm)
    - [Stopping early](#stopping-early)
    - [Writes](#writes)

## Purpose

The morning loop: build the day's draw, work through it a board at a time,
recall each due pair in front of its group, get graded, and record what stuck.

## Scope

Covers the draw, what a board is, how answering and grading work, and what the
loop writes.

Does **not** cover the schema or the scheduling maths (see [Data.md](../Data.md)),
the screen's layout (see [app/Drilling.md](../app/Drilling.md)), the wording of the grading prompt
(see [Claude.md](../Claude.md)), or how pairs came to exist (see
[Wordsmithing.md](Wordsmithing.md)).

## Decisions

- **A board is the unit of everything** — one group, one screenful, one grading
  call, one confirm. It is what makes the context worth reading: you read the
  group once and answer everything of its that is due.
- **Confirm is the only write point.** Grading is read-only, so a contested grade
  never writes a miss row that has to be taken back, and an abandoned board
  changes nothing.
- **The draw is built by a button, not on open.** Seeing "14 boards · 118 due"
  before starting is worth the click.
- **The size of the draw is predicted before it is built, and remembered after.**
  How big a morning is going to be is the one thing worth knowing before
  committing to it, and how big it turned out against that prediction is worth
  knowing after. See [Data.md](../Data.md#the-expectation).
- **The clock never ends a board.** A board started before midnight and answered
  after it is the same board: the current draw is the one most recently built, not
  the one matching today's date. See [Data.md](../Data.md#the-draw).
- **Built once a day, and the day remembers it.** Drilling consumes draw rows, so
  a morning worked to the end empties them — and if "built" meant "has rows", the
  button would come back and draw the same day again, drilling pairs twice. A
  `draw_day` marker records that the day was built. See
  [Data.md](../Data.md#the-draw).
- **`N` is a pacing commitment, not a batch.** Asking for three boards gives three
  boards in sequence, each with its own submit, grade and confirm. One board per
  Claude call; a confirm never spans groups.
- **A wrong source fails the pair.** `sessions_correct` is one integer, so the two
  boxes collapse to one verdict, and the source is meant to be load-bearing —
  the point is being able to walk a memory back to where it came from.
- **A missed pair shows its answer, not its note.** The answer is what is being
  judged and what the next drill will want; the note behind it is one join away
  if it is ever needed.
- **Grading returns a verdict and, on a miss, the right answer and the right
  source. No commentary.** Both boxes are graded, so a miss must say which one
  failed and what it should have been. Enough to judge whether to contest, and
  nothing paid for per pair beyond that.
- **Stale pairs are still drilled.** A pair whose placement is flagged
  `pairs_stale` was worded for a group it no longer sits in, so it may read oddly
  and its elimination guard is off. It is drawn anyway — holding stale pairs out
  of the draw would mean a lazy fortnight of not wordsmithing quietly shrinks the
  practice.
- **No skipping.** A board taken is a board worked.
- **Board order within a mode is arbitrary.** Nothing about which group comes
  first is worth designing.

## Design

### The flow

```
"1,204 pairs · ~87 expected" ──▶ build the draw
                                       │
        "118 drawn · ~87 expected · 34 due · 6 boards · 4 on the roll"
                                       │
                            ┌──────────┴──────────┐
                      do N boards           do N from the roll
                            │                     │
                            └── submit ─▶ grade ─▶ contest ─▶ confirm ──▶ the fork
```

### Building the draw

A button, once a day. Every live `recall_pair` flips its own coin at
`p = e^(-α · sessions_correct)` — see [Data.md](../Data.md#background) — and each
winner gets a `draw` row for today, alongside a `draw_day` marker recording the
date, the size of the draw, and the size it was
[expected](../Data.md#the-expectation) to be. There is no cap; the draw is
however big it comes out.

Idempotent on the marker: once today has been built the button is gone for the
rest of the day, whether or not any of it is left. Building first deletes the rows
of every earlier draw — an undrilled pair had no session, its counter is untouched,
and it has already flipped again on equal terms.

Until that next build, the previous draw is still **the current draw** and is
still workable. That is what makes a sitting survive midnight, and it is why a
morning after several days away shows the remains of the last draw with the Build
button beside it.

### The fork

Once the day is built, this is where every board and batch is started from, and
where the morning ends. When the last pair has been confirmed the numbers read
zero and the fork says so — `118 drawn · ~87 expected · none left` — rather than
offering to build again.

The draw splits by placement. Drawn pairs whose placement has a group become
**boards**, one per group; drawn pairs on the roll are loose. The user picks a
mode and a count: *N boards*, or *N from the roll*. After each board or batch is
confirmed, control returns here with the numbers updated.

### A board

One group. Every pair belonging to that group is on it:

| | shown | typed into | graded |
|---|---|---|---|
| **due pair** — has a `draw` row today | question | answer, source | yes |
| **context pair** — every other pair in the group | question **and** answer, and its source | — | no |

Context pairs are the point of the whole design: the due question is answered
with its neighbours' answers visible, so the fact is placed in a structure rather
than fished for alone.

This makes **group size the context reading budget**. Every non-due pair in the
group is read every time any of the group comes up, so the ceiling on group size
is what decides whether a morning is bearable. It is a constraint, not a
preference — see [Regrouping.md](Regrouping.md).

### A roll batch

`N` pairs whose placement has no group, drawn today, presented together. They are
unrelated to each other and carry no context — each is a question and two boxes.
Otherwise identical to a board: one submit, one grading call, one confirm.

### Answering

Each due pair takes two boxes:

- **the answer** — what the pair asks for
- **the source** — the author and year it came from

Both are required and both are graded.

### Grading

On submit, the board's due pairs go to Claude in one call: for each, the question,
the true answer, the true source, and what the user wrote in each box. It returns
per pair:

- a **verdict for each box** — the answer, and the source. The pair is correct
  only if both are.
- for each box that failed, **what it should have been** — shown so the user can
  judge whether to contest.

Nothing is written yet.

### Contest and confirm

Each missed pair carries a contest control. Contesting means Claude was wrong and
the answer stood: the pair counts as correct and no miss is recorded. It is the
user's call and takes no round trip.

**Confirm** commits the board in one transaction — see [Writes](#writes). Until
it is pressed, nothing on the board has happened; a board graded and abandoned
leaves its `draw` rows in place, to be worked later in the day or swept by
tomorrow's build.

### Stopping early

Stopping is walking away. Pairs still holding `draw` rows were never sessions:
their `sessions_correct` is untouched, no miss is recorded, and the next build
sweeps the rows and flips them again at exactly the same odds.

Nothing expires at midnight. What ends a draw is the next one being built.

### Writes

| Action | Writes |
|---|---|
| Build the draw | `DELETE draw WHERE day < today`; `INSERT draw` per pair that flipped heads; `INSERT draw_day (day, drawn, expected)` |
| Submit, grade, contest | nothing |
| Confirm a board or roll batch | one transaction: for each **correct or contested** pair `UPDATE recall_pair SET sessions_correct = sessions_correct + 1`; for each **missed** pair `UPDATE recall_pair SET sessions_correct = 0` and `INSERT miss (recall_pair_id, day, user_answer, user_source)`; `DELETE draw` for every pair on the board |
