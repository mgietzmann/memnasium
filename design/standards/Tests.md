# Test Standard

**Status:** implemented

## Table of Contents

- [Test Standard](#test-standard)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Tests come from the docs](#tests-come-from-the-docs)
    - [The database is real](#the-database-is-real)
    - [Claude is not](#claude-is-not)
    - [The corpus fixture](#the-corpus-fixture)
    - [Properties, not examples](#properties-not-examples)
    - [Randomness](#randomness)
    - [Endpoints over units](#endpoints-over-units)
    - [The app](#the-app)
    - [What is not tested](#what-is-not-tested)

## Purpose

What memnasium tests, and what a good test looks like here. The design docs are
the specification; this says how to hold the code to them.

## Scope

Covers what to test, how tests are named and organised, and what is deliberately
left untested.

Does **not** cover linting, types or docstrings ([Code.md](Code.md)), the tools
([../Stack.md](../Stack.md)), or the rules being tested — those live in the docs
each test names.

## Decisions

- **Chose to anchor every test to a design doc** over testing whatever the code
  happens to do. A test that mirrors the implementation passes forever and catches
  nothing; a test that names a decision fails when the decision is broken.
- **Chose never to mock the database.** SQLite is a file, so a real one costs
  nothing — and the hardest logic here is the queries and the confirm transaction,
  which a mock would not exercise at all.
- **Chose always to stub Claude.** Grading is the one call out; tests pass a
  canned verdict set through the injectable client and never touch the API.
- **Chose to test the tools through the store, not the transport.** An MCP tool is
  an adapter over the same function a route calls ([Code.md](Code.md#one-definition-of-a-rule)),
  so testing the route tests the tool. What *is* tested about MCP is the roster:
  the drill loop must not be exposed.
- **Chose distribution tests for the draw**, because a single trial of a coin flip
  asserts nothing and a seeded one asserts the seed.
- **Chose endpoint tests over unit tests.** One call exercises route, validation,
  query and schema together, and that is the seam that actually breaks.
- **Chose no coverage target.** A percentage rewards testing getters. Every
  Decision with observable behaviour having a test is checkable by reading, and
  points at the things that matter.

## Design

### Tests come from the docs

A test names the rule it enforces and where the rule lives:

```python
def test_a_placed_note_cannot_be_edited():                     # flows/Entry.md
def test_a_note_with_a_group_never_holds_a_roll_placement():   # Data.md
def test_a_moved_placement_flags_its_pairs_stale():            # flows/Regrouping.md
def test_a_combined_pair_inherits_the_lower_count():           # flows/Wordsmithing.md
def test_confirming_a_board_twice_is_refused():                # api/API.md
def test_a_contested_miss_writes_no_row():                     # flows/Drilling.md
```

A failure then says which decision broke, not which function. And when a doc
changes, its name is `grep`-able — the tests that need rewriting are the ones
citing it.

The bar is: **every Decision in a design doc that has observable behaviour has a
test.** Not a percentage. The docs are the coverage map.

### The database is real

Every test gets a temporary SQLite file, built from the same schema the app uses,
and thrown away after. No mocks, no fakes, no in-memory substitute for the query
layer.

```python
@pytest.fixture
def db(tmp_path): ...    # a real file, real schema, real transactions
```

This is the rule most likely to be broken by reflex, and the most important one
here: the queries *are* the logic, and
[confirm](../flows/Drilling.md#writes) is a transaction or it is a bug.

### Claude is not

The grade call sits behind an injectable function
([Claude.md](../Claude.md#stack)). Tests pass a stub returning a fixed verdict
set. What gets tested is the app's side of the contract:

- a response missing an id, carrying an extra one, or reordered is rejected
- a `right_answer` present on a correct box, or absent on a failed one, is rejected
- one retry happens, with the specific error fed back
- a second failure raises and the board writes nothing

### The corpus fixture

One small corpus, built once, reused everywhere — with the awkward cases baked in
so they are always in play:

```
sources   Riddell 2018 · Duffy 2010

groups    Onset of piscivory  ── note 1 ── pair A (sessions_correct 0)
                              └─ note 2 ── pair B, pair C     ← two pairs, one note
          Nearshore residence ── note 2                       ← note 2 again, a second
                              └─ note 3                          placement, its own pairs
the roll  note 4                                              ← placed, no group
(nothing) note 5                                              ← entered, never triaged
```

A multi-group note, a multi-pair placement, a roll note and an untriaged note are
always present, so a test never has to remember to include them.

### Properties, not examples

Worth generating against rather than enumerating:

| Property |
|---|
| a board holds every pair of its group exactly once, partitioned into due and context |
| no pair appears on two boards in one day |
| a pair's draw rate over many days approaches `e^(-α · sessions_correct)` |
| `sessions_correct` never goes below zero and never rises by more than one per confirm |
| a pair-set write leaves the placement with exactly the pairs it was given |
| an inherited count is never higher than the lowest of its predecessors |
| confirming a board deletes exactly the draw rows for the pairs on it |
| a [stranded](../Project.md#glossary) draw row is confirmable, is never served as a board or roll pair, and is not counted by `/home` |
| a miss is dated by its pair's `draw` row, never by the wall clock — confirming a board built yesterday writes yesterday |
| a pair never holds two `draw` rows, whatever order builds and confirms interleave |

Examples still cover the specific shapes in the docs; properties cover the ones
nobody thought of.

### Randomness

The draw is a coin flip per pair, so an unseeded test of a single outcome is
flaky forever and a seeded one tests the seed.

- Assert on a **distribution** over many trials — a pair at
  `sessions_correct = 4` comes up near `e^(-2) ≈ 13.5%` of days, within tolerance.
- Seed only where the test is about something *other* than the draw and just needs
  a deterministic one.

A test that builds a draw and asserts a particular pair came out is wrong even
when it passes.

### Endpoints over units

Most tests go through `TestClient` against a real temp database. The pyramid is
upside down on purpose: one call covers routing, validation, the query and the
response schema, and those seams are where this app will actually break.

Unit tests are for the things with no I/O — the draw probability, the pair-set
diff, the grade-response validator.

### The app

Vitest plus Testing Library, and only for behaviour:

- `Submit` is disabled until every box on a board has something in it
- a context pair renders its answer and offers no input
- `contest` flips a missed pair to correct and survives to `Confirm`
- the source picker holds its pick across a save
- `✎` and `✕` are absent on a note that has a placement

Query by what the user sees, never by class name.

### What is not tested

| Not tested | Because |
|---|---|
| layout and styling | [Style.md](Style.md) is the spec, and a screenshot test on a design that is still moving costs more than it catches |
| generated client types | they come from the schema, so a mismatch is a build error |
| MathJax rendering | it is the library's job; what is tested is that the LaTeX reaches it unmangled |
| third-party behaviour | SQLite, FastAPI and React are not ours to test |
| the skills themselves | they are prompts, not code — the design they follow is [flows/](../flows), and what is testable about them is the API they call |
