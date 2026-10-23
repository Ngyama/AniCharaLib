import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.usefixtures("mini")


def character_id(client: TestClient, key: str) -> int:
    items = client.get("/api/characters", params={"page_size": 100}).json()["items"]
    return next(i["id"] for i in items if i["key"] == key)


def work_id(client: TestClient, key: str) -> int:
    items = client.get("/api/works").json()["items"]
    return next(w["id"] for w in items if w["key"] == key)


def test_attribute_dictionary_structure(client: TestClient):
    body = client.get("/api/attributes").json()
    assert body["total_attributes"] == 10
    assert [c["key"] for c in body["categories"]] == ["hair", "personality", "other"]
    hair = body["categories"][0]
    assert hair["domain"] == "appearance"
    assert [g["key"] for g in hair["groups"]] == ["hair-color", "hairstyle"]
    colors = {a["key"]: a for a in hair["groups"][0]["attributes"]}
    assert list(colors) == ["pink-hair", "red-hair", "black-hair", "blue-hair"]  # file order
    assert colors["pink-hair"]["character_count"] == 3
    assert colors["blue-hair"]["character_count"] == 0
    assert colors["pink-hair"]["swatch"] == "#eda3bf"


def test_character_detail(client: TestClient):
    body = client.get(f"/api/characters/{character_id(client, 'alpha')}").json()
    assert body["name"] == "阿尔法"
    assert body["alt_name"] == "アルファ"
    assert (body["birth_month"], body["birth_day"]) == (4, 3)
    assert body["palette"] == ["#eda3bf"]

    names = {(n["language"], n["name"], n["name_type"]) for n in body["names"]}
    assert names == {
        ("zh", "阿尔法", "name"),
        ("ja", "アルファ", "name"),
        ("en", "Alpha Example", "name"),
        ("romaji", "Aruufa", "name"),
        ("zh", "小A", "alias"),
        ("ja", "あーちゃん", "alias"),
    }

    sections = body["attribute_sections"]
    assert [(s["key"], s["domain"]) for s in sections] == [
        ("hair", "appearance"),
        ("personality", "personality"),
        ("other", "other"),
    ]
    # Only groups the character actually has attributes in.
    assert [g["key"] for g in sections[0]["groups"]] == ["hair-color", "hairstyle"]
    assert [a["key"] for a in sections[1]["groups"][0]["attributes"]] == ["weak-willed"]


def test_character_without_attributes_has_no_sections(client: TestClient):
    body = client.get(f"/api/characters/{character_id(client, 'zeta')}").json()
    assert body["attribute_sections"] == []
    assert body["palette"] == []


def test_character_in_multiple_works(client: TestClient):
    body = client.get(f"/api/characters/{character_id(client, 'alpha')}").json()
    assert [(w["key"], w["role"]) for w in body["works"]] == [
        ("work-one", "main"),
        ("work-two", "cameo"),
    ]
    for key in ("work-one", "work-two"):
        work = client.get(f"/api/works/{work_id(client, key)}").json()
        assert "alpha" in [c["key"] for c in work["characters"]]


def test_work_detail_lists_characters_by_role(client: TestClient):
    body = client.get(f"/api/works/{work_id(client, 'work-two')}").json()
    assert body["title"] == "作品二"
    assert body["character_count"] == 4
    roles = [(c["key"], c["role"]) for c in body["characters"]]
    assert roles == [("delta", "main"), ("echo", "main"), ("zeta", "minor"), ("alpha", "cameo")]


def test_work_list_and_filters(client: TestClient):
    body = client.get("/api/works").json()
    assert body["total"] == 2
    counts = {w["key"]: w["character_count"] for w in body["items"]}
    assert counts == {"work-one": 3, "work-two": 4}
    assert [w["key"] for w in client.get("/api/works", params={"q": "work one"}).json()["items"]] == [
        "work-one"
    ]
    assert client.get("/api/works", params={"work_type": "manga"}).json()["total"] == 1
    assert client.get("/api/works", params={"work_type": "podcast"}).status_code == 422


def test_not_found(client: TestClient):
    assert client.get("/api/characters/999999").status_code == 404
    assert client.get("/api/works/999999").status_code == 404
