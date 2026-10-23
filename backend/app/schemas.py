"""Pydantic response schemas — the API contract consumed by the frontend (see frontend/src/api/types.ts)."""

from typing import Literal

from pydantic import BaseModel

Gender = Literal["female", "male", "other", "unknown"]
Domain = Literal["appearance", "personality", "other"]
CharacterSort = Literal["relevance", "name", "newest", "most_tagged"]


# ── attribute dictionary ────────────────────────────────────────────────────


class AttributeOut(BaseModel):
    id: int
    key: str
    name: str
    name_ja: str | None
    name_en: str | None
    swatch: str | None
    parent_key: str | None
    character_count: int


class AttributeGroupOut(BaseModel):
    id: int
    key: str
    name: str
    name_ja: str | None
    name_en: str | None
    featured: bool
    attributes: list[AttributeOut]


class AttributeCategoryOut(BaseModel):
    id: int
    key: str
    domain: Domain
    name: str
    name_ja: str | None
    name_en: str | None
    groups: list[AttributeGroupOut]


class AttributeDictionary(BaseModel):
    categories: list[AttributeCategoryOut]
    total_attributes: int


# ── characters ──────────────────────────────────────────────────────────────


class AttributeTag(BaseModel):
    key: str
    name: str
    swatch: str | None = None
    # True when the tag is one of the attributes the current search filtered on.
    matched: bool = False


class WorkRef(BaseModel):
    id: int
    key: str
    title: str
    work_type: str
    role: str


class CharacterListItem(BaseModel):
    id: int
    key: str
    name: str
    alt_name: str | None
    gender: Gender
    image_url: str | None
    # Swatch colours of the character's attributes in dictionary order (hair, eyes, skin ...),
    # used by the frontend placeholder portrait.
    palette: list[str]
    works: list[WorkRef]
    tags: list[AttributeTag]


class CharacterPage(BaseModel):
    items: list[CharacterListItem]
    total: int
    page: int
    page_size: int
    pages: int
    # Requested attribute keys that do not exist in the dictionary. Strict search treats them
    # as unsatisfiable, so the result is empty whenever this list is non-empty.
    unknown_attributes: list[str] = []


class CharacterNameOut(BaseModel):
    name: str
    language: str
    name_type: str


class AttributeSectionGroup(BaseModel):
    key: str
    name: str
    attributes: list[AttributeTag]


class AttributeSection(BaseModel):
    key: str
    domain: Domain
    name: str
    groups: list[AttributeSectionGroup]


class CharacterDetail(BaseModel):
    id: int
    key: str
    name: str
    alt_name: str | None
    names: list[CharacterNameOut]
    gender: Gender
    birth_month: int | None
    birth_day: int | None
    age: str | None
    height_cm: int | None
    blood_type: str | None
    summary: str | None
    image_url: str | None
    palette: list[str]
    works: list[WorkRef]
    # Only categories / groups the character actually has attributes in.
    attribute_sections: list[AttributeSection]


# ── works ───────────────────────────────────────────────────────────────────


class WorkListItem(BaseModel):
    id: int
    key: str
    title: str
    title_original: str | None
    title_en: str | None
    work_type: str
    release_year: int | None
    summary: str | None
    image_url: str | None
    character_count: int


class WorkPage(BaseModel):
    items: list[WorkListItem]
    total: int
    page: int
    page_size: int
    pages: int


class WorkCharacter(CharacterListItem):
    role: str


class WorkDetail(WorkListItem):
    characters: list[WorkCharacter]
