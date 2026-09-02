# Fish API

**Status:** drafted

## Table of Contents

- [Fish API](#fish-api)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Endpoints](#endpoints)
    - [Searching](#searching)
    - [The walk](#the-walk)
    - [Entering a character](#entering-a-character)
    - [The clade chain](#the-clade-chain)
    - [Entering an image](#entering-an-image)
    - [Serving an image](#serving-an-image)
    - [Errors](#errors)
    - [Known limits](#known-limits)

## Purpose

The HTTP surface for the knowledge graph: finding what is already recorded, and adding what has just
been read.

## Scope

Covers the entry and lookup endpoints and their payloads.

Does **not** cover the model behind them (see [../data/Fish.md](../data/Fish.md)), the form that
drives them (see [../app/Fish.md](../app/Fish.md)), or playing (see [Kin.md](Kin.md)).

## Decisions

- **Chose one transactional POST per entry** over separate create calls, so a submission that fails
  half way cannot leave orphan clades behind — per [../app/Fish.md](../app/Fish.md).
- **Chose a reference-or-object union** for `clade` and `source`: a bare name or id means *reuse*,
  an object means *create*. The client already did the lookups, so it can say which it meant, and
  the server never has to guess with an upsert.
- **Chose `new_ancestors` + `parent`** over sending explicit clade and edge lists, because an ordered
  chain cannot express something that is not a chain.
- **Chose `404` on clade lookup as the walk's signal.** The form needs one question — *is this
  already known* — and a missing resource is already the answer to it.
- **Chose to accept any image and store WebP**, per [../data/Fish.md](../data/Fish.md). The server
  converts and scales on upload, so there is no content negotiation, no stored mime type, and no way
  for the player to supply the wrong thing.
- **Chose to return canonical references** from a create, so the sticky form's next submission sends
  a bare reference instead of trying to create the same clade twice.

## Design

### Endpoints

```
GET  /api/fish/clades?q=&level=     search
GET  /api/fish/clades/{name}        one clade and its ancestors
GET  /api/fish/sources?q=           search
POST /api/fish/characters           enter a character
POST /api/fish/images               enter an image
GET  /api/fish/images/{img_id}      the WebP
```

### Searching

```json
GET /api/fish/clades?q=artific&level=genus
[ {"name": "Artificialus", "common_name": null, "level": "genus"} ]
```

Matches scientific and common name. `level` is optional and is what the walk uses when it is asking
for one particular rank.

```json
GET /api/fish/sources?q=brown
[ {"src": 17, "author": "Brown", "year": 2014, "title": "…", "label": "Brown, 2014"} ]
```

`label` is the citation as it is shown on a card and a chip — derived, never stored.

### The walk

```json
GET /api/fish/clades/Artificialus%20claudus
{ "name": "Artificialus claudus", "common_name": "spotted claudfish", "level": "species",
  "ancestors": [ {"name": "Artificialus",   "level": "genus"},
                 {"name": "Artificialidae", "level": "family"},
                 {"name": "Perciformes",    "level": "order"} ] }
```

`ancestors` runs narrowest to broadest and is what fills the form's read-only chain. `404` means the
clade is new, and the form asks for the next rank up. Scientific names are percent-encoded in the
path.

### Entering a character

```json
POST /api/fish/characters
{ "clade":  { "name": "Artificialus claudus", "common_name": "spotted claudfish",
              "level": "species",
              "new_ancestors": [ {"name": "Artificialus",   "level": "genus"},
                                 {"name": "Artificialidae", "level": "family"} ],
              "parent": "Perciformes" },
  "source": { "author": "Brown", "year": 2014, "title": "…" },
  "text":   "three dorsal spines" }
```

Anything already recorded is sent as a bare reference instead — `"clade": "Artificialus claudus"`,
`"source": 17`. A created source gets its `src` assigned by the database.

```json
201
{ "clade": "Artificialus claudus", "source": 17, "char_id": 88 }
```

The response is what the next submission should send, which is how the sticky form stops creating
and starts referring.

One submission is one transaction, writing the clades and parent edges from the chain, the source if
it is new, the character, and both of its edges. New edges start at
`sessions_since_last_failed = 0`.

### The clade chain

`new_ancestors` runs narrowest to broadest and `parent` names the existing clade the top of it hangs
from:

```
clade                 Artificialus claudus  →  Artificialus        new_ancestors[0]
new_ancestors[0]      Artificialus          →  Artificialidae      new_ancestors[1]
new_ancestors[last]   Artificialidae        →  Perciformes         parent
```

| `new_ancestors` | `parent` | Parent edges created              |
| --------------- | -------- | --------------------------------- |
| `[]`            | a name   | clade → parent                    |
| some            | a name   | the chain, then its top → parent  |
| `[]`            | `null`   | none; the clade is a root         |
| some            | `null`   | the chain only; its top is a root |

Two things the server checks rather than trusts: every step goes to a **strictly broader** level —
ranks may be skipped but never repeat or invert — and `parent` already exists. A `parent` that does
not means the client stopped walking early.

### Entering an image

`multipart/form-data`, the same body as a character under a `json` part, with `text` replaced by an
`image` part carrying the file. Any common image format is accepted; the server scales it and stores
WebP (see [../Stack.md](../Stack.md)).

```
POST /api/fish/images
  json   { "clade": …, "source": … }
  image  <image bytes, any common format>
```

```json
201
{ "clade": "Artificialus claudus", "source": 17, "img_id": "8f21…" }
```

### Serving an image

```
GET /api/fish/images/8f21…    →  200  image/webp
```

This is what a Kin board's image cards point at (see [Kin.md](Kin.md)).

### Errors

| Case                                          | Status |
| --------------------------------------------- | ------ |
| clade or image not found                      | `404`  |
| creating a clade that already exists           | `409`  |
| `parent` does not exist                        | `400`  |
| a chain step that is not strictly broader      | `400`  |
| a level outside the enum                       | `400`  |
| an upload that is not a decodable image        | `400`  |

### Known limits

- **No idempotency key.** Submitting the same character twice creates two of them, matching
  [../app/Fish.md](../app/Fish.md)'s decision not to detect duplicates. If it ever becomes a
  problem, the key belongs on these two POSTs.
