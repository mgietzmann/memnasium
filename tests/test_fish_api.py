"""Entry and lookup over HTTP — design/api/Fish.md, against a real temporary database."""

import io
import json
import sqlite3
from pathlib import Path

import httpx2
import pytest
from fastapi.testclient import TestClient
from PIL import Image


def png(size: tuple[int, int] = (40, 30)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, (10, 120, 200)).save(buffer, format="PNG")
    return buffer.getvalue()


def post_character(client: TestClient, **body: object) -> httpx2.Response:
    return client.post("/api/fish/characters", json=body)


def post_image(
    client: TestClient, body: dict[str, object], data: bytes | None = None
) -> httpx2.Response:
    return client.post(
        "/api/fish/images",
        data={"json": json.dumps(body)},
        files={"image": ("x.png", data if data is not None else png(), "image/png")},
    )


# ───────────────────────────────────────────────────────────────────── the walk


def test_a_known_clade_comes_back_with_its_ancestors_narrowest_first(
    client: TestClient, taxonomy: sqlite3.Connection
) -> None:  # api/Fish.md
    body = client.get("/api/fish/clades/Artificialus%20claudus").json()
    assert body["common_name"] == "spotted claudfish"
    assert [a["name"] for a in body["ancestors"]] == [
        "Artificialus",
        "Artificialidae",
        "Perciformes",
    ]


def test_an_unknown_clade_is_a_404_which_is_the_walks_signal(
    client: TestClient, taxonomy: sqlite3.Connection
) -> None:  # api/Fish.md
    assert client.get("/api/fish/clades/Nothingus").status_code == 404


def test_a_skipped_level_still_walks_to_the_root(
    client: TestClient, taxonomy: sqlite3.Connection
) -> None:  # data/Fish.md — adjacency is not required
    body = client.get("/api/fish/clades/Artificialus%20borealis").json()
    assert [a["name"] for a in body["ancestors"]] == ["Artificialidae", "Perciformes"]


def test_search_matches_scientific_and_common_names(
    client: TestClient, taxonomy: sqlite3.Connection
) -> None:  # algorithms/Fish.md
    found = client.get("/api/fish/clades", params={"q": "claud"}).json()
    assert {row["name"] for row in found} == {"Artificialus claudus", "Artificialoides minor"}


def test_search_can_be_restricted_to_one_level(
    client: TestClient, taxonomy: sqlite3.Connection
) -> None:  # algorithms/Fish.md
    found = client.get("/api/fish/clades", params={"q": "artific", "level": "genus"}).json()
    assert {row["name"] for row in found} == {"Artificialus", "Artificialoides"}


def test_a_level_outside_the_enum_is_rejected(
    client: TestClient, taxonomy: sqlite3.Connection
) -> None:  # api/Fish.md — the error table
    assert client.get("/api/fish/clades", params={"q": "a", "level": "phylum"}).status_code == 400


def test_a_source_carries_the_label_a_chip_displays(
    client: TestClient, taxonomy: sqlite3.Connection
) -> None:  # algorithms/Fish.md
    found = client.get("/api/fish/sources", params={"q": "bro"}).json()
    assert found[0]["label"] == "Brown, 2014"


# ────────────────────────────────────────────────────────────── entering a character


def test_a_bare_reference_reuses_rather_than_creating(
    client: TestClient, taxonomy: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # api/Fish.md — the reference-or-object union
    before = db.execute("SELECT count(*) c FROM clades").fetchone()["c"]
    response = post_character(
        client, clade="Artificialus claudus", source=17, text="three dorsal spines"
    )
    assert response.status_code == 201
    assert db.execute("SELECT count(*) c FROM clades").fetchone()["c"] == before


def test_the_response_is_what_the_next_submission_should_send(
    client: TestClient, taxonomy: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # api/Fish.md — canonical references, so the sticky form stops creating
    body = post_character(
        client,
        clade={"name": "Artificialus novus", "level": "species", "parent": "Artificialus"},
        source={"author": "Nkemdirim", "year": 2023, "title": "New claudfishes"},
        text="four dorsal spines",
    ).json()
    assert body["clade"] == "Artificialus novus"
    again = post_character(client, clade=body["clade"], source=body["source"], text="pale flank")
    assert again.status_code == 201


def test_a_chain_writes_every_clade_and_every_parent_edge(
    client: TestClient, db: sqlite3.Connection
) -> None:  # api/Fish.md — new_ancestors + parent
    db.execute("INSERT INTO clades (name, level) VALUES ('Perciformes', 'order')")
    body = post_character(
        client,
        clade={
            "name": "Artificialus claudus",
            "common_name": "spotted claudfish",
            "level": "species",
            "new_ancestors": [
                {"name": "Artificialus", "level": "genus"},
                {"name": "Artificialidae", "level": "family"},
            ],
            "parent": "Perciformes",
        },
        source={"author": "Brown", "year": 2014, "title": "Spines"},
        text="three dorsal spines",
    ).json()
    assert body["clade"] == "Artificialus claudus"
    edges = dict(db.execute("SELECT name, parent FROM clade_parent_edges").fetchall())
    assert edges == {
        "Artificialus claudus": "Artificialus",
        "Artificialus": "Artificialidae",
        "Artificialidae": "Perciformes",
    }


def test_a_chain_with_no_parent_leaves_its_top_a_root(
    client: TestClient, db: sqlite3.Connection
) -> None:  # api/Fish.md — the clade chain table
    post_character(
        client,
        clade={
            "name": "Artificialus claudus",
            "level": "species",
            "new_ancestors": [{"name": "Artificialus", "level": "genus"}],
            "parent": None,
        },
        source={"author": "Brown", "year": 2014, "title": "Spines"},
        text="three dorsal spines",
    )
    assert (
        db.execute("SELECT 1 FROM clade_parent_edges WHERE name = 'Artificialus'").fetchone()
        is None
    )


def test_a_parent_must_sit_at_a_strictly_broader_level(
    client: TestClient, taxonomy: sqlite3.Connection
) -> None:  # data/Fish.md
    response = post_character(
        client,
        clade={"name": "Artificialus alter", "level": "genus", "parent": "Artificialus"},
        source=17,
        text="x",
    )
    assert response.status_code == 400


def test_a_chain_step_that_inverts_is_rejected(
    client: TestClient, taxonomy: sqlite3.Connection
) -> None:  # api/Fish.md — every step goes to a strictly broader level
    response = post_character(
        client,
        clade={
            "name": "Artificialus novus",
            "level": "species",
            "new_ancestors": [
                {"name": "Novidae", "level": "family"},
                {"name": "Novus", "level": "genus"},
            ],
            "parent": "Perciformes",
        },
        source=17,
        text="x",
    )
    assert response.status_code == 400


def test_a_parent_that_does_not_exist_means_the_client_stopped_walking_early(
    client: TestClient, taxonomy: sqlite3.Connection
) -> None:  # api/Fish.md — the error table
    response = post_character(
        client,
        clade={"name": "Artificialus novus", "level": "species", "parent": "Nothingidae"},
        source=17,
        text="x",
    )
    assert response.status_code == 400


def test_creating_a_clade_that_already_exists_conflicts(
    client: TestClient, taxonomy: sqlite3.Connection
) -> None:  # api/Fish.md — the error table
    response = post_character(
        client,
        clade={"name": "Artificialus opus", "level": "species", "parent": "Artificialus"},
        source=17,
        text="x",
    )
    assert response.status_code == 409


def test_a_submission_that_fails_leaves_no_orphan_clades(
    client: TestClient, taxonomy: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # api/Fish.md — one transactional POST per entry
    post_character(
        client,
        clade={
            "name": "Artificialus novus",
            "level": "species",
            "new_ancestors": [{"name": "Novidae", "level": "family"}],
            "parent": "Nothingidae",
        },
        source={"author": "Nobody", "year": 1999, "title": "-"},
        text="x",
    )
    assert db.execute("SELECT 1 FROM clades WHERE name = 'Novidae'").fetchone() is None
    assert db.execute("SELECT 1 FROM sources WHERE author = 'Nobody'").fetchone() is None


def test_a_character_writes_both_of_its_edges_at_zero(
    client: TestClient, taxonomy: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # app/Fish.md — what a submission writes
    char_id = post_character(
        client, clade="Artificialus opus", source=17, text="three dorsal spines"
    ).json()["char_id"]
    clade_edge = db.execute(
        "SELECT * FROM clade_character_edges WHERE char_id = ?", (char_id,)
    ).fetchone()
    src_edge = db.execute(
        "SELECT * FROM character_src_edges WHERE char_id = ?", (char_id,)
    ).fetchone()
    assert clade_edge["name"] == "Artificialus opus"
    assert src_edge["src"] == 17
    assert clade_edge["sessions_since_last_failed"] == 0
    assert src_edge["sessions_since_last_failed"] == 0


def test_the_same_character_twice_makes_two_of_them(
    client: TestClient, taxonomy: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # app/Fish.md — known limit: no duplicate detection
    post_character(client, clade="Artificialus opus", source=17, text="three dorsal spines")
    post_character(client, clade="Artificialus opus", source=17, text="three dorsal spines")
    assert db.execute("SELECT count(*) c FROM characters").fetchone()["c"] == 2


# ───────────────────────────────────────────────────────────────── entering an image


def test_an_upload_is_stored_as_webp_whatever_was_pasted(
    client: TestClient, taxonomy: sqlite3.Connection, images_dir: Path
) -> None:  # Stack.md — normalise uploads rather than reject them
    body = post_image(client, {"clade": "Artificialus opus", "source": 17}).json()
    stored = images_dir / f"{body['img_id']}.webp"
    assert stored.is_file()
    with Image.open(stored) as image:
        assert image.format == "WEBP"


def test_an_upload_is_scaled_so_its_longest_side_fits(
    client: TestClient, taxonomy: sqlite3.Connection, images_dir: Path
) -> None:  # Stack.md — longest side ≤ 1600px
    body = post_image(client, {"clade": "Artificialus opus", "source": 17}, png((3000, 1500)))
    with Image.open(images_dir / f"{body.json()['img_id']}.webp") as image:
        assert max(image.size) == 1600


def test_an_undecodable_upload_is_rejected(
    client: TestClient, taxonomy: sqlite3.Connection
) -> None:  # api/Fish.md — the error table
    assert (
        post_image(
            client, {"clade": "Artificialus opus", "source": 17}, b"not an image"
        ).status_code
        == 400
    )


def test_an_image_writes_both_of_its_edges(
    client: TestClient, taxonomy: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # app/Fish.md — what a submission writes
    img_id = post_image(client, {"clade": "Artificialus opus", "source": 17}).json()["img_id"]
    assert (
        db.execute("SELECT name FROM clade_image_edges WHERE img_id = ?", (img_id,)).fetchone()[
            "name"
        ]
        == "Artificialus opus"
    )
    assert (
        db.execute("SELECT src FROM image_src_edges WHERE img_id = ?", (img_id,)).fetchone()["src"]
        == 17
    )


def test_a_stored_image_is_served_as_webp(
    client: TestClient, taxonomy: sqlite3.Connection
) -> None:  # api/Fish.md — serving an image
    img_id = post_image(client, {"clade": "Artificialus opus", "source": 17}).json()["img_id"]
    response = client.get(f"/api/fish/images/{img_id}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/webp"


def test_an_unknown_image_is_a_404(
    client: TestClient, taxonomy: sqlite3.Connection
) -> None:  # api/Fish.md — the error table
    assert client.get("/api/fish/images/nope").status_code == 404


def test_an_image_is_shareable_across_clades(
    client: TestClient, taxonomy: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # data/Fish.md — images are nodes, reusable across clades
    img_id = post_image(client, {"clade": "Artificialus opus", "source": 17}).json()["img_id"]
    db.execute("INSERT INTO clade_image_edges (name, img_id) VALUES ('Artificialus', ?)", (img_id,))
    assert (
        db.execute(
            "SELECT count(*) c FROM clade_image_edges WHERE img_id = ?", (img_id,)
        ).fetchone()["c"]
        == 2
    )


def test_a_character_belongs_to_exactly_one_clade(
    client: TestClient, taxonomy: sqlite3.Connection, db: sqlite3.Connection
) -> None:  # data/Fish.md — characters are never shared
    char_id = post_character(client, clade="Artificialus opus", source=17, text="x").json()[
        "char_id"
    ]
    with pytest.raises(sqlite3.IntegrityError):
        db.execute(
            "INSERT INTO clade_character_edges (name, char_id) VALUES ('Artificialus', ?)",
            (char_id,),
        )
