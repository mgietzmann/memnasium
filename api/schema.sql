-- memnasium schema. The knowledge graph is design/data/Fish.md; the play state is design/data/Kin.md.
-- This file is the source of truth for both; data/memnasium.sql is a dump of a live database.

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────────────────── the knowledge graph

-- Node tables. Identity and payload only; every relationship is an edge.

CREATE TABLE clades (
    name        TEXT PRIMARY KEY,
    common_name TEXT,
    level       TEXT NOT NULL CHECK (
                    level IN ('class', 'order', 'suborder', 'family',
                              'subfamily', 'genus', 'species')),
    created     TEXT NOT NULL DEFAULT (datetime('now'))
) STRICT;

CREATE TABLE images (
    img_id  TEXT PRIMARY KEY,
    img     TEXT NOT NULL,  -- the file under data/images, always WebP
    created TEXT NOT NULL DEFAULT (datetime('now'))
) STRICT;

CREATE TABLE characters (
    char_id INTEGER PRIMARY KEY,
    text    TEXT NOT NULL,
    created TEXT NOT NULL DEFAULT (datetime('now'))
) STRICT;

CREATE TABLE sources (
    src     INTEGER PRIMARY KEY,
    author  TEXT NOT NULL,
    year    INTEGER NOT NULL,
    title   TEXT NOT NULL,
    created TEXT NOT NULL DEFAULT (datetime('now'))
) STRICT;

-- Edge tables. Every one carries the practice state; the key is the pair of node keys.
-- Strict level ordering on a parent edge is checked by the API, not here.

CREATE TABLE clade_parent_edges (
    name                       TEXT NOT NULL REFERENCES clades(name),
    parent                     TEXT NOT NULL REFERENCES clades(name),
    sessions_since_last_failed INTEGER NOT NULL DEFAULT 0,
    created                    TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (name, parent)
) STRICT;

-- A clade has at most one parent; a clade with no row here is a root.
CREATE UNIQUE INDEX clade_parent_edges_one_parent ON clade_parent_edges(name);
CREATE INDEX clade_parent_edges_by_parent ON clade_parent_edges(parent);

CREATE TABLE clade_image_edges (
    name                       TEXT NOT NULL REFERENCES clades(name),
    img_id                     TEXT NOT NULL REFERENCES images(img_id),
    sessions_since_last_failed INTEGER NOT NULL DEFAULT 0,
    created                    TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (name, img_id)
) STRICT;

CREATE INDEX clade_image_edges_by_img ON clade_image_edges(img_id);

CREATE TABLE clade_character_edges (
    name                       TEXT NOT NULL REFERENCES clades(name),
    char_id                    INTEGER NOT NULL REFERENCES characters(char_id),
    sessions_since_last_failed INTEGER NOT NULL DEFAULT 0,
    created                    TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (name, char_id)
) STRICT;

-- A character describes exactly one clade.
CREATE UNIQUE INDEX clade_character_edges_one_clade ON clade_character_edges(char_id);

CREATE TABLE image_src_edges (
    img_id                     TEXT NOT NULL REFERENCES images(img_id),
    src                        INTEGER NOT NULL REFERENCES sources(src),
    sessions_since_last_failed INTEGER NOT NULL DEFAULT 0,
    created                    TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (img_id, src)
) STRICT;

-- A fact has one source, the place it was first seen.
CREATE UNIQUE INDEX image_src_edges_one_src ON image_src_edges(img_id);

CREATE TABLE character_src_edges (
    char_id                    INTEGER NOT NULL REFERENCES characters(char_id),
    src                        INTEGER NOT NULL REFERENCES sources(src),
    sessions_since_last_failed INTEGER NOT NULL DEFAULT 0,
    created                    TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (char_id, src)
) STRICT;

CREATE UNIQUE INDEX character_src_edges_one_src ON character_src_edges(char_id);

-- ──────────────────────────────────────────────────────────────── Kin play state

-- Disposable. At most one set exists; generating drops the previous one and its boards.

CREATE TABLE kin_sets (
    set_id       INTEGER PRIMARY KEY,
    generated_on TEXT NOT NULL  -- the date the draw was made, YYYY-MM-DD
) STRICT;

CREATE TABLE kin_boards (
    board_id        INTEGER PRIMARY KEY,
    set_id          INTEGER NOT NULL REFERENCES kin_sets(set_id) ON DELETE CASCADE,
    level           TEXT NOT NULL CHECK (
                        level IN ('class', 'order', 'suborder', 'family',
                                  'subfamily', 'genus', 'species')),
    first_submitted TEXT,  -- stamped by the submission that scores
    ended           TEXT   -- stamped when every slot locked, or Move on was taken
) STRICT;

CREATE INDEX kin_boards_by_set ON kin_boards(set_id);

CREATE TABLE kin_set_anchors (
    set_id   INTEGER NOT NULL REFERENCES kin_sets(set_id) ON DELETE CASCADE,
    name     TEXT NOT NULL REFERENCES clades(name),
    -- copied from clades so grouping never joins for it, and held to the same enum
    level    TEXT NOT NULL CHECK (
                 level IN ('class', 'order', 'suborder', 'family',
                           'subfamily', 'genus', 'species')),
    board_id INTEGER REFERENCES kin_boards(board_id) ON DELETE CASCADE,
    PRIMARY KEY (set_id, name)
) STRICT;

CREATE INDEX kin_set_anchors_undealt ON kin_set_anchors(set_id, level, board_id);
CREATE INDEX kin_set_anchors_by_board ON kin_set_anchors(board_id);

-- One table per edge kind. The edge carries its own slot state, not the board:
-- a shared image's src edge appears on two boards and is answered and scored once.

CREATE TABLE kin_set_clade_image_edges (
    edge_id       INTEGER PRIMARY KEY,
    set_id        INTEGER NOT NULL REFERENCES kin_sets(set_id) ON DELETE CASCADE,
    name          TEXT NOT NULL REFERENCES clades(name),
    img_id        TEXT NOT NULL REFERENCES images(img_id),
    due           INTEGER NOT NULL CHECK (due IN (0, 1)),
    answered_name TEXT REFERENCES clades(name),
    locked        INTEGER NOT NULL CHECK (locked IN (0, 1)),
    UNIQUE (set_id, name, img_id)
) STRICT;

CREATE TABLE kin_set_clade_character_edges (
    edge_id       INTEGER PRIMARY KEY,
    set_id        INTEGER NOT NULL REFERENCES kin_sets(set_id) ON DELETE CASCADE,
    name          TEXT NOT NULL REFERENCES clades(name),
    char_id       INTEGER NOT NULL REFERENCES characters(char_id),
    due           INTEGER NOT NULL CHECK (due IN (0, 1)),
    answered_name TEXT REFERENCES clades(name),
    locked        INTEGER NOT NULL CHECK (locked IN (0, 1)),
    UNIQUE (set_id, name, char_id)
) STRICT;

CREATE TABLE kin_set_image_src_edges (
    edge_id      INTEGER PRIMARY KEY,
    set_id       INTEGER NOT NULL REFERENCES kin_sets(set_id) ON DELETE CASCADE,
    img_id       TEXT NOT NULL REFERENCES images(img_id),
    src          INTEGER NOT NULL REFERENCES sources(src),
    due          INTEGER NOT NULL CHECK (due IN (0, 1)),
    answered_src INTEGER REFERENCES sources(src),
    locked       INTEGER NOT NULL CHECK (locked IN (0, 1)),
    UNIQUE (set_id, img_id, src)
) STRICT;

CREATE TABLE kin_set_character_src_edges (
    edge_id      INTEGER PRIMARY KEY,
    set_id       INTEGER NOT NULL REFERENCES kin_sets(set_id) ON DELETE CASCADE,
    char_id      INTEGER NOT NULL REFERENCES characters(char_id),
    src          INTEGER NOT NULL REFERENCES sources(src),
    due          INTEGER NOT NULL CHECK (due IN (0, 1)),
    answered_src INTEGER REFERENCES sources(src),
    locked       INTEGER NOT NULL CHECK (locked IN (0, 1)),
    UNIQUE (set_id, char_id, src)
) STRICT;

-- Board tables are membership and nothing else.

CREATE TABLE kin_board_clade_image_edges (
    board_id INTEGER NOT NULL REFERENCES kin_boards(board_id) ON DELETE CASCADE,
    edge_id  INTEGER NOT NULL REFERENCES kin_set_clade_image_edges(edge_id) ON DELETE CASCADE,
    PRIMARY KEY (board_id, edge_id)
) STRICT;

CREATE TABLE kin_board_clade_character_edges (
    board_id INTEGER NOT NULL REFERENCES kin_boards(board_id) ON DELETE CASCADE,
    edge_id  INTEGER NOT NULL REFERENCES kin_set_clade_character_edges(edge_id) ON DELETE CASCADE,
    PRIMARY KEY (board_id, edge_id)
) STRICT;

CREATE TABLE kin_board_image_src_edges (
    board_id INTEGER NOT NULL REFERENCES kin_boards(board_id) ON DELETE CASCADE,
    edge_id  INTEGER NOT NULL REFERENCES kin_set_image_src_edges(edge_id) ON DELETE CASCADE,
    PRIMARY KEY (board_id, edge_id)
) STRICT;

CREATE TABLE kin_board_character_src_edges (
    board_id INTEGER NOT NULL REFERENCES kin_boards(board_id) ON DELETE CASCADE,
    edge_id  INTEGER NOT NULL REFERENCES kin_set_character_src_edges(edge_id) ON DELETE CASCADE,
    PRIMARY KEY (board_id, edge_id)
) STRICT;
