from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.presenters import character_detail, character_list_item
from app.schemas import CharacterDetail, CharacterPage, CharacterSort, Gender
from app.search import CharacterQuery, load_characters, search_characters

router = APIRouter(prefix="/api/characters", tags=["characters"])


@router.get("", response_model=CharacterPage, summary="List / search characters")
def list_characters(
    db: Session = Depends(get_db),
    q: Annotated[str | None, Query(max_length=100, description="Name or alias, any language")] = None,
    attrs: Annotated[
        list[str],
        Query(
            description=(
                "Attribute keys; repeat the parameter or separate with commas. "
                "Same group → OR, different groups → AND."
            )
        ),
    ] = [],
    gender: Gender | None = None,
    work_id: int | None = None,
    sort: CharacterSort = "relevance",
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
) -> CharacterPage:
    result = search_characters(
        db,
        CharacterQuery(
            q=q,
            attribute_keys=attrs,
            gender=gender,
            work_id=work_id,
            sort=sort,
            page=page,
            page_size=page_size,
        ),
    )
    return CharacterPage(
        items=[character_list_item(c, result.matched_attribute_ids) for c in result.characters],
        total=result.total,
        page=page,
        page_size=page_size,
        pages=ceil(result.total / page_size),
        unknown_attributes=result.unknown_attributes,
    )


@router.get("/{character_id}", response_model=CharacterDetail, summary="Character detail")
def get_character(character_id: int, db: Session = Depends(get_db)) -> CharacterDetail:
    characters = load_characters(db, [character_id])
    if not characters:
        raise HTTPException(status_code=404, detail="Character not found")
    return character_detail(characters[0])
