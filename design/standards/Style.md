# Style Standard

**Status:** implemented

## Table of Contents

- [Style Standard](#style-standard)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Palette](#palette)
    - [Encoding state](#encoding-state)
    - [Board states](#board-states)
    - [Typography](#typography)
    - [Density](#density)

## Purpose

How memnasium looks: one dark palette, the rules for signalling state without relying on colour, and
the type and spacing everything is built from.

## Scope

Covers colour, typography, spacing, and how interface state is encoded.

Does **not** cover what any screen contains — see [app/Kin.md](../app/Kin.md), [app/Fish.md](../app/Fish.md), and
[games/Kin.md](../games/Kin.md).

## Decisions

- **Chose dark** because the interface exists to surround photographs of fish, and a dark neutral
  ground keeps the photo the only bright thing on screen.
- **Chose neutral greys with a single accent**, after networkearth.io — restrained, system-native,
  no decoration competing with the images.
- **Chose to encode every state without hue first**, then add colour as reinforcement. Colour-blind
  safety is not a palette choice, it is a rule about never letting hue carry meaning alone.
- **Chose never to pair red against green**, rather than banning red. Red alone on a neutral dark
  ground is unambiguous and is the right colour for a destructive confirmation; it is the red/green
  *pair* carrying a distinction that fails for roughly one man in twelve. The board avoids the
  question anyway — wrong attachments clear rather than turning red (see
  [games/Kin.md](../games/Kin.md)).
- **Chose blue over green for "correct"** because a single accent that also reads as a link and a
  primary button keeps the palette to one hue.
- **Chose the system font stack** over a webfont: nothing to load, and scientific names in italic
  render correctly on every platform.

## Design

### Palette

| Token         | Hex       | Use                                    |
| ------------- | --------- | -------------------------------------- |
| `bg`          | `#111417` | page ground                            |
| `surface`     | `#191d22` | cards, panels                          |
| `raised`      | `#22272e` | chips, filled slots, hover             |
| `line`        | `#30363d` | dividers and card borders              |
| `outline`     | `#6e7681` | empty-slot outline, focus ring         |
| `text`        | `#e6edf3` | body and headings                      |
| `muted`       | `#8b949e` | labels, counts, secondary text         |
| `accent`      | `#58a6ff` | locked-correct, primary action, links  |
| `danger`      | `#ff7b72` | destructive confirmation only          |

Measured against WCAG:

```
                 on bg    on surface   on raised
text             15.64      14.33        12.72     AAA
muted             6.01       5.51         4.88     AA
accent            7.32       6.70         5.95     AA / AAA on bg
danger            7.33       6.72         5.96     AA / AAA on bg
outline           3.69*      3.69         3.27     AA for UI components (3:1)
```

`line` is decorative only and carries no meaning; anything a player must see uses `outline` or
better.

### Encoding state

Every state must survive being rendered in greyscale. Colour may reinforce a distinction; it may
never be the only thing carrying it.

| Signal        | Allowed as sole carrier |
| ------------- | ----------------------- |
| shape, border | yes                     |
| fill vs empty | yes                     |
| glyph         | yes                     |
| position      | yes                     |
| **hue**       | **no**                  |

### Board states

The three states of a slot in [Kin](../app/Kin.md), each separated by border and fill before any colour is applied:

```
   empty              filled                locked
┌ ─ ─ ─ ─ ─ ┐    ┌───────────┐        ┌═══════════┐
│           │    │ A. opus   │        │ A. opus ✓ │
└ ─ ─ ─ ─ ─ ┘    └───────────┘        └═══════════┘
 dashed           solid, raised        solid accent
 outline          fill                 border + check
```

- **empty** — dashed `outline` border, `bg` fill, no text.
- **filled** — solid `line` border, `raised` fill, `text`.
- **locked** — solid `accent` border, `raised` fill, and a check glyph.

Turn off every colour and the dash, the solid, and the check still tell them apart.

### Typography

```
sans   -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif
mono   ui-monospace, Menlo, Monaco, "Cascadia Mono", Consolas, monospace
```

| Element                | Treatment                          |
| ---------------------- | ---------------------------------- |
| scientific names       | *italic*, `text`                   |
| common names           | roman, `muted`                     |
| citations              | roman, `muted`, `author, year`     |
| level labels, counts   | `muted`, small caps or uppercase   |
| character text         | roman, `text`                      |

Scientific names are italic everywhere they appear — board, entry form, games list. That is the
convention the player already reads in the literature.

### Density

- Base unit **8px**; every gap and padding is a multiple.
- Cards get 16px padding, 16px between them.
- The board's photo is the largest thing on screen and nothing competes with it for saturation.
- No shadows, no gradients. Depth comes from `surface` / `raised`, one step at a time.
