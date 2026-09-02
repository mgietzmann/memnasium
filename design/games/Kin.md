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
    - [The board](#the-board)
    - [Scoring](#scoring)
    - [Worked example](#worked-example)
    - [Known limits](#known-limits)

## Purpose

The first memnasium game. Kin drills telling apart **close relatives** — it deliberately builds each
round out of clades that sit near each other in the tree, so the player has to discriminate rather
than recognise.

## Scope

Covers the daily loop, edge selection, group construction, the board, and how a round updates
practice state.

Does **not** cover the data model (see [Data.md](../Data.md)) or any other game.

## Background

Recognition is easy when the answer is the only plausible one on screen. Put ten congeners side by
side and the same question gets hard in exactly the way field identification is hard. Kin makes
nearness the point: the group is the confusion set.

## Decisions

- **Chose nearest-relative groups over random groups** because a random group is answerable by
  elimination and teaches nothing about discrimination.
- **Chose distance as plain path length in the parent tree** over "shared rank" because
  [Data.md](../Data.md) allows rank skips, which produce odd distances that a shared-rank rule
  cannot express.
- **Chose one group per level** over mixed-level groups because "which of these is it" is only a
  question when the candidates are comparable.
- **Chose all-at-once submission** over per-edge feedback because per-edge feedback turns the board
  into a search, and the last edge into a freebie.
- **Chose to score only the first attempt** because retries are practice, not evidence — a player
  who needs three tries did not recall it.
- **Chose to require a complete board to submit** over partial submission, so there is no way to
  duck an edge — every due edge on a played board gets scored.
- **Chose to score an abandoned board not at all** because a board the player never submitted
  produced no evidence about any of its edges.
- **Chose played days over calendar days** for Δt because the decay models forgetting between
  *practice*, and time away does not make a fact more due than the last one you missed.
- **Chose not to hide parent edges.** The tree is the board's scaffolding — hiding it would make
  distance unreadable to the player. Drilling it is a different game.
- **Chose tap-then-tap over drag** to draw an edge, because dragging a line between two targets is
  fiddly on a trackpad and worse on touch.
- **Chose a grid of cards over a single tall column** so photos stay large enough to identify and a
  group of ten still fits on one screen without scrolling.
- **Chose a citation slot on each card over a fourth column** because a source is a short label, and
  a column of them would double the board's width to hold `(Brown, 2014)`.
- **Chose to consume nothing** — source chips and species stay selectable after use — so the board
  cannot be solved by elimination. The player has to actually know.
- **Chose to print attachments on the card over drawing lines**, because lines from a grid back to a
  left-hand column are the spaghetti the grid was chosen to avoid, and a filled slot reads faster
  than a traced line.

## Design

### The day

The day's shape — generating a set, picking a group size, progress, carry-over — is the shell's, and
lives in [app/Games.md](../app/Games.md). Kin supplies the three pieces beneath it: which edges are candidates,
how a group is built, and what the board is.

### Selection

Each candidate edge is drawn independently with probability

```
p = e^(-α · Δt)        α = 0.2        Δt = sessions_since_last_failed
```

so a freshly missed edge (Δt = 0) is certain to appear, and the chance halves every ~3.5 played
sessions. Edges that win their draw are **due** for the day.

Candidate edge types:

| Edge table              | In play |
| ----------------------- | ------- |
| `clade_image_edges`     | yes     |
| `clade_character_edges` | yes     |
| `character_src_edges`   | yes     |
| `image_src_edges`       | yes     |
| `clade_parent_edges`    | no — scaffolding |

### Grouping

An **anchor** is a clade with at least one due edge. Groups are built one at a time:

1. Pick an anchor at random from the remaining anchors. Its level *L* fixes the group's level.
2. Take the *n−1* remaining anchors at level *L* that are nearest the anchor by path length through
   `clade_parent_edges`, ties broken at random.
3. If fewer than *n−1* remain at level *L*, the group is short. No padding with clades that have
   nothing due.

Anchors leave the pool once their board is submitted; an abandoned board returns them (see
[app/Games.md](../app/Games.md)). The next group starts over at step 1, possibly at a different level.

Distance is the number of parent edges on the path between two clades:

```
Family ─── Genus ─── Species A
   └───────────────── Species B          d(A,B) = 3
```

Two species under one genus are 2 apart; skips make odd distances normal, which is fine — only the
ordering matters.

### The board

Three regions: the group's clades on the left, a grid of **cards** in the middle, and the pool of
**citations** on the right.

```
 CLADES            CARDS                                CITATIONS
┌──────────┐   ┌──────────────┐ ┌──────────────┐      ┌──────────────┐
│A. claudus│   │ A. opus      │ │      ▢       │      │ Brown, 2014  │
└──────────┘   ├──────────────┤ ├──────────────┤      ├──────────────┤
┌──────────┐   │  [ photo ]   │ │ "3 dorsal    │      │ Miller, 2019 │
│A. opus   │   │              │ │   spines"    │      ├──────────────┤
└──────────┘   ├──────────────┤ ├──────────────┤      │ Okafor, 2021 │
┌──────────┐   │ Brown, 2014  │ │      ▢       │      └──────────────┘
│A.borealis│   └──────────────┘ └──────────────┘
└──────────┘   ┌──────────────┐ ┌──────────────┐
               │      ▢       │ │      ▢       │
               ├──────────────┤ ├──────────────┤
               │  [ photo ]   │ │ "black caudal│
               │              │ │   blotch"    │
               ├──────────────┤ ├──────────────┤
               │      ▢       │ │      ▢       │
               └──────────────┘ └──────────────┘
```

A **card** is one image node or one character node, and is on the board if either of its edges is
due. Every card has the same three bands — a clade slot on top, the payload, a source slot beneath:

| Slot  | Edge                                          | If not due            |
| ----- | --------------------------------------------- | --------------------- |
| clade | `clade_image_edges` / `clade_character_edges` | shown already filled  |
| src   | `image_src_edges` / `character_src_edges`     | shown already filled  |

No lines are ever drawn. An attachment is the name printed in the slot, so a card either reads
`A. opus` / `Brown, 2014` or shows an empty box. The citation pool holds the sources behind the
board's due `src` edges, and nothing else.

**Interaction** — one grammar, both slots:

```
tap clade → tap a card's clade slot     fills it
tap chip  → tap a card's src slot       fills it
tap a filled slot                       clears it
```

Nothing is consumed. A clade takes several cards (a species has more than one character), and a
citation chip backs as many cards as the player puts it on, so counting what is left over tells the
player nothing.

**States.** Every blank must be filled before **Submit** enables. On submit, correct attachments
**lock** and incorrect ones clear, and the player fills them again. This repeats until the board is
fully locked, or the player takes **Move on**, which is always available, asks to confirm, and then
gives the board up. How the three slot states look is in
[standards/Style.md](../standards/Style.md).

### Scoring

An edge scores once, the first time the board is submitted with that edge in place:

| First submission | `sessions_since_last_failed` |
| ---------------- | ---------------------------- |
| correct          | += 1                         |
| incorrect        | → 0                          |

Later retries change nothing — they are practice, not evidence.

A board ends one of three ways:

| Ending          | Edges already locked | Every other edge          | Anchors      |
| --------------- | ------------------- | ------------------------- | ------------ |
| all locked      | scored               | —                         | consumed     |
| **Move on**     | keep their score     | → 0, including unsubmitted | consumed    |
| walked away     | keep their score     | unchanged                 | back in pool |

**Move on** is giving up, so anything not already recalled counts as missed — taking it before the
first submission fails the whole board, which is why it confirms first. Walking away is not an answer at all: the board is
discarded, nothing further is scored, and the anchors return for a later group.

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

- **The citation pool can be trivial.** It holds only the sources behind due `src` edges, so if
  every due card cites the same paper the pool is one chip and the source half is a giveaway.
  Accepted; the fix is pulling distractor citations from outside the group.
