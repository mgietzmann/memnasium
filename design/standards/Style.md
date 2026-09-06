# Style Standard

**Status:** changed

## Table of Contents

- [Style Standard](#style-standard)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Palette](#palette)
    - [Choosing a theme](#choosing-a-theme)
    - [Encoding state](#encoding-state)
    - [Pair states](#pair-states)
    - [Due and context](#due-and-context)
    - [Typography](#typography)
    - [Density](#density)

## Purpose

How memnasium looks: two palettes over one set of tokens, the rules for
signalling state without relying on colour, and the type and spacing everything
is built from.

## Scope

Covers colour, typography, spacing, and how interface state is encoded.

Does **not** cover what any screen contains — see [app/](../app).

## Decisions

- **Chose dark as the default, with light available.** The app is read for half
  an hour every morning, often early, and a board is a dense wall of text — a dark
  neutral ground is the kinder one to read that on, so it is what an unconfigured
  install gets. But the same board is read at a desk at noon, and dark-on-bright
  is the worse half of that trade. Both grounds, one switch.
- **Chose two palettes over one set of tokens, not two stylesheets.** The nine
  tokens are the entire colour vocabulary and nothing outside `:root` names a
  colour, so a theme is nine values. A second stylesheet would be a second place
  for `accent` to mean something and would drift within a month.
- **Chose to hold both palettes to the same contrast floor.** Light is not a
  courtesy mode. Every token is measured on all three grounds in both themes and
  the [Encoding state](#encoding-state) rules are unchanged, so nothing reads
  worse for having switched.
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

Nine tokens, two sets of values. Every colour in the app is one of these; nothing
outside `:root` names a colour.

| Token | Dark | Light | Use |
|---|---|---|---|
| `bg` | `#111417` | `#ffffff` | page ground |
| `surface` | `#191d22` | `#f6f8fa` | cards, panels, the context column |
| `raised` | `#22272e` | `#eaeef2` | inputs, hover |
| `line` | `#30363d` | `#d0d7de` | dividers and borders |
| `outline` | `#6e7681` | `#6e7681` | input outline, focus ring |
| `text` | `#e6edf3` | `#1f2328` | body and headings |
| `muted` | `#8b949e` | `#59636e` | labels, counts, sources, context answers |
| `accent` | `#58a6ff` | `#0860c4` | correct, primary action, links |
| `danger` | `#ff7b72` | `#c01c28` | a missed box, destructive confirmation |

`outline` is the one token that does not move: a mid grey at 4:1 against a near-black
ground is a mid grey at 4.6:1 against a near-white one, and a second value would be
two things to keep true for no gain.

Measured against WCAG:

```
   dark          on bg    on surface   on raised
   text          15.64      14.33        12.72     AAA
   muted          6.01       5.51         4.88     AA
   accent         7.32       6.70         5.95     AA / AAA on bg
   danger         7.33       6.72         5.96     AA / AAA on bg
   outline        4.02       3.69         3.27     AA for UI components (3:1)

   light         on bg    on surface   on raised
   text          15.80      14.84        13.55     AAA
   muted          6.11       5.74         5.24     AA
   accent         6.03       5.67         5.17     AA
   danger         6.11       5.74         5.24     AA
   outline        4.59       4.32         3.94     AA for UI components (3:1)
```

`line` is decorative only and carries no meaning; anything that must be seen uses
`outline` or better.

Read down a column and the ratios collide. In both themes `accent` and `danger`
land within a hair of each other; in light, `muted` matches them both exactly, so
a missed box and a plain label are the same grey. Only `text` and `outline` are
separable by luminance alone.

That is not a flaw to design out — pulling four tokens apart by contrast would
cost the palette its evenness and still leave hue doing the work. It is
[Encoding state](#encoding-state) restated in numbers: every one of these
distinctions is already carried by a glyph, a rule or a ground, and none of them
may be carried by hue.

### Choosing a theme

Three states, in order of precedence:

| State | Ground |
|---|---|
| the toggle was used, and chose dark | dark |
| the toggle was used, and chose light | light |
| never used | light if the OS asks for light, otherwise dark |

Which falls out of the tokens themselves without a branch in the app:

```
:root                              the dark values
@media (prefers-color-scheme: light)    the light values
:root[data-theme="dark"|"light"]        the chosen values, either direction
```

Dark is the base and light is the query, so a machine with *no* stated preference
lands on dark — the [default](#decisions) — while one asking for light is
honoured. The attribute has to override in both directions, or the toggle can
only ever move a viewer away from what the OS said and never back.

The choice is per browser and survives a reload. It is not in the database:
nothing about which ground a board is read on belongs in the study record, and it
is the one setting in memnasium that is about the room rather than the corpus.

`color-scheme` follows the ground, so form controls and scrollbars match.

The toggle itself lives in the top bar — see
[app/Home.md](../app/Home.md#navigation).

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
