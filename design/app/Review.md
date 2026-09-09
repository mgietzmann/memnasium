# Review (screen)

**Status:** implemented

## Table of Contents

- [Review (screen)](#review-screen)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Which misses](#which-misses)
    - [Layout](#layout)
    - [A miss](#a-miss)
    - [Order](#order)
    - [Nothing missed](#nothing-missed)

## Purpose

The study guide: everything blown in the last drill, laid out by group, with the
right answer beside what was actually typed.

## Scope

Covers the layout of the review screen and which misses it shows.

Does **not** cover what a [miss](../Project.md#glossary) is or how one is
written (see [Data.md](../Data.md#misses)), the route it reads (see
[api/API.md](../api/API.md#the-record)), or how misses are read from a Claude
Code session (see [../flows/Regrouping.md](../flows/Regrouping.md)).

## Decisions

- **Right answer left, what was typed right.** The truth is the thing being
  studied; the mistake is the annotation. On a [board](Drilling.md#after-submit)
  the order is reversed — there the typed answer is what the eye is already on —
  and Review is read cold, hours later, when the only thing worth leading with
  is the fact.
- **Both boxes are always shown.** A `miss` row records what was typed in the
  answer box and in the source box, but not which of them Claude failed, so the
  screen cannot say "only the source was wrong". Showing both and letting the
  eye compare is honest; a per-box verdict column on `miss` would be precise
  only for rows written after it shipped.
- **The window is the last *draw*, not the last miss.** A draw built this
  morning and half worked is the drill being reviewed, so its three misses show
  and yesterday's twelve do not. Anchoring on the last day that *has* misses
  would keep showing yesterday all through a clean morning.
- **A drill in progress is reviewable.** Nothing here writes, so reading back
  the first four boards mid-sitting cannot corrupt anything. This is the one
  screen that is useful before the day is finished.
- **No controls.** No date picker, no window widener, no way to mark something
  learned. It is a page to read. Widening the window is a change to one query
  parameter — see [api/API.md](../api/API.md#the-record) — not a control that
  has to exist on day one.
- **The pair is shown as it stands now, and so is where it stands.** A `miss`
  points at a `recall_pair`, so a pair reworded or
  [retired](../Project.md#glossary) since the drill reads in its new words — and
  a [placement](../Project.md#glossary) moved since the drill takes its misses
  with it, appearing under a rule the pair was not drilled under, or under
  `The roll`. Both need an authoring pass between the drill and the reading,
  which is rare enough to accept rather than version the pair text and its group
  for. The page is the record read through the corpus as it stands, not a
  photograph of the morning.

## Design

### Which misses

The day is the most recent row in `draw_day` — the last draw **built**, whether
it was worked to the end, half worked, or not started. The app does not compute
it: `GET /misses?since=last-drill` resolves it in the store, and the screen
renders what comes back.

| The morning | Review shows |
|---|---|
| today built, four boards worked, three blown | those three |
| today built, nothing worked yet | [nothing missed](#nothing-missed) |
| today built, worked clean | [nothing missed](#nothing-missed) |
| today not built, yesterday's finished | yesterday's misses |

[Stranded](../Project.md#glossary) rows are not special here. A miss is written
against the day on its own `draw` row, so a board confirmed after midnight lands
on the draw it belonged to and is reviewed with it.

### Layout

```
┌────────────────────────────────────────────────────────────┐
│  ← Home                            Review              ☀   │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   9 missed on 8 September                                  │
│                                                            │
│   ── Onset of piscivory ───────────────────────────────    │
│                                                            │
│   At what length do Puget Sound Chinook turn               │
│   piscivorous inshore?                                     │
│                        70 mm  │  you said  130 mm          │
│                   Duffy 2010  │  you said  Duffy 2012      │
│                                                            │
│   …offshore?                                               │
│                       130 mm  │  you said  70 mm           │
│                   Duffy 2010  │  you said  Duffy 2010      │
│                                                            │
│   ── Smolt outmigration timing ────────────────────────    │
│                                                            │
│   …                                                        │
│                                                            │
│   ── The roll ─────────────────────────────────────────    │
│                                                            │
│   …                                                        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

One column, full width, scrolled. The header line is a count and the day it
belongs to, written out — the page is about one past day, so the date is stated
rather than assumed, which is the opposite of [Home](Home.md#layout).

Group names are rules, not panels: the page is read top to bottom in one pass
and boxes would break it into things to be visited. Pairs that were on
[the roll](../Project.md#glossary) have no group, so they sit under a final
`The roll` rule.

The top bar is the standard one — see [Home](Home.md#navigation).

### A miss

```
   At what length do Puget Sound Chinook turn
   piscivorous inshore?
                       70 mm  │  you said  130 mm
                  Duffy 2010  │  you said  Duffy 2012
```

The question in `text`, then two rows split by the same `line` rule a board's
columns use. Left of the rule is the pair's `answer` and its source,
right-aligned against the rule; right of it is `user_answer` and `user_source`,
each behind a `muted` `you said`. Both sides render LaTeX. The source row is
shown even when what was typed matches, because the screen does not know which
box failed.

No glyphs. Every row on this page is a miss, so a `✗` on each one carries
nothing the page title has not already said — see
[standards/Style.md](../standards/Style.md#encoding-state).

### Order

| | Ordered by |
|---|---|
| groups | name, ascending; `The roll` always last |
| misses within a group | `miss.id` ascending |

`miss` stores a day and nothing finer, so `id` is the only thing that orders a
sitting. Ascending is the order the rows were written, which is the order the
boards were worked — see
[api/API.md](../api/API.md#the-record), where that ordering is a guarantee of
the route rather than something this screen infers. The route answers newest
first; a single day is short and the app re-sorts it.

A pair can be missed at most once in a day — one `draw` row per pair — so
nothing repeats inside the window.

### Nothing missed

```
│                                                            │
│   Nothing missed.                                          │
│                                                            │
```

No date. The day rides on the miss rows, so an empty answer has no day to name,
and inventing one would mean a second question of the store to print a line that
says nothing. The same line covers a clean morning, a morning not yet started,
and an install that has never drilled.
