from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.models import (
    Attribute,
    AttributeCategory,
    AttributeGroup,
    Character,
    CharacterAttribute,
    CharacterName,
    CharacterWork,
    Work,
)
from app.seed import SeedData, SeedError, SeedStats, load_data, run_seed
from tests.conftest import mini_data

TABLES = (
    AttributeCategory,
    AttributeGroup,
    Attribute,
    Work,
    Character,
    CharacterName,
    CharacterWork,
    CharacterAttribute,
)


def table_counts(db: Session) -> dict[str, int]:
    return {m.__tablename__: db.scalar(select(func.count()).select_from(m)) for m in TABLES}


def test_demo_seed_is_idempotent(db: Session, client: TestClient):
    data = load_data()
    run_seed(db, data)
    first = table_counts(db)
    ids_first = dict(db.execute(select(Character.key, Character.id)).all())

    run_seed(db, data)
    run_seed(db, data)
    assert table_counts(db) == first
    # Rows are updated in place, not recreated.
    assert dict(db.execute(select(Character.key, Character.id)).all()) == ids_first

    assert first["characters"] == len(data.characters)
    assert 20 <= first["characters"] <= 30
    assert first["attribute_categories"] == 11
    # Search still works on the re-seeded demo data.
    body = client.get(
        "/api/characters", params={"attrs": "pink-hair,red-hair,twin-tails,weak-willed"}
    ).json()
    assert sorted(i["key"] for i in body["items"]) == ["haruno-sakurano", "himura-akane"]


def test_demo_data_has_required_variety(db: Session):
    data = load_data()
    run_seed(db, data)
    genders = set(db.scalars(select(Character.gender)))
    assert {"female", "male"} <= genders
    multi_work = db.scalar(
        select(func.count()).select_from(
            select(CharacterWork.character_id)
            .group_by(CharacterWork.character_id)
            .having(func.count() > 1)
            .subquery()
        )
    )
    assert multi_work >= 2
    shared_work = db.scalar(
        select(func.count()).select_from(
            select(CharacterWork.work_id)
            .group_by(CharacterWork.work_id)
            .having(func.count() > 1)
            .subquery()
        )
    )
    assert shared_work >= 3


def test_reseed_applies_changes_and_prunes(
    db: Session, seed: Callable[[SeedData | None], SeedStats]
):
    seed(None)
    alpha_id = db.scalar(select(Character.id).where(Character.key == "alpha"))

    data = mini_data()
    alpha = data.characters[0]
    alpha["name"] = "阿尔法改"
    alpha["attributes"] = ["red-hair", "twin-tails"]  # drop pink-hair / weak-willed / student
    alpha["aliases"] = [{"name": "小A", "language": "zh"}]  # drop the Japanese alias
    alpha["works"] = [{"work": "work-two", "role": "main"}]
    data.characters = [c for c in data.characters if c["key"] != "zeta"]
    # Remove an attribute from the dictionary entirely.
    data.categories[0]["groups"][0]["attributes"] = [
        a for a in data.categories[0]["groups"][0]["attributes"] if a["key"] != "blue-hair"
    ]
    stats = seed(data)
    assert stats.deleted["characters"] == 1
    assert stats.deleted["attributes"] == 1
    db.expire_all()

    alpha_row = db.get(Character, alpha_id)
    assert alpha_row is not None and alpha_row.name == "阿尔法改"
    assert sorted(link.attribute.key for link in alpha_row.attribute_links) == [
        "red-hair",
        "twin-tails",
    ]
    assert [(link.work.key, link.role) for link in alpha_row.work_links] == [("work-two", "main")]
    assert ("ja", "あーちゃん") not in {(n.language, n.name) for n in alpha_row.names}
    assert ("zh", "阿尔法改") in {(n.language, n.name) for n in alpha_row.names}
    assert db.scalar(select(Character).where(Character.key == "zeta")) is None
    assert db.scalar(select(Attribute).where(Attribute.key == "blue-hair")) is None

    # Seeding the same data again changes nothing.
    before = table_counts(db)
    seed(data)
    assert table_counts(db) == before


def test_dictionary_change_needs_no_schema_change(
    db: Session, client: TestClient, seed: Callable[[SeedData | None], SeedStats]
):
    data = mini_data()
    data.categories.append(
        {
            "key": "aura",
            "domain": "appearance",
            "zh": "气场",
            "groups": [
                {"key": "aura-color", "zh": "气场颜色", "attributes": [{"key": "gold-aura", "zh": "金色气场"}]}
            ],
        }
    )
    data.characters[1]["attributes"].append("gold-aura")
    seed(data)
    body = client.get("/api/attributes").json()
    assert body["categories"][-1]["key"] == "aura"
    assert [i["key"] for i in client.get("/api/characters", params={"attrs": "gold-aura"}).json()["items"]] == [
        "bravo"
    ]


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda d: d.characters[0]["attributes"].append("no-such-tag"), "unknown attribute"),
        (lambda d: d.characters[0]["works"].append({"work": "nope"}), "unknown work"),
        (lambda d: d.characters.append(dict(d.characters[0])), "duplicate character key"),
        (lambda d: d.characters[0].update(gender="robot"), "gender must be"),
        (lambda d: d.characters[0].update(birthday="13-01"), "birthday must be"),
        (lambda d: d.categories[0].update(domain="smell"), "domain must be"),
        (
            lambda d: d.categories[0]["groups"][0]["attributes"].append({"key": "pink-hair", "zh": "x"}),
            "duplicate attribute key",
        ),
        (
            lambda d: d.categories[0]["groups"][0]["attributes"][0].update(parent="ghost"),
            "unknown parent",
        ),
    ],
)
def test_seed_validation(db: Session, mutate, message: str):
    data = mini_data()
    mutate(data)
    with pytest.raises(SeedError) as info:
        run_seed(db, data)
    assert message in str(info.value)
    # Nothing was written.
    assert db.scalar(text("SELECT count(*) FROM characters")) == 0
