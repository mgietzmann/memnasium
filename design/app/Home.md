# Home

**Status:** implemented

## Table of Contents

- [Home](#home)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Layout](#layout)
    - [The counts](#the-counts)
    - [Navigation](#navigation)

## Purpose

The app's front page: what is waiting on the user, whether today's draw exists,
and the two doors into the app.

## Scope

Covers the home screen and how the app is navigated.

Does **not** cover the screens it leads to (see [Entry.md](Entry.md),
[Drilling.md](Drilling.md)), what the counts mean (see [Data.md](../Data.md)), or
the skills that drain them (see [../flows/](../flows)).

## Decisions

- **The expectation is shown with a `~`, always.** The draw is a coin flip per
  pair, so its size is a random variable and its mean is not a count. A bare
  number beside `118 drawn` would read as a promise the maths never made. See
  [Data.md](../Data.md#the-expectation).
- **After a build the expectation shown is the stored one, not a fresh sum.**
  `118 drawn · ~87 expected` is a claim about one draw; recomputing live would
  slide all morning as pairs are confirmed and stop being about that draw at all.
- **Home exists for the counts.** Grouping and wordsmithing happen in a Claude
  Code session, so their backlogs are invisible from the app. This is the only place
  the user would ever learn that six placements have sat pairless for a month.
- **Nothing on Home links to a skill.** The counts say there is work; doing it
  means opening a Claude Code session. The seam is accepted rather than papered over with a
  button that cannot do anything.
- **Two doors only.** Entry and Drill. There is no third thing the app does.

## Design

### Layout

```
┌────────────────────────────────────────────────────────────┐
│  memnasium                                                 │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   The draw    2 Sep · 118 drawn · ~87 expected · 34 due     │
│               6 boards · 4 on the roll        [ Build ]    │
│                                                            │
│   1,204 pairs                                              │
│                                                            │
│   ── waiting on you ──────────────────────────────────     │
│   14  notes not yet grouped                                │
│    6  placements with no pairs                             │
│    3  placements with stale pairs                          │
│                                                            │
│        [  Enter a note  ]        [  Drill  ]               │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

`1,204 pairs` is the live corpus — every non-retired pair, across groups and the
roll. It sits in the draw's own panel, under the line it gives scale to, and is
the only thing here that says how big the thing being practised actually is.

Neither it nor the expectation is drawn until `GET /home` has answered: a corpus
line reading `0 pairs` while the request is in flight, or after it fails, is a
confident false statement rather than a loading state.

The draw line reads the **current** draw — the one most recently built — and
`[ Build ]` is offered only when today has no draw of its own yet. The sketch
above is a draw carried over from yesterday, which is the one state where every
part of the line is on screen at once. The rest:

| State | Reads | `[ Build ]` |
|---|---|---|
| never built | `not built yet · ~87 expected` | yes |
| today's, in progress | `3 Sep · 118 drawn · ~87 expected · 34 due · 6 boards · 4 on the roll` | no |
| today's, finished | `3 Sep · 118 drawn · ~87 expected · none left` | no |
| carried over | as the sketch, with its own date | yes |

A finished day still reads `drawn` and `expected` rather than "not built yet", so
the button never comes back and draws the same day twice — see
[Data.md](../Data.md#the-draw).

Before any draw exists the expectation is summed live: what a build now would
come out at. Afterwards it is the value frozen on that draw, so it sits beside
`drawn` as a like-for-like — that pairing is the whole reason it is stored. Both
arrive from `GET /home`; neither is computed in the app — see
[api/API.md](../api/API.md#the-drill-loop).

Building is the same action as on [Drilling.md](Drilling.md#drill-home); it is
offered here because it is the first thing done in a morning.

### The counts

| Line | Is | Drained by |
|---|---|---|
| notes not yet grouped | `note` rows with no `placement` | [Grouping](../flows/Grouping.md) |
| placements with no pairs | `placement` rows with no `recall_pair` | [Wordsmithing](../flows/Wordsmithing.md) |
| placements with stale pairs | `placement` rows with `pairs_stale = 1` | [Wordsmithing](../flows/Wordsmithing.md) |

A count of zero is shown as zero, not hidden. The absence of work is information.

### Navigation

Three screens, no deeper. Every screen carries a `← Home` in its top left; there
is no other way back and nothing nests.

```
Home ──┬── Entry
       └── Drill ── a board / a roll batch ── back to Drill
```
