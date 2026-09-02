"""Matching and ranking for the clade and source searches — design/algorithms/Fish.md.

Nothing here touches the database. It takes rows and a query and says which match, in what
order: a linear scan over thousands of rows, which needs no index to be instant.
"""

import unicodedata
from dataclasses import dataclass
from typing import NamedTuple

LIMIT = 20
"""Enough that a real match is visible, few enough to scan."""

_LIGATURES = str.maketrans(
    {"æ": "ae", "œ": "oe", "ø": "o", "ß": "ss", "đ": "d", "ł": "l", "ð": "d", "þ": "th"}
)


def normalise(text: str) -> str:
    """Fold a query or a candidate so the two can be compared.

    `Sphyræna  Barracuda ` and `sphyraena barracuda` normalise alike. Nothing else is touched —
    no stemming, no fuzzy distance, no transposition tolerance.
    """
    folded = text.strip().casefold().translate(_LIGATURES)
    # Compatibility decomposition can hand back an uppercase letter — `𝓐` becomes `A` — so the
    # fold is applied again on the other side of it, which is also what makes this idempotent.
    decomposed = unicodedata.normalize("NFKD", folded).casefold()
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(stripped.split())


@dataclass(frozen=True)
class CladeRow:
    """A `clades` row as search sees it."""

    name: str
    common_name: str | None
    level: str


@dataclass(frozen=True)
class SourceRow:
    """A `sources` row as search sees it."""

    src: int
    author: str
    year: int
    title: str


class _Ranked(NamedTuple):
    rank: int
    tiebreak: tuple[str | int, ...]
    position: int


def _rank_clade(query: str, row: CladeRow) -> int | None:
    """Which matching rule a clade satisfies, lowest first, or None when none does.

    Matching a word of the scientific name is what lets a species be found by its specific
    epithet without typing the genus.
    """
    name = normalise(row.name)
    if name == query:
        return 0
    if name.startswith(query):
        return 1
    if any(word.startswith(query) for word in name.split(" ")):
        return 2
    if row.common_name is not None and query in normalise(row.common_name):
        return 3
    return None


def search_clades(rows: list[CladeRow], q: str, level: str | None = None) -> list[CladeRow]:
    """Rank every clade matching `q`, restricted to `level` when one is given.

    Every kind of match comes back, ordered, because the form's next action is *create* and the
    player needs to be sure nothing already matches. Ties break alphabetically by scientific
    name, so the same query always gives the same list.

    Args:
        rows: Every clade to consider.
        q: What the player typed.
        level: When given, the only level results may sit at — the walk asking *is there a
            genus called this*.

    Returns:
        At most `LIMIT` rows, best match first.
    """
    query = normalise(q)
    if not query:
        return []
    ranked: list[_Ranked] = []
    for position, row in enumerate(rows):
        if level is not None and row.level != level:
            continue
        rank = _rank_clade(query, row)
        if rank is not None:
            ranked.append(_Ranked(rank, (normalise(row.name),), position))
    ranked.sort()
    return [rows[r.position] for r in ranked[:LIMIT]]


def _rank_source(query: str, row: SourceRow) -> int | None:
    """Which matching rule a source satisfies, lowest first, or None when none does."""
    if normalise(row.author).startswith(query):
        return 0
    if query == str(row.year):
        return 1
    if query in normalise(row.title):
        return 2
    return None


def search_sources(rows: list[SourceRow], q: str) -> list[SourceRow]:
    """Rank every source matching `q`: author prefix, then year, then title.

    Two sources sharing an author and a year are indistinguishable by their label. That is
    design/data/Fish.md's known limit, and search does not fix it.

    Returns:
        At most `LIMIT` rows, best match first, ties broken by author then year.
    """
    query = normalise(q)
    if not query:
        return []
    ranked: list[_Ranked] = []
    for position, row in enumerate(rows):
        rank = _rank_source(query, row)
        if rank is not None:
            ranked.append(_Ranked(rank, (normalise(row.author), row.year), position))
    ranked.sort()
    return [rows[r.position] for r in ranked[:LIMIT]]


def citation(author: str, year: int) -> str:
    """A source as it is displayed: `author, year`. Derived here, never stored."""
    return f"{author}, {year}"
