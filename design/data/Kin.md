# Kin play state

**Status:** implemented

## Table of Contents

- [Kin play state](#kin-play-state)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Lifecycle](#lifecycle)
    - [The set](#the-set)
    - [The board](#the-board)
    - [Derived facts](#derived-facts)
    - [Scoring back](#scoring-back)

## Purpose

What Kin writes down while it is being played: the day's draw, which anchors have been dealt, and
the state of the board in front of the player. All of it disposable — it exists so a half-finished
day survives closing the app.

## Scope

Covers Kin's play tables and how they are filled and emptied.

Does **not** cover the knowledge being drilled (see [Fish.md](Fish.md)), the rules these tables
serve (see [../games/Kin.md](../games/Kin.md)), or the screen that drives them (see
[../app/Kin.md](../app/Kin.md)).

## Decisions

- **Chose to persist the board** over holding it in memory, so closing the app mid-board resumes
  where the player left off instead of discarding their work.
- **Chose `kin_` on every table.** Play state is game-shaped, not shared — a second game brings its
  own tables rather than squeezing into these.
- **Chose one table per edge kind** over a single table with a type column, because everything that
  touches these rows dispatches on the kind anyway, and typing keeps every column a real foreign key
  — including the answer the player gave (`answered_name → clades`, `answered_src → sources`).
- **Chose to write anchors down** rather than deriving them. The anchor is the unit everything
  counts in — progress, the games list, both grouping steps — and deriving it is a four-way union,
  a join to `clades` for the level, and an anti-join across every board in the set. That is the
  most-run query in the game.
- **Chose `board_id` on the anchor row** over a separate board-anchors table. Once the set tracks
  anchors at all, a second table saying which are dealt is the same fact in two places.
- **Chose to keep finished boards** for the life of the set: they are the only record of which
  anchors have already been spent.
- **Chose to drop a set when the next one is generated**, not when it is spent. A spent set
  is still the answer to "is the player done for today" — `generated_on` is what distinguishes that
  from never having generated — and it is the window in which a finished set can still be looked at.
- **Chose to keep slot state on the set row, not the board row.** An edge is the unit of practice,
  and an image shared between two clades puts one `image_src` edge on two boards. State on the edge
  makes it one blank, answered once and scored once.
- **Chose not to store an `anchor` column.** Caching the clade a source edge belongs to cannot
  represent an image edged to two clades, and the join it saved runs twice per board rather than
  once per candidate edge.
- **Chose `ended` on the board** over deriving it. Three callers ask whether a board is open, and
  each was paying a scan across four tables for one bit.
- **Chose to record the answer given, but only for the life of the set.** Keeping it means anything
  that wants to look at a finished set — what got confused with what — still can before the set is
  recycled. Keeping it longer would be a history feature nobody has designed.
- **Chose not to store whether an answer was correct**, since it is the answer compared against the
  set row that holds the truth.

## Design

### Lifecycle

```
generate ─► kin_sets + kin_set_anchors + kin_set_* rows   one draw, carried over until spent
   │
   ├─► deal ─► kin_boards + kin_board_*      one board at a time
   │             │
   │             ├─ submit ─► scores once, locks what was right
   │             └─ move on ─► scores the rest as misses
   │
   └─► next generate ─► the previous set and its boards are dropped
```

### The set

A set is one day's draw for one game. At most one exists at a time: generating drops the previous
set and everything hanging off it.

```
kin_sets(set_id, generated_on)
```

Its anchors, written down rather than derived:

```
kin_set_anchors(set_id, name, level, board_id)
```

`board_id` null means undealt; set, it names the board the anchor was dealt onto. `level` is copied
from `clades` so that grouping — which filters peers by level on every board — does not join for it.

Its edges, one table per kind. `due` is what the draw decided; rows without it came along because
their anchor did.

```
kin_set_clade_image_edges     (edge_id, set_id, name,    img_id,  due, answered_name, locked)
kin_set_clade_character_edges (edge_id, set_id, name,    char_id, due, answered_name, locked)
kin_set_image_src_edges       (edge_id, set_id, img_id,  src,     due, answered_src,  locked)
kin_set_character_src_edges   (edge_id, set_id, char_id, src,     due, answered_src,  locked)
```

**The edge carries its own state, not the board.** An image may be edged to a genus *and* a species
(see [Fish.md](Fish.md)), so a single `image_src` edge can turn up on two boards. Holding `locked`
here rather than per-board means it is one blank until it is answered and locked on both boards
afterwards — never asked twice, never scored twice, and never prefilled on one board with the answer
another board is about to ask for.

The set is built in two steps, and only the first decides who is in it:

```
1.  draw each candidate edge with p = e^(-α·Δt)
2.  anchors  = the clades those drawn edges belong to
3.  set rows = every edge of every anchor, `due` marking the ones drawn in step 1
```

Step 3 never adds an anchor. A clade whose edges were all missed stays out, even if one of its
images is pulled in as prefill for a clade that did get drawn — only the edge to the anchor comes
along, not the other clade. A drawn `src` edge makes an anchor of **every** clade its image or
character hangs off, which is what lets a shared image's card appear on both their boards.

`edge_id` is unique within its own table only. Nothing needs to name an edge across kinds, because
every table that refers to one is itself per-kind.

### The board

```
kin_boards(board_id, set_id, level, first_submitted, ended)

kin_board_clade_image_edges     (board_id, edge_id)
kin_board_clade_character_edges (board_id, edge_id)
kin_board_image_src_edges       (board_id, edge_id)
kin_board_character_src_edges   (board_id, edge_id)
```

The board tables are membership and nothing else — every slot's state lives on the set row.

Dealing a board takes the chosen anchors and enters **all** of their set edges — an anchor is never
split across two boards, so every card is complete. Which edges belong to an anchor is a join
through the card: a `clade_image` or `clade_character` edge names its clade directly, and a `src`
edge reaches its clade through the image or character it hangs off.

| Row state           | `answered_*` | `locked` | Shows          | Player can touch it |
| ------------------- | ------------ | -------- | -------------- | ------------------- |
| not due (prefill)   | null         | true     | the true value | no                  |
| due, not yet right  | their pick   | false    | blank          | yes                 |
| due, got it right   | their pick   | true     | the true value | no                  |
| due, given up on    | their pick or null | true | the true value | no                |

Prefilled rows are born locked, which is exactly what the player sees: filled and not editable.
**Move on** locks every remaining due row so the board can be read back with the answers showing —
its `answered_*` stays whatever was submitted, `null` where nothing ever was.

Nothing renders from `answered_*` — a locked slot shows the true value out of its set row. The
column exists so a finished set can be looked at before it is recycled, and `null` on a due row
means no answer was ever given, which is what **Move on** leaves behind.

**The player's picks only reach the database on submit.** There is no half-filled board: a slot the
player has clicked but not submitted lives in the client. `answered_*` is written once, on the
submission that scores, so it is the answer that counted rather than the last thing tried.

`first_submitted` on the board is what makes scoring happen once. Every submission after it changes
`locked` and nothing else. An edge shared between two boards is scored by whichever board is
submitted first; by the time the second is dealt the edge is already locked, so it is not asked
again.

`ended` marks a board finished — every slot locked, or **Move on** taken. It is the twin of
`first_submitted`: a nullable stamp answering a question three callers ask, rather than a scan
across four tables.

### Derived facts

Nothing below is stored, because storing it would be a second copy:

| Fact                | How                                                        |
| ------------------- | ---------------------------------------------------------- |
| anchors left        | `kin_set_anchors` where `board_id` is null                   |
| a board's palette   | `kin_set_anchors` for that `board_id`                        |
| the open board      | the one `kin_boards` row with `ended` null                   |
| the day is done     | no anchors left, no open board, `generated_on` is today      |
| a new set is due    | no set at all, or no anchors left and `generated_on` is older |

`level` on `kin_boards` and on `kin_set_anchors` are the exceptions — both recoverable from
`clades`, both kept because they are read on every board and every grouping step.

### Scoring back

Scoring writes to [Fish.md](Fish.md)'s edge tables, dispatching on kind:

```
kin_board_clade_image_edges      → clade_image_edges     (name, img_id)
kin_board_clade_character_edges  → clade_character_edges (name, char_id)
kin_board_image_src_edges        → image_src_edges       (img_id, src)
kin_board_character_src_edges    → character_src_edges   (char_id, src)
```

Only `due` rows are scored; prefill never moves a counter. The rule itself — first submission only,
`+= 1` or `→ 0` — is [../games/Kin.md](../games/Kin.md)'s.
