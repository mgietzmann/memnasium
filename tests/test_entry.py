"""Entry's rules — design/flows/Entry.md."""

import sqlite3

import pytest

from api import models, store
from tests.conftest import Corpus


def test_an_ungrouped_note_can_be_corrected(db: sqlite3.Connection, corpus: Corpus) -> None:
    # flows/Entry.md#correcting-a-mistake
    fixed = store.edit_note(db, corpus.note5, models.NoteEdit(statement="corrected"))
    assert fixed.statement == "corrected"


def test_a_placed_note_cannot_be_edited(db: sqlite3.Connection, corpus: Corpus) -> None:
    # flows/Entry.md#correcting-a-mistake
    with pytest.raises(store.RefusedError):
        store.edit_note(db, corpus.note1, models.NoteEdit(statement="nope"))


def test_a_placed_note_cannot_be_deleted(db: sqlite3.Connection, corpus: Corpus) -> None:
    # flows/Entry.md#correcting-a-mistake
    with pytest.raises(store.RefusedError):
        store.delete_note(db, corpus.note1)


def test_an_ungrouped_note_can_be_deleted(db: sqlite3.Connection, corpus: Corpus) -> None:
    store.delete_note(db, corpus.note5)
    with pytest.raises(store.NotFoundError):
        store.get_note(db, corpus.note5)


def test_a_note_reports_whether_it_is_placed(db: sqlite3.Connection, corpus: Corpus) -> None:
    # app/Entry.md#entered-today — the edit and delete controls hang off this
    by_id = {n.id: n for n in store.list_notes(db)}
    assert by_id[corpus.note1].placed is True
    assert by_id[corpus.note5].placed is False


def test_a_source_is_found_by_author_year_or_publication(
    db: sqlite3.Connection, corpus: Corpus
) -> None:
    # flows/Entry.md#the-source
    assert [s.id for s in store.search_sources(db, "ridd")] == [corpus.riddell]
    assert [s.id for s in store.search_sources(db, "2010")] == [corpus.duffy]
    assert [s.id for s in store.search_sources(db, "SE Alaska")] == [corpus.riddell]
