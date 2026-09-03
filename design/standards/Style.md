# Style Standard

**Status:** drafted

## Table of Contents

- [Style Standard](#style-standard)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Palette](#palette)
    - [Encoding state](#encoding-state)
    - [Pair states](#pair-states)
    - [Due and context](#due-and-context)
    - [Typography](#typography)
    - [Density](#density)

## Purpose

How memnasium looks: one dark palette, the rules for signalling state without
relying on colour, and the type and spacing everything is built from.

## Scope

Covers colour, typography, spacing, and how interface state is encoded.

Does **not** cover what any screen contains — see [app/](../app).

## Decisions

- **Chose dark.** The app is read for half an hour every morning, often early,
  and a board is a dense wall of text. A dark neutral ground is the kinder one to
  read that on. (v1 chose dark to surround photographs; there are no photographs
  here, so the reason is different even though the answer is the same.)
- **Chose neutral greys with a single accent**, after networkearth.io —
  restrained, system-native, nothing decorative competing with the text.
- **Chose to encode every state without hue first**, then add colour as
  reinforcement. Colour-blind safety is not a palette choice, it is a rule about
  never letting hue carry meaning alone.
- **Chose never to pair red against green.** A grading screen is exactly where
  that pairing is reached for, and it fails for roughly one man in twelve. A miss
  is marked by a glyph and a rule, with `danger` only reinforcing it; a correct
  box is a tick in `accent`.
- **Chose blue over green for "correct"**, so a single accent also serves as the
  link and primary-button colour and the palette stays at one hue.
- **Chose the system font stack** over a webfont: nothing to load, and scientific
  names in italic render correctly on every platform.
- **Chose to render maths in the body colour.** MathJax defaults to its own; a
  formula that is a different grey from the sentence around it reads as a
  quotation.

## Design

### Palette

| Token | Hex | Use |
|---|---|---|
| `bg` | `#111417` | page ground |
| `surface` | `#191d22` | cards, panels, the context column |
| `raised` | `#22272e` | inputs, hover |
| `line` | `#30363d` | dividers and borders |
| `outline` | `#6e7681` | input outline, focus ring |
| `text` | `#e6edf3` | body and headings |
| `muted` | `#8b949e` | labels, counts, sources, context answers |
| `accent` | `#58a6ff` | correct, primary action, links |
| `danger` | `#ff7b72` | a missed box, destructive confirmation |

Measured against WCAG:

```
                 on bg    on surface   on raised
text             15.64      14.33        12.72     AAA
muted             6.01       5.51         4.88     AA
accent            7.32       6.70         5.95     AA / AAA on bg
danger            7.33       6.72         5.96     AA / AAA on bg
outline           4.02       3.69         3.27     AA for UI components (3:1)
```

`line` is decorative only and carries no meaning; anything that must be seen uses
`outline` or better.

### Encoding state

Every state must survive being rendered in greyscale. Colour may reinforce a
distinction; it may never be the only thing carrying it.

| Signal | Allowed as sole carrier |
|---|---|
| shape, border | yes |
| fill vs empty | yes |
| glyph | yes |
| position | yes |
| **hue** | **no** |

### Pair states

A due pair before and after grading. The glyph and the rule carry it; colour only
agrees.

```
   unanswered              correct                  missed
┌────────────────┐   ┌────────────────┐   ┌────────────────┐
│ answer         │   │ 70 mm       ✓  │   │ 130 mm      ✗  │
└────────────────┘   └────────────────┘   ├────────────────┤
 outline, raised      accent rule,         │ → 70 mm        │
                      tick                 └────────────────┘
                                            danger rule, cross,
                                            the truth beneath
```

Each box is graded on its own, so an answer can carry a tick while the source
beneath it carries a cross. Turn off every colour and the tick, the cross and the
`→` line still tell them apart.

### Due and context

The two columns of a [board](../app/Drilling.md#a-board) are separated by ground
and weight before anything else:

| | ground | text | has |
|---|---|---|---|
| **due** | `bg` | `text` | inputs |
| **context** | `surface` | question `text`, answer and source `muted` | nothing to click |

Context is quieter than the thing being answered but never so quiet it is hard to
read — it is the half of the board doing the actual teaching.

### Typography

```
sans   -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif
mono   ui-monospace, Menlo, Monaco, "Cascadia Mono", Consolas, monospace
```

| Element | Treatment |
|---|---|
| scientific names | *italic*, `text` |
| sources | roman, `muted`, `author year` |
| group names, counts, labels | `muted`, uppercase |
| questions | roman, `text` |
| answers | roman, `text` on the left, `muted` in context |
| maths | MathJax, inheriting the surrounding colour and size |

Scientific names are italic everywhere they appear. That is the convention the
literature already reads in.

### Density

- Base unit **8px**; every gap and padding is a multiple.
- Panels get 16px padding, 16px between them.
- A board's two columns are separated by a `line` rule and 24px, so the split is
  structural rather than implied by whitespace.
- No shadows, no gradients. Depth comes from `surface` / `raised`, one step at a
  time.
