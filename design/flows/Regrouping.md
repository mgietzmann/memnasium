# Regrouping

**Status:** drafted

## Table of Contents

- [Regrouping](#regrouping)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [The flow](#the-flow)
    - [Three ways in](#three-ways-in)
    - [Pulling notes](#pulling-notes)
    - [Settling a group](#settling-a-group)
    - [Moving placements](#moving-placements)
    - [Writes](#writes)

## Purpose

Reshaping what already exists: splitting a group that has grown too big,
harvesting a group out of the roll, and pulling a note into context when
drilling it alone has stopped working.

## Scope

Covers how a reshaping starts, how candidate members are found, what the user
confirms, and what moves.

Does **not** cover placing newly entered notes (see [Grouping.md](Grouping.md)),
rewriting the pairs that a move invalidates (see
[Wordsmithing.md](Wordsmithing.md)), or the schema (see [Data.md](../Data.md)).

## Decisions

- **The user decides a group is wrong.** Trouble in a morning's drilling is the
  signal, and only the user feels it. Claude never volunteers that a group needs
  splitting.
- **The user names the new group; Claude finds its members.** The judgment is the
  user's, the search is Claude's.
- **Search is a tool, not a guess.** Notes are pulled by group, by source, by text
  in the statement, or by any combination — see [Pulling notes](#pulling-notes).
- **The drill record is evidence.** "These are giving me trouble" is a feeling
  first and a query second: the [misses](../Data.md#misses) say which pairs have
  actually been blown, and how often. Claude reads them; the user still decides.
- **A move flags `pairs_stale`.** Pairs written for the old siblings are wrong in
  the new group; they are kept for their `sessions_correct` and marked for
  rewriting.
- **A group emptied by a move is deleted.** It matches nothing and would clutter
  every future recommendation.
- **Promotion off the roll is an `UPDATE`.** A note never holds a roll placement
  and a group placement at once.

## Design

### The flow

```
"this group is too big"          ─┐
"pull me the notes about X"      ─┼─▶ user reads them ─▶ user names a group
"what is still sitting in the roll" ─┘                          │
                                                  Claude finds candidate members
                                                                │
                                                     user confirms the members
                                                                │
                                          placements move · pairs flagged stale
                                          · emptied groups deleted
```

### Three ways in

| Way in | What the user says | What Claude does first |
|---|---|---|
| **A group is too big** | "*Productivity in upwelling systems* is unworkable" | Pulls the group's notes and its pair count so they can be read together |
| **A hunch** | "Pull me everything that mentions spawning timing" | Runs the search and shows what came back |
| **The roll is deep** | "What patterns are still sitting in the roll?" | Reads the roll's notes and describes the clusters it sees |
| **Something keeps failing** | "What have I been blowing?" | Reads the [misses](../Data.md#misses) and reports which pairs, and in which groups |

The third is the only one where Claude proposes a shape, and even there it
describes what it sees rather than creating anything.

### Pulling notes

One search, combinable:

| Filter | Example |
|---|---|
| **group** — one or several | the notes in *Onset of piscivory* |
| **the roll** | everything with no context yet |
| **source** | everything from Riddell 2018 |
| **text in the statement** | everything mentioning `piscivor` |
| **the drill record** | every pair missed since a date, and how often |

Group descriptions are read directly, so "pull the groups whose descriptions look
relevant" is Claude choosing the group ids and then pulling by group.

### Settling a group

The user names it. Claude drafts a description for approval, then searches for
members and proposes them with their statements, so the user can strike the ones
that do not belong. Nothing moves until the list is confirmed.

### Moving placements

A confirmed move rewrites `placement.group_id` and sets `pairs_stale = 1`. The
pairs travel with the placement, keeping `sessions_correct` — the memory was real
even if the wording now needs redoing.

Moving a note off the roll updates its existing placement. Moving a note between
groups updates that placement. Adding a note to a *further* group is a new
placement with no pairs, which is a fresh set of questions for the new context.

If a move empties a group, that group is deleted.

### Writes

| Action | Writes |
|---|---|
| Create the new group | `INSERT groups (name, description)` |
| Move a placement into it | `UPDATE placement SET group_id, pairs_stale = 1` |
| Add a note to a further group | `INSERT placement (note_id, group_id)` |
| Empty a group | `DELETE groups` |
| Reword a description | `UPDATE groups SET description` |

Every moved or new placement is now in the [wordsmithing](Wordsmithing.md) queue.
