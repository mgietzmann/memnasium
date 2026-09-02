# Kin algorithms

**Status:** drafted

## Table of Contents

- [Kin algorithms](#kin-algorithms)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [The draw](#the-draw)
    - [Load over time](#load-over-time)
    - [Distance](#distance)
    - [Building a group](#building-a-group)
    - [Cost](#cost)

## Purpose

The three procedures Kin needs stated exactly: which edges are drawn, how far apart two clades are,
and how a group is chosen.

## Scope

Covers the draw, the distance metric, and group construction — the definitive statement of each.

Does **not** cover why Kin works this way (see [../games/Kin.md](../games/Kin.md)), the tables these
read (see [../data/Kin.md](../data/Kin.md)), or the endpoints that run them (see
[../api/Kin.md](../api/Kin.md)).

## Decisions

- **Chose an independent draw per edge** over sampling a fixed number, so an edge's chance depends
  only on how well it is known and never on how much else is due that day.
- **Chose `α = 0.4`**, which lengthens an interval by half on each correct answer. `0.2` needed
  fifteen correct answers to reach a three-week interval and doubled the daily review load; `0.69`
  would double the interval each time and let a fish go quiet after four.
- **Chose Δt to count practices, not days.** An edge that is not drawn keeps its `Δt`, so intervals
  grow only through recall. Counting calendar days instead would bound the daily load at `r/α`, but
  an edge answered correctly would keep decaying whether or not it was ever seen again — after
  fifty days its chance is nil and it can never fail, so it would be retired permanently. Nothing
  older than about a month would ever be drilled.
- **Chose no cap on the set** because the draw is self-limiting: every correct answer lengthens that
  edge's interval, so a corpus's daily load decays as it is learned.
- **Chose distance as path length through the parent tree**, not shared rank, because ranks may be
  skipped (see [../data/Fish.md](../data/Fish.md)) and skips make shared-rank rules wrong.
- **Chose random tie-breaking** over any deterministic order, so repeated days at the same distance
  do not produce the same group every time.
- **Chose to sort unreachable clades last** rather than excluding them, so a short group is still
  filled when the tree is a forest.

## Design

### The draw

Every candidate edge is drawn independently:

```
p(edge) = e^(−α · Δt)          α = 0.4
                               Δt = the edge's sessions_since_last_failed
```

`Δt = 0` is certain, and every correct answer multiplies the expected wait by `e^0.4 = 1.49` — a
50% longer interval each time it is recalled.

| Correct answers | Expected wait |
| --------------- | ------------- |
| 0               | every day     |
| 2               | 2 days        |
| 4               | 5 days        |
| 6               | 11 days       |
| 8               | 25 days       |
| 10              | 55 days       |
| 12              | 4 months      |

Candidates are the four edge kinds in [../games/Kin.md](../games/Kin.md); parent edges are never
drawn.

```
1.  for every candidate edge:  draw uniform u ∈ [0,1);  due ⟺ u < e^(−0.4·Δt)
2.  anchors  := the clades those due edges belong to
3.  set      := every edge of every anchor, `due` marking those from step 1
```

Step 2 is the only step that decides membership. Step 3 never adds an anchor — an image shared
between a genus and a species brings only the edge to the anchor, not the other clade.

An edge belongs to a clade by:

| Edge kind        | Its clade                             |
| ---------------- | ------------------------------------- |
| `clade_image`     | the `name` in the row                 |
| `clade_character` | the `name` in the row                 |
| `image_src`       | the clade of the image's `clade_image` edge |
| `character_src`   | the clade of the character's `clade_character` edge |

The last two are why `anchor` is stored on those set tables — recovering it later would be a join.

### Load over time

The set has no cap and does not need one. An edge answered correctly moves to `Δt + 1`, so its
intervals grow like `e^(0.4k)` and by age *T* days its expected contribution to a draw is about
`2/T`. Summed over a steady entry rate *r*, the daily draw settles near

```
        r
────────────────  ·  ln(1 + T/c)          c = 1/(e^α − 1) ≈ 2 at α = 0.4
   e^α − 1
```

**Logarithmic in the corpus, linear in the entry rate.** Reading twice as fast doubles the daily
review forever; reading for twice as long barely moves it. Measured against simulation at
*r* = 10/day:

| Day  | Predicted | Simulated |
| ---- | --------- | --------- |
| 100  | 80        | 81        |
| 1000 | 126       | 126       |
| 3000 | 148       | 179       |

The approximation drifts late — it assumes every edge advances on schedule, and stragglers
accumulate — so treat it as a floor.

Two properties follow, both intended:

- **A missed edge returns every day.** A failure sets `Δt = 0`, so `p = 1` until it is answered
  correctly. A handful of genuinely confusable clades becomes a daily floor.
- **Entry is bursty.** New edges start at `Δt = 0`, so a heavy reading session makes the next draw
  large. It clears within a week or two as those edges are answered.

### Distance

Let `chain(X)` be `X`, its parent, its grandparent, and so on to a root, and `i_X(Y)` the position of
`Y` in that chain, counting `i_X(X) = 0`.

```
L        := the first clade appearing in both chain(A) and chain(B)
d(A, B)  := i_A(L) + i_B(L)
```

`d` is undefined when the chains share nothing — clades under different roots.

```
Family ─── Genus ─── Species A
   └───────────────── Species B          chain(A) = [A, Genus, Family, …]
                                         chain(B) = [B, Family, …]
                                         L = Family,  d = 2 + 1 = 3
```

Skips make odd distances normal. Only the ordering matters, never the absolute number.

### Building a group

Given a requested size *n* and the set's undealt anchors:

```
1.  A     := a uniformly random undealt anchor
2.  L     := A's level
3.  peers := the other undealt anchors whose level is L
4.  sort peers by d(A, ·) ascending, undefined last, ties shuffled
5.  group := A + the first n−1 of peers
6.  deal every edge of every clade in group onto the board
```

- The group is short when fewer than *n−1* peers exist. There is no padding with clades that have
  nothing due.
- Anchors at other levels are untouched and wait for a later group, which may be at a different
  level.
- Step 6 takes **all** of an anchor's set edges, due or not, so no anchor is ever split across two
  boards.

### Cost

Nothing here needs optimising, and the reason is the `level` enum: it caps a chain at seven entries,
so every walk is bounded.

| Step             | Work                                    |
| ---------------- | --------------------------------------- |
| the draw         | one pass over every candidate edge, once a day |
| a chain          | ≤ 7 rows                                |
| `d(A, B)`        | ≤ 14 comparisons                        |
| sorting peers    | `|peers|` distances, then a sort        |

The draw is the only step linear in the whole database, and it runs once a day.
