# API

**Status:** changed

## Table of Contents

- [API](#api)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Two readers](#two-readers)
    - [The drill loop](#the-drill-loop)
    - [Entry and lookup](#entry-and-lookup)
    - [Reshaping](#reshaping)
    - [Writing a pair set](#writing-a-pair-set)
    - [The MCP tools](#the-mcp-tools)
    - [Errors](#errors)

## Purpose

The one surface over the store. The app calls it over HTTP; the skills call the
same routes through an MCP server that fronts them. There is no second
implementation of any rule.

## Scope

Covers the routes, who calls each, and which of them the MCP server exposes.

Does **not** cover the schema (see [Data.md](../Data.md)), what each act means
(see [flows/](../flows)), the grading call (see [Claude.md](../Claude.md)), or
payload field-by-field detail, which is generated from the models — see
[standards/Code.md](../standards/Code.md).

## Decisions

- **One surface, two front doors.** The app calls the routes; an MCP server wraps
  a subset of them as tools. Both sit on one store module, so an invariant lives
  in exactly one place.
- **The MCP tools are curated, not the API auto-exposed.** Nothing from the drill
  loop writes is a tool. If `POST /confirm` were reachable from a Claude Code
  session, an agent could
  mark pairs correct — silently editing the record of what was actually recalled.
  That must only ever happen because the user sat down and typed an answer.
- **Grading and confirming are separate routes.** Contest sits between them, so
  grading must write nothing. See
  [flows/Drilling.md](../flows/Drilling.md#contest-and-confirm).
- **`GET /home` is coarse.** It is a dashboard; one call beats three. The corpus
  size and the [expectation](../Data.md#the-expectation) ride along with the
  backlog counts rather than earning a route of their own.
- **The draw is read only through `GET /home`.** It once had a route of
  its own, but every screen that wants the draw also wants the corpus and the
  expectation beside it, so the second route became a second way to ask the same
  question — the thing [Two readers](#two-readers) exists to avoid. `POST /draw`
  builds; nothing else reads a draw on its own.
- **A pair set is written whole.** One route expresses first write, reword, split
  and combine, so the inheritance rule lives in the API and not in three callers.
  See [Writing a pair set](#writing-a-pair-set).
- **No auth.** Single user, loopback, one process. A token would protect nothing
  from anyone.
- **Authoring needs the app running.** The MCP server fronts this API, so
  `make run` is a prerequisite for grouping and wordsmithing, not just drilling.

## Design

### Two readers

| Reader | Wants | Gets |
|---|---|---|
| the app | fine-grained routes matching screens | the drill loop, entry, lookup |
| a skill | coarse, intention-shaped calls | batch placement, whole pair sets, search |

Most routes serve exactly one of them. The overlap is entry and lookup.

### The drill loop

App only. None of these is an MCP tool.

| Route | Does |
|---|---|
| `GET /home` | the three backlog counts, the corpus size and expectation, and today's draw status |
| `POST /draw` | build today's draw, returning it. Idempotent on the `draw_day` marker — a date that already has one is reported, never redrawn |
| `GET /draw/boards?n=` | the next *n* boards of **today's** draw: a group, its due pairs, and its context pairs with answers and sources |
| `GET /draw/roll?n=` | *n* due roll pairs of **today's** draw |
| `POST /grade` | a board's typed answers → verdicts. The only Claude call; writes nothing |
| `POST /confirm` | the transaction in [flows/Drilling.md](../flows/Drilling.md#writes), against the day on each pair's own `draw` row |

Every route here reads today except `POST /confirm`, which reads the pairs it is
given. That asymmetry is the whole of what lets a board survive midnight — see
[Data.md](../Data.md#the-draw).

`GET /home` returns:

```json
{
  "ungrouped_notes": 14,
  "placements_without_pairs": 6,
  "placements_stale": 3,
  "pairs": 1204,
  "expected": 87.4,
  "draw": { "day": "2026-09-05", "drawn": 118, "expected": 87.4, "due": 34, "boards": 6, "roll": 4 }
}
```

`pairs` is every **live** pair — not retired, across groups and the roll. It is
the size of the corpus and is always present.

`expected` appears at the **top level only while today has no draw**, and is then
the live sum over those pairs — what a build right now would come out at, moving
as pairs are written. Once today's marker exists the top-level field is `null` and
the number that matters is `draw.expected`, frozen at that build. Two fields
rather than one because they are two different claims; the maths behind both is
[Data.md](../Data.md#the-expectation).

`draw` is **today's** draw, and is `null` whenever today has no `draw_day` —
whether none was ever built or the last one was yesterday. This is the only route
that reads it: both [Home](../app/Home.md) and
[Drill home](../app/Drilling.md#drill-home) fetch `/home`. A morning worked to the
end returns `drawn` with zeros beside it, not `null`, or the app would read a
finished day as an unbuilt one and offer to draw it again.

`day` is therefore always today when present, and is kept in the payload as the
statement of which day these numbers belong to rather than as something the app
compares against. Exactly one thing outlives the date: a board already on screen,
whose pairs still confirm because `confirm` reads their `draw` rows and not the
calendar. See [Data.md](../Data.md#the-draw).

### Entry and lookup

Called by both.

| Route | Does |
|---|---|
| `GET /sources?q=` | search author, year, publication |
| `POST /sources` | create one |
| `POST /notes` | create a note against a source |
| `PATCH /notes/{id}` | edit a statement. Refused once the note has a placement |
| `DELETE /notes/{id}` | same rule |
| `GET /notes` | filter by `ungrouped`, `roll`, `group_id`, `source_id`, and `q` over the statement — combinable. Every note carries `placed`, which is what makes `✎`/`✕` disappear on [Entry](../app/Entry.md#entered-today) |
| `GET /groups` | every group with its description, note count and live pair count |
| `GET /groups/{id}` | one group's notes and pairs |

`GET /notes` is what [Regrouping](../flows/Regrouping.md#pulling-notes) pulls
through. Its filters compose: everything from one source mentioning `piscivor`
is one call.

### Reshaping

Skills only.

| Route | Does |
|---|---|
| `POST /groups` | create, from a name and description the user approved |
| `PATCH /groups/{id}` | reword name or description |
| `POST /placements` | batch place — `[{note_id, group_id\|null}]` |
| `PATCH /placements/{id}` | move to another group. Sets `pairs_stale`; deletes a group the move empties |
| `GET /placements?pending` | the wordsmithing queue |
| `PUT /placements/{id}/pairs` | write the pair set; clears `pairs_stale` |
| `GET /misses` | the drill record, filtered by `group_id`, `placement_id` or `since`, newest first |

`GET /placements?pending` returns placements with no pairs or with
`pairs_stale = 1`, each carrying everything
[Wordsmithing](../flows/Wordsmithing.md#what-claude-reads) needs: the note, the
group, the group's other notes, and the group's existing pairs.

### Writing a pair set

`PUT /placements/{id}/pairs` takes the whole set at once:

```json
[
  { "id": 812, "question": "…inshore?",        "answer": "70 mm" },
  {             "question": "…offshore?",       "answer": "130 mm", "inherit_from": [812] },
  {             "question": "…what changes it?", "answer": "…",      "inherit_from": [903, 904] }
]
```

| Entry | Means |
|---|---|
| has `id` | reword that pair; `sessions_correct` untouched |
| no `id`, no `inherit_from` | a new pair at `sessions_correct = 0` |
| no `id`, with `inherit_from` | a new pair inheriting the **lower** `sessions_correct` of those named |
| a live pair of this placement, absent from the set | **retired** — `retired = 1`, its `draw` row dropped, its `miss` rows untouched |

One shape covers first write, reword, split, combine and drop, and the
inheritance rule in [Wordsmithing](../flows/Wordsmithing.md#rewriting) is enforced
here rather than remembered by every caller. The call clears `pairs_stale`.

A combine is therefore a new pair with two `inherit_from` ids, and the two
originals falling out of the set and retiring. Nothing is deleted: `miss` rows
point at pairs forever, so a pair that has been drilled can never go away — see
[Data.md](../Data.md#decisions). Retired pairs are absent from every read: boards,
context, group pair counts, `GET /placements?pending`.

### The MCP tools

Eleven, wrapping the routes above. Nothing that *writes* in
[the drill loop](#the-drill-loop) is among them — `list_misses` reads the record
and cannot touch it.

| Tool | Route |
|---|---|
| `list_ungrouped_notes` | `GET /notes?ungrouped` |
| `list_groups` | `GET /groups` |
| `get_group` | `GET /groups/{id}` |
| `search_notes` | `GET /notes` with filters |
| `place_notes` | `POST /placements` |
| `create_group` | `POST /groups` |
| `update_group` | `PATCH /groups/{id}` |
| `move_placement` | `PATCH /placements/{id}` |
| `list_pending_placements` | `GET /placements?pending` |
| `write_pairs` | `PUT /placements/{id}/pairs` |
| `list_misses` | `GET /misses` |

### Errors

Every refusal is a typed error with a reason, never a silent no-op. The ones that
are rules rather than accidents:

| Refused | Because |
|---|---|
| editing or deleting a placed note | [flows/Entry.md](../flows/Entry.md#correcting-a-mistake) |
| a roll placement for a note that has a group placement | [Data.md](../Data.md#decisions) |
| a second placement of a note into the same group | `UNIQUE (note_id, group_id)` — on `POST` **and** on a `PATCH` move into a group the note is already in |
| retiring the last live pair of a placement | it would leave a placement that reads as pairless and re-enter the wordsmithing queue forever |
| `POST /confirm` for a pair with no `draw` row | it was already confirmed, or a build has since swept it. Not being *today's* row is not a refusal — a [stranded](../Project.md#glossary) board commits normally |
| a grade response that fails validation twice | [Claude.md](../Claude.md#enforcing-the-contract) |
