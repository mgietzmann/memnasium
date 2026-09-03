# Wordsmithing

**Status:** drafted

## Table of Contents

- [Wordsmithing](#wordsmithing)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [The flow](#the-flow)
    - [The queue](#the-queue)
    - [What Claude reads](#what-claude-reads)
    - [One answer, one pair](#one-answer-one-pair)
    - [Writing a question](#writing-a-question)
    - [Rewriting](#rewriting)
    - [Review](#review)
    - [Writes](#writes)

## Purpose

Turning a placement into the questions that actually get drilled: short, sharp
question/answer pairs cut from a note and worded for the group the note sits in.

## Scope

Covers what makes a good pair, how many a note earns, how a rewrite differs from
a first write, and what the user approves.

Does **not** cover how notes came to be placed (see [Grouping.md](Grouping.md),
[Regrouping.md](Regrouping.md)), how pairs are drilled (see
[Drilling.md](Drilling.md)), or the schema (see [Data.md](../Data.md)).

## Decisions

- **One answer, one pair.** A pair holds a single fact. Two numbers that are
  genuinely two facts are two pairs; a list that only means anything whole is one
  pair whose answer is the list.
- **Pairs are written per placement, not per note.** The same note in two groups
  gets two sets of questions, worded for the siblings each will sit beside.
- **One-liners where possible.** The whole point of pairs over raw notes is that a
  board of them reads in seconds. A long answer is a signal the pair holds more
  than one fact.
- **A question must be answerable from its own note.** Sibling answers are visible
  on the board, so a question that can be solved by elimination from them tests
  reading, not recall.
- **The source is never in the pair.** It is asked as its own box at drill time and
  walks from the note — see [Drilling.md](Drilling.md#answering).
- **Claude reads the group's notes, not just its pairs.** The notes are what say
  whether a fact is genuinely distinct from its neighbours.
- **The user approves per note.** A run comes back, the user strikes what is wrong,
  the rest lands. A badly worded pair does not merely annoy — it teaches the wrong
  thing and resets a counter on a technicality.
- **A rewrite may split or combine, with approval, and the counters are
  inherited.** The memory was real even when the wording was not, so nothing goes
  back to zero for a rewording.
- **A replaced pair is retired, not deleted.** Its misses are kept forever, so it
  keeps its row and stops being drilled. See [Data.md](../Data.md#decisions).

## Design

### The flow

```
placements with no pairs, or flagged stale
                │
   Claude reads the note, its group's notes, its group's pairs
                │
      proposes pairs, one pass of notes at a time
                │
        user strikes what is wrong ──▶ written, stale flag cleared
```

### The queue

A placement is waiting when it has **no pairs** (newly placed) or when
`pairs_stale = 1` (moved into a different group, so its pairs were written for
the wrong siblings). See [Data.md](../Data.md#groups-placements-and-the-roll).

Roll placements are in the queue too. Their pairs have no context to be worded
against, which makes them the ones most in need of being self-contained.

### What Claude reads

| Input | Why |
|---|---|
| the note's statement | the material |
| the group's other notes | whether this fact is genuinely distinct |
| the group's existing pairs | what is already asked, and what could be eliminated |

### One answer, one pair

A pair holds one fact.

```
Note 512  Puget Sound: onset of piscivory is 70 mm inshore, 130 mm offshore

  Q  At what length do Puget Sound Chinook turn piscivorous inshore?
  A  70 mm
  Q  At what length do Puget Sound Chinook turn piscivorous offshore?
  A  130 mm
```

Two facts, two pairs, two counters — they can and should diverge. But where the
list *is* the answer, splitting it destroys it:

```
Note 604  River outflow direction reverses under wind stress, tidal phase,
          and freshwater discharge

  Q  What makes river outflow direction change?
  A  Wind stress, tidal phase, and freshwater discharge
```

Asking for one of the three would be asking a different, easier question.

### Writing a question

- **Specific enough to be unambiguous in its group.** "At what length?" is a
  broken question on a board of five length thresholds.
- **Not answerable by elimination.** Siblings are visible with their answers.
- **Short.** One line of question, one line of answer, whenever the fact allows.
- **LaTeX is preserved** from the note and rendered on the board.

### Rewriting

A stale placement's pairs are rewritten against their new group. The pairs stay —
they carry `sessions_correct`, which the move did not invalidate.

A rewrite may change the number of pairs, with the user's say-so either way:

| | Result |
|---|---|
| **split** — one pair becomes two | the original is reworded and kept; the second is a new pair inheriting its `sessions_correct` |
| **combine** — two pairs become one | a new pair inheriting the **lower** of the two; both originals are retired |

Combining takes the lower count deliberately: the weaker of the two memories is
the honest description of the merged one. It produces a **new** pair rather than
keeping one of the originals, because neither original is the question any more —
and both keep their own miss history under their own ids.

The stale flag clears when the rewrite is written.

### Review

A pass of notes comes back with their proposed pairs. The user strikes or corrects
what is wrong; everything else is written. Splits and combines during a rewrite
are called out explicitly rather than left to be noticed.

### Writes

The placement's whole pair set is written in one call — see
[api/API.md](../api/API.md#writing-a-pair-set), which is where the rules below are
enforced.

| Action | Writes |
|---|---|
| First write for a placement | `INSERT recall_pair` per approved pair (`sessions_correct = 0`) |
| Reword an existing pair | `UPDATE recall_pair SET question, answer` |
| Split a pair | `UPDATE` the original; `INSERT` the second, inheriting the original's `sessions_correct` |
| Combine pairs | `INSERT` the new pair with the lower `sessions_correct`; `UPDATE ... SET retired = 1` on both originals |
| Drop a pair | `UPDATE recall_pair SET retired = 1` |
| Finish a placement | `UPDATE placement SET pairs_stale = 0` |
