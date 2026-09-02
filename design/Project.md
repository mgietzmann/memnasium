# memnasium

**Status:** implemented

## Table of Contents

- [memnasium](#memnasium)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [The idea](#the-idea)
    - [The documents](#the-documents)
    - [The code](#the-code)
    - [Running it](#running-it)
    - [Glossary](#glossary)

## Purpose

The front door. What memnasium is, where every document lives, and how to run the thing.

## Scope

Covers the shape of the project and the vocabulary everything else uses.

Does **not** cover any component — each has its own doc below — or the working practice, which is
[CLAUDE.md](../CLAUDE.md).

## Decisions

- **Chose a folder per layer and a file per subject**, so a subject's four documents sit at the same
  filename in four folders and the map is memorable without being read.
- **Chose one front door per subject** — [games/Kin.md](games/Kin.md) for the game,
  [data/Fish.md](data/Fish.md) for the knowledge — rather than a single index that would drift.
- **Chose to keep the glossary here.** A coined term used in seven documents cannot be defined in
  any one of them without the other six pointing sideways.

## Design

### The idea

A gym for memory. You read something worth keeping, you write it down here, and the app makes you
recall it on a schedule that stretches every time you get it right.

Everything is stored as a **graph** — clades, images, characters and sources as nodes, the
relationships between them as edges — and every **game** is one way of hiding part of that graph and
asking for it back. The first is [Kin](games/Kin.md), which drills telling apart close relatives.
Recalling the **source** alongside the fact is the point, not a decoration: it is what lets a paper
get written without breaking flow to hunt for a citation.

### The documents

Each folder is a layer, each file a subject.

```
             Fish (the knowledge)        Kin (the first game)
games/            —                      what the game is
data/             the graph              what it stores while played
api/              entry and lookup       playing over HTTP
app/              the entry form         the screen and the board
algorithms/       search                 the draw, distance, grouping
```

Plus what is not per-subject:

| Doc                                          | Holds                                  |
| -------------------------------------------- | -------------------------------------- |
| [Stack.md](Stack.md)                          | what it is built from, and how it runs  |
| [app/Navigation.md](app/Navigation.md)        | home and the games list                 |
| [app/Components.md](app/Components.md)        | the reusable pieces                     |
| [standards/Design-docs.md](standards/Design-docs.md) | how these documents are written  |
| [standards/Style.md](standards/Style.md)      | colour, type, how state is shown        |
| [standards/Code.md](standards/Code.md)        | linting, types, docstrings              |
| [standards/Tests.md](standards/Tests.md)      | what is tested and how                  |

Start at a **front door** — [games/Kin.md](games/Kin.md) or [data/Fish.md](data/Fish.md) — each of
which links down to its own layers.

### The code

```
api/                    FastAPI — mirrors design/api/*.md
app/                    Vite + React + TypeScript — mirrors design/app/*.md
  package-lock.json     committed
data/
  memnasium.sql         the dump — committed
  memnasium.db          the live database — gitignored
  images/               WebP, named by img_id — committed
design/                 these documents
uv.lock                 committed
Makefile
```

A payload is defined once, as a Pydantic model, and the client's types are generated from it — see
[standards/Code.md](standards/Code.md).

### Running it

`uv` and `node` are the only prerequisites — uv brings its own Python, node brings npm. Everything
else `make run` does for you.

| Command        | Does                                                              |
| -------------- | ----------------------------------------------------------------- |
| `make run`     | builds the app if stale, restores the db if missing, serves, opens a browser |
| `make dev`     | Uvicorn with reload plus the Vite dev server, which proxies `/api` |
| `make test`    | pytest and the app's tests — [standards/Tests.md](standards/Tests.md) |
| `make lint`    | ruff, mypy, eslint, tsc — [standards/Code.md](standards/Code.md)   |
| `make backup`  | dumps the database to `data/memnasium.sql`, ready to commit        |
| `make restore` | rebuilds `data/memnasium.db` from the dump                         |

One process serves both the API and the built app, so there is no CORS and no second port. Why any
of it is what it is: [Stack.md](Stack.md).

### Glossary

Coined terms are defined here once and used identically everywhere. No synonyms.

**The knowledge**

| Term          | Means                                                                   |
| ------------- | ----------------------------------------------------------------------- |
| **clade**     | a named group at any level — a species, a genus, a family                |
| **level**     | how broad a clade is, from a fixed enum: class … species. What taxonomy calls a rank; this project only ever says *level* |
| **character** | one distinguishing feature of a clade, written as text                   |
| **image**     | a picture of a clade                                                     |
| **source**    | a publication something was read in                                      |
| **citation**  | a source as it is displayed: `author, year`                              |
| **node**      | a clade, image, character or source                                      |
| **edge**      | a relationship between two nodes, and the unit of practice               |
| **the walk**  | the entry form climbing the tree until it reaches a clade already known  |

**Playing**

| Term          | Means                                                                   |
| ------------- | ----------------------------------------------------------------------- |
| **game**      | one way of hiding part of the graph and asking for it back               |
| **session**   | a day on which a set was generated                                       |
| **set**       | the edges drawn for one session                                          |
| **spent**     | a set whose anchors have all been dealt and played                       |
| **carry-over** | a set outliving the day it was drawn: it is played to the end before another is drawn |
| **due**       | an edge drawn to be answered, rather than shown filled in                |
| **prefill**   | a slot shown already filled, because its edge was not drawn              |
| **anchor**    | a clade with at least one due edge                                       |
| **group**     | the anchors dealt onto one board — an anchor plus its nearest relatives  |
| **board**     | one round: a group, its cards, and the palettes                          |
| **distance**  | path length between two clades through the parent tree                   |
| **move on**   | giving up a board; everything not already right scores as missed         |

**On screen**

| Term       | Means                                                            |
| ---------- | ---------------------------------------------------------------- |
| **card**   | an image or character on a board, with a clade slot and a source slot |
| **slot**   | a blank holding one reference; empty, filled, or locked           |
| **chip**   | a tappable label — a clade in the palette, a citation in the pool  |
| **locked** | filled and no longer editable, because it was right or never asked |
