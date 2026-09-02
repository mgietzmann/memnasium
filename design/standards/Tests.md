# Test Standard

**Status:** drafted

## Table of Contents

- [Test Standard](#test-standard)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Tests come from the docs](#tests-come-from-the-docs)
    - [The database is real](#the-database-is-real)
    - [The taxonomy fixture](#the-taxonomy-fixture)
    - [Properties, not examples](#properties-not-examples)
    - [Randomness](#randomness)
    - [Endpoints over units](#endpoints-over-units)
    - [The app](#the-app)
    - [What is not tested](#what-is-not-tested)

## Purpose

What memnasium tests, and what a good test looks like here. The design docs are the specification;
this says how to hold the code to them.

## Scope

Covers what to test, how tests are named and organised, and what is deliberately left untested.

Does **not** cover linting, types or docstrings ([Code.md](Code.md)), the tools
([../Stack.md](../Stack.md)), or the rules being tested — those live in the docs each test names.

## Decisions

- **Chose to anchor every test to a design doc** over testing whatever the code happens to do. A
  test that mirrors the implementation passes forever and catches nothing; a test that names a
  decision fails when the decision is broken.
- **Chose never to mock the database.** SQLite is a file, so a real one costs nothing — and the
  hardest logic in this project is the queries, which a mock would not exercise at all.
- **Chose property tests for the tree algorithms**, because hand-written examples always miss the
  rank-skip cases, which are exactly where distance goes wrong.
- **Chose endpoint tests over unit tests.** The app is small enough that one call exercises route,
  validation, query and schema together, and that is the seam that actually breaks.
- **Chose no coverage target.** A percentage rewards testing getters. Every Decision with observable
  behaviour having a test is checkable by reading and points at the things that matter.
- **Chose one shared taxonomy fixture** so tests read as scenarios instead of each inventing its own
  fish.

## Design

### Tests come from the docs

A test names the rule it enforces and where the rule lives:

```python
def test_an_anchor_is_never_split_across_two_boards():   # data/Kin.md
def test_move_on_before_first_submission_fails_every_due_edge():   # games/Kin.md
def test_a_parent_must_sit_at_a_strictly_broader_level():   # data/Fish.md
```

A failure then says which decision broke, not which function. And when a doc changes, its name is
`grep`-able — the tests that need rewriting are the ones citing it.

The bar is: **every Decision in a design doc that has observable behaviour has a test.** Not a
percentage. The docs are the coverage map.

### The database is real

Every test gets a temporary SQLite file, built from the same schema the app uses, and thrown away
after. No mocks, no fakes, no in-memory substitute for the query layer.

```python
@pytest.fixture
def db(tmp_path): ...    # a real file, real schema, real transactions
```

This is the rule most likely to be broken by reflex, and the most important one here: the queries
*are* the logic.

### The taxonomy fixture

One small tree, built once, reused everywhere — with the awkward cases baked in so they are always
in play:

```
Perciformes (order)
├── Artificialidae (family)
│   ├── Artificialus (genus)
│   │   ├── A. claudus (species)
│   │   └── A. opus (species)
│   └── A. borealis (species)          ← genus skipped
└── Miniformes (order)                 ← a second root's worth of subtree
```

A skip and a distant branch are always present, so a test never has to remember to include them.

### Properties, not examples

The algorithms in [../algorithms/Kin.md](../algorithms/Kin.md) have invariants worth generating
against, with Hypothesis producing random trees:

| Property                                             |
| ---------------------------------------------------- |
| `d(A, B) == d(B, A)` and `d(A, A) == 0`               |
| `d` is undefined exactly when two clades share no root |
| every clade in a group has the same level             |
| a group is never larger than the size asked for       |
| expanding the set never adds an anchor                |
| every card on a board has both of its edges           |

Examples still cover the specific shapes in the docs; properties cover the ones nobody thought of.

### Randomness

The draw and tie-breaking are random, so an unseeded test of them is flaky forever.

- Seed the generator, or
- assert on a distribution over many trials — never on a single outcome.

A test that calls the draw and asserts a particular edge came out is wrong even when it passes.

### Endpoints over units

Most tests go through `TestClient` against a real temp database. The pyramid is upside down here on
purpose: one call covers routing, validation, the query and the response schema, and those seams are
where this app will actually break.

Unit tests are for the things with no I/O — distance, the draw, search ranking.

### The app

Vitest plus Testing Library, and only for behaviour:

- a `Slot` moves empty → filled → locked and refuses interaction when locked
- a `Chip` stays selectable after being used
- Submit is disabled until every slot is filled
- Move on asks before it acts

Query by what the player sees, never by class name.

### What is not tested

| Not tested                | Because                                        |
| ------------------------- | ---------------------------------------------- |
| layout and styling        | [Style.md](Style.md) is the spec, and a screenshot test on a design that is still moving costs more than it catches |
| generated client types    | they come from the schema, so a mismatch is a build error |
| third-party behaviour     | SQLite, FastAPI and React are not ours to test  |
