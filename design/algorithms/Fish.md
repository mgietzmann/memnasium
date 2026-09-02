# Fish algorithms

**Status:** implemented

## Table of Contents

- [Fish algorithms](#fish-algorithms)
  - [Table of Contents](#table-of-contents)
  - [Purpose](#purpose)
  - [Scope](#scope)
  - [Decisions](#decisions)
  - [Design](#design)
    - [Normalising](#normalising)
    - [Matching clades](#matching-clades)
    - [Ranking](#ranking)
    - [Matching sources](#matching-sources)
    - [Cost](#cost)

## Purpose

What "search" means when the entry form looks something up — which rows match a query and in what
order they come back.

## Scope

Covers matching and ranking for the clade and source searches.

Does **not** cover the endpoints (see [../api/Fish.md](../api/Fish.md)), the form (see
[../app/Fish.md](../app/Fish.md)), or the model (see [../data/Fish.md](../data/Fish.md)).

## Decisions

- **Chose prefix matching on scientific names, substring on common names.** Scientific names are
  typed from the front — nobody searches for `ficialus` — while a common name is one word of a
  phrase, and `perch` should find *spotted claudperch*.
- **Chose to fold case and diacritics** so `Sphyræna` is found by typing `sphyraena`.
- **Chose to rank rather than filter.** Every kind of match comes back, ordered, because the entry
  form's next action is *create* and the player needs to be sure nothing already matches.
- **Chose alphabetical as the final tie-break** rather than recency, so the same query always gives
  the same list.
- **Chose a fixed result limit of 20**, enough that a real match is visible and few enough to scan.

## Design

### Normalising

Query and candidate go through the same fold before comparison:

```
trim  →  casefold  →  strip diacritics  →  collapse internal whitespace
```

`Sphyræna  Barracuda ` and `sphyraena barracuda` normalise alike. Nothing else is touched — no
stemming, no fuzzy distance, no transposition tolerance.

### Matching clades

```
GET /api/fish/clades?q=<query>&level=<level>
```

A clade matches when the normalised query is:

| Rule                                   | Example                          |
| -------------------------------------- | -------------------------------- |
| a prefix of the scientific name         | `artific` → *Artificialus opus*  |
| a prefix of any word of it              | `opus`    → *Artificialus opus*  |
| a substring of the common name          | `perch`   → *spotted claudperch* |

Matching a word of the scientific name is what lets a species be found by its specific epithet
without typing the genus.

`level`, when given, restricts results to that level — the walk asking *is there a genus called
this*.

### Ranking

Ties broken alphabetically by scientific name:

```
1.  exact match on the scientific name
2.  prefix of the scientific name
3.  prefix of a word of the scientific name
4.  substring of the common name
```

Then the first 20.

### Matching sources

```
GET /api/fish/sources?q=<query>
```

| Rule                            | Example              |
| ------------------------------- | -------------------- |
| a prefix of the author           | `bro`  → Brown, 2014 |
| the year, exactly               | `2014` → Brown, 2014 |
| a substring of the title         | `spine` → …          |

Ranked author-prefix, then year, then title, ties by author then year. Each result carries the
`label` — `author, year` — that a chip and a citation slot display, derived here and never stored.

Two sources sharing an author and a year are indistinguishable by label. That is
[../data/Fish.md](../data/Fish.md)'s known limit, and search does not fix it.

### Cost

A linear scan over clades or sources, both in the thousands. No index is required for this to be
instant, and none is designed. If the corpus ever makes it feel slow, the fix is an index on the
normalised names — the matching rules are chosen to be index-friendly, since all but the common-name
and title rules are prefix tests.
