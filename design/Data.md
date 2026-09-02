# Data

**Status:** drafted

## Table of Contents

- [Data](#data)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Background](#background)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Shape](#shape)
    - [Node tables](#node-tables)
    - [Edge tables](#edge-tables)
    - [Levels](#levels)
    - [Naming](#naming)
    - [Known limits](#known-limits)

## Purpose

Defines the data memnasium stores for the fish identification games: what a fact is, how facts
connect, and where the per-fact practice state lives.

## Scope

Covers the logical data model — tables, columns, keys, and the rules that hold between them.

Does **not** cover physical representation (file format, database engine, migrations), which is
settled once the games make their access patterns clear. Does **not** cover the games themselves or
the scheduling algorithm that reads `sessions_since_last_failed`.

## Background

Every game in memnasium is the same shape underneath: a graph is shown with something missing, and
the player supplies it. "Which family does *Artificialus* belong to?" hides an edge. "What species
is this?" hides a node. Modelling the data as an explicit graph means a new game is a new choice of
what to hide, not a new schema.

## Decisions

- **Nodes hold identity and payload only; every relationship is an edge.** Putting a foreign key on
  a node table would state the same relationship twice — once as a column, once as an edge row — and
  the two would drift.
- **`parent` is an edge, not a column on `clades`.** Placement in the tree is the thing most worth
  drilling, so it needs a row that can carry practice state.
- **Characters get a surrogate id.** Using the character text as a key makes a long string a
  composite key and collides whenever two clades share a characteristic.
- **Practice state lives on edge tables only.** Games test relationships; a node on its own has
  nothing to get wrong.
- **`level` is an enum, not free text.** Games ask for a rank by name, so the set of ranks has to be
  closed and comparable.
- **The parent chain may skip ranks.** Real taxonomy has gaps — a species whose genus is unknown
  sits directly under a family — so adjacency is not enforced; only strict rank ordering is.
- **Images are nodes, reusable across clades.** One plate often illustrates a genus and a species.
- **Every fact carries a source.** The point of the gym is to recall the citation with the fact, so
  images and characters both edge to `sources`.

## Design

### Shape

```
                  ┌──────────────┐
      ┌──parent───┤    clades    ├───character───┐
      │           └──────┬───────┘               │
      └──────────────────┤                       ▼
                       image              ┌────────────┐
                         │                │ characters │
                         ▼                └─────┬──────┘
                   ┌──────────┐                 │
                   │  images  │               src
                   └────┬─────┘                 │
                        │                       │
                       src ──► ┌─────────┐ ◄────┘
                               │ sources │
                               └─────────┘
```

### Node tables

Entered by hand from the sources being read.

| Table        | Columns                                        |
| ------------ | ---------------------------------------------- |
| `clades`     | `name` (PK, scientific), `common_name` (null), `level`, `created` |
| `images`     | `img_id` (PK), `img`, `created`                 |
| `characters` | `char_id` (PK), `text`, `created`               |
| `sources`    | `src` (PK, generated), `author`, `year`, `title`, `created` |

- `clades.name` is the scientific name at any rank — `Artificialus claudus` (species) and
  `Artificialus` (genus) are both rows.
- `sources.author` is the primary author's last name.
- `images.img` is the image itself; how it is stored is a representation question, out of scope here.

### Edge tables

Every edge table has a `sessions_since_last_failed` column and a `created` column. The primary key
is the pair of node keys.

| Table                    | Columns                                    | Meaning                    |
| ------------------------ | ------------------------------------------ | -------------------------- |
| `clade_parent_edges`     | `name`, `parent` → `clades`                 | placement in the tree      |
| `clade_image_edges`      | `name` → `clades`, `img_id` → `images`      | this pictures that clade   |
| `clade_character_edges`  | `name` → `clades`, `char_id` → `characters` | this clade is told by that |
| `image_src_edges`        | `img_id` → `images`, `src` → `sources`      | where the image came from  |
| `character_src_edges`    | `char_id` → `characters`, `src` → `sources` | where the claim came from  |

`sessions_since_last_failed` counts consecutive **sessions** in which the edge was recalled on the
first attempt, and resets to zero on a miss. Retries within a session do not move it. It is the
input to scheduling, which decays how often an edge is shown as the count climbs (see
[games/Kin.md](games/Kin.md)).

### Levels

`level` is one of, from broadest to narrowest:

```
class  order  suborder  family  subfamily  genus  species
```

Rules:

- `clade_parent_edges.parent` must sit at a **strictly broader** level than `name`.
- Adjacency is not required — `species` may sit directly under `family`.
- A clade has at most one parent. A clade with no parent row is a root.
- Adding a rank is a schema change, deliberately: the set stays small or the games get vague.

### Naming

- Tables are **plural** and named for their contents: `clades`, `sources`.
- Edge tables are `<from>_<to>_edges`: `clade_image_edges`.
- A column that is a foreign key keeps the referenced table's key name (`src`, `name`, `img_id`), so
  a join is visible by eye.

### Known limits

- **Single player.** `sessions_since_last_failed` sits on the fact itself, so the graph belongs to one
  person. A second player means lifting practice state into its own table keyed by player and edge.
  Accepted for now; the schema change is contained to the edge tables.
