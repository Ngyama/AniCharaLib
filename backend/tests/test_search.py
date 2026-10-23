import pytest
from fastapi.testclient import TestClient


def keys(client: TestClient, **params) -> list[str]:
    response = client.get("/api/characters", params=params)
    assert response.status_code == 200, response.text
    return sorted(item["key"] for item in response.json()["items"])


pytestmark = pytest.mark.usefixtures("mini")


def test_no_filters_returns_everyone(client: TestClient):
    body = client.get("/api/characters").json()
    assert body["total"] == 6
    assert body["unknown_attributes"] == []


def test_same_group_is_or(client: TestClient):
    # pink OR red hair
    assert keys(client, attrs="pink-hair,red-hair") == ["alpha", "bravo", "charlie", "delta"]


def test_different_groups_are_and(client: TestClient):
    assert keys(client, attrs="pink-hair,twin-tails") == ["alpha", "charlie"]


def test_multi_category_combination(client: TestClient):
    # (粉发 OR 红发) AND 双马尾 AND 弱气
    assert keys(client, attrs="pink-hair,red-hair,twin-tails,weak-willed") == ["alpha", "bravo"]


def test_same_group_or_inside_personality(client: TestClient):
    # gentle OR weak-willed, both in personality-traits
    assert keys(client, attrs="gentle,weak-willed") == ["alpha", "bravo", "delta", "echo"]


def test_repeated_and_comma_separated_params_are_equivalent(client: TestClient):
    repeated = client.get(
        "/api/characters", params=[("attrs", "pink-hair"), ("attrs", "twin-tails")]
    ).json()
    comma = client.get("/api/characters", params={"attrs": "pink-hair, twin-tails"}).json()
    assert repeated["total"] == comma["total"] == 2


def test_name_and_attributes_combined(client: TestClient):
    assert keys(client, q="阿尔法", attrs="twin-tails") == ["alpha"]
    assert keys(client, q="阿尔法", attrs="ponytail") == []
    assert keys(client, q="Bravo", attrs="red-hair,twin-tails") == ["bravo"]


def test_name_search_covers_all_languages_and_aliases(client: TestClient):
    assert keys(client, q="アルファ") == ["alpha"]  # Japanese name
    assert keys(client, q="alpha example") == ["alpha"]  # English, case-insensitive
    assert keys(client, q="aruu") == ["alpha"]  # romaji substring
    assert keys(client, q="小A") == ["alpha"]  # Chinese alias
    assert keys(client, q="あーちゃん") == ["alpha"]  # Japanese alias
    assert keys(client, q="法") == ["alpha"]  # single CJK character
    assert keys(client, q="尔") == ["alpha", "delta"]  # 阿尔法 and 德尔塔


def test_like_wildcards_are_literal(client: TestClient):
    assert keys(client, q="%") == ["zeta"]  # only "Zeta 100%" contains a literal %
    assert keys(client, q="_") == []


def test_no_results(client: TestClient):
    body = client.get(
        "/api/characters", params={"attrs": "black-hair,ponytail"}
    ).json()
    assert body["total"] == 0
    assert body["items"] == []
    assert body["pages"] == 0
    assert keys(client, q="不存在的名字") == []


def test_untagged_attribute_matches_nobody(client: TestClient):
    # blue-hair exists in the dictionary, but no character is tagged with it.
    body = client.get("/api/characters", params={"attrs": "blue-hair"}).json()
    assert body["total"] == 0
    assert body["unknown_attributes"] == []


def test_unknown_attribute_is_reported_and_matches_nobody(client: TestClient):
    body = client.get("/api/characters", params={"attrs": "pink-hair,no-such-tag"}).json()
    assert body["total"] == 0
    assert body["unknown_attributes"] == ["no-such-tag"]


def test_missing_attribute_is_not_a_match(client: TestClient):
    # zeta has no attributes at all; it must not appear in any attribute search.
    for attr in ("pink-hair", "twin-tails", "weak-willed", "student"):
        assert "zeta" not in keys(client, attrs=attr)


def test_gender_and_work_filters(client: TestClient):
    assert keys(client, gender="male") == ["echo"]
    work_two = client.get("/api/works", params={"q": "作品二"}).json()["items"][0]["id"]
    assert keys(client, work_id=work_two, attrs="weak-willed") == ["alpha", "delta", "echo"]


def test_pagination(client: TestClient):
    pages = [
        client.get("/api/characters", params={"page": p, "page_size": 4, "sort": "name"}).json()
        for p in (1, 2, 3)
    ]
    assert [p["total"] for p in pages] == [6, 6, 6]
    assert [p["pages"] for p in pages] == [2, 2, 2]
    assert [len(p["items"]) for p in pages] == [4, 2, 0]
    seen = [i["key"] for p in pages for i in p["items"]]
    assert len(seen) == len(set(seen)) == 6


def test_pagination_validation(client: TestClient):
    assert client.get("/api/characters", params={"page": 0}).status_code == 422
    assert client.get("/api/characters", params={"page_size": 101}).status_code == 422


def test_sorting(client: TestClient):
    def order(sort: str) -> list[str]:
        items = client.get("/api/characters", params={"sort": sort}).json()["items"]
        return [i["key"] for i in items]

    assert order("relevance") == ["alpha", "bravo", "charlie", "delta", "echo", "zeta"]
    assert order("newest")[0] == "zeta"
    assert order("most_tagged")[:2] == ["alpha", "echo"]
    assert client.get("/api/characters", params={"sort": "bogus"}).status_code == 422


def test_matched_tags_come_first_on_cards(client: TestClient):
    item = client.get("/api/characters", params={"attrs": "weak-willed", "q": "布拉沃"}).json()[
        "items"
    ][0]
    assert item["tags"][0] == {"key": "weak-willed", "name": "弱气", "swatch": None, "matched": True}
    assert [t["key"] for t in item["tags"][1:]] == ["red-hair", "twin-tails"]


def test_empty_database(client: TestClient, db):
    from sqlalchemy import text

    db.execute(text("TRUNCATE characters CASCADE"))
    db.commit()
    body = client.get("/api/characters", params={"attrs": "pink-hair"}).json()
    assert body == {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 24,
        "pages": 0,
        "unknown_attributes": [],
    }
