# Data

**Status:** drafted

## Table of Contents

- [Data](#data)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Background](#background)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Schema](#schema)
    - [Sources and notes](#sources-and-notes)
    - [Groups, placements, and the roll](#groups-placements-and-the-roll)
    - [Recall pairs](#recall-pairs)
    - [The draw](#the-draw)
    - [Misses](#misses)
    - [Lifecycle](#lifecycle)

## Purpose

Defines everything memnasium stores: the notes taken from reading, the groups
they are practised inside, the question/answer pairs actually drilled, the
day's draw, and the record of what was missed.

## Scope

Covers tables, columns, keys, and what each row means, plus which step of the
flow writes which rows.

Does **not** cover the skills that write this data, the drill app that reads it,
the Claude grading contract, or the physical stack. Coined terms are defined in
[Project.md](Project.md#glossary) and used identically here.

## Background

A **note** is a fact taken from reading. It is never drilled. What gets drilled
is a **recall pair** — a question, its answer, and the source it came from —
wordsmithed down from a note so it reads in seconds.

A pair is practised inside a **group**: when a pair comes up, every other pair in
its group is shown alongside it with its answer visible, so the fact is recalled
in context rather than as trivia. A pair with no group sits on **the roll** and
comes up alone.

Scheduling runs off a single integer per pair. A **session** is one drill of one
pair. Each day, every pair flips its own coin:

```
p = e^(-α · sessions_correct),   α = 0.5
```

Right → `sessions_correct += 1`. Wrong → `0`. Not drawn, or drawn and never
worked → nothing happened to it, and it flips again tomorrow at the same `p`.

The lag is the expected gap between drills, `e^(α · n)` days:

| `sessions_correct` | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 |
|---|---|---|---|---|---|---|---|---|---|---|
| expected gap (days) | 1 | 1.6 | 2.7 | 4.5 | 7.4 | 12 | 20 | 33 | 55 | 90 |

A new pair sits at 0, so `p = 1` and its first appearance is guaranteed.

## Decisions

- **The recall pair is the scheduled unit, not the note.** Two pairs off one note
  are independent memories and diverge on purpose.
- **Chose `sessions_correct` over a date anchor and a recall-day clock.** Ageing
  by drilling rather than by calendar means a fortnight away costs nothing, and
  it is one integer instead of three dates and a clock table.
- **Chose `placement` over putting `group_id` on the pair.** Grouping and
  wordsmithing are separate skills run days apart; the placement is what records
  "this note belongs here" before any pair exists. The wordsmithing queue is
  exactly *placements with no pairs*.
- **The roll is `group_id IS NULL`,** not a real group row. A residency with no
  context is still a residency; a group row would drill as one vast board.
- **A note in several groups is several placements, hence several pair sets.**
  The same fact worded differently per context, drilled on independent schedules.
  Both may come up the same morning; that is allowed.
- **Notes are immutable once placed.** A note may be corrected or deleted while
  it has no placement; after that it is frozen, so no pair can go stale against
  it. Nothing retires a placed note. Revisit if that stops being true.
- **A moved placement flags `pairs_stale`.** Its pairs were worded for the old
  group's siblings and must be rewritten. Deleting them instead would lose
  `sessions_correct`, so they are kept and marked. The wordsmithing queue is
  *placements with no pairs, or flagged stale*.
- **A pair is retired, never deleted.** `miss` rows point at it and are kept
  forever, so deleting one would either break the reference or throw away the
  study record. A pair dropped by a rewrite — or absorbed by a combine — is
  flagged `retired`: it stops being drawn, stops appearing as context, and keeps
  its history. This is why a pair set can shrink without a cascade.
- **A group emptied by a split is deleted.** It is the one thing in the schema
  that goes away: an empty group matches nothing and clutters every future
  recommendation.
- **A note with a group placement never also has a roll placement.** Otherwise the
  same fact drills twice — once alone, once in context — and the roll stops
  meaning "has no context yet". Promotion off the roll is an `UPDATE`.
- **`miss` stores only what the user wrote — both boxes.** A pair is failed on the
  answer or on the source, so both are kept. The question, the right answer, the
  true source and the raw note all walk out from `recall_pair_id`; storing them
  again would drift.
- **Misses accumulate forever, one row per missed drill.** "I have blown this six
  times" is worth having and costs a few kilobytes.
- **A contested grade writes nothing.** Contesting means the miss was never a
  miss, so there is no row and no correction to reconcile later.
- **Undrilled draw rows are swept, not carried.** They were never sessions, so
  nothing is owed to them; the pair flips again tomorrow at the same `p`.

## Design

### Schema

```sql
-- A publication a note was read in. Deduplicated on entry by search.
CREATE TABLE source (
    id          INTEGER PRIMARY KEY,
    author      TEXT NOT NULL,          -- primary author
    year        INTEGER NOT NULL,
    publication TEXT                    -- book/paper title; optional
);

-- A fact taken from reading, verbatim. Never drilled; never edited.
CREATE TABLE note (
    id         INTEGER PRIMARY KEY,
    source_id  INTEGER NOT NULL REFERENCES source(id),
    statement  TEXT NOT NULL,           -- multi-line, may contain LaTeX
    created_on TEXT NOT NULL            -- ISO date
);

-- A named set of notes that belong together; the frame a pair is recalled in.
CREATE TABLE groups (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT NOT NULL           -- the matching key when placing a note
);

-- A note's residency: in a group, or on the roll (group_id IS NULL).
CREATE TABLE placement (
    id          INTEGER PRIMARY KEY,
    note_id     INTEGER NOT NULL REFERENCES note(id),
    group_id    INTEGER REFERENCES groups(id),
    pairs_stale INTEGER NOT NULL DEFAULT 0,   -- 0/1; pairs need rewriting
    UNIQUE (note_id, group_id)
);

-- SQLite treats NULLs as distinct in a UNIQUE index, so the roll needs its own.
CREATE UNIQUE INDEX placement_roll ON placement (note_id) WHERE group_id IS NULL;

-- The drilled thing: one question, its answer, and its scheduling state.
CREATE TABLE recall_pair (
    id               INTEGER PRIMARY KEY,
    placement_id     INTEGER NOT NULL REFERENCES placement(id),
    question         TEXT NOT NULL,
    answer           TEXT NOT NULL,
    sessions_correct INTEGER NOT NULL DEFAULT 0,
    retired          INTEGER NOT NULL DEFAULT 0    -- 0/1; no longer drilled or shown
);

-- Today's due pairs. One row per pair that flipped heads; deleted when drilled.
CREATE TABLE draw (
    day            TEXT NOT NULL,       -- ISO date
    recall_pair_id INTEGER NOT NULL REFERENCES recall_pair(id),
    PRIMARY KEY (day, recall_pair_id)
);

-- One missed drill. Contested grades write nothing.
CREATE TABLE miss (
    id             INTEGER PRIMARY KEY,
    recall_pair_id INTEGER NOT NULL REFERENCES recall_pair(id),
    day            TEXT NOT NULL,       -- ISO date
    user_answer    TEXT NOT NULL,       -- what was typed in the answer box
    user_source    TEXT NOT NULL        -- what was typed in the source box
);
```

### Sources and notes

`source` exists so the same publication is one row however many notes come from
it, and so entry can search it rather than retyping and duplicating. `author` and
`year` are required — every note came from somewhere, and the source is recalled
and graded along with the answer. `publication` is optional lookup metadata.

`note.statement` holds the note as it was written, verbatim, LaTeX and all.
Rendering is the app's problem; storage is plain text.

### Groups, placements, and the roll

A group is a named set with a **description tight enough to decide whether a new
note belongs** — the description is what the grouping skill matches against.
Groups do not nest and carry no keywords.

A `placement` is one note's residency in one group. Many-to-many falls out: a
note about larval retention in the California Bight genuinely belongs to
*spawning habitat*, *upwelling productivity* and *larval retention* at once, and
gets a placement in each.

`group_id IS NULL` is **the roll** — a note that has no context yet. Its pairs
come up alone, with nothing shown alongside.

A placement with no pairs is a note that has been grouped but not yet
wordsmithed. A placement with `pairs_stale = 1` has pairs written for a group it
no longer sits in. Together they are the queue the wordsmithing skill works from.

A note with any group placement must not also hold a roll placement — moving a
note off the roll is an `UPDATE placement SET group_id`, never a second row.

### Recall pairs

A pair is a question, its answer, and the source — three things asked and three
things graded. The source is not stored on the pair; it walks
`recall_pair → placement → note → source`.

One placement may carry several pairs when a note is long enough to warrant more
than one question. They are independent items with independent
`sessions_correct`.

A **retired** pair is not drawn, is not shown as context, and is not counted in a
group's size. It stays only so the `miss` rows pointing at it keep their meaning.
Every read of a group's pairs filters it out.

Because pairs are written *per placement*, the same note in two groups yields two
sets of pairs, worded for their own context. A question must be **answerable from
its own note, not by elimination from its siblings** — with sibling answers
visible on the board, a group of thresholds can otherwise be solved by reading
rather than recall.

### The draw

Once a day, every pair that is not retired flips
`p = e^(-α · sessions_correct)` and the winners get a `draw` row. There is no cap:
the draw is however big it comes out.

A pair written *after* the day's draw was built is not in it, and waits until
tomorrow. At `sessions_correct = 0` it will certainly be drawn then.

Drilling a pair deletes its `draw` row and updates `sessions_correct`. Remaining
today is `COUNT(*) WHERE day = today`. Rows left over when the next day's draw is
built are deleted — an undrilled pair had no session, so its counter is untouched
and it simply flips again.

The pairs drawn are grouped by their placement's group to form the boards the app
serves; a drawn pair with a null group is drilled on its own.

### Misses

One row per missed drill, kept forever. This is the study record: what was asked,
what was said, what was right, and how many times this particular pair has been
blown. Only the two boxes the user typed into are stored — a pair is failed on
either, so both are kept. Everything else is a join away.

A **contested** grade — Claude marked it wrong, the user overrode — writes no row
and counts as correct.

### Lifecycle

| Step | Writes |
|---|---|
| Enter a note | `INSERT source` if new; `INSERT note` |
| Group new notes | `INSERT placement` per residency (`group_id` NULL for the roll); `INSERT groups` when a new group is coined |
| Wordsmith | `INSERT recall_pair` for placements that have none |
| Move a placement (split, or off the roll) | `INSERT groups` if new; `UPDATE placement SET group_id, pairs_stale = 1`; `DELETE groups` if a group was emptied. Pairs follow with `sessions_correct` intact |
| Rewrite stale pairs | `UPDATE recall_pair SET question, answer`; `UPDATE placement SET pairs_stale = 0` |
| Drop or absorb a pair | `UPDATE recall_pair SET retired = 1`; `DELETE draw` for it. Its `miss` rows are untouched |
| Build the day's draw | `DELETE draw WHERE day < today`; `INSERT draw` per pair that flipped heads |
| Drill a pair, correct | `UPDATE recall_pair SET sessions_correct = sessions_correct + 1`; `DELETE draw` row |
| Drill a pair, missed | `UPDATE recall_pair SET sessions_correct = 0`; `INSERT miss (user_answer, user_source)`; `DELETE draw` row |
| Contest a grade | as correct: `sessions_correct + 1`, `DELETE draw` row, no `miss` row |
