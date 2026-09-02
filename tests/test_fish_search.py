"""Matching and ranking — design/algorithms/Fish.md."""

from hypothesis import given
from hypothesis import strategies as st

from api.fish.search import (
    LIMIT,
    CladeRow,
    SourceRow,
    citation,
    normalise,
    search_clades,
    search_sources,
)

CLADES = [
    CladeRow("Artificialidae", None, "family"),
    CladeRow("Artificialoides minor", "spotted claudperch", "species"),
    CladeRow("Artificialus", None, "genus"),
    CladeRow("Artificialus claudus", "spotted claudfish", "species"),
    CladeRow("Artificialus opus", None, "species"),
    CladeRow("Sphyraena barracuda", "great barracuda", "species"),
]

SOURCES = [
    SourceRow(17, "Brown", 2014, "Spines of the Artificialidae"),
    SourceRow(22, "Okafor", 2021, "A revision of Artificialus"),
    SourceRow(31, "Miller", 2019, "Caudal blotches in reef fishes"),
]


def names(rows: list[CladeRow]) -> list[str]:
    return [row.name for row in rows]


def test_query_and_candidate_go_through_the_same_fold() -> None:  # algorithms/Fish.md
    assert normalise("Sphyræna  Barracuda ") == normalise("sphyraena barracuda")


def test_diacritics_are_stripped_so_accents_need_not_be_typed() -> None:  # algorithms/Fish.md
    assert normalise("Poecilía") == "poecilia"


def test_a_prefix_of_the_scientific_name_matches() -> None:  # algorithms/Fish.md
    assert "Artificialus opus" in names(search_clades(CLADES, "artific"))


def test_a_prefix_of_a_word_of_the_scientific_name_matches() -> None:  # algorithms/Fish.md
    assert names(search_clades(CLADES, "opus")) == ["Artificialus opus"]


def test_a_substring_of_the_common_name_matches() -> None:  # algorithms/Fish.md
    assert names(search_clades(CLADES, "perch")) == ["Artificialoides minor"]


def test_a_substring_of_the_scientific_name_does_not_match() -> None:  # algorithms/Fish.md
    assert search_clades(CLADES, "ficialus") == []


def test_matches_are_ranked_not_filtered() -> None:  # algorithms/Fish.md
    ranked = names(search_clades(CLADES, "claud"))
    # a word of one scientific name, and a substring of two common names — every kind comes back
    assert ranked == ["Artificialus claudus", "Artificialoides minor"]


def test_ties_break_alphabetically_so_a_query_always_gives_the_same_list() -> (
    None
):  # algorithms/Fish.md
    first = names(search_clades(CLADES, "artificial"))
    assert first == sorted(first)
    assert names(search_clades(CLADES, "artificial")) == first


def test_level_restricts_results_which_is_what_the_walk_asks_with() -> None:  # algorithms/Fish.md
    assert names(search_clades(CLADES, "artific", level="genus")) == ["Artificialus"]


def test_results_are_capped_at_twenty() -> None:  # algorithms/Fish.md
    many = [CladeRow(f"Artificialus s{i:03d}", None, "species") for i in range(50)]
    assert len(search_clades(many, "artific")) == LIMIT


def test_an_empty_query_matches_nothing() -> None:  # algorithms/Fish.md
    assert search_clades(CLADES, "   ") == []


def test_a_prefix_of_the_author_matches() -> None:  # algorithms/Fish.md
    assert [r.src for r in search_sources(SOURCES, "bro")] == [17]


def test_the_year_matches_exactly() -> None:  # algorithms/Fish.md
    assert [r.src for r in search_sources(SOURCES, "2014")] == [17]


def test_a_substring_of_the_title_matches() -> None:  # algorithms/Fish.md
    assert [r.src for r in search_sources(SOURCES, "blotches")] == [31]


def test_sources_rank_author_then_year_then_title() -> None:  # algorithms/Fish.md
    ranked = [r.src for r in search_sources(SOURCES, "o")]
    assert ranked[0] == 22  # Okafor, an author prefix
    assert set(ranked[1:]) == {17, 31}  # the rest only match a title


def test_the_label_is_derived_and_never_stored() -> None:  # algorithms/Fish.md
    assert citation("Brown", 2014) == "Brown, 2014"


@given(st.text())
def test_normalising_is_idempotent(text: str) -> None:  # algorithms/Fish.md
    assert normalise(normalise(text)) == normalise(text)
