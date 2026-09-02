# Kin play state

**Status:** drafted

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
- **Chose board membership as its own table** rather than a column on the set rows, since a board is
  built one at a time and the set should not be rewritten to deal one.
- **Chose to keep finished boards** for the life of the set: they are the only record of which
  anchors have already been spent.
- **Chose to drop a set when the next one is generated**, not when it is exhausted. An exhausted set
  is still the answer to "is the player done for today" — `generated_on` is what distinguishes that
  from never having generated — and it is the window in which a finished set can still be looked at.
- **Chose to store `anchor` only where it is not implied.** On the clade edges the anchor is the
  clade in the row; on the source edges it would take a join to recover, so it is written down.
- **Chose to record the answer given, but only for the life of the set.** Keeping it means anything
  that wants to look at a finished set — what got confused with what — still can before the set is
  recycled. Keeping it longer would be a history feature nobody has designed.
- **Chose not to store whether an answer was correct**, since it is the answer compared against the
  set row that holds the truth.

## Design

### Lifecycle

```
generate ─► kin_sets + kin_set_* rows        one draw, carried over until spent
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

Its edges, one table per kind. `due` is what the draw decided; rows without it came along because
their anchor did.

```
kin_set_clade_image_edges     (edge_id, set_id, name,    img_id,         due)
kin_set_clade_character_edges (edge_id, set_id, name,    char_id,        due)
kin_set_image_src_edges       (edge_id, set_id, img_id,  src,  anchor,   due)
kin_set_character_src_edges   (edge_id, set_id, char_id, src,  anchor,   due)
```

The set is built in two steps, and only the first decides who is in it:

```
1.  draw each candidate edge with p = e^(-α·Δt)
2.  anchors  = the clades those drawn edges belong to
3.  set rows = every edge of every anchor, `due` marking the ones drawn in step 1
```

Step 3 never adds an anchor. A clade whose edges were all missed stays out, even if one of its
images is pulled in as prefill for a clade that did get drawn — only the edge to the anchor comes
along, not the other clade.

`edge_id` is unique within its own table only. Nothing needs to name an edge across kinds, because
every table that refers to one is itself per-kind.

### The board

```
kin_boards(board_id, set_id, level, first_submitted)
kin_board_anchors(board_id, name)

kin_board_clade_image_edges     (board_id, edge_id, answered_name, locked)
kin_board_clade_character_edges (board_id, edge_id, answered_name, locked)
kin_board_image_src_edges       (board_id, edge_id, answered_src,  locked)
kin_board_character_src_edges   (board_id, edge_id, answered_src,  locked)
```

Dealing a board takes the chosen anchors and copies **all** of their set edges in — an anchor is
never split across two boards, so every card is complete.

| Row state           | `answered_*` | `locked` | Shows            | Player can touch it |
| ------------------- | ------------ | -------- | ---------------- | ------------------- |
| not due (prefill)   | null         | true     | the true value   | no                  |
| due, not yet right  | their pick   | false    | blank            | yes                 |
| due, got it right   | their pick   | true     | the true value   | no                  |

Prefilled rows are born locked, which is exactly what the player sees: filled and not editable.

Nothing renders from `answered_*` — a locked slot shows the true value out of its set row. The
column exists so a finished set can be looked at before it is recycled, and `null` on a due row
means no answer was ever given, which is what **Move on** leaves behind.

**The player's picks only reach the database on submit.** There is no half-filled board: a slot the
player has clicked but not submitted lives in the client. `answered_*` is written once, on the
submission that scores, so it is the answer that counted rather than the last thing tried.

`first_submitted` on the board is what makes scoring happen once. Every submission after it changes
`locked` and nothing else.

### Derived facts

Nothing below is stored, because storing it would be a second copy:

| Fact                | How                                                        |
| ------------------- | ---------------------------------------------------------- |
| the day's anchors   | distinct `name` / `anchor` across the four `kin_set_*` tables |
| anchors left        | those anchors, minus everything in `kin_board_anchors`      |
| the open board      | the one `kin_boards` row whose edges are not all locked     |
| the day is done     | no anchors left, no open board, `generated_on` is today      |
| a new set is due    | no set at all, or no anchors left and `generated_on` is older |

`level` on `kin_boards` is the exception — recoverable from the anchors' clades, kept anyway because
it is what the board is *about* and reading it should not take a join.

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
