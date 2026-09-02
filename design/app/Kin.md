# Kin screen

**Status:** drafted

## Table of Contents

- [Kin screen](#kin-screen)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [The screen](#the-screen)
    - [Day state](#day-state)
    - [The board](#the-board)
    - [Interaction](#interaction)
    - [Submitting](#submitting)

## Purpose

What playing Kin looks like: the header that carries the day's state, and the board underneath it.

## Scope

Covers the Kin screen and its board.

Does **not** cover the game's rules — selection, grouping, scoring — which are
[../games/Kin.md](../games/Kin.md); the tables behind it ([../data/Kin.md](../data/Kin.md)); the
calls it makes ([../api/Kin.md](../api/Kin.md)); or getting here
([Navigation.md](Navigation.md)).

## Decisions

- **Chose an explicit Generate over generating on open**, so opening Kin to look at it does not
  spend the day's draw.
- **Chose to ask for group size before every group** rather than once a day, because the player's
  appetite changes as they tire.
- **Chose tap-then-tap over drag** to fill a slot, because dragging a line between two targets is
  fiddly on a trackpad and worse on touch.
- **Chose a grid of cards over a single tall column** so photos stay large enough to identify.
- **Chose a citation slot on each card over a fourth column** because a source is a short label, and
  a column of them would double the board's width to hold `(Brown, 2014)`.
- **Chose to print attachments on the card over drawing lines**, because lines from a grid back to a
  left-hand column are spaghetti, and a filled slot reads faster than a traced line.
- **Chose to consume nothing** — citations and clades stay selectable after use — so the board
  cannot be solved by elimination.
- **Chose to confirm Move on**, because taking it on an unsubmitted board fails every edge at once.
- **Chose to show the answers after Move on** rather than returning straight to the group picker. A
  player who gave up has already paid for the miss; sending them away without the answer means they
  learned nothing from it.

## Design

### The screen

A header carrying the day's state, and the board beneath it.

```
┌──────────────────────────────────────────────────────┐
│  Kin                       7 anchors left            │
├──────────────────────────────────────────────────────┤
│                                                      │
│                    < the board >                     │
│                                                      │
└──────────────────────────────────────────────────────┘
```

| Day state         | Header offers                                    |
| ----------------- | ------------------------------------------------ |
| not generated     | **Generate today's set**                         |
| between groups    | group size picker, then **Start**                |
| board in progress | anchors left, with **Submit** / **Move on** below |
| board ended       | the filled-in board, and **Next**                  |

Finishing a board returns the player to the between-groups state with the count updated, so the loop
is pick a size → play → pick a size. When no anchors are left the screen says the day is done.

### Day state

```
       ┌──────────────┐  generate   ┌──────────────┐
       │not generated │────────────►│between groups│◄────────┐
       └──────────────┘             └──────┬───────┘         │
                                      pick size        all locked
                                           ▼            or Move on
                                    ┌──────────────┐         │
                        ┌───────────│    board     │──►[ answers ]
                    close app       └──────────────┘   Next
                   (resumes as it was)
```

- A draw is made once and **carries over** until it is spent; it is not redrawn on a later day.
- **Move on** ends a board as a give-up. **Closing the app** ends nothing — the board is persisted
  and resumes untouched.
- Whether the day reads *done for today* or *not generated* depends on when the set was drawn; the
  table is in [Navigation.md](Navigation.md).

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

A **card** is one image or one character. Every card belonging to a group's clades is on the board —
**all** of them, not only the ones with a due edge. A card has three bands: a clade slot on top, the
payload, a source slot beneath.

| Slot  | Edge                                          | If not due           |
| ----- | --------------------------------------------- | -------------------- |
| clade | `clade_image_edges` / `clade_character_edges` | shown already filled |
| src   | `image_src_edges` / `character_src_edges`     | shown already filled |

Most of a board is prefilled. Ten anchors with a handful of characters and images each runs to
dozens of cards, only some of them blank, and the board scrolls. That is the point — the prefilled
cards are the context that makes discriminating the blank ones possible.

No lines are ever drawn. An attachment is the name printed in the slot, so a card either reads
`A. opus` / `Brown, 2014` or shows an empty box. The citation pool holds the sources behind the
board's due `src` slots, and nothing else.

### Interaction

One grammar, both slots:

```
tap clade → tap a card's clade slot     fills it
tap chip  → tap a card's src slot       fills it
tap a filled slot                       clears it
```

Nothing is consumed. A clade takes several cards, and a citation backs as many cards as the player
puts it on, so counting what is left over tells the player nothing.

### Submitting

Every blank must be filled before **Submit** enables — there is no partial submission. On submit,
correct slots **lock** and incorrect ones clear for the player to fill again. This repeats until the
board is fully locked, or the player takes **Move on**, which is always available and confirms
first.

**Move on** fills the board in rather than clearing it away: every remaining slot locks and shows
what it should have been, and the player reads it before continuing.

```
   confirm            the answers            back to the picker
 ┌───────────┐      ┌─────────────┐         ┌──────────────┐
 │ Give up   │─────►│ board, all  │────────►│between groups│
 │ this board│      │ slots locked│  Next   └──────────────┘
 └───────────┘      └─────────────┘
```

A finished board reaches the same state — every slot locked — so the two endings look alike on
screen and differ only in what was scored.

How the three slot states look is [../standards/Style.md](../standards/Style.md). What a submission
does to the counters is [../games/Kin.md](../games/Kin.md).
