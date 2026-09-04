# Design Documentation Standard

**Status:** drafted

This document defines how design documents are written. Every design doc under `design/` follows it. This doc follows it too.

## Table of Contents

- [Design Documentation Standard](#design-documentation-standard)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Section skeleton](#section-skeleton)
    - [Rules](#rules)
    - [Template](#template)

## Purpose

Keep design docs fast to read, consistent across the project, and free of drift. A new contributor should be able to open any doc and know where to look, trust how current it is, and follow a link rather than read the same fact written three different ways.

## Scope

Covers the structure, ordering, and writing rules for **design documents**.

Does **not** cover code style (see [Code.md](Code.md)), test conventions (see [Tests.md](Tests.md)), or product/visual style (see [Style.md](Style.md)).

## Decisions

- **Fixed section order, same in every doc.** Sameness is speed — a reader finds what they need without reading the whole doc.
- **No "open questions" section.** Pin down what the doc needs to decide while writing it. A design doc that needs to park questions isn't done.
- **Decisions before Design.** The reader sees *why* the shape is what it is before reading the shape.
- **Background is optional.** Include it only when the design doesn't make sense without context or theory.
- **Too long → split the component into a new doc.** Length is a signal the component is too big, not a cue to demote content to "implementation detail."
- **Single source of truth.** Drift — the same fact written in several places, then some of them going stale — is the main thing that kills a multi-doc design.

## Design

### Section skeleton

Every design doc has these sections, in this order:

1. **Status** — one line at the very top: one of `drafted` / `changed` / `under implementation` / `implemented`. A committed design is an agreed design, so there is no draft/agreed distinction; the status tracks where the doc sits in a build (`drafted` = new, never built; `changed` = revised for a build, not yet coded; then `under implementation`, then `implemented`). 
2. **Table of Contents** — links to every section.
3. **Purpose** — what it is, what it does, why it exists.
4. **Scope** — what this doc covers, and what it does **not**, each "not" with a pointer to the doc that does.
5. **Background** *(optional)* — context or theory a reader needs before the design makes sense.
6. **Decisions** — the *why* behind the choices. One line each: "Chose X over Y because Z."
7. **Design** — the body: what the component is and how it works, at design altitude (not line-by-line implementation).

### Rules

- **Concise and thorough.** Clear and complete, but fast to read. No walls of text. A human should get through any one doc quickly.
- **Single source of truth.** Every fact lives in exactly one doc. Everywhere else links to it. Define a thing once; point to it from then on.
- **Capture why with what.** Every non-obvious choice gets a line in Decisions. In three months, no one should have to re-litigate a settled choice from scratch.
- **Show, don't prose.** Prefer an example, a code/SQL snippet, a table, or an ASCII diagram over paragraphs. These read in seconds; prose doesn't.
- **Shared vocabulary.** Coined terms (*the roll*, *placement*, *recall pair*, *board*, *the draw*) are defined once in the glossary in [Project.md](../Project.md#glossary) and used identically everywhere. No synonyms.
- **Status stays current.** When implementation starts or finishes, update the Status line.

### Template

```markdown
# <Component Name>

**Status:** drafted

## Table of Contents

- [<Component Name>](#component-name)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Background](#background)        <!-- optional -->
  - [Decisions](#decisions)
  - [Design](#design)

## Purpose

<what it is, what it does, why it exists>

## Scope

Covers <…>. Does not cover <…> (see <link>).

## Background        <!-- optional -->

<context or theory the reader needs>

## Decisions

- Chose X over Y because Z.

## Design

<the body — examples, snippets, tables, diagrams over prose>
```
