"""Load the attribute dictionary and demo data from backend/data/*.yaml into PostgreSQL.

    python -m app.seed               # sync using backend/data
    python -m app.seed --data-dir X  # sync from another directory

The YAML files are the source of truth: rows are matched by their stable ``key`` and
created, updated or deleted so the database mirrors the files. Running the seed any
number of times yields the same result.
"""

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.config import BACKEND_DIR
from app.models import (
    CHARACTER_ROLES,
    DOMAINS,
    GENDERS,
    NAME_LANGUAGES,
    WORK_TYPES,
    Attribute,
    AttributeCategory,
    AttributeGroup,
    Character,
    CharacterAttribute,
    CharacterName,
    CharacterWork,
    Work,
)

DEFAULT_DATA_DIR = BACKEND_DIR / "data"
KEY_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
BIRTHDAY_PATTERN = re.compile(r"^(\d{2})-(\d{2})$")


class SeedError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("Seed data is invalid:\n  - " + "\n  - ".join(errors))


@dataclass
class SeedData:
    categories: list[dict[str, Any]]
    works: list[dict[str, Any]]
    characters: list[dict[str, Any]]


@dataclass
class SeedStats:
    counts: dict[str, int] = field(default_factory=dict)
    deleted: dict[str, int] = field(default_factory=dict)

    def __str__(self) -> str:
        parts = [f"{name}: {count}" for name, count in self.counts.items()]
        removed = [f"{name}: {count}" for name, count in self.deleted.items() if count]
        text = "Seed complete - " + ", ".join(parts)
        if removed:
            text += " (removed " + ", ".join(removed) + ")"
        return text


def load_data(data_dir: Path = DEFAULT_DATA_DIR) -> SeedData:
    def read(name: str, root_key: str) -> list[dict[str, Any]]:
        with open(data_dir / name, encoding="utf-8") as f:
            return (yaml.safe_load(f) or {}).get(root_key) or []

    return SeedData(
        categories=read("attributes.yaml", "categories"),
        works=read("works.yaml", "works"),
        characters=read("characters.yaml", "characters"),
    )


# ── validation ──────────────────────────────────────────────────────────────


def validate(data: SeedData) -> None:
    errors: list[str] = []

    def check_key(kind: str, key: Any, seen: set[str]) -> None:
        if not isinstance(key, str) or not KEY_PATTERN.match(key):
            errors.append(f"{kind} key {key!r} must be lowercase kebab-case")
        elif key in seen:
            errors.append(f"duplicate {kind} key {key!r}")
        else:
            seen.add(key)

    category_keys: set[str] = set()
    group_keys: set[str] = set()
    attribute_keys: set[str] = set()
    parents: list[tuple[str, str]] = []
    for category in data.categories:
        check_key("category", category.get("key"), category_keys)
        if category.get("domain") not in DOMAINS:
            errors.append(f"category {category.get('key')!r}: domain must be one of {DOMAINS}")
        if not category.get("zh"):
            errors.append(f"category {category.get('key')!r}: missing zh name")
        for group in category.get("groups") or []:
            check_key("group", group.get("key"), group_keys)
            if not group.get("zh"):
                errors.append(f"group {group.get('key')!r}: missing zh name")
            for attribute in group.get("attributes") or []:
                check_key("attribute", attribute.get("key"), attribute_keys)
                if not attribute.get("zh"):
                    errors.append(f"attribute {attribute.get('key')!r}: missing zh name")
                if attribute.get("parent"):
                    parents.append((attribute["key"], attribute["parent"]))
    for key, parent in parents:
        if parent not in attribute_keys:
            errors.append(f"attribute {key!r}: unknown parent {parent!r}")
        elif parent == key:
            errors.append(f"attribute {key!r} cannot be its own parent")

    work_keys: set[str] = set()
    for work in data.works:
        check_key("work", work.get("key"), work_keys)
        if not work.get("title"):
            errors.append(f"work {work.get('key')!r}: missing title")
        if work.get("work_type") not in WORK_TYPES:
            errors.append(f"work {work.get('key')!r}: work_type must be one of {WORK_TYPES}")

    character_keys: set[str] = set()
    for character in data.characters:
        key = character.get("key")
        check_key("character", key, character_keys)
        if not character.get("name"):
            errors.append(f"character {key!r}: missing name")
        if character.get("gender", "unknown") not in GENDERS:
            errors.append(f"character {key!r}: gender must be one of {GENDERS}")
        birthday = character.get("birthday")
        if birthday is not None:
            match = BIRTHDAY_PATTERN.match(str(birthday))
            if not match or not (1 <= int(match[1]) <= 12 and 1 <= int(match[2]) <= 31):
                errors.append(f"character {key!r}: birthday must be MM-DD, got {birthday!r}")
        for language in (character.get("names") or {}).keys():
            if language not in NAME_LANGUAGES:
                errors.append(f"character {key!r}: unknown name language {language!r}")
        for alias in character.get("aliases") or []:
            if alias.get("language") not in NAME_LANGUAGES or not alias.get("name"):
                errors.append(f"character {key!r}: invalid alias {alias!r}")
        for link in character.get("works") or []:
            if link.get("work") not in work_keys:
                errors.append(f"character {key!r}: unknown work {link.get('work')!r}")
            if link.get("role", "main") not in CHARACTER_ROLES:
                errors.append(f"character {key!r}: role must be one of {CHARACTER_ROLES}")
        attrs = character.get("attributes") or []
        for attribute_key in attrs:
            if attribute_key not in attribute_keys:
                errors.append(f"character {key!r}: unknown attribute {attribute_key!r}")
        duplicates = {a for a in attrs if attrs.count(a) > 1}
        if duplicates:
            errors.append(f"character {key!r}: duplicate attributes {sorted(duplicates)}")

    if errors:
        raise SeedError(errors)


# ── sync ────────────────────────────────────────────────────────────────────


def _by_key(session: Session, model: type) -> dict[str, Any]:
    return {row.key: row for row in session.scalars(select(model))}


def sync_dictionary(session: Session, categories: list[dict[str, Any]], stats: SeedStats) -> None:
    existing_categories = _by_key(session, AttributeCategory)
    existing_groups = _by_key(session, AttributeGroup)
    existing_attributes = _by_key(session, Attribute)
    attributes_by_key: dict[str, Attribute] = {}
    parent_of: dict[str, str | None] = {}

    for c_index, c_data in enumerate(categories):
        category = existing_categories.get(c_data["key"]) or AttributeCategory(key=c_data["key"])
        category.domain = c_data["domain"]
        category.name_zh = c_data["zh"]
        category.name_ja = c_data.get("ja")
        category.name_en = c_data.get("en")
        category.sort_order = c_index
        session.add(category)

        for g_index, g_data in enumerate(c_data.get("groups") or []):
            group = existing_groups.get(g_data["key"]) or AttributeGroup(key=g_data["key"])
            group.category = category
            group.name_zh = g_data["zh"]
            group.name_ja = g_data.get("ja")
            group.name_en = g_data.get("en")
            group.featured = bool(g_data.get("featured", False))
            group.sort_order = g_index
            session.add(group)

            for a_index, a_data in enumerate(g_data.get("attributes") or []):
                attribute = existing_attributes.get(a_data["key"]) or Attribute(key=a_data["key"])
                attribute.group = group
                attribute.name_zh = a_data["zh"]
                attribute.name_ja = a_data.get("ja")
                attribute.name_en = a_data.get("en")
                attribute.description = a_data.get("description")
                attribute.swatch = a_data.get("swatch")
                attribute.sort_order = a_index
                session.add(attribute)
                attributes_by_key[attribute.key] = attribute
                parent_of[attribute.key] = a_data.get("parent")

    for key, parent_key in parent_of.items():
        attributes_by_key[key].parent = attributes_by_key[parent_key] if parent_key else None
    session.flush()

    category_keys = [c["key"] for c in categories]
    group_keys = [g["key"] for c in categories for g in c.get("groups") or []]
    stats.deleted["attributes"] = _prune(session, Attribute, list(attributes_by_key))
    stats.deleted["attribute_groups"] = _prune(session, AttributeGroup, group_keys)
    stats.deleted["attribute_categories"] = _prune(session, AttributeCategory, category_keys)
    stats.counts["attribute_categories"] = len(category_keys)
    stats.counts["attribute_groups"] = len(group_keys)
    stats.counts["attributes"] = len(attributes_by_key)


def sync_works(session: Session, works: list[dict[str, Any]], stats: SeedStats) -> None:
    existing = _by_key(session, Work)
    for w_data in works:
        work = existing.get(w_data["key"]) or Work(key=w_data["key"])
        work.title = w_data["title"]
        work.title_original = w_data.get("title_original")
        work.title_en = w_data.get("title_en")
        work.work_type = w_data["work_type"]
        work.release_year = w_data.get("release_year")
        work.summary = w_data.get("summary")
        work.image_url = w_data.get("image_url")
        session.add(work)
    session.flush()
    stats.deleted["works"] = _prune(session, Work, [w["key"] for w in works])
    stats.counts["works"] = len(works)


def _desired_names(c_data: dict[str, Any]) -> dict[tuple[str, str], str]:
    """(language, name) → name_type. The primary name is always indexed as a zh name."""
    names: dict[tuple[str, str], str] = {("zh", c_data["name"]): "name"}
    for language, name in (c_data.get("names") or {}).items():
        if name:
            names.setdefault((language, str(name)), "name")
    for alias in c_data.get("aliases") or []:
        names.setdefault((alias["language"], str(alias["name"])), "alias")
    return names


def sync_characters(session: Session, characters: list[dict[str, Any]], stats: SeedStats) -> None:
    works = {w.key: w for w in session.scalars(select(Work))}
    attributes = {a.key: a for a in session.scalars(select(Attribute))}
    existing = {
        c.key: c
        for c in session.scalars(
            select(Character).options(
                selectinload(Character.names),
                selectinload(Character.work_links),
                selectinload(Character.attribute_links),
            )
        )
    }

    for c_data in characters:
        character = existing.get(c_data["key"])
        if character is None:
            character = Character(key=c_data["key"])
            session.add(character)
        character.name = c_data["name"]
        character.gender = c_data.get("gender", "unknown")
        birthday = c_data.get("birthday")
        if birthday:
            month, day = BIRTHDAY_PATTERN.match(str(birthday)).groups()  # type: ignore[union-attr]
            character.birth_month, character.birth_day = int(month), int(day)
        else:
            character.birth_month = character.birth_day = None
        character.age = str(c_data["age"]) if c_data.get("age") is not None else None
        character.height_cm = c_data.get("height_cm")
        character.blood_type = c_data.get("blood_type")
        character.summary = c_data.get("summary")
        character.image_url = c_data.get("image_url")

        # Diff child rows instead of replacing them, so unchanged rows are kept as-is and
        # unique constraints never see a delete + re-insert of the same entry.
        desired_names = _desired_names(c_data)
        current_names = {(n.language, n.name): n for n in character.names}
        for entry_key, name_row in current_names.items():
            if entry_key not in desired_names:
                character.names.remove(name_row)
            else:
                name_row.name_type = desired_names[entry_key]
        for (language, name), name_type in desired_names.items():
            if (language, name) not in current_names:
                character.names.append(
                    CharacterName(name=name, language=language, name_type=name_type)
                )

        desired_works = {
            works[link["work"]].id: (link.get("role", "main"), index)
            for index, link in enumerate(c_data.get("works") or [])
        }
        for link in list(character.work_links):
            if link.work_id not in desired_works:
                character.work_links.remove(link)
            else:
                link.role, link.sort_order = desired_works[link.work_id]
        current_work_ids = {link.work_id for link in character.work_links}
        for work_id, (role, index) in desired_works.items():
            if work_id not in current_work_ids:
                character.work_links.append(
                    CharacterWork(work_id=work_id, role=role, sort_order=index)
                )

        desired_attributes = {attributes[k].id for k in c_data.get("attributes") or []}
        for link in list(character.attribute_links):
            if link.attribute_id not in desired_attributes:
                character.attribute_links.remove(link)
        current_attribute_ids = {link.attribute_id for link in character.attribute_links}
        for attribute_id in desired_attributes - current_attribute_ids:
            character.attribute_links.append(CharacterAttribute(attribute_id=attribute_id))

    session.flush()
    stats.deleted["characters"] = _prune(session, Character, [c["key"] for c in characters])
    stats.counts["characters"] = len(characters)


def _prune(session: Session, model: type, keep_keys: list[str]) -> int:
    result = session.execute(delete(model).where(model.key.not_in(keep_keys)))
    return result.rowcount or 0


def run_seed(session: Session, data: SeedData) -> SeedStats:
    validate(data)
    stats = SeedStats()
    sync_dictionary(session, data.categories, stats)
    sync_works(session, data.works, stats)
    sync_characters(session, data.characters, stats)
    session.commit()
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    args = parser.parse_args(argv)
    # Error messages may contain CJK text; never crash on a legacy console code page.
    sys.stdout.reconfigure(errors="backslashreplace")  # type: ignore[union-attr]
    sys.stderr.reconfigure(errors="backslashreplace")  # type: ignore[union-attr]

    from app.db import SessionLocal

    try:
        data = load_data(args.data_dir)
        with SessionLocal() as session:
            print(run_seed(session, data))
    except SeedError as exc:
        print(exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
