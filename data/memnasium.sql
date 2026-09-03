PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE clades (
    name        TEXT PRIMARY KEY,
    common_name TEXT,
    level       TEXT NOT NULL CHECK (
                    level IN ('class', 'order', 'suborder', 'family',
                              'subfamily', 'genus', 'species')),
    created     TEXT NOT NULL DEFAULT (datetime('now'))
) STRICT;
INSERT INTO clades VALUES('Clupeidae',NULL,'family','2026-09-02 14:22:17');
INSERT INTO clades VALUES('Clupeoidei',NULL,'suborder','2026-09-02 14:22:17');
INSERT INTO clades VALUES('Clupeiformes',NULL,'order','2026-09-02 14:22:17');
INSERT INTO clades VALUES('Actinopterygii',NULL,'class','2026-09-02 14:22:17');
INSERT INTO clades VALUES('Clupea pallasii','Pacific herring','species','2026-09-02 14:28:16');
INSERT INTO clades VALUES('Clupea',NULL,'genus','2026-09-02 14:28:16');
INSERT INTO clades VALUES('Engraulidae',NULL,'family','2026-09-02 20:49:46');
INSERT INTO clades VALUES('Osmeridae',NULL,'family','2026-09-02 20:57:12');
INSERT INTO clades VALUES('Osmeriformes',NULL,'order','2026-09-02 20:57:12');
CREATE TABLE images (
    img_id  TEXT PRIMARY KEY,
    img     TEXT NOT NULL,  -- the file under data/images, always WebP
    created TEXT NOT NULL DEFAULT (datetime('now'))
) STRICT;
INSERT INTO images VALUES('72f8cdf71da649cdb34c87c19087da4b','72f8cdf71da649cdb34c87c19087da4b.webp','2026-09-02 14:26:15');
INSERT INTO images VALUES('a6074cdbec3b4dda9a39c68d95f1620b','a6074cdbec3b4dda9a39c68d95f1620b.webp','2026-09-02 14:29:06');
INSERT INTO images VALUES('c798023b7c564139a440682df420e36c','c798023b7c564139a440682df420e36c.webp','2026-09-02 20:53:09');
INSERT INTO images VALUES('b836f5e213454c7fa559f9120f7b4d54','b836f5e213454c7fa559f9120f7b4d54.webp','2026-09-02 20:59:52');
CREATE TABLE characters (
    char_id INTEGER PRIMARY KEY,
    text    TEXT NOT NULL,
    created TEXT NOT NULL DEFAULT (datetime('now'))
) STRICT;
INSERT INTO characters VALUES(1,'Scutes present along the belly','2026-09-02 14:22:17');
INSERT INTO characters VALUES(2,'Maxillae not extending posteriorly past eyes','2026-09-02 14:23:04');
INSERT INTO characters VALUES(3,'No lateral black spots','2026-09-02 14:28:16');
INSERT INTO characters VALUES(4,'No striations on the operculum','2026-09-02 14:28:45');
INSERT INTO characters VALUES(5,'No enlarged scales on the base of the caudal fin','2026-09-02 14:28:59');
INSERT INTO characters VALUES(6,'No scutes along belly.','2026-09-02 20:49:46');
INSERT INTO characters VALUES(7,'Maxillae extending posteriorly far past eyes','2026-09-02 20:50:09');
INSERT INTO characters VALUES(8,'Presence of a dorsal adipose fin.','2026-09-02 20:57:12');
CREATE TABLE sources (
    src     INTEGER PRIMARY KEY,
    author  TEXT NOT NULL,
    year    INTEGER NOT NULL,
    title   TEXT NOT NULL,
    created TEXT NOT NULL DEFAULT (datetime('now'))
) STRICT;
INSERT INTO sources VALUES(1,'Mecklenburg',2002,'Fishes of Alaska','2026-09-02 14:22:17');
CREATE TABLE clade_parent_edges (
    name                       TEXT NOT NULL REFERENCES clades(name),
    parent                     TEXT NOT NULL REFERENCES clades(name),
    sessions_since_last_failed INTEGER NOT NULL DEFAULT 0,
    created                    TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (name, parent)
) STRICT;
INSERT INTO clade_parent_edges VALUES('Clupeidae','Clupeoidei',0,'2026-09-02 14:22:17');
INSERT INTO clade_parent_edges VALUES('Clupeoidei','Clupeiformes',0,'2026-09-02 14:22:17');
INSERT INTO clade_parent_edges VALUES('Clupeiformes','Actinopterygii',0,'2026-09-02 14:22:17');
INSERT INTO clade_parent_edges VALUES('Clupea pallasii','Clupea',0,'2026-09-02 14:28:16');
INSERT INTO clade_parent_edges VALUES('Clupea','Clupeidae',0,'2026-09-02 14:28:16');
INSERT INTO clade_parent_edges VALUES('Engraulidae','Clupeiformes',0,'2026-09-02 20:49:46');
INSERT INTO clade_parent_edges VALUES('Osmeridae','Osmeriformes',0,'2026-09-02 20:57:12');
INSERT INTO clade_parent_edges VALUES('Osmeriformes','Actinopterygii',0,'2026-09-02 20:57:12');
CREATE TABLE clade_image_edges (
    name                       TEXT NOT NULL REFERENCES clades(name),
    img_id                     TEXT NOT NULL REFERENCES images(img_id),
    sessions_since_last_failed INTEGER NOT NULL DEFAULT 0,
    created                    TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (name, img_id)
) STRICT;
INSERT INTO clade_image_edges VALUES('Clupeidae','72f8cdf71da649cdb34c87c19087da4b',0,'2026-09-02 14:26:15');
INSERT INTO clade_image_edges VALUES('Clupea pallasii','a6074cdbec3b4dda9a39c68d95f1620b',0,'2026-09-02 14:29:06');
INSERT INTO clade_image_edges VALUES('Engraulidae','c798023b7c564139a440682df420e36c',0,'2026-09-02 20:53:09');
INSERT INTO clade_image_edges VALUES('Osmeridae','b836f5e213454c7fa559f9120f7b4d54',0,'2026-09-02 20:59:52');
CREATE TABLE clade_character_edges (
    name                       TEXT NOT NULL REFERENCES clades(name),
    char_id                    INTEGER NOT NULL REFERENCES characters(char_id),
    sessions_since_last_failed INTEGER NOT NULL DEFAULT 0,
    created                    TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (name, char_id)
) STRICT;
INSERT INTO clade_character_edges VALUES('Clupeidae',1,0,'2026-09-02 14:22:17');
INSERT INTO clade_character_edges VALUES('Clupeidae',2,0,'2026-09-02 14:23:04');
INSERT INTO clade_character_edges VALUES('Clupea pallasii',3,0,'2026-09-02 14:28:16');
INSERT INTO clade_character_edges VALUES('Clupea pallasii',4,0,'2026-09-02 14:28:45');
INSERT INTO clade_character_edges VALUES('Clupea pallasii',5,0,'2026-09-02 14:28:59');
INSERT INTO clade_character_edges VALUES('Engraulidae',6,0,'2026-09-02 20:49:46');
INSERT INTO clade_character_edges VALUES('Engraulidae',7,0,'2026-09-02 20:50:09');
INSERT INTO clade_character_edges VALUES('Osmeridae',8,0,'2026-09-02 20:57:12');
CREATE TABLE image_src_edges (
    img_id                     TEXT NOT NULL REFERENCES images(img_id),
    src                        INTEGER NOT NULL REFERENCES sources(src),
    sessions_since_last_failed INTEGER NOT NULL DEFAULT 0,
    created                    TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (img_id, src)
) STRICT;
INSERT INTO image_src_edges VALUES('72f8cdf71da649cdb34c87c19087da4b',1,0,'2026-09-02 14:26:15');
INSERT INTO image_src_edges VALUES('a6074cdbec3b4dda9a39c68d95f1620b',1,0,'2026-09-02 14:29:06');
INSERT INTO image_src_edges VALUES('c798023b7c564139a440682df420e36c',1,0,'2026-09-02 20:53:09');
INSERT INTO image_src_edges VALUES('b836f5e213454c7fa559f9120f7b4d54',1,0,'2026-09-02 20:59:52');
CREATE TABLE character_src_edges (
    char_id                    INTEGER NOT NULL REFERENCES characters(char_id),
    src                        INTEGER NOT NULL REFERENCES sources(src),
    sessions_since_last_failed INTEGER NOT NULL DEFAULT 0,
    created                    TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (char_id, src)
) STRICT;
INSERT INTO character_src_edges VALUES(1,1,0,'2026-09-02 14:22:17');
INSERT INTO character_src_edges VALUES(2,1,0,'2026-09-02 14:23:04');
INSERT INTO character_src_edges VALUES(3,1,0,'2026-09-02 14:28:16');
INSERT INTO character_src_edges VALUES(4,1,0,'2026-09-02 14:28:45');
INSERT INTO character_src_edges VALUES(5,1,0,'2026-09-02 14:28:59');
INSERT INTO character_src_edges VALUES(6,1,0,'2026-09-02 20:49:46');
INSERT INTO character_src_edges VALUES(7,1,0,'2026-09-02 20:50:09');
INSERT INTO character_src_edges VALUES(8,1,0,'2026-09-02 20:57:12');
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
CREATE UNIQUE INDEX clade_parent_edges_one_parent ON clade_parent_edges(name);
CREATE INDEX clade_parent_edges_by_parent ON clade_parent_edges(parent);
CREATE INDEX clade_image_edges_by_img ON clade_image_edges(img_id);
CREATE UNIQUE INDEX clade_character_edges_one_clade ON clade_character_edges(char_id);
CREATE UNIQUE INDEX image_src_edges_one_src ON image_src_edges(img_id);
CREATE UNIQUE INDEX character_src_edges_one_src ON character_src_edges(char_id);
CREATE INDEX kin_boards_by_set ON kin_boards(set_id);
CREATE INDEX kin_set_anchors_undealt ON kin_set_anchors(set_id, level, board_id);
CREATE INDEX kin_set_anchors_by_board ON kin_set_anchors(board_id);
COMMIT;
