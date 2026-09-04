# memnasium

**Status:** changed

## Table of Contents

- [memnasium](#memnasium)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [The idea](#the-idea)
    - [The loop](#the-loop)
    - [The documents](#the-documents)
    - [The code](#the-code)
    - [Running it](#running-it)
    - [Glossary](#glossary)

## Purpose

The front door. What memnasium is, where every document lives, and how to run
the thing.

## Scope

Covers the shape of the project and the vocabulary everything else uses.

Does **not** cover any component — each has its own doc below — or the working
practice, which is [CLAUDE.md](../CLAUDE.md).

## Decisions

- **Chose to split by act, not by layer.** A folder per layer would put grouping's
  data, API and prompt in three places. The acts — [entry](flows/Entry.md),
  [grouping](flows/Grouping.md), [wordsmithing](flows/Wordsmithing.md),
  [regrouping](flows/Regrouping.md), [drilling](flows/Drilling.md) — are how the
  thing is actually thought about, so they are how it is written down.
- **Chose to keep the glossary here.** A coined term used in nine documents cannot
  be defined in any one of them without the other eight pointing sideways.
- **Chose two front doors and one surface.** The app is entry and drilling; the
  skills are grouping, wordsmithing and regrouping. Both go through
  [one API](api/API.md) over [one store](standards/Code.md#one-definition-of-a-rule).
- **Chose to author through Claude Code rather than build screens for it.**
  Grouping and wordsmithing are judgement and craft, done in conversation. Only
  the two acts that are neither — typing a note in, and being tested — got a UI.

## Design

### The idea

A gym for memory. You read something worth keeping, you write it down here, and
the app makes you recall it on a schedule that stretches every time you get it
right.

What makes it different from a pile of flashcards is **context**. A fact recalled
alone is trivia; the same fact recalled next to its neighbours is a structure you
can actually hold. So notes are gathered into [groups](#glossary), broken down
into short [recall pairs](#glossary), and a pair is never drilled alone — the rest
of its group sits beside it, answered, while you work.

```
Note 240 alone                      Note 240 in its group
─────────────────                   ─────────────────────────────────
Puget Sound: piscivory at           Yukon, freshwater      85–90 mm
70 mm inshore, 130 mm offshore      BC, by mass            50–100 g
                                    California Current     inverts first
                                    Puget Sound, inshore   ?
Two numbers to memorise.            A gradient with a story.
```

### The loop

```
   ┌── the app ──────────┐        ┌── a Claude Code session ────────────────┐
   │                     │        │                                         │
   │  1. Entry           │──note──▶  2. Grouping ──▶ 3. Wordsmithing        │
   │     source + note   │        │     placements      recall pairs        │
   │                     │        │                          │              │
   │  5. Drilling        │◀───────┼──────────────────────────┘              │
   │     draw · board    │        │  4. Regrouping ── splits, harvests the  │
   │     grade · confirm │        │                   roll, adds context    │
   └─────────────────────┘        └─────────────────────────────────────────┘
```

| Step | Where | Doc |
|---|---|---|
| 1. Enter a note against its source | app | [flows/Entry.md](flows/Entry.md) |
| 2. Place it in a group, or on the roll | skill | [flows/Grouping.md](flows/Grouping.md) |
| 3. Cut it into recall pairs | skill | [flows/Wordsmithing.md](flows/Wordsmithing.md) |
| 4. Split, harvest, give something context | skill | [flows/Regrouping.md](flows/Regrouping.md) |
| 5. Draw, work a board, be graded | app | [flows/Drilling.md](flows/Drilling.md) |

Steps 2–4 are how the corpus is kept in shape, and the counts on
[Home](app/Home.md#the-counts) are the only thing that will remind you they are
owed.

### The documents

Start at [the loop](#the-loop) and follow the act you care about.

| Doc | Holds |
|---|---|
| [Data.md](Data.md) | every table, the scheduling maths, what each act writes |
| [Stack.md](Stack.md) | what it is built from and how it runs |
| [Claude.md](Claude.md) | the one API call: grading a board |
| [api/API.md](api/API.md) | the routes, and the MCP tools over them |
| [flows/](flows) | the five acts — what each is, and why |
| [app/](app) | the three screens — [Home](app/Home.md), [Entry](app/Entry.md), [Drilling](app/Drilling.md) |
| [standards/Design-docs.md](standards/Design-docs.md) | how these documents are written |
| [standards/Code.md](standards/Code.md) | linting, types, docstrings, the gate |
| [standards/Tests.md](standards/Tests.md) | what is tested and how |
| [standards/Style.md](standards/Style.md) | colour, type, how state is shown |

A subject written twice is a subject that will drift, so each fact lives in one
doc and everywhere else links to it.

### The code

```
api/                    FastAPI — the routes, the store, the MCP tools
  store.py                every invariant, under both front doors
  mcp.py                  the eleven tools, mounted on the same app
  claude.py               the grade call (Claude.md)
  schema.sql              the DDL (Data.md)
app/                    Vite + React + TypeScript — mirrors design/app/*.md
  package-lock.json       committed
.claude/skills/         built from design/flows/*.md
  grouping/ wordsmithing/ regrouping/
.mcp.json               points a Claude Code session at the MCP tools
data/
  memnasium.sql           the dump — committed
  memnasium.db            the live database — gitignored
design/                 these documents
uv.lock                 committed
Makefile
```

A payload is defined once, as a Pydantic model, and the client's types are
generated from it — see [standards/Code.md](standards/Code.md).

### Running it

`uv` and `node` are the only prerequisites — uv brings its own Python, node brings
npm. Everything else `make run` does for you.

| Command | Does |
|---|---|
| `make run` | builds the app if stale, restores the db if missing, serves, opens a browser |
| `make dev` | Uvicorn with reload plus the Vite dev server, which proxies `/api` |
| `make test` | pytest and the app's tests — [standards/Tests.md](standards/Tests.md) |
| `make lint` | ruff, mypy, eslint, tsc — [standards/Code.md](standards/Code.md) |
| `make backup` | dumps the database to `data/memnasium.sql`, ready to commit |
| `make restore` | rebuilds `data/memnasium.db` from the dump |

One process serves the API, the built app and the MCP endpoint, so there is no
CORS and no second port — and **`make run` has to be up to do any authoring**, not
just drilling. Why any of it is what it is: [Stack.md](Stack.md).

### Glossary

Coined terms are defined here once and used identically everywhere. No synonyms.

**The knowledge**

| Term | Means |
|---|---|
| **source** | a publication something was read in — author, year, and optionally the title |
| **note** | a fact taken from reading, stored verbatim. Never drilled |
| **group** | a named set of notes that belong together, with a description tight enough to decide whether a new note belongs |
| **placement** | one note's residency in one group, or on the roll |
| **the roll** | where a note sits when it has no context yet — a placement with no group |
| **recall pair** | a question and its answer, cut from a note and worded for the group it sits in. The thing that is actually drilled |
| **retired** | said of a pair that is no longer drilled or shown. Pairs are retired rather than deleted, so their misses keep their meaning |
| **stale** | said of a placement whose pairs were written for a group it no longer sits in |

**Practising**

| Term | Means |
|---|---|
| **live** | said of a pair that is not retired. Every count of pairs — a group's size, the corpus, the expectation — is over live pairs only |
| **the draw** | the once-a-day coin flip that decides which pairs come up |
| **the expectation** | the mean size of a draw, `Σ e^(-α · n)` over live pairs. Shown before a build as a prediction, and stored with the draw so it can be read beside what actually came out |
| **session** | one drill of one pair. A pair not drawn had no session. Nowhere in memnasium does *session* mean anything else — a Claude Code session is always said in full |
| **`sessions_correct`** | consecutive correct drills of a pair. Sets how likely it is to be drawn |
| **board** | one group's pairs, worked as a unit: its due pairs and its context pairs |
| **due pair** | a pair drawn today — asked, answered, graded |
| **context pair** | any other pair in the group, shown question and answer, not graded |
| **roll batch** | *n* due roll pairs worked together. A board without context |
| **run** | the *n* boards or roll pairs asked for in one go. A drilling word only — grouping and wordsmithing work in **passes** |
| **contest** | overriding a verdict to correct when the grading was wrong |
| **miss** | a failed drill, and the row recording what was typed |
| **confirm** | the moment a board is written. Nothing before it counts |

**Doing the work**

| Term | Means |
|---|---|
| **entry** | typing a note in against its source |
| **pass** | the batch of notes a skill proposes on at once, answered in one message |
| **grouping** | placing newly entered notes — Claude recommends, the user decides |
| **wordsmithing** | cutting placements into recall pairs |
| **regrouping** | splitting a group, harvesting the roll, giving something context |
| **drilling** | the morning loop: draw, board, grade, confirm |
