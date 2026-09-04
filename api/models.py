"""Every payload, defined once.

The app's TypeScript types are generated from the OpenAPI schema these produce
— see design/standards/Code.md#one-definition-of-a-payload. Nothing here is
typed by hand on the client.
"""

from pydantic import BaseModel, Field

# --------------------------------------------------------------------------- #
# Sources and notes
# --------------------------------------------------------------------------- #


class Source(BaseModel):
    """A publication a note was read in."""

    id: int
    author: str
    year: int
    publication: str | None = None


class SourceCreate(BaseModel):
    """What creating a source asks for. Author and year are required."""

    author: str = Field(min_length=1)
    year: int
    publication: str | None = None


class Note(BaseModel):
    """A note, with the source it came from.

    `placed` is what makes the edit and delete controls disappear on the entry
    screen — see design/app/Entry.md#entered-today.
    """

    id: int
    statement: str
    created_on: str
    source: Source
    placed: bool


class NoteCreate(BaseModel):
    """What saving a note asks for."""

    source_id: int
    statement: str = Field(min_length=1)


class NoteEdit(BaseModel):
    """A correction to a note that has no placement."""

    statement: str = Field(min_length=1)


# --------------------------------------------------------------------------- #
# Groups and placements
# --------------------------------------------------------------------------- #


class Group(BaseModel):
    """A group, with the two counts that say how big it has grown."""

    id: int
    name: str
    description: str
    note_count: int
    pair_count: int


class GroupCreate(BaseModel):
    """A group the user named and whose description the user approved."""

    name: str = Field(min_length=1)
    description: str = Field(min_length=1)


class GroupEdit(BaseModel):
    """A reworded name or description. Omitted fields are left alone."""

    name: str | None = None
    description: str | None = None


class Pair(BaseModel):
    """A live recall pair, with the source it walks to."""

    id: int
    placement_id: int
    question: str
    answer: str
    sessions_correct: int
    source: Source


class GroupDetail(BaseModel):
    """One group's notes and pairs."""

    group: Group
    notes: list[Note]
    pairs: list[Pair]


class PlacementRequest(BaseModel):
    """One residency to create. `group_id` of `None` is the roll."""

    note_id: int
    group_id: int | None = None


class Placement(BaseModel):
    """A note's residency, as read back."""

    id: int
    note_id: int
    group_id: int | None
    pairs_stale: bool


class PlacementMove(BaseModel):
    """Where a placement is moving to. `None` is the roll."""

    group_id: int | None = None


class PendingPlacement(BaseModel):
    """A placement waiting on wordsmithing, with everything Claude reads.

    See design/flows/Wordsmithing.md#what-claude-reads.
    """

    placement: Placement
    note: Note
    group: Group | None
    pairs: list[Pair]
    group_notes: list[Note]
    group_pairs: list[Pair]


# --------------------------------------------------------------------------- #
# Writing a pair set
# --------------------------------------------------------------------------- #


class PairWrite(BaseModel):
    """One entry in a pair set.

    An entry with an `id` rewords that pair. An entry with neither `id` nor
    `inherit_from` is a new pair at zero. An entry with `inherit_from` is a new
    pair taking the lower `sessions_correct` of the pairs it names. A live pair
    of the placement absent from the set is retired — see
    design/api/API.md#writing-a-pair-set.
    """

    id: int | None = None
    question: str = Field(min_length=1)
    answer: str = Field(min_length=1)
    inherit_from: list[int] = Field(default_factory=list)


# --------------------------------------------------------------------------- #
# The drill loop
# --------------------------------------------------------------------------- #


class DrawSummary(BaseModel):
    """The current draw, as numbers.

    `day` may be earlier than today: the current draw is the one most recently
    built and stays current until the next one replaces it — see
    design/Data.md#the-draw. `drawn` is how many came out and `expected` is how
    many were expected to, frozen at build time — neither falls; the other three
    do, as the morning is worked.
    """

    day: str
    drawn: int
    expected: float
    due: int
    boards: int
    roll: int


class Home(BaseModel):
    """The three backlog counts, the live corpus, and the current draw.

    `pairs` is every live pair and is always present. `expected` is the live sum
    over them — what a build right now would come out at — and is set **only**
    when no draw has ever been built; once there is a marker the number that
    matters is `draw.expected`, frozen at that draw's build. See
    design/api/API.md#the-drill-loop.
    """

    ungrouped_notes: int
    placements_without_pairs: int
    placements_stale: int
    pairs: int
    expected: float | None = None
    draw: DrawSummary | None = None


class DuePair(BaseModel):
    """A pair to be answered. Its answer is deliberately not sent."""

    id: int
    question: str


class ContextPair(BaseModel):
    """A pair shown answered alongside the due ones."""

    id: int
    question: str
    answer: str
    source: Source


class Board(BaseModel):
    """One group's pairs, worked as a unit."""

    group_id: int
    group_name: str
    pair_count: int
    due: list[DuePair]
    context: list[ContextPair]


class RollBatch(BaseModel):
    """`n` due roll pairs. A board without context."""

    due: list[DuePair]


class Answer(BaseModel):
    """What was typed into one due pair's two boxes."""

    recall_pair_id: int
    user_answer: str
    user_source: str


class GradeRequest(BaseModel):
    """A board's typed answers. Grading writes nothing."""

    answers: list[Answer]


class Verdict(BaseModel):
    """One pair's grade. The pair is missed unless both boxes are correct."""

    recall_pair_id: int
    answer_correct: bool
    source_correct: bool
    right_answer: str | None = None
    right_source: str | None = None


class GradeResponse(BaseModel):
    """One verdict per answer submitted."""

    verdicts: list[Verdict]


class ConfirmResult(BaseModel):
    """One pair's outcome, after any contest the user made."""

    recall_pair_id: int
    correct: bool
    user_answer: str
    user_source: str


class ConfirmRequest(BaseModel):
    """A whole board's outcomes, committed in one transaction."""

    results: list[ConfirmResult]


class Miss(BaseModel):
    """One missed drill, with what it was a miss of."""

    id: int
    recall_pair_id: int
    day: str
    user_answer: str
    user_source: str
    question: str
    answer: str
    group_id: int | None
    group_name: str | None
