# Drilling (screens)

**Status:** drafted

## Table of Contents

- [Drilling (screens)](#drilling-screens)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Drill home](#drill-home)
    - [A board](#a-board)
    - [After submit](#after-submit)
    - [A roll batch](#a-roll-batch)
    - [Between boards](#between-boards)

## Purpose

The two screens of a morning: the fork where the draw is built and a mode is
picked, and the board where pairs are recalled and graded.

## Scope

Covers the layout and the states each screen moves through.

Does **not** cover the loop's rules, grading, or what gets written (see
[../flows/Drilling.md](../flows/Drilling.md)), the scheduling maths (see
[Data.md](../Data.md)), or the grading prompt (see [Claude.md](../Claude.md)).

## Decisions

- **A board is two columns: work on the left, reference on the right.** This is
  the whole design made literal — the user is never scrolling away from the
  question to see the thing that disambiguates it. The columns scroll
  independently.
- **One screen, three states.** Answering, graded, confirmed. A board does not
  navigate anywhere to show its results.
- **`N` sticks.** The same number gets typed every morning; the last one used is
  remembered per mode.
- **A roll batch is the board screen minus the context column.** Not a second
  screen.

## Design

### Drill home

Before the draw is built, this screen is one button.

```
┌────────────────────────────────────────────────────────────┐
│  ← Home                                            Drill   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│    Today's draw — 3 Sep                                    │
│                                                            │
│      118  due pairs                                        │
│       14  boards            [ 3 ]  [  Work boards  ]       │
│       22  on the roll       [ 10 ] [  Work the roll  ]     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

The three numbers fall as the morning is worked. `[ 3 ]` and `[ 10 ]` hold the
last values used. A mode with nothing left in it has its row and control
disabled.

### A board

```
┌────────────────────────────────────────────────────────────┐
│  Onset of piscivory · 6 pairs           board 2 of 3       │
├──────────────────────────────┬─────────────────────────────┤
│  DUE                    2    │  CONTEXT                4   │
│                              │                             │
│  At what length do Puget     │  Yukon, freshwater?         │
│  Sound Chinook turn          │    85–90 mm                 │
│  piscivorous inshore?        │    Bradford 2009            │
│  ┌────────────────────────┐  │                             │
│  │ answer                 │  │  British Columbia, mass?    │
│  └────────────────────────┘  │    50–100 g                 │
│  ┌────────────────────────┐  │    Healey 1991              │
│  │ source                 │  │                             │
│  └────────────────────────┘  │  California Current, order? │
│                              │    inverts first, piscivory │
│  …offshore?                  │    later, moving offshore   │
│  ┌────────────────────────┐  │    Brodeur 1992             │
│  │ answer                 │  │                             │
│  └────────────────────────┘  │  Puget Sound, offshore?     │
│  ┌────────────────────────┐  │    130 mm                   │
│  │ source                 │  │    Duffy 2010               │
│  └────────────────────────┘  │                             │
│                              │                             │
│              [  Submit  ]    │                             │
└──────────────────────────────┴─────────────────────────────┘
```

The header names the group, its live pair count — the
[context reading budget](../flows/Drilling.md#a-board), so it is on screen every
time the group comes up — and the position in the run. The left column holds
every due pair — question, an **answer** box and a **source** box. The right
column holds every other pair in the group, question and answer and source, read
only. Both render LaTeX. `board 2 of 3` counts the run the user asked for, not
the day.

`Submit` is disabled until every box on the left has something in it.

### After submit

The same screen. Each due pair grows its verdict in place; the context column
does not move.

```
│  At what length do Puget     │
│  Sound Chinook turn          │
│  piscivorous inshore?        │
│    you said  130 mm          │
│    ✗ missed  →  70 mm        │
│    you said  Duffy 2012      │
│    ✗ source  →  Duffy 2010   │
│                  [ contest ] │
```

A correct pair shows a tick and nothing else. A missed pair shows, for each box
that failed, what was typed and what it should have been — so a pair blown only
on the source still reveals the source. A box that was right shows a tick. `[ contest ]` toggles the
pair to correct and is the user's call — no round trip.

`Submit` becomes `Confirm`. Nothing has been written until it is pressed; leaving
the screen before then leaves the board exactly as it was, to be worked again
later — see [../flows/Drilling.md](../flows/Drilling.md#contest-and-confirm).

### A roll batch

The board screen with the context column removed and the header reading
`The roll — 10 pairs`. The left column spans the width. Everything else — submit,
grading, contest, confirm — is identical.

### Between boards

Confirming goes straight to the next board of the run. After the last one the run
ends at [Drill home](#drill-home), numbers updated, and the user picks again.
