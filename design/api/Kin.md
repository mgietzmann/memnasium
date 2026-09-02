# Kin API

**Status:** drafted

## Table of Contents

- [Kin API](#kin-api)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Endpoints](#endpoints)
    - [State](#state)
    - [Generating a set](#generating-a-set)
    - [Dealing a board](#dealing-a-board)
    - [Submitting](#submitting)
    - [Moving on](#moving-on)
    - [Errors](#errors)

## Purpose

The HTTP surface for playing Kin: generating the day's set, dealing a board, submitting it, and
giving up on it.

## Scope

Covers the play endpoints and their payloads.

Does **not** cover the rules behind them (see [../games/Kin.md](../games/Kin.md)), the tables they
read and write (see [../data/Kin.md](../data/Kin.md)), or entering fish (see [Fish.md](Fish.md)).

## Decisions

- **Chose opaque slot handles over exposing `edge_id`.** Play `edge_id`s are unique only within
  their own table, so a raw id would have to travel with its kind — the schema leaking onto the
  wire. A handle unique to the board keeps the client from ever learning there are four tables.
- **Chose to send the whole board on submit** rather than saving slots as they are clicked, because
  a slot only becomes an answer at submission — see [../data/Kin.md](../data/Kin.md).
- **Chose per-game state over a shared games endpoint.** Play tables are `kin_`-prefixed, so there
  is no cross-game query; the games list asks each game for its own state.
- **Chose to keep images out of this API.** An image is knowledge, not play, so the board carries
  `img_id` and the bytes come from [Fish.md](Fish.md).
- **Chose never to return the right answer.** A wrong slot comes back `"wrong"` and nothing else;
  the only way to see the answer is to get it right or to take **Move on**.

## Design

### Endpoints

```
GET  /api/kin/state              what the games-list card shows
POST /api/kin/set                generate the day's draw
POST /api/kin/board              deal a group
GET  /api/kin/board              the open board
POST /api/kin/board/submit       answer it
POST /api/kin/board/move-on      give it up
```

### State

```json
GET /api/kin/state
{ "generated_on": "2026-09-02", "anchors_total": 12, "anchors_left": 7, "open_board": true }
```

`generated_on` is null when no set exists. Together with `anchors_left` it is everything the games
card needs — an exhausted set drawn today reads *done for today*, the same set read tomorrow reads
*not generated*. The full table is in [../app/Navigation.md](../app/Navigation.md).

### Generating a set

```
POST /api/kin/set   →  200, the same body as GET /api/kin/state
```

Idempotent, and it honours carry-over: called twice in a day it returns the existing set, and called
on a day whose previous set still has anchors left it returns that one rather than drawing a new
one. A new set is drawn only when there is no set at all, or the one there is was exhausted on an
earlier day — and drawing it drops the old set and its boards.

### Dealing a board

```json
POST /api/kin/board          { "size": 3 }
```

```json
{ "board_id": 7,
  "level": "species",
  "clades":    [ {"name": "Artificialus claudus", "common_name": "spotted claudfish"},
                 {"name": "Artificialus opus",    "common_name": null} ],
  "citations": [ {"src": 17, "label": "Brown, 2014"},
                 {"src": 22, "label": "Okafor, 2021"} ],
  "cards": [
    { "kind": "image", "img_id": "8f21…",
      "clade": {"slot": "a1", "state": "locked", "value": "Artificialus opus"},
      "src":   {"slot": "a2", "state": "due",    "value": null} },
    { "kind": "character", "text": "three dorsal spines",
      "clade": {"slot": "a3", "state": "due",    "value": null},
      "src":   {"slot": "a4", "state": "locked", "value": 17} }
  ] }
```

- `clades` is the palette and the group's anchors; `citations` is the pool, holding only the sources
  behind due `src` slots.
- Every card of every anchor comes down, prefilled where the edge was not drawn — most of a board is
  `locked`.
- A slot is `due` (blank, the player fills it) or `locked` (shown filled, not editable). `value` is
  a clade name on a clade slot and a `src` on a source slot.
- `size` is a maximum. A short group comes back short, per [../games/Kin.md](../games/Kin.md).

`GET /api/kin/board` returns the same body for the board already open, which is how a board resumes
after the app is closed. `404` when there is none.

### Submitting

```json
POST /api/kin/board/submit   { "slots": {"a2": 22, "a3": "Artificialus claudus"} }
```

Every `due` slot must be present or the call is rejected. The client greys Submit out until the
board is full (see [../games/Kin.md](../games/Kin.md)), so the `400` is the server not trusting the
client rather than the way the rule is enforced.

```json
{ "results": {"a2": "correct", "a3": "wrong"},
  "complete": false,
  "scored": true }
```

`scored` is true only on the first submission, the one that moves
`sessions_since_last_failed`. Later submissions re-lock and report, and change no counters.
`complete` true means every slot is locked and the board is finished.

### Moving on

```
POST /api/kin/board/move-on   →  { "complete": true, "scored": true }
```

Ends the board as a give-up: everything not already locked scores as a miss and the anchors are
spent. The client confirms before calling this — it can fail a whole board in one tap.

### Errors

| Case                                   | Status |
| -------------------------------------- | ------ |
| no set generated yet                   | `409`  |
| dealing a board while one is open      | `409`  |
| submitting with slots missing          | `400`  |
| submitting an unknown slot handle      | `400`  |
| no open board                          | `404`  |
