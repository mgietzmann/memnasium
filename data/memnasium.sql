BEGIN TRANSACTION;
CREATE TABLE draw (
    day            TEXT NOT NULL,       -- ISO date
    recall_pair_id INTEGER NOT NULL REFERENCES recall_pair(id),
    PRIMARY KEY (day, recall_pair_id)
);
CREATE TABLE draw_day (
    day   TEXT PRIMARY KEY,      -- ISO date
    drawn INTEGER NOT NULL       -- how many pairs came out, for the day's record
);
CREATE TABLE groups (
    id          INTEGER PRIMARY KEY,
    name        TEXT NOT NULL,
    description TEXT NOT NULL           -- the matching key when placing a note
);
CREATE TABLE miss (
    id             INTEGER PRIMARY KEY,
    recall_pair_id INTEGER NOT NULL REFERENCES recall_pair(id),
    day            TEXT NOT NULL,       -- ISO date
    user_answer    TEXT NOT NULL,       -- what was typed in the answer box
    user_source    TEXT NOT NULL        -- what was typed in the source box
);
CREATE TABLE note (
    id         INTEGER PRIMARY KEY,
    source_id  INTEGER NOT NULL REFERENCES source(id),
    statement  TEXT NOT NULL,           -- multi-line, may contain LaTeX
    created_on TEXT NOT NULL            -- ISO date
);
CREATE TABLE placement (
    id          INTEGER PRIMARY KEY,
    note_id     INTEGER NOT NULL REFERENCES note(id),
    group_id    INTEGER REFERENCES groups(id),
    pairs_stale INTEGER NOT NULL DEFAULT 0,   -- 0/1; pairs need rewriting
    UNIQUE (note_id, group_id)
);
CREATE TABLE recall_pair (
    id               INTEGER PRIMARY KEY,
    placement_id     INTEGER NOT NULL REFERENCES placement(id),
    question         TEXT NOT NULL,
    answer           TEXT NOT NULL,
    sessions_correct INTEGER NOT NULL DEFAULT 0,
    retired          INTEGER NOT NULL DEFAULT 0    -- 0/1; no longer drilled or shown
);
CREATE TABLE source (
    id          INTEGER PRIMARY KEY,
    author      TEXT NOT NULL,          -- primary author
    year        INTEGER NOT NULL,
    publication TEXT                    -- book/paper title; optional
);
CREATE UNIQUE INDEX placement_roll ON placement (note_id) WHERE group_id IS NULL;
COMMIT;
