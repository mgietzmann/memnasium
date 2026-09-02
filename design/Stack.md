# Stack

**Status:** implemented

## Table of Contents

- [Stack](#stack)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [The pieces](#the-pieces)
    - [Prerequisites](#prerequisites)
    - [Repository layout](#repository-layout)
    - [Running it](#running-it)
    - [On disk](#on-disk)
    - [Images](#images)
    - [Backup](#backup)

## Purpose

What memnasium is built out of, and how it is run.

## Scope

Covers the technology choices and why each was made, how images are stored, and what git holds.

Does **not** cover the repository tree or the commands — both are [Project.md](Project.md) — what is
built (the front doors are [games/Kin.md](games/Kin.md) and [data/Fish.md](data/Fish.md)), or code
and test conventions ([standards/Code.md](standards/Code.md),
[standards/Tests.md](standards/Tests.md)).

## Decisions

- **Chose SQLite** over anything faster, because speed is not the constraint. The data is thousands
  of rows and the heaviest query runs once a day; what is actually needed is real transactions —
  [api/Fish.md](api/Fish.md)'s entry writes a clade chain, a source, a node and two edges as one
  unit — and no server to operate.
- **Chose FastAPI** because Pydantic expresses the reference-or-object union in the entry body
  directly, and multipart upload comes for free.
- **Chose Vite + React + TypeScript** with no meta-framework: nothing is server-rendered, nothing is
  routed on a server, and the app is one local page.
- **Chose plain CSS custom properties** over a styling library, because
  [standards/Style.md](standards/Style.md) is already a token palette and there are only six
  components ([app/Components.md](app/Components.md)).
- **Chose the browser over a packaged desktop app.** `make run` serves the built app and opens a
  tab. `pywebview` is a ten-line upgrade to a real window if the tab ever grates; Electron is a
  build pipeline in exchange for a window.
- **Chose WebP over PNG for stored images.** Fish photographs are 1–3 MB as PNG and 100–300 KB as
  WebP at the same visible quality, and everything is going into git. WebP also beats PNG on the
  taxonomic plates, and keeps the one-format, no-mime-column property PNG was chosen for.
- **Chose to normalise uploads rather than reject them.** The server converts whatever is pasted in,
  so the format is an internal fact rather than something the player has to get right.
- **Chose uv** for Python. It replaces pip, venv, poetry and pyenv with one tool, and it installs
  the interpreter itself — so a fresh clone needs nothing but uv, and the Makefile never activates
  an environment.
- **Chose npm** for the app. It ships with Node and Vite defaults to it; pnpm's advantages are disk
  space and monorepo speed, and this is one app with one `package.json`.
- **Chose to commit a SQL dump instead of the database file.** SQLite is a binary that changes every
  day, and git would store a whole new copy per commit. A dump is line-oriented, so a day of play is
  a few hundred changed lines.

## Design

### The pieces

| Layer    | Choice                        |
| -------- | ----------------------------- |
| API      | FastAPI on Uvicorn            |
| Database | SQLite                        |
| App      | Vite + React + TypeScript     |
| Styling  | CSS custom properties         |
| Python   | uv                            |
| App deps | npm                           |
| Checks   | ruff, mypy, eslint, tsc, pytest — see [standards/Code.md](standards/Code.md) |
| Images   | Pillow, WebP                  |

### Prerequisites

Two things installed, nothing else:

```
uv        brings its own Python
node      brings npm
```

`make run` does the rest — `uv sync`, `npm ci`, a Vite build, then the server.

### Repository layout

The tree is in [Project.md](Project.md), which is the one reference for it. What matters here is
which parts of it are committed — see [Backup](#backup).

### Running it

One process serves both the API and the built app, so there is no CORS and no second port, and the
app is static files off the same origin as `/api`.

The commands are listed in [Project.md](Project.md), which is the one reference for them.

### On disk

```
data/memnasium.db     every table in data/Fish.md and data/Kin.md
data/images/8f21….webp
```

The database holds no image bytes — only `img_id`, which is the filename.

### Images

An upload is normalised before it is stored:

```
whatever was pasted  →  decode  →  scale so the longest side ≤ 1600px  →  WebP  →  data/images/{img_id}.webp
```

1600px is enough to tell fish apart on screen and keeps a file in the low hundreds of kilobytes.
Nothing else is stored — no original, no thumbnail. `GET /api/fish/images/{img_id}` serves the file
as `image/webp`.

### Backup

Git is the backup, so nothing binary that changes may be committed.

```
committed     data/memnasium.sql     text, diffs cleanly
              data/images/*.webp     write-once, so each file is stored exactly once
ignored       data/memnasium.db      rebuilt by make restore
```

`make backup` before committing; `make restore` on a fresh clone. Images are never edited or
deleted ([app/Fish.md](app/Fish.md)), so the repository grows only by what is actually added.
