# Kin

**Status:** drafted

## Table of Contents

- [Kin](#kin)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Background](#background)
  - [Decisions](#decisions)
  - [Design](#design)
    - [The day](#the-day)
    - [Selection](#selection)
    - [Grouping](#grouping)
    - [Scoring](#scoring)
    - [Worked example](#worked-example)
    - [Known limits](#known-limits)

## Purpose

The first memnasium game. Kin drills telling apart **close relatives** — it deliberately builds each
round out of clades that sit near each other in the tree, so the player has to discriminate rather
than recognise.

## Scope

Covers edge selection, group construction, and how a submission updates practice state. This is
Kin's front door — the rest of it:

| Layer  | Doc                                | Answers                    |
| ------ | ---------------------------------- | -------------------------- |
| screen | [app/Kin.md](../app/Kin.md)        | what the player sees        |
| wire   | [api/Kin.md](../api/Kin.md)        | what the client calls       |
| tables | [data/Kin.md](../data/Kin.md)      | what gets written down      |
| how    | [algorithms/Kin.md](../algorithms/Kin.md) | the draw, distance, grouping |

Does **not** cover the knowledge being drilled (see [data/Fish.md](../data/Fish.md)) or any other
game.

## Background

Recognition is easy when the answer is the only plausible one on screen. Put ten congeners side by
side and the same question gets hard in exactly the way field identification is hard. Kin makes
nearness the point: the group is the confusion set.

## Decisions

- **Chose nearest-relative groups over random groups** because a random group is answerable by
  elimination and teaches nothing about discrimination.
- **Chose distance as plain path length in the parent tree** over "shared level" because
  [Fish.md](../data/Fish.md) allows level skips, which produce odd distances that a shared-level
  rule cannot express.
- **Chose one group per level** over mixed-level groups because "which of these is it" is only a
  question when the candidates are comparable.
- **Chose all-at-once submission** over per-edge feedback because per-edge feedback turns the board
  into a search, and the last edge into a freebie.
- **Chose to score only the first attempt** because retries are practice, not evidence — a player
  who needs three tries did not recall it.
- **Chose to require a complete board to submit** over partial submission, so there is no way to
  duck an edge — every due edge on a played board gets scored.
- **Chose to persist and resume a board** over discarding it, so closing the app mid-board is not
  an answer and not a reroll — the board is exactly where it was when the player returns.
- **Chose played days over calendar days** for Δt because the decay models forgetting between
  *practice*, and time away does not make a fact more due than the last one you missed.
- **Chose not to hide parent edges.** The tree is the board's scaffolding — hiding it would make
  distance unreadable to the player. Drilling it is a different game.

## Design

### The day

The day's shape — generating a set, picking a group size, carry-over — is the screen's, and lives in
[app/Kin.md](../app/Kin.md). This doc is the rules underneath it: which edges are candidates, how a
group is built, and what a submission does.

### Selection

Every candidate edge is drawn on its own, with a chance that falls the longer it has gone without
being missed — so a freshly missed edge is certain to come back and a well-known one rarely does.
Edges that win their draw are **due** for the day. The formula and the procedure are
[algorithms/Kin.md](../algorithms/Kin.md).

Candidate edge types:

| Edge table              | In play |
| ----------------------- | ------- |
| `clade_image_edges`     | yes     |
| `clade_character_edges` | yes     |
| `character_src_edges`   | yes     |
| `image_src_edges`       | yes     |
| `clade_parent_edges`    | no — scaffolding |

An **anchor** is a clade with at least one due edge, and the set carries every edge of every anchor —
the drawn ones to be answered, the rest shown filled in.

### Grouping

A group is one anchor picked at random plus its nearest relatives **at the same level**, up to the
size the player asked for. Nearness is path length through the parent tree, so the group is a
confusion set: congeners first, then the rest of the family.

A group runs short rather than padding with clades that have nothing due, and the next group may sit
at a different level. Anchors leave the pool once dealt, and an anchor is never split across two
boards. Distance, tie-breaking and the exact procedure are
[algorithms/Kin.md](../algorithms/Kin.md).

### Scoring

An edge scores once, the first time the board is submitted with that edge in place:

| First submission | `sessions_since_last_failed` |
| ---------------- | ---------------------------- |
| correct          | += 1                         |
| incorrect        | → 0                          |

Later retries change nothing — they are practice, not evidence.

A board ends one of two ways:

| Ending      | Edges already locked | Every other edge           | Anchors  |
| ----------- | -------------------- | -------------------------- | -------- |
| all locked  | scored                | —                          | consumed |
| **Move on** | keep their score      | → 0, including unsubmitted | consumed |

Closing the app is not an ending. The board is written down (see [data/Kin.md](../data/Kin.md)) and
comes back exactly as it was, locks and all.

**Move on** is giving up, so anything not already recalled counts as missed — taking it before the
first submission fails the whole board, which is why it confirms first.

### Worked example

`n = 3`, anchor *Artificialus claudus*.

```
anchor pool at species level:  claudus, opus, minor, borealis
d(claudus, opus)     = 2   (same genus)
d(claudus, minor)    = 4   (same family, via another genus)
d(claudus, borealis) = 3   (family, skipped genus)

group = { claudus, opus, borealis }
```

The board carries three species, their due images and characters, and the source nodes for any due
`character_src` edges. *minor* waits for the next group.

### Known limits

Neither palette is padded — both hold only what the group actually contains — so both can get small
enough to answer by elimination. Accepted, and recorded so it is not mistaken for an oversight.

- **The citation pool can be trivial.** It holds only the sources behind due `src` edges, so if
  every due card cites the same paper the pool is one chip and the source half is a giveaway.
- **A small group is answerable by elimination.** The clade palette holds the group's anchors and
  nothing else, so a group of one has a single chip and every clade slot on that board is free; a
  group of two is a coin flip. Asking for a small group is the player's own choice — but a group can
  also be *involuntarily* short, when a level has only one or two anchors left, and then the free
  answer is not chosen.

The fix for both is the same and was declined: pad each palette with plausible extras from outside
the group — nearest same-level clades, other sources — keeping the group itself at real anchors.
