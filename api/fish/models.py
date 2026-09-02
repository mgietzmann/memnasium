"""The payloads of design/api/Fish.md, defined once.

The app's types are generated from the OpenAPI schema these produce — see
design/standards/Code.md. Nothing about a body is typed by hand on the client.
"""

from pydantic import BaseModel, Field

from api.levels import Level


class CladeResult(BaseModel):
    """A clade as a search result."""

    name: str
    common_name: str | None
    level: Level


class Ancestor(BaseModel):
    """One step of a clade's parent chain."""

    name: str
    level: Level


class CladeDetail(BaseModel):
    """One clade and its ancestors, narrowest to broadest.

    This is what the entry form's walk reads: a `404` instead means the clade is new.
    """

    name: str
    common_name: str | None
    level: Level
    ancestors: list[Ancestor]


class SourceResult(BaseModel):
    """A source as a search result, carrying the citation a chip displays."""

    src: int
    author: str
    year: int
    title: str
    label: str


class NewAncestor(BaseModel):
    """A clade the walk found missing, to be created with the entry."""

    name: str
    level: Level


class NewClade(BaseModel):
    """A clade to create, with the chain of ancestors that must be created above it.

    `new_ancestors` runs narrowest to broadest and `parent` names the existing clade the top of
    it hangs from. A `parent` of null makes the top of the chain a root.
    """

    name: str
    common_name: str | None = None
    level: Level
    new_ancestors: list[NewAncestor] = Field(default_factory=list)
    parent: str | None = None


class NewSource(BaseModel):
    """A source to create. Its `src` is assigned by the database."""

    author: str
    year: int
    title: str


class CharacterEntry(BaseModel):
    """One character, its clade and its source.

    `clade` and `source` are a reference-or-object union: a bare name or id means *reuse*, an
    object means *create*. The client already did the lookups, so it says which it meant.
    """

    clade: str | NewClade
    source: int | NewSource
    text: str


class ImageEntryBody(BaseModel):
    """The `json` part of an image upload — a character entry without the text."""

    clade: str | NewClade
    source: int | NewSource


class CharacterCreated(BaseModel):
    """What the next submission should send, which is how the sticky form stops creating."""

    clade: str
    source: int
    char_id: int


class ImageCreated(BaseModel):
    """What the next submission should send, which is how the sticky form stops creating."""

    clade: str
    source: int
    img_id: str
