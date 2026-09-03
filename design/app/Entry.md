# Entry (screen)

**Status:** drafted

## Table of Contents

- [Entry (screen)](#entry-screen)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Layout](#layout)
    - [The source bar](#the-source-bar)
    - [Statement and preview](#statement-and-preview)
    - [Entered today](#entered-today)

## Purpose

The screen for typing a note in against its source.

## Scope

Covers the layout and behaviour of the entry screen.

Does **not** cover what entry means or what it writes (see
[../flows/Entry.md](../flows/Entry.md)) or the schema (see [Data.md](../Data.md)).

## Decisions

- **Statement and preview sit side by side.** This is a desktop app; stacking the
  preview under a textarea wastes the width and hides the maths below the fold.
- **The source bar is above both and always visible.** It is sticky state, so it
  is shown rather than remembered.
- **Creating a source is a link under an empty search result**, never a button
  beside the search box — see [../flows/Entry.md](../flows/Entry.md#decisions).
- **Correction lives in a list of what was just entered.** The rule is that an
  ungrouped note can be fixed; the screen makes that reachable at the moment it
  is wanted, which is seconds after saving.

## Design

### Layout

```
┌────────────────────────────────────────────────────────────┐
│  ← Home                                            Entry   │
├────────────────────────────────────────────────────────────┤
│  Source   Riddell 2018 — Chinook Salmon in SE Alaska  [×]  │
│           ┌──────────────────────────────────────────┐     │
│           │ search sources…                          │     │
│           └──────────────────────────────────────────┘     │
├──────────────────────────────┬─────────────────────────────┤
│  Statement                   │  Preview                    │
│  ┌────────────────────────┐  │                             │
│  │ Onset of piscivory in  │  │  Onset of piscivory in      │
│  │ Puget Sound is $70$ mm │  │  Puget Sound is 70 mm       │
│  │ inshore …              │  │  inshore …                  │
│  └────────────────────────┘  │                             │
│                              │              [   Save   ]   │
├──────────────────────────────┴─────────────────────────────┤
│  Entered today                                             │
│   517  Yukon fish transition in freshwater at 85–90 mm  ✎ ✕ │
│   516  Nearshore residence lasts 30–60 d                ✎ ✕ │
└────────────────────────────────────────────────────────────┘
```

### The source bar

Shows the picked source, or nothing when none is picked. Typing in the search box
matches author, year and publication and lists what it finds; picking one sets it
and closes the list. `[×]` clears it.

When the search finds nothing, the empty result carries a **create this source**
link, which opens author / year / publication fields inline. Author and year are
required.

`Save` is disabled while no source is picked. There is no way to enter a note
without one.

### Statement and preview

A textarea holding the note verbatim. The right column renders it — LaTeX and
all — as it is typed, so what will appear on a board is known before saving.

`Save` writes the note and clears the statement. The source stays.

### Entered today

The notes saved since the screen was opened, newest first, with their id and the opening of
their statement. `✎` edits one in place; `✕` deletes it. Both are present only while
`placed` is false on the note — `GET /notes` reports it, so the controls go away
the moment [grouping](../flows/Grouping.md) has run rather than only on reload.
