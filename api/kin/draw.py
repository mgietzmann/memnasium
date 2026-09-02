"""The three procedures Kin needs stated exactly — design/algorithms/Kin.md.

Nothing here touches the database: which edges are drawn, how far apart two clades are, and how
a group is chosen, as pure functions over a parent map.
"""

import math
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

ALPHA = 0.4
"""Lengthens an interval by half on each correct answer: e^0.4 = 1.49."""

MAX_CHAIN = 7
"""The level enum caps a chain at seven entries, which is what bounds every walk."""


def draw_probability(sessions_since_last_failed: int) -> float:
    """The chance an edge is drawn: `e^(−α · Δt)`.

    `Δt = 0` is certain, so a missed edge returns in the very next set.

    Args:
        sessions_since_last_failed: Consecutive sessions the edge was recalled first time.
    """
    return math.exp(-ALPHA * sessions_since_last_failed)


def is_due(sessions_since_last_failed: int, rng: random.Random) -> bool:
    """Draw one candidate edge, independently of every other.

    An edge's chance depends only on how well it is known and never on how much else is due
    that day.
    """
    return rng.random() < draw_probability(sessions_since_last_failed)


def chain(parents: Mapping[str, str], name: str) -> list[str]:
    """A clade, its parent, its grandparent, and so on to a root.

    Args:
        parents: Each clade's parent, absent for a root.
        name: Where to start.

    Returns:
        Names from `name` outward, `name` first.
    """
    walked = [name]
    seen = {name}
    for _ in range(MAX_CHAIN):
        parent = parents.get(walked[-1])
        if parent is None or parent in seen:
            break
        walked.append(parent)
        seen.add(parent)
    return walked


def distance(parents: Mapping[str, str], a: str, b: str) -> int | None:
    """Path length between two clades through the parent tree.

    Args:
        parents: Each clade's parent, absent for a root.
        a: Scientific name of the first clade.
        b: Scientific name of the second clade.

    Returns:
        Steps from `a` up to the shared ancestor and back down to `b`, or None when they share
        no ancestor — clades under different roots.
    """
    chain_a = chain(parents, a)
    chain_b = chain(parents, b)
    positions_b = {name: i for i, name in enumerate(chain_b)}
    for i, name in enumerate(chain_a):
        if name in positions_b:
            return i + positions_b[name]
    return None


@dataclass(frozen=True)
class Anchor:
    """An undealt anchor: a clade with at least one due edge, and the level it sits at."""

    name: str
    level: str


def build_group(
    parents: Mapping[str, str],
    undealt: Sequence[Anchor],
    size: int,
    rng: random.Random,
) -> list[str]:
    """One anchor picked at random plus its nearest relatives at the same level.

    Nearness is path length through the parent tree, so the group is a confusion set: congeners
    first, then the rest of the family. Unreachable clades sort last rather than being excluded,
    so a short group is still filled when the tree is a forest. Ties are shuffled, so repeated
    days at the same distance do not produce the same group.

    Args:
        parents: Each clade's parent, absent for a root.
        undealt: Every anchor with no board yet.
        size: The most clades the player asked for. The group runs short rather than padding
            with clades that have nothing due.
        rng: Seeded in tests; the draw and tie-breaking are otherwise random.

    Returns:
        The group's clade names, the picked anchor first. Empty when nothing is undealt.
    """
    if not undealt or size < 1:
        return []
    picked = rng.choice(list(undealt))
    peers = [a.name for a in undealt if a.level == picked.level and a.name != picked.name]

    def key(name: str) -> tuple[int, float, float]:
        d = distance(parents, picked.name, name)
        return (1, 0.0, rng.random()) if d is None else (0, float(d), rng.random())

    peers.sort(key=key)
    return [picked.name, *peers[: size - 1]]
