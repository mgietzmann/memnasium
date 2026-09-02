"""The draw, distance, and grouping — design/algorithms/Kin.md.

Examples cover the shapes in the docs; Hypothesis covers the ones nobody thought of.
"""

import math
import random

import pytest
from hypothesis import given
from hypothesis import strategies as st

from api.kin.draw import ALPHA, Anchor, build_group, chain, distance, draw_probability, is_due

# The taxonomy fixture's tree, as a parent map — see design/standards/Tests.md.
PARENTS = {
    "Artificialidae": "Perciformes",
    "Artificialus": "Artificialidae",
    "Artificialus claudus": "Artificialus",
    "Artificialus opus": "Artificialus",
    "Artificialus borealis": "Artificialidae",
    "Artificialoides": "Artificialidae",
    "Artificialoides minor": "Artificialoides",
    "Minimidae": "Miniformes",
    "Minimus parvus": "Minimidae",
}

SPECIES = [
    Anchor("Artificialus claudus", "species"),
    Anchor("Artificialus opus", "species"),
    Anchor("Artificialus borealis", "species"),
    Anchor("Artificialoides minor", "species"),
]


@st.composite
def forests(draw: st.DrawFn) -> dict[str, str]:
    """A random forest: each node's parent is an earlier node, or nothing."""
    count = draw(st.integers(min_value=1, max_value=12))
    parents: dict[str, str] = {}
    for i in range(1, count):
        parent = draw(st.integers(min_value=-1, max_value=i - 1))
        if parent >= 0:
            parents[f"n{i}"] = f"n{parent}"
    return parents


# ────────────────────────────────────────────────────────────────────── the draw


def test_a_missed_edge_is_certain_to_come_back() -> None:  # algorithms/Kin.md
    assert draw_probability(0) == 1.0
    assert is_due(0, random.Random(1)) is True


def test_every_correct_answer_lengthens_the_interval_by_half() -> None:  # algorithms/Kin.md
    for dt in range(10):
        ratio = draw_probability(dt) / draw_probability(dt + 1)
        assert ratio == pytest.approx(math.exp(ALPHA)) and ratio == pytest.approx(1.4918, abs=1e-4)


def test_the_draw_is_independent_per_edge() -> None:  # algorithms/Kin.md
    # asserting on a distribution over many trials, never on a single outcome
    rng = random.Random(7)
    drawn = sum(is_due(4, rng) for _ in range(20000))
    assert abs(drawn / 20000 - draw_probability(4)) < 0.02


# ─────────────────────────────────────────────────────────────────────── distance


def test_the_worked_example_distances() -> None:  # games/Kin.md
    assert distance(PARENTS, "Artificialus claudus", "Artificialus opus") == 2
    assert distance(PARENTS, "Artificialus claudus", "Artificialoides minor") == 4
    assert distance(PARENTS, "Artificialus claudus", "Artificialus borealis") == 3


def test_clades_under_different_roots_have_no_distance() -> None:  # algorithms/Kin.md
    assert distance(PARENTS, "Artificialus claudus", "Minimus parvus") is None


def test_a_chain_runs_from_the_clade_out_to_its_root() -> None:  # algorithms/Kin.md
    assert chain(PARENTS, "Artificialus claudus") == [
        "Artificialus claudus",
        "Artificialus",
        "Artificialidae",
        "Perciformes",
    ]


@given(forests(), st.integers(0, 11), st.integers(0, 11))
def test_distance_is_symmetric_and_zero_on_itself(
    parents: dict[str, str], i: int, j: int
) -> None:  # algorithms/Kin.md
    a, b = f"n{i}", f"n{j}"
    assert distance(parents, a, b) == distance(parents, b, a)
    assert distance(parents, a, a) == 0


@given(forests(), st.integers(0, 11), st.integers(0, 11))
def test_distance_is_undefined_exactly_when_two_clades_share_no_root(
    parents: dict[str, str], i: int, j: int
) -> None:  # algorithms/Kin.md
    a, b = f"n{i}", f"n{j}"
    shared_root = chain(parents, a)[-1] == chain(parents, b)[-1]
    assert (distance(parents, a, b) is not None) == shared_root


# ─────────────────────────────────────────────────────────────────────── grouping


def test_a_group_is_the_anchor_and_its_nearest_relatives() -> None:  # algorithms/Kin.md
    rng = random.Random(0)
    # force the pick by offering one anchor plus peers
    group = build_group(PARENTS, SPECIES, 3, rng)
    assert len(group) == 3
    assert group[0] in {a.name for a in SPECIES}


def test_the_worked_example_group() -> None:  # games/Kin.md
    # claudus picked; opus (2) and borealis (3) beat minor (4)
    only_claudus_first = [SPECIES[0], *SPECIES[1:]]
    for seed in range(50):
        group = build_group(PARENTS, only_claudus_first, 3, random.Random(seed))
        if group[0] == "Artificialus claudus":
            assert set(group) == {
                "Artificialus claudus",
                "Artificialus opus",
                "Artificialus borealis",
            }


def test_every_clade_in_a_group_sits_at_the_same_level() -> None:  # games/Kin.md
    mixed = [*SPECIES, Anchor("Artificialus", "genus"), Anchor("Artificialoides", "genus")]
    for seed in range(30):
        group = build_group(PARENTS, mixed, 4, random.Random(seed))
        levels = {a.level for a in mixed if a.name in group}
        assert len(levels) == 1


def test_a_group_is_never_larger_than_the_size_asked_for() -> None:  # algorithms/Kin.md
    for seed in range(30):
        assert len(build_group(PARENTS, SPECIES, 2, random.Random(seed))) <= 2


def test_a_group_runs_short_rather_than_padding() -> None:  # games/Kin.md
    lonely = [Anchor("Artificialus claudus", "species"), Anchor("Artificialus", "genus")]
    for seed in range(30):
        group = build_group(PARENTS, lonely, 5, random.Random(seed))
        assert len(group) == 1


def test_unreachable_clades_sort_last_rather_than_being_excluded() -> None:  # algorithms/Kin.md
    forest = [Anchor("Artificialus claudus", "species"), Anchor("Minimus parvus", "species")]
    group = build_group(PARENTS, forest, 2, random.Random(3))
    assert len(group) == 2


def test_ties_are_shuffled_so_repeated_days_differ() -> None:  # algorithms/Kin.md
    peers = [
        Anchor("Artificialus claudus", "species"),
        Anchor("Artificialus opus", "species"),
        Anchor("Artificialus borealis", "species"),
        Anchor("Artificialoides minor", "species"),
    ]
    seen = {tuple(build_group(PARENTS, peers, 2, random.Random(s))) for s in range(40)}
    assert len(seen) > 1
