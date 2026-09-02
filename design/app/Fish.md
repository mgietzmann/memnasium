# Fish entry

**Status:** drafted

## Table of Contents

- [Fish entry](#fish-entry)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [The form](#the-form)
    - [The clade block](#the-clade-block)
    - [The source block](#the-source-block)
    - [The payload](#the-payload)
    - [What sticks](#what-sticks)
    - [What a submission writes](#what-a-submission-writes)
    - [Known limits](#known-limits)

## Purpose

The half of memnasium where facts go in. One screen for typing what you just read — a character or
an image, the clade it belongs to, and the source it came from — built so that entering ten
characters for one fish costs barely more than entering one.

## Scope

Covers the data entry screen: its fields, how a clade is resolved or created, and what a submission
writes.

Does **not** cover the data model (see [Fish.md](../data/Fish.md)), navigation to this screen (see
[Navigation.md](Navigation.md)), or any game.

## Decisions

- **Chose a clade field over a species field.** [Fish.md](../data/Fish.md) hangs characters and images off
  any clade, and [Kin](../games/Kin.md) builds boards at any level — a species-only form would
  leave every genus and family board empty.
- **Chose to walk the tree upward only as far as needed.** The walk stops at the first ancestor
  already in the database, so entering a second species in a known genus asks nothing extra.
- **Chose to let the walk skip ranks**, matching [Fish.md](../data/Fish.md) — the entry form is where the
  gaps in real taxonomy actually arrive.
- **Chose sticky fields with a cleared payload** after submit, because the slow part of entry is the
  clade and the source, and they are exactly what a run of entries has in common.
- **Chose to share stickiness across the two tabs**, so an image can be added to the fish whose
  characters were just typed without re-entering anything.
- **Chose explicit create over implicit create.** A name that does not match anything offers a
  *create* action rather than being made on submit, so a typo cannot silently mint a clade.
- **Chose no editing or deleting.** Across 500+ notes in an earlier version of this the author
  needed to hand-correct three times, so an editor would be a large build against a rare event.
  Corrections are made against the database directly.

## Design

### The form

Two tabs over one form. The tabs differ only in the payload band.

```
┌─ Data entry ───────────────────────────────────────┐
│   [ Images ]   [ Characters ]                      │
├────────────────────────────────────────────────────┤
│  Clade    Artificialus claudus      species        │
│  Common   spotted claudfish                        │
│  Genus    Artificialus                  ✓ known    │
│  Family   Artificialidae                ✓ known    │
├────────────────────────────────────────────────────┤
│  Source   Brown, 2014                   ✓ known    │
├────────────────────────────────────────────────────┤
│  Character   three dorsal spines                   │
├────────────────────────────────────────────────────┤
│                                     [ Submit ]     │
└────────────────────────────────────────────────────┘
```

### The clade block

The clade field is a search over existing `clades` by scientific and common name. What happens next
depends on whether it matched:

| Case              | Behaviour                                                        |
| ----------------- | ---------------------------------------------------------------- |
| matches a clade   | common name and the whole ancestor chain fill in, read-only       |
| no match          | offers **create**; the player picks a level and the walk begins   |

The **walk** asks for the parent one rank at a time, broadest-narrowest order per
[Fish.md](../data/Fish.md), starting just above the new clade's level:

```
new: Artificialus claudus (species)
  ├─ Genus?    → "Artificialus"      not in database → keep walking
  ├─ Family?   → "Artificialidae"    ✓ known         → stop
  └─ everything above Artificialidae is already known
```

- Any rank may be **skipped**, which produces a parent edge that jumps a level.
- The walk stops at the first rank whose answer already exists — that clade's own ancestors are
  already recorded, so there is nothing left to ask.
- A skipped-to-root walk (no ancestor known, none supplied) leaves the new clade a root.

### The source block

The same search-or-create, over `sources`. A match fills the citation; no match opens three fields —
author, year, title — and creates the source on submit. The field displays `author, year`.

### The payload

The only thing the tabs disagree about.

| Tab        | Payload field                        | Writes         |
| ---------- | ------------------------------------ | -------------- |
| Characters | the character text                   | `characters`   |
| Images     | the image (file picked or pasted)    | `images`       |

### What sticks

After a successful submit the form stays where it is, and so does everything except the payload:

```
Clade    ██ stays          Source   ██ stays
Common   ██ stays          Payload  ░░ cleared, focused
Ancestors ██ stays
```

The player types the next character and submits again. Switching tabs keeps all of it, so a run
reads: five characters for *A. claudus*, switch to Images, add its photo, all without retyping the
fish or the paper.

### What a submission writes

One submit, from a form naming clade *C*, source *S*, and a payload:

```
characters tab                       images tab
  characters      + the text           images          + the image
  clade_character_edges  C ─ char      clade_image_edges  C ─ img
  character_src_edges    char ─ S      image_src_edges    img ─ S
```

Plus, only when they were newly created: the `clades` rows and `clade_parent_edges` from the walk,
and the `sources` row. Every new edge starts at `sessions_since_last_failed = 0`, so it is certain
to be drawn the next time its game is generated.

### Known limits

- **Corrections happen outside the app**, by decision above. Nothing in the UI undoes a submission.
- **No duplicate detection on payloads.** Typing the same character twice for one clade makes two
  `characters` rows, and both will be drilled.
