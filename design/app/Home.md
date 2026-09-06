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
- **Home speaks about today, and only today.** The draw line reads today's draw
  or says there isn't one. An earlier draw that was never finished is
  [stranded](../Project.md#glossary) — still confirmable if a board is open on
  screen, never mentioned here. Yesterday's `drawn` is a fact about yesterday, and
  a morning that opens with it is being told about work it can no longer do.
- **Until today is built the expectation is live, and it moves.** It is a
  prediction of the build about to happen, so a morning after an authoring binge
  must show the corpus as it now stands — that is the entire use of the number.
- **After the build the expectation freezes.** `118 drawn · ~87 expected` is a
  claim about one draw; recomputing live would slide all morning as pairs are
  confirmed and stop being about that draw at all. Prediction before, record
  after, and the switch is the build.
- **The theme toggle is the only control in the top bar.** It belongs on every
  screen rather than on Home alone — the ground is wrong at the moment it is
  noticed, which is usually mid-board. See
  [standards/Style.md](../standards/Style.md#choosing-a-theme).
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
│  memnasium                                              ☀  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│   The draw    118 drawn · ~87 expected · 34 due            │
│               6 boards · 4 on the roll                     │
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

The draw line reads **today's** draw. There are three states and no date on any
of them — the line is always about today, so saying so would be noise:

| State | Reads | `[ Build ]` |
|---|---|---|
| today not built | `not built yet · ~87 expected` | yes |
| today's, in progress | `118 drawn · ~87 expected · 34 due · 6 boards · 4 on the roll` | no |
| today's, finished | `118 drawn · ~87 expected · none left` | no |

The sketch above is the middle row. A finished day still reads `drawn` and
`expected` rather than "not built yet", so the button never comes back and draws
the same day twice — see [Data.md](../Data.md#the-draw).

`not built yet` is what a day opens on whether the last draw was yesterday or in
March. Anything left of that draw is [stranded](../Project.md#glossary): it is not
counted here, not offered by [Drill](Drilling.md#drill-home), and swept by the
build.

Until today is built the expectation is summed live — what a build now would come
out at, moving as notes are wordsmithed into pairs. From the build on it is the
value frozen on that draw, sitting beside `drawn` as a like-for-like; that pairing
is the whole reason it is stored. Both arrive from `GET /home`; neither is
computed in the app — see [api/API.md](../api/API.md#the-drill-loop).

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

Three screens, no deeper. The top bar is the same on all three: `← Home` on the
left — `memnasium` on Home itself, which has nowhere to go back to — the screen's
name on the right, and the theme toggle beyond it at the far right. There is no
other way back and nothing nests.

The toggle is one control showing the ground it will switch **to** — `☾` while
light, `☀` while dark. Dark is the [default](../standards/Style.md#choosing-a-theme),
so `☀` is what every sketch in these docs shows. There is no third "system"
position: an install that has never been touched follows the OS, and touching it
once is a choice. What each ground is
made of, and where the choice is kept, is
[standards/Style.md](../standards/Style.md#choosing-a-theme).

```
Home ──┬── Entry
       └── Drill ── a board / a roll batch ── back to Drill
```
