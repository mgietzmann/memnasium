# Components

**Status:** drafted

## Table of Contents

- [Components](#components)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Inventory](#inventory)
    - [Chip](#chip)
    - [Slot](#slot)
    - [Search field](#search-field)
    - [Tabs](#tabs)
    - [Button](#button)
    - [Confirm](#confirm)
    - [Things that are not one component](#things-that-are-not-one-component)

## Purpose

The reusable pieces the screens are assembled from, so the same behaviour is not rebuilt three times
with three different feels.

## Scope

Covers the shared elements, their states, and where each one is used.

Does **not** cover colour, type, or spacing (see [../standards/Style.md](../standards/Style.md)), or
the screens themselves — [Navigation.md](Navigation.md), [Kin.md](Kin.md), [Fish.md](Fish.md).
Framework-agnostic: no stack has been chosen.

## Decisions

- **Chose to name only what is genuinely shared.** A component that exists to unify things which
  merely look alike ends up with a prop for every difference and a meaning for none.
- **Chose to keep the three kinds of card apart**, since they share a rectangle and nothing else.
- **Chose to define components by state rather than by appearance**, so
  [../standards/Style.md](../standards/Style.md) stays the only place colour is decided.

## Design

### Inventory

| Component    | Used in                                                | Varies by            |
| ------------ | ------------------------------------------------------ | -------------------- |
| Chip         | clade palette, citation pool, search results            | label, selected      |
| Slot         | a Kin card's clade and src bands                        | empty / filled / locked |
| Search field | the Fish form's clade and source fields                 | endpoint, `level` filter |
| Tabs         | the Fish form                                           | —                    |
| Button       | Generate, Start, Submit, Move on                        | primary or danger    |
| Confirm      | Move on                                                 | —                    |

### Chip

A short tappable label. The most reused thing in the app — it is the clade palette, the citation
pool, and every row of a search result.

```
┌──────────────┐   ┌──────────────┐
│ Brown, 2014  │   │ Brown, 2014  │   ← selected
└──────────────┘   ╘══════════════╛
```

States: `idle`, `selected`. A chip is never consumed — selecting one does not remove it, per
[Kin.md](Kin.md).

### Slot

A blank that holds one reference. Only Kin uses it, but it is the piece the whole board is made of.

```
┌ ─ ─ ─ ─ ─ ┐    ┌───────────┐        ┌═══════════┐
│           │    │ A. opus   │        │ A. opus ✓ │
└ ─ ─ ─ ─ ─ ┘    └───────────┘        └═══════════┘
   empty            filled              locked
```

Filling is tap-a-chip-then-tap-the-slot; tapping a filled slot clears it; a locked slot does not
respond. The three states are drawn in [../standards/Style.md](../standards/Style.md).

### Search field

Type-ahead over one endpoint, showing chips for the matches and offering **create** when nothing
matches — the explicit-create rule from [Fish.md](Fish.md).

```
┌────────────────────────────┐
│ artific                    │
├────────────────────────────┤
│ Artificialus       genus   │
│ Artificialus opus  species │
│ + create "artific"         │
└────────────────────────────┘
```

Parameterised by which endpoint it searches and, for the walk, which `level` it is restricted to.

### Tabs

One row, one selection, contents swap beneath. Used once — the Fish form's Images and Characters —
and named here so a second use does not invent its own.

### Button

Two kinds only:

| Kind    | Used for                  | Behaviour                          |
| ------- | ------------------------- | ---------------------------------- |
| primary | Generate, Start, Submit   | disabled until its form is complete |
| danger  | Move on                   | always enabled, always confirms     |

### Confirm

A modal asking once before something irreversible. One use today — Move on, which can fail a whole
board in a tap.

### Things that are not one component

Three unrelated things are called *card*:

| Called a card | Actually                    | In                  |
| ------------- | --------------------------- | ------------------- |
| home card     | a navigation target          | [Navigation.md](Navigation.md) |
| game card     | a status readout            | [Navigation.md](Navigation.md) |
| board card    | an image or character with two slots | [Kin.md](Kin.md) |

They share a bordered rectangle, which is a [Style.md](../standards/Style.md) surface, not a
component. Each is built where it is used.
