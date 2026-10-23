"""Deterministic character search, executed entirely in PostgreSQL.

Attribute rules:
  * attributes in the same group (二级分类) are OR-ed   — 粉发 OR 红发
  * different groups are AND-ed                        — (粉发 OR 红发) AND 双马尾 AND 弱气
  * only explicitly tagged characters match; a missing tag is never treated as a match
  * an unknown attribute key cannot be satisfied, so it yields an empty result

The name query matches the primary name and every name / alias in any language
(case-insensitive substring). Name and attribute conditions are combined with AND.
"""

from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy import Select, case, exists, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.models import (
    Attribute,
    AttributeGroup,
    Character,
    CharacterAttribute,
    CharacterName,
    CharacterWork,
)


@dataclass
class CharacterQuery:
    q: str | None = None
    attribute_keys: list[str] = field(default_factory=list)
    gender: str | None = None
    work_id: int | None = None
    sort: str = "relevance"
    page: int = 1
    page_size: int = 24


@dataclass
class CharacterResult:
    characters: list[Character]
    total: int
    matched_attribute_ids: set[int]
    unknown_attributes: list[str]


def normalize_keys(raw: list[str]) -> list[str]:
    """Accept both repeated parameters and comma separated values; drop blanks and duplicates."""
    keys: list[str] = []
    for value in raw:
        for part in value.split(","):
            part = part.strip()
            if part and part not in keys:
                keys.append(part)
    return keys


def like_pattern(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def search_characters(session: Session, query: CharacterQuery) -> CharacterResult:
    keys = normalize_keys(query.attribute_keys)
    rows = []
    if keys:
        rows = session.execute(
            select(Attribute.id, Attribute.key, Attribute.group_id).where(Attribute.key.in_(keys))
        ).all()
    found = {row.key for row in rows}
    unknown = [k for k in keys if k not in found]
    if unknown:
        return CharacterResult([], 0, set(), unknown)

    ids_by_group: dict[int, list[int]] = defaultdict(list)
    for row in rows:
        ids_by_group[row.group_id].append(row.id)

    stmt: Select = select(Character.id)
    for attribute_ids in ids_by_group.values():
        stmt = stmt.where(
            exists().where(
                CharacterAttribute.character_id == Character.id,
                CharacterAttribute.attribute_id.in_(attribute_ids),
            )
        )

    text = (query.q or "").strip()
    if text:
        pattern = like_pattern(text)
        stmt = stmt.where(
            or_(
                Character.name.ilike(pattern, escape="\\"),
                exists().where(
                    CharacterName.character_id == Character.id,
                    CharacterName.name.ilike(pattern, escape="\\"),
                ),
            )
        )
    if query.gender:
        stmt = stmt.where(Character.gender == query.gender)
    if query.work_id is not None:
        stmt = stmt.where(
            exists().where(
                CharacterWork.character_id == Character.id,
                CharacterWork.work_id == query.work_id,
            )
        )

    total = session.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    stmt = stmt.order_by(*_ordering(query.sort, text))
    stmt = stmt.limit(query.page_size).offset((query.page - 1) * query.page_size)
    page_ids = list(session.scalars(stmt))

    characters = load_characters(session, page_ids)
    matched = {i for ids in ids_by_group.values() for i in ids}
    return CharacterResult(characters, total, matched, [])


def _ordering(sort: str, text: str) -> list:
    if sort == "name":
        return [Character.name, Character.id]
    if sort == "newest":
        return [Character.created_at.desc(), Character.id.desc()]
    if sort == "most_tagged":
        tag_count = (
            select(func.count())
            .where(CharacterAttribute.character_id == Character.id)
            .scalar_subquery()
        )
        return [tag_count.desc(), Character.id]
    # relevance: with a name query, exact and prefix matches of the primary name come first.
    if text:
        lowered = text.lower()
        rank = case(
            (func.lower(Character.name) == lowered, 0),
            (func.lower(Character.name).startswith(lowered, autoescape=True), 1),
            else_=2,
        )
        return [rank, Character.id]
    return [Character.id]


def load_characters(session: Session, ids: list[int]) -> list[Character]:
    """Load characters with everything the list / detail views need, preserving ``ids`` order."""
    if not ids:
        return []
    loaded = session.scalars(
        select(Character)
        .where(Character.id.in_(ids))
        .options(
            selectinload(Character.names),
            selectinload(Character.work_links).selectinload(CharacterWork.work),
            selectinload(Character.attribute_links)
            .selectinload(CharacterAttribute.attribute)
            .selectinload(Attribute.group)
            .selectinload(AttributeGroup.category),
        )
    ).all()
    by_id = {c.id: c for c in loaded}
    return [by_id[i] for i in ids if i in by_id]
