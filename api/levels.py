"""The `level` enum and the one comparison the tree rules need.

`level` is closed and ordered so that a parent can be required to sit at a strictly broader
level than its child — see design/data/Fish.md.
"""

from enum import StrEnum


class Level(StrEnum):
    """How broad a clade is, from broadest to narrowest.

    Adding a member is a schema change, deliberately: the set stays small or the games get vague.
    """

    CLASS = "class"
    ORDER = "order"
    SUBORDER = "suborder"
    FAMILY = "family"
    SUBFAMILY = "subfamily"
    GENUS = "genus"
    SPECIES = "species"

    @property
    def breadth(self) -> int:
        """Position in the ordering, 0 for the broadest level."""
        return LEVEL_ORDER.index(self)

    def is_broader_than(self, other: "Level") -> bool:
        """Whether this level is strictly broader than `other`.

        Levels may be skipped — `family` is broader than `species` — but never repeat or invert.
        """
        return self.breadth < other.breadth


LEVEL_ORDER: tuple[Level, ...] = (
    Level.CLASS,
    Level.ORDER,
    Level.SUBORDER,
    Level.FAMILY,
    Level.SUBFAMILY,
    Level.GENUS,
    Level.SPECIES,
)
