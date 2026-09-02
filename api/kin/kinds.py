"""The four edge kinds, as one table everything dispatches on.

design/data/Kin.md chose one play table per edge kind over a single table with a type column,
because everything that touches these rows dispatches on the kind anyway. This is that dispatch,
written once so the queries can be built from it.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EdgeKind:
    """One of the four kinds of edge Kin plays.

    Attributes:
        prefix: The two letters a slot handle starts with.
        set_table: Where the day's draw and the slot state live.
        board_table: Which board the edge was dealt onto — membership and nothing else.
        knowledge_table: The design/data/Fish.md table scoring writes back to.
        keys: The two node-key columns, shared by the set table and the knowledge table.
        truth: Which of those two columns is the answer the player supplies.
        answer: The column recording what they gave.
    """

    prefix: str
    set_table: str
    board_table: str
    knowledge_table: str
    keys: tuple[str, str]
    truth: str
    answer: str

    @property
    def other(self) -> str:
        """The key column that is not the answer — the card the slot sits on."""
        return self.keys[0] if self.keys[1] == self.truth else self.keys[1]


CLADE_IMAGE = EdgeKind(
    prefix="ci",
    set_table="kin_set_clade_image_edges",
    board_table="kin_board_clade_image_edges",
    knowledge_table="clade_image_edges",
    keys=("name", "img_id"),
    truth="name",
    answer="answered_name",
)

CLADE_CHARACTER = EdgeKind(
    prefix="cc",
    set_table="kin_set_clade_character_edges",
    board_table="kin_board_clade_character_edges",
    knowledge_table="clade_character_edges",
    keys=("name", "char_id"),
    truth="name",
    answer="answered_name",
)

IMAGE_SRC = EdgeKind(
    prefix="is",
    set_table="kin_set_image_src_edges",
    board_table="kin_board_image_src_edges",
    knowledge_table="image_src_edges",
    keys=("img_id", "src"),
    truth="src",
    answer="answered_src",
)

CHARACTER_SRC = EdgeKind(
    prefix="cs",
    set_table="kin_set_character_src_edges",
    board_table="kin_board_character_src_edges",
    knowledge_table="character_src_edges",
    keys=("char_id", "src"),
    truth="src",
    answer="answered_src",
)

KINDS: tuple[EdgeKind, ...] = (CLADE_IMAGE, CLADE_CHARACTER, IMAGE_SRC, CHARACTER_SRC)
BY_PREFIX: dict[str, EdgeKind] = {kind.prefix: kind for kind in KINDS}


def handle(kind: EdgeKind, edge_id: int) -> str:
    """The slot handle for one edge: its kind and its id, `ci-41`."""
    return f"{kind.prefix}-{edge_id}"


def parse_handle(text: str) -> tuple[EdgeKind, int] | None:
    """Read a slot handle back, or None when it is not one."""
    prefix, _, rest = text.partition("-")
    kind = BY_PREFIX.get(prefix)
    if kind is None or not rest.isdigit():
        return None
    return kind, int(rest)
