"""Convert ORM objects into response schemas."""

from app.models import Attribute, Character, CharacterWork, Work
from app.schemas import (
    AttributeSection,
    AttributeSectionGroup,
    AttributeTag,
    CharacterDetail,
    CharacterListItem,
    CharacterNameOut,
    WorkListItem,
    WorkRef,
)

CARD_TAG_LIMIT = 4
PALETTE_LIMIT = 3
# Languages tried, in order, for the secondary name shown under the primary name.
ALT_NAME_LANGUAGES = ("ja", "en", "romaji")


def _dictionary_order(attribute: Attribute) -> tuple[int, int, int, int]:
    group = attribute.group
    return (group.category.sort_order, group.sort_order, attribute.sort_order, attribute.id)


def sorted_attributes(character: Character) -> list[Attribute]:
    return sorted((link.attribute for link in character.attribute_links), key=_dictionary_order)


def _tag(attribute: Attribute, matched: bool = False) -> AttributeTag:
    return AttributeTag(
        key=attribute.key, name=attribute.name_zh, swatch=attribute.swatch, matched=matched
    )


def alt_name(character: Character) -> str | None:
    for language in ALT_NAME_LANGUAGES:
        for entry in character.names:
            if entry.language == language and entry.name_type == "name" and entry.name != character.name:
                return entry.name
    return None


def work_ref(link: CharacterWork) -> WorkRef:
    return WorkRef(
        id=link.work.id,
        key=link.work.key,
        title=link.work.title,
        work_type=link.work.work_type,
        role=link.role,
    )


def palette(attributes: list[Attribute]) -> list[str]:
    return [a.swatch for a in attributes if a.swatch][:PALETTE_LIMIT]


def character_list_item(
    character: Character, matched_attribute_ids: set[int] | None = None
) -> CharacterListItem:
    attributes = sorted_attributes(character)
    matched_ids = matched_attribute_ids or set()
    # Attributes the user searched for come first, then the featured groups (hair colour,
    # hairstyle, eye colour, archetype ...), as configured in the dictionary.
    matched = [a for a in attributes if a.id in matched_ids]
    featured = [a for a in attributes if a.group.featured and a.id not in matched_ids]
    tags = [_tag(a, True) for a in matched] + [_tag(a) for a in featured]
    return CharacterListItem(
        id=character.id,
        key=character.key,
        name=character.name,
        alt_name=alt_name(character),
        gender=character.gender,  # type: ignore[arg-type]
        image_url=character.image_url,
        palette=palette(attributes),
        works=[work_ref(link) for link in character.work_links],
        tags=tags[: max(CARD_TAG_LIMIT, len(matched))],
    )


def character_detail(character: Character) -> CharacterDetail:
    attributes = sorted_attributes(character)
    sections: list[AttributeSection] = []
    for attribute in attributes:
        group, category = attribute.group, attribute.group.category
        if not sections or sections[-1].key != category.key:
            sections.append(
                AttributeSection(
                    key=category.key, domain=category.domain, name=category.name_zh, groups=[]  # type: ignore[arg-type]
                )
            )
        section = sections[-1]
        if not section.groups or section.groups[-1].key != group.key:
            section.groups.append(AttributeSectionGroup(key=group.key, name=group.name_zh, attributes=[]))
        section.groups[-1].attributes.append(_tag(attribute))

    return CharacterDetail(
        id=character.id,
        key=character.key,
        name=character.name,
        alt_name=alt_name(character),
        names=[
            CharacterNameOut(name=n.name, language=n.language, name_type=n.name_type)
            for n in character.names
        ],
        gender=character.gender,  # type: ignore[arg-type]
        birth_month=character.birth_month,
        birth_day=character.birth_day,
        age=character.age,
        height_cm=character.height_cm,
        blood_type=character.blood_type,
        summary=character.summary,
        image_url=character.image_url,
        palette=palette(attributes),
        works=[work_ref(link) for link in character.work_links],
        attribute_sections=sections,
    )


def work_list_item(work: Work, character_count: int) -> WorkListItem:
    return WorkListItem(
        id=work.id,
        key=work.key,
        title=work.title,
        title_original=work.title_original,
        title_en=work.title_en,
        work_type=work.work_type,
        release_year=work.release_year,
        summary=work.summary,
        image_url=work.image_url,
        character_count=character_count,
    )
