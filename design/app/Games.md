# Games

**Status:** drafted

## Table of Contents

- [Games](#games)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Games list](#games-list)
    - [Game screen](#game-screen)
    - [Day state](#day-state)
    - [Known limits](#known-limits)

## Purpose

The shell every game sits inside: choosing a game, generating the day's set, picking how much to
take on, and seeing how far in you are. Whatever is true of all games lives here so no game has to
say it again.

## Scope

Covers the games list and the parts of a game screen that are the same no matter which game is
being played.

Does **not** cover any individual game's board (see [../games/Kin.md](../games/Kin.md)), getting to
this screen (see [Navigation.md](Navigation.md)), or data entry (see [Entry.md](Entry.md)).

## Decisions

- **Chose a card per game showing today's state** over a plain list, because the only thing worth
  knowing at a glance is whether today's work is done.
- **Chose an explicit Generate over generating on open**, so opening a game to look at it does not
  spend the day's draw.
- **Chose to carry an unfinished day over** rather than redrawing, because a redraw would let the
  player reroll a group they did not like.
- **Chose to confirm Move on**, because taking it on an unsubmitted board fails every edge at once.
- **Chose to split giving up from walking away.** *Move on* is an answer — the player is done
  guessing, so the rest counts as missed. Closing the app is not an answer, so it scores nothing and
  the anchors come back.
- **Chose to ask for group size before every group** rather than once a day, per
  [../games/Kin.md](../games/Kin.md) — the player's appetite changes as they tire.

## Design

### Games list

One card per game. The card's job is to say whether the day is generated and how far in the player
is.

```
┌──────────────────────────┐  ┌──────────────────────────┐
│ Kin                      │  │ <next game>              │
│ 5 / 12 anchors           │  │ not generated            │
└──────────────────────────┘  └──────────────────────────┘
```

| Card state       | Shown             |
| ---------------- | ----------------- |
| not yet drawn    | `not generated`   |
| drawn, unplayed  | `0 / n anchors`   |
| part way         | `k / n anchors`   |
| finished         | `done for today`  |

Progress is counted in **anchors resolved**, not edges — it is the unit the player chooses in and
the only one they can feel.

### Game screen

A header that carries the day's state, and beneath it whatever the game's board is.

```
┌──────────────────────────────────────────────────────┐
│  Kin                       7 anchors left    [ ⚙ ]   │
├──────────────────────────────────────────────────────┤
│                                                      │
│                  < the game's board >                │
│                                                      │
└──────────────────────────────────────────────────────┘
```

The header shows one of three things, by day state:

| Day state         | Header offers                          |
| ----------------- | -------------------------------------- |
| not generated     | **Generate today's set**               |
| between groups    | group size picker, then **Start**      |
| board in progress | anchors left, and **Submit** / **Move on** on the board |

Finishing a board returns the player to the between-groups state with the count updated, so the
loop is pick a size → play → pick a size. When no anchors are left the screen says the day is done.

### Day state

```
       ┌──────────────┐  generate   ┌──────────────┐
       │not generated │────────────►│between groups│◄────────┐
       └──────────────┘             └──────┬───────┘         │
                                      pick size        all locked
                                           ▼            or Move on
                                    ┌──────────────┐         │
                        ┌───────────│    board     │─────────┘
                   walk away        └──────────────┘
                   (anchors return, nothing scored)
```

- A day's draw is made once and **carries over** until it is finished; it is not redrawn on a later
  day. The next draw happens only after the previous set is exhausted.
- **Move on** ends a board as a give-up: its anchors are spent and its unrecalled edges score as
  misses. **Walking away** — closing the app mid-board — discards the board, scores nothing further,
  and returns its anchors to the pool.
- **Move on confirms first.** It is one tap away from failing a whole board.
- A **played session** is a day on which a set was generated. Days the player never opens the app do
  not count, which is what keeps `sessions_since_last_failed` measuring practice rather than time.

### Known limits

- **Walking away rerolls the group.** A board the player closes is discarded and its anchors return,
  so the next group is a different one. Accepted: the pool is nearest-neighbour, so a reroll lands
  somewhere similar, and the only person it cheats is the player. The fix, if it ever matters, is
  persisting the board across app restarts rather than discarding it.
