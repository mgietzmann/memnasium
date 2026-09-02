# Navigation

**Status:** drafted

## Table of Contents

- [Navigation](#navigation)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Map](#map)
    - [Home](#home)

## Purpose

How the player gets anywhere. memnasium does two things — play games and take notes — and this is
the doc that says so.

## Scope

Covers the top-level map and the home screen.

Does **not** cover the games list or a game screen (see [Games.md](Games.md)), data entry (see
[Entry.md](Entry.md)), or how anything looks (see [standards/Style.md](../standards/Style.md)).

## Decisions

- **Chose two cards on home over a sidebar or a tab bar**, because there are exactly two things to
  do and persistent chrome would be chrome around nothing.
- **Chose to land on home rather than on today's game**, so opening the app to add a note does not
  route through the games list.

## Design

### Map

```
Home ──┬──► Games ──► Game screen ──► board
       └──► Entry
```

### Home

Two cards, nothing else.

```
┌─────────────────────┐  ┌─────────────────────┐
│       Games         │  │       Entry         │
│  play today's sets  │  │  add what you read  │
└─────────────────────┘  └─────────────────────┘
```
