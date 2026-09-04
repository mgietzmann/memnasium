# Entry

**Status:** under implementation

## Table of Contents

- [Entry](#entry)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [The flow](#the-flow)
    - [The source](#the-source)
    - [The statement](#the-statement)
    - [Correcting a mistake](#correcting-a-mistake)
    - [Waiting to be grouped](#waiting-to-be-grouped)
    - [Writes](#writes)

## Purpose

How a fact taken from reading gets into memnasium. Entry produces a note and its
source, and nothing else — the note is inert until [grouping](Grouping.md) picks
it up.

## Scope

Covers what entry asks for, how a source is found or made, what may still be
corrected, and what entry writes.

Does **not** cover the tables themselves (see [Data.md](../Data.md)), the screen's
layout (see [app/Entry.md](../app/Entry.md)), grouping or wordsmithing (see [Grouping.md](Grouping.md),
[Wordsmithing.md](Wordsmithing.md)).

## Decisions

- **Entry is in the app, not a skill.** Source search and live maths preview are
  UI work, and note-taking happens while reading, not while at a Claude Code
  prompt.
- **The source is sticky.** Twenty notes come out of one paper. The source is
  picked once and held across saves until it is changed.
- **Picking a source is cheap; creating one is deliberate.** Duplicate sources are
  not prevented by better search — `Riddell` and `Riddell, B.` are one careless
  click apart and permanent — so creating is a second, explicit move.
- **One note at a time.** Notes are triaged elsewhere and the keepers entered
  here; batch paste solves a problem this workflow does not have.
- **LaTeX with live preview.** The notes carry equations. Storage is plain text;
  the preview shows what the drill board will render.
- **A note may be corrected only while it has no placement.** Notes are otherwise
  immutable so pairs cannot go stale against them — but the typo you spot two
  seconds after saving is the real case, and an ungrouped note has no pairs to
  invalidate.
- **No duplicate-note detection.** A problem worth solving when it shows up.

## Design

### The flow

```
pick a source ──▶ paste the statement ──▶ save ──▶ INSERT note
     │                                              created_on = today
     └── stays picked for the next note             no placement, no pairs
```

### The source

A search box over existing sources, matching on author, year, and publication.
Typing `ridd` surfaces `Riddell 2018 — Chinook Salmon in Southeast Alaska`;
selecting it sets the source for this note and every note after it until it is
changed.

Creating a new source is a separate action, reached only after the search has
been made, and asks for **author** (required), **year** (required) and
**publication** (optional). Author and year are required because the source is
recalled and graded alongside every answer — see [Drilling.md](Drilling.md).

### The statement

A multi-line text field holding the note verbatim, LaTeX and all. A live preview
renders the maths as it is typed, so what is stored is known to render before it
is saved.

### Correcting a mistake

A note may be edited or deleted for as long as it has no `placement` row. Once
grouped it is frozen: pairs have been written against it, and the promise that
they cannot drift is worth more than the ability to fix a comma.

### Waiting to be grouped

An entered note has no placement and no pairs. It is not drawn, not drilled, and
nothing in the drill loop will ever surface it. Left to itself it is invisible.

So the count of **notes with no placement** is shown in the app, standing as the
queue for [grouping](Grouping.md). Without it, notes fall into a hole and are
found weeks later.

### Writes

| Action | Writes |
|---|---|
| Create a source | `INSERT source` |
| Save a note | `INSERT note` (`source_id` = the picked source, `created_on` = today) |
| Edit an ungrouped note | `UPDATE note SET statement` |
| Delete an ungrouped note | `DELETE note` |
