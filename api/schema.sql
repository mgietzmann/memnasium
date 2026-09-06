-- The DDL for memnasium. The single source of truth is design/Data.md#schema.

-- A publication a note was read in. Deduplicated on entry by search.
CREATE TABLE IF NOT EXISTS source (
    id          INTEGER PRIMARY KEY,
    author      TEXT NOT NULL,          -- primary author
    year        INTEGER NOT NULL,
    publication TEXT                    -- book/paper title; optional
);

-- A fact taken from reading, verbatim. Never drilled; never edited.
CREATE TABLE IF NOT EXISTS note (
    id         INTEGER PRIMARY KEY,
    source_id  INTEGER NOT NULL REFERENCES source(id),
    statement  TEXT NOT NULL,           -- multi-line, may contain LaTeX
    created_on TEXT NOT NULL            -- ISO date
);

-- A named set of notes that belong together; the frame a pair is recalled in.
CREATE TABLE IF NOT EXISTS groups (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT NOT NULL           -- the matching key when placing a note
);

-- A note's residency: in a group, or on the roll (group_id IS NULL).
CREATE TABLE IF NOT EXISTS placement (
    id          INTEGER PRIMARY KEY,
    note_id     INTEGER NOT NULL REFERENCES note(id),
    group_id    INTEGER REFERENCES groups(id),
    pairs_stale INTEGER NOT NULL DEFAULT 0,   -- 0/1; pairs need rewriting
    UNIQUE (note_id, group_id)
);

-- SQLite treats NULLs as distinct in a UNIQUE index, so the roll needs its own.
CREATE UNIQUE INDEX IF NOT EXISTS placement_roll ON placement (note_id) WHERE group_id IS NULL;

-- The drilled thing: one question, its answer, and its scheduling state.
CREATE TABLE IF NOT EXISTS recall_pair (
    id               INTEGER PRIMARY KEY,
    placement_id     INTEGER NOT NULL REFERENCES placement(id),
    question         TEXT NOT NULL,
    answer           TEXT NOT NULL,
    sessions_correct INTEGER NOT NULL DEFAULT 0,
    retired          INTEGER NOT NULL DEFAULT 0    -- 0/1; no longer drilled or shown
);

-- One row per date whose draw was built. Drilling deletes draw rows, so the rows
-- cannot say whether a day was built; this states it.
CREATE TABLE IF NOT EXISTS draw_day (
    day      TEXT PRIMARY KEY,   -- ISO date
    drawn    INTEGER NOT NULL,   -- how many pairs came out, for the day's record
    expected REAL NOT NULL       -- how many were expected to, computed at build
);

-- Due pairs. One row per pair that flipped heads; deleted when drilled.
-- The pair is the key, not (day, recall_pair_id): `confirm` looks a pair up by id
-- alone to learn which draw it belongs to, so a second row would silently
-- mis-date a miss.
CREATE TABLE IF NOT EXISTS draw (
    recall_pair_id INTEGER PRIMARY KEY REFERENCES recall_pair(id),
    day            TEXT NOT NULL        -- ISO date
);

-- Every read but `confirm`'s is "what is due today".
CREATE INDEX IF NOT EXISTS draw_day_idx ON draw (day);

-- One missed drill. Contested grades write nothing.
CREATE TABLE IF NOT EXISTS miss (
    id             INTEGER PRIMARY KEY,
    recall_pair_id INTEGER NOT NULL REFERENCES recall_pair(id),
    day            TEXT NOT NULL,       -- ISO date
    user_answer    TEXT NOT NULL,       -- what was typed in the answer box
    user_source    TEXT NOT NULL        -- what was typed in the source box
);
