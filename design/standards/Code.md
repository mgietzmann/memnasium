# Code Standard

**Status:** drafted

## Table of Contents

- [Code Standard](#code-standard)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Tooling](#tooling)
    - [Types](#types)
    - [One definition of a payload](#one-definition-of-a-payload)
    - [Docstrings](#docstrings)
    - [Two rules that catch bugs](#two-rules-that-catch-bugs)
    - [The gate](#the-gate)

## Purpose

How code in memnasium is written and what has to pass before it is committed.

## Scope

Covers linting, formatting, type checking, docstrings, and the commit gate, for both the Python API
and the TypeScript app.

Does **not** cover test conventions (`standards/Tests.md`), how anything looks
([Style.md](Style.md)), what the tools are ([../Stack.md](../Stack.md)), or how design docs are
written ([Design-docs.md](Design-docs.md)).

## Decisions

- **Chose strict type checking from the first commit**, because strictness is free at the start and
  expensive to retrofit.
- **Chose to generate the client's types from the API schema** rather than hand-write them, so a
  payload has one definition instead of three that drift.
- **Chose docstrings on public surfaces only.** Requiring them everywhere produces
  `"""Get the name."""` on `get_name`, which is noise that trains people to skip docstrings.
- **Chose a `make lint` gate over a pre-commit hook**, because a hook that gets in the way is a hook
  that gets disabled.
- **Chose 100 columns** to match the design docs, so a snippet can move between the two.

## Design

### Tooling

| Side       | Lint & format | Types         |
| ---------- | ------------- | ------------- |
| Python     | `ruff`        | `mypy --strict` |
| TypeScript | `eslint` + `prettier` | `tsc --strict` |

One formatter per side, no arguing. `snake_case` in Python, `camelCase` in TypeScript, and the names
from the glossary spelled the same in both.

### Types

Both checkers run in strict mode. Everything crossing a function boundary is annotated; local
inference is left alone.

### One definition of a payload

The shapes in [../api/Kin.md](../api/Kin.md) and [../api/Fish.md](../api/Fish.md) are written once,
as Pydantic models, and the client's types are generated from the OpenAPI schema those produce:

```
Pydantic model  ──►  OpenAPI schema  ──►  generated TypeScript types
```

Nothing about a request or response body is typed by hand on the client. A field renamed in Python
breaks the app's build, which is the point.

### Docstrings

Google style. Required on every module and every public function, class, and method. Not required on
private helpers whose name and signature already say it — but a private helper that needs
explaining needs a docstring, not a comment.

```python
def distance(a: str, b: str) -> int | None:
    """Path length between two clades through the parent tree.

    Args:
        a: Scientific name of the first clade.
        b: Scientific name of the second clade.

    Returns:
        Steps from `a` up to the shared ancestor and back down to `b`,
        or None when they share no ancestor.
    """
```

A docstring says what and why. It never restates the types, which are already in the signature.

### Two rules that catch bugs

- **No bare `except`.** Catch the exception you mean. A bare one swallows the failure the rest of
  the system was about to tell you about.
- **No `Any` across a module boundary.** Inside a function it is a shortcut; in a signature it is a
  hole in every check downstream.

### The gate

```
make lint        ruff + mypy + eslint + tsc
make test        standards/Tests.md
```

Both pass before a commit. There is no hook — the discipline is the gate, and CI is a later problem
than a project with one contributor has.
