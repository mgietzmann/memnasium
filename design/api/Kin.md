# Kin API

**Status:** implemented

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

- **Chose derived slot handles over exposing `edge_id`.** Play `edge_id`s are unique only within
  their own table, so a raw id would have to travel with its kind. A handle built from both is
  stable without being stored, which it has to be — the client gets it from one request and sends it
  back on another, across an app restart.
- **Chose to send the whole board on submit** rather than saving slots as they are clicked, because
  a slot only becomes an answer at submission — see [../data/Kin.md](../data/Kin.md).
- **Chose per-game state over a shared games endpoint.** Play tables are `kin_`-prefixed, so there
  is no cross-game query; the games list asks each game for its own state.
- **Chose to keep images out of this API.** An image is knowledge, not play, so the board carries
  `img_id` and the bytes come from [Fish.md](Fish.md).
- **Chose to send `labels` alongside `citations`.** The pool is what the player may pick from; a
  prefilled slot still has to print a source that is not in it. One is a choice list, the other a
  lookup — folding them together would put un-pickable chips in the pool.
- **Chose never to return the right answer while a board is live.** A wrong slot comes back
  `"wrong"` and nothing else. **Move on** ends the board and returns it with every value showing,
  because a player who has given up has to be told what it was — failing and learning nothing is the
  worst outcome a memory gym can produce.

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
card needs — a spent set drawn today reads *done for today*, the same set read tomorrow reads
*not generated*. The full table is in [../app/Navigation.md](../app/Navigation.md).

### Generating a set

```
POST /api/kin/set   →  200, the same body as GET /api/kin/state
```

Idempotent, and it honours carry-over: called twice in a day it returns the existing set, and called
on a day whose previous set still has anchors left it returns that one rather than drawing a new
one. A new set is drawn only when there is no set at all, or the one there is was spent on an
earlier day — and drawing it drops the old set and its boards.

A set is **spent** only when its anchors are all dealt *and* no board is open. A board that is still
being played holds the set open however the anchor count reads, so this endpoint returns the
existing set rather than drawing over a board the player is in the middle of.

### Dealing a board

```json
POST /api/kin/board          { "size": 3 }
```

```json
{ "board_id": 7,
  "level": "species",
  "ended": false,
  "scored": false,
  "clades":    [ {"name": "Artificialus claudus", "common_name": "spotted claudfish"},
                 {"name": "Artificialus opus",    "common_name": null} ],
  "citations": [ {"src": 17, "label": "Brown, 2014"},
                 {"src": 22, "label": "Okafor, 2021"} ],
  "labels":    { "17": "Brown, 2014", "22": "Okafor, 2021", "31": "Miller, 2019" },
  "cards": [
    { "kind": "image", "img_id": "8f21…",
      "clade": {"slot": "ci-41", "state": "locked", "value": "Artificialus opus"},
      "src":   {"slot": "is-19", "state": "due",    "value": null} },
    { "kind": "character", "text": "three dorsal spines",
      "clade": {"slot": "cc-7",  "state": "due",    "value": null},
      "src":   {"slot": "cs-88", "state": "locked", "value": 17} }
  ] }
```

- `clades` is the palette and the group's anchors; `citations` is the pool, holding only the sources
  behind due `src` slots.
- Every card of every anchor comes down, prefilled where the edge was not drawn — most of a board is
  `locked`.
- A slot is `due` (blank, the player fills it) or `locked` (shown filled, not editable). `value` is
  a clade name on a clade slot and a `src` on a source slot.
- `size` is a maximum. A short group comes back short, per [../games/Kin.md](../games/Kin.md).
- `ended` and `scored` are on every board body, not only the one **Move on** returns. On a live
  board they are `false`.

**`citations` is the pool; `labels` is how a `src` is read.** A slot's `value` is a `src` — a number
— and a *prefilled* source slot shows its true value, which may be a source no due slot uses and so
is not in the pool. `labels` carries every source shown anywhere on the board, keyed by `src`, so a
locked slot can render `Brown, 2014`.

```
citations  →  the chips the player may choose from — due sources only
labels     →  how to print any src the board shows — a superset
```

`labels` gives nothing away: every entry beyond the pool belongs to a locked slot, whose value is
already on screen. It must never be drawn as chips.

A **slot handle** is its edge's kind and id — `ci-41`, `cc-7`, `is-19`, `cs-88` for the four kinds in
[../data/Kin.md](../data/Kin.md). Derived, never stored, and identical across requests and restarts,
so a resumed board hands back the same handles. The client learns nothing from it but which slot it
is talking about.

A shared image's `src` slot carries the same handle on every board it appears on, because it is the
same edge. Answering it on one board locks it on the other.

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
`complete` true means every slot is locked and the board is finished — the same state `ended`
records in [../data/Kin.md](../data/Kin.md).

### Moving on

```
POST /api/kin/board/move-on
```

Ends the board as a give-up: everything not already locked scores as a miss, every slot is locked,
and the anchors are spent. The client confirms before calling this — it can fail a whole board in
one tap.

The response is the **completed board** — the same body as `POST /api/kin/board`, with every slot
`locked` and carrying its true value:

```json
{ "board_id": 7, "level": "species", "ended": true, "scored": false,
  "clades": [...], "citations": [...], "labels": {...},
  "cards": [ { "kind": "character", "text": "three dorsal spines",
               "clade": {"slot": "cc-7", "state": "locked", "value": "Artificialus claudus"},
               "src":   {"slot": "cs-88", "state": "locked", "value": 17} } ] }
```

So giving up teaches the answer. The screen shows it before moving on (see
[../app/Kin.md](../app/Kin.md)).

`scored` is true only when this was the board's **first** submission — `first_submitted` was null.
Give up after having submitted once and the counters were already moved by that submission; move-on
locks the rest and changes nothing, so it reports `false`.

### Errors

| Case                                   | Status |
| -------------------------------------- | ------ |
| no set generated yet                   | `409`  |
| dealing a board while one is open      | `409`  |
| submitting with slots missing          | `400`  |
| submitting an unknown slot handle      | `400`  |
| no open board                          | `404`  |
