# Grouping

**Status:** implemented

## Table of Contents

- [Grouping](#grouping)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [The flow](#the-flow)
    - [The queue](#the-queue)
    - [Recommending](#recommending)
    - [Deciding](#deciding)
    - [Flagging](#flagging)
    - [Writes](#writes)

## Purpose

Getting newly entered notes out of the queue and into a group, or deliberately
onto the roll. Claude finds candidate groups and commits what the user chooses;
the user decides every placement.

## Scope

Covers the routine pass over notes that have just been entered: what Claude
reads, what it recommends, what the user answers, and what gets written.

Does **not** cover reshaping existing groups, harvesting the roll, or splitting —
that is [Regrouping.md](Regrouping.md). Does not cover turning placements into
questions (see [Wordsmithing.md](Wordsmithing.md)), the schema (see
[Data.md](../Data.md)), or the tools the skill calls (see [api/API.md](../api/API.md)).

## Decisions

- **Claude recommends and commits; the user decides.** The groups are the user's
  mental map, not Claude's ontology, so no placement is ever silent.
- **Claude never coins a group.** New groups exist because the user asked for one.
  Claude may draft the description for approval — that is capture, not decision.
- **"Nothing matches" is a real answer.** A recommender that always recommends is
  noise, and the roll is a legitimate destination, not a failure.
- **Descriptions first, notes on demand.** Every group description fits in context
  at any plausible corpus size; a group's actual notes are pulled only when a
  candidate is borderline.
- **Notes are worked in passes, decided in one message.** A pass of notes comes back
  with their candidates and the user answers them together. Forty separate
  exchanges would kill the habit.
- **Claude flags, it does not act.** A stale group description or a group that has
  grown fat is worth saying out loud and never worth fixing unasked.
- **Size is shown, not judged.** A candidate is listed with its note count so the
  user can see a group getting big. Whether that matters is the user's call.

## Design

### The flow

```
ungrouped notes ──▶ Claude reads all group descriptions
                              │
                    per note: candidates + why, or "nothing matches"
                              │
      user answers the pass: group X · X and Y · the roll · new group Z
                              │
                       Claude writes placements
```

### The queue

Notes with **no placement at all** — entered and never triaged. This is distinct
from a note on the roll, which holds a placement with a null `group_id` and *has*
been decided on. See [Data.md](../Data.md#groups-placements-and-the-roll).

### Recommending

Claude reads every group's name and description — the description is the matching
key — and for each note in the pass offers the plausible fits:

```
Note 512  Puget Sound: onset of piscivory 70 mm inshore, 130 mm offshore
  → Onset of piscivory (4 notes)  — regional thresholds for the same transition
  → What Chinook eat (22 notes)   — weaker; this is about a transition, not diet

Note 519  Trawl surveys underestimate juvenile abundance nearshore
  → nothing matches. Closest is Sampling bias (2 notes) and it is not close.
```

Each candidate carries its **note count** and one line of *why*. Where a
recommendation turns on something the description does not settle, Claude pulls
that group's notes and says what it found.

### Deciding

The user replies for the whole pass. A note may go to one group, several, or the
roll; or the user may name a new group, in which case Claude drafts a description
for approval and creates it with that note in it.

Nothing is written until the user has answered. Decisions commit as they are
given — arguing about note 519 does not un-commit note 512.

### Flagging

Two things Claude says and never acts on:

- **A description has drifted** — it no longer describes what the group holds, so
  every future recommendation against it gets worse.
- **Roll notes may belong with a newly created group** — offered as a handoff to
  [Regrouping.md](Regrouping.md), not done here.

### Writes

| Action | Writes |
|---|---|
| Place into an existing group | `INSERT placement (note_id, group_id)` |
| Place on the roll | `INSERT placement (note_id, group_id = NULL)` |
| Create a group the user named | `INSERT groups (name, description)`, then the placement |

Every placement lands with no pairs, which is what puts it in the
[wordsmithing](Wordsmithing.md) queue.
