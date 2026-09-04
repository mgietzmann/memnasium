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
    - [Running it](#running-it)
    - [The MCP server](#the-mcp-server)
    - [On disk](#on-disk)
    - [Backup](#backup)

## Purpose

What memnasium is built out of, and how it is run.

## Scope

Covers the technology choices and why each was made, how the MCP server is
served, and what git holds.

Does **not** cover the repository tree or the command list — both are
[Project.md](Project.md) — the routes ([api/API.md](api/API.md)), the Claude call
([Claude.md](Claude.md)), or code and test conventions
([standards/Code.md](standards/Code.md), [standards/Tests.md](standards/Tests.md)).

## Decisions

- **Chose SQLite** over anything faster, because speed is not the constraint. The
  data is thousands of rows and the heaviest query runs once a day; what is
  actually needed is real transactions —
  [confirming a board](flows/Drilling.md#writes) updates counters, writes misses
  and clears draw rows as one unit — and no server to operate.
- **Chose FastAPI**, because Pydantic expresses the payloads directly and the
  client's types are generated from them rather than written twice.
- **Chose Vite + React + TypeScript** with no meta-framework: nothing is
  server-rendered, nothing is routed on a server, and the app is one local page.
- **Chose plain CSS custom properties** over a styling library. Three screens.
- **Chose MathJax** for maths, over KaTeX. Notes carry LaTeX and both entry and
  the board render it. KaTeX is smaller and renders synchronously, but The Biggest
  Book hit real notes that only MathJax rendered, and the same corpus is coming
  here. Coverage beats size.
- **Chose the browser over a packaged desktop app.** `make run` serves the built
  app and opens a tab. `pywebview` is a small upgrade to a real window if the tab
  ever grates; Electron is a build pipeline in exchange for a window.
- **Chose to serve the MCP server from the same process** as the API, over
  `stdio`. A stdio server would spawn its own copy of the app and hold a second
  connection to the same SQLite file; sharing the process means one store module,
  one set of invariants, one lock. See [The MCP server](#the-mcp-server).
- **Chose uv** for Python. It replaces pip, venv, poetry and pyenv with one tool
  and installs the interpreter itself, so a fresh clone needs nothing but uv and
  the Makefile never activates an environment.
- **Chose npm** for the app. It ships with Node and Vite defaults to it.
- **Chose to commit a SQL dump instead of the database file.** SQLite is a binary
  that changes every day and git would store a whole new copy per commit. A dump
  is line-oriented, so a morning's drilling is a few hundred changed lines.

## Design

### The pieces

| Layer | Choice |
|---|---|
| API | FastAPI on Uvicorn |
| MCP | an MCP server mounted in the same app — see [below](#the-mcp-server) |
| Database | SQLite |
| App | Vite + React + TypeScript |
| Maths | MathJax (`better-react-mathjax`) |
| Styling | CSS custom properties |
| Python | uv |
| App deps | npm |
| Claude | the `anthropic` SDK — see [Claude.md](Claude.md#stack) |
| Checks | ruff, mypy, eslint, tsc, pytest, vitest — see [standards/Code.md](standards/Code.md) |

### Prerequisites

Two things installed, nothing else:

```
uv        brings its own Python
node      brings npm
```

`make run` does the rest — `uv sync`, `npm ci`, a Vite build, then the server.

### Running it

One process serves the API, the built app and the MCP endpoint, so there is no
CORS, no second port, and the app is static files off the same origin as `/api`.

The commands are listed in [Project.md](Project.md), which is the one reference
for them.

### The MCP server

The [ten tools](api/API.md#the-mcp-tools) are mounted on the same FastAPI app,
over HTTP, and call the same store module the routes do. `.mcp.json` in the repo
points a Claude Code session at them, so opening a session in this repo has the
tools without any setup.

```
                    ┌──────────── one process ────────────┐
   the app  ──HTTP──▶  /api/*        ─┐                    │
   a skill  ──MCP───▶  /mcp          ─┼─▶ store ─▶ SQLite  │
   the browser ─────▶  built assets  ─┘                    │
                    └─────────────────────────────────────┘
```

The consequence, stated plainly because it is a real cost: **`make run` must be
up to do any authoring.** Grouping and wordsmithing are not offline acts.

### On disk

```
data/memnasium.db     every table in Data.md
data/memnasium.sql    the dump
```

No images, no uploads, no files. Everything memnasium holds is rows.

### Backup

Git is the backup, so nothing binary that changes may be committed.

```
committed     data/memnasium.sql     text, diffs cleanly
ignored       data/memnasium.db      rebuilt by make restore
```

`make backup` before committing; `make restore` on a fresh clone.
