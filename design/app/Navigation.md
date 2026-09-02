# Navigation

**Status:** implemented

## Table of Contents

- [Navigation](#navigation)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Map](#map)
    - [Home](#home)
    - [Games](#games)

## Purpose

How the player gets anywhere. memnasium does two things — play games and take notes — and this is
the doc that says so.

## Scope

Covers the top-level map, the home screen, and the games list.

Does **not** cover any game's own screen (see [Kin.md](Kin.md)), entering fish (see
[Fish.md](Fish.md)), or how anything looks (see [../standards/Style.md](../standards/Style.md)).

## Decisions

- **Chose two cards on home over a sidebar or a tab bar**, because there are exactly two things to
  do and persistent chrome would be chrome around nothing.
- **Chose to land on home rather than on today's game**, so opening the app to add a note does not
  route through the games list.
- **Chose a card per game showing that game's own state** over a plain list, because the only thing
  worth knowing at a glance is whether today's work is done.
- **Chose to let each game report its own state.** Play tables are per-game (see
  [../data/Kin.md](../data/Kin.md)), so there is no shared query and the list is a row of answers,
  not one.
- **Chose to let an open board outrank the anchor count.** A set whose anchors are all dealt is not
  finished if a board is still being played, and treating it as finished is what lets a new draw
  discard it.

## Design

### Map

```
Home ──┬──► Games ──► a game's screen
       └──► Fish entry
```

### Home

Two cards, nothing else.

```
┌─────────────────────┐  ┌─────────────────────┐
│       Games         │  │       Entry         │
│  play today's sets  │  │  add what you read  │
└─────────────────────┘  └─────────────────────┘
```

### Games

One card per game, each showing whatever state that game reports.

```
┌──────────────────────────┐  ┌──────────────────────────┐
│ Kin                      │  │ <next game>              │
│ 5 / 12 anchors           │  │ not generated            │
└──────────────────────────┘  └──────────────────────────┘
```

| Set's `generated_on` | Anchors left | Open board | Shown              |
| -------------------- | ------------ | ---------- | ------------------ |
| no set at all        | —            | —          | `not generated`    |
| any                  | any          | **yes**    | `board in progress` |
| today                | `n`          | no         | `0 / n anchors`    |
| today                | some         | no         | `k / n anchors`    |
| today                | none         | no         | `done for today`   |
| before today         | some         | no         | `k / n anchors`    |
| before today         | none         | no         | `not generated`    |

**An open board outranks everything else.** A board persists and resumes (see [Kin.md](Kin.md)), so
while one is open the set is not spent no matter how the anchors count — every anchor can be dealt
and the last board still be half-played. Without this row a card reads `not generated` over a live
board and invites a draw that would throw it away.

Otherwise: a set outlives the day it was drawn on, so the date it was drawn is what separates
*finished today* from *never started*. A set left unfinished is picked up where it was, with no new
draw — that is carry-over. A set finished on an earlier day, with no board open, is **spent**, and
the next generate replaces it.

Progress is counted in **anchors resolved**, not edges — it is the unit the player chooses in and
the only one they can feel.
