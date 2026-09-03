# Home

**Status:** drafted

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
│   Today's draw          not built yet    [ Build ]         │
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

Once today's draw is built, the top line reads its numbers instead — `118 due ·
14 boards · 22 on the roll` — and `[ Build ]` is gone. Building is the same
action as on [Drilling.md](Drilling.md#drill-home); it is offered here because it
is the first thing done in a morning.

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
