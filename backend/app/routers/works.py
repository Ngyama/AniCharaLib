from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import WORK_TYPES, CHARACTER_ROLES, CharacterWork, Work
from app.presenters import character_list_item, work_list_item
from app.schemas import WorkCharacter, WorkDetail, WorkPage
from app.search import like_pattern, load_characters

router = APIRouter(prefix="/api/works", tags=["works"])

character_count = (
    select(func.count())
    .where(CharacterWork.work_id == Work.id)
    .correlate(Work)
    .scalar_subquery()
    .label("character_count")
)


@router.get("", response_model=WorkPage, summary="List works")
def list_works(
    db: Session = Depends(get_db),
    q: Annotated[str | None, Query(max_length=100, description="Title in any language")] = None,
    work_type: Annotated[str | None, Query(description=f"One of {', '.join(WORK_TYPES)}")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 24,
) -> WorkPage:
    stmt = select(Work, character_count)
    text = (q or "").strip()
    if text:
        pattern = like_pattern(text)
        stmt = stmt.where(
            or_(
                Work.title.ilike(pattern, escape="\\"),
                Work.title_original.ilike(pattern, escape="\\"),
                Work.title_en.ilike(pattern, escape="\\"),
            )
        )
    if work_type:
        if work_type not in WORK_TYPES:
            raise HTTPException(status_code=422, detail=f"Unknown work_type {work_type!r}")
        stmt = stmt.where(Work.work_type == work_type)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.execute(
        stmt.order_by(Work.release_year.desc().nulls_last(), Work.id)
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()
    return WorkPage(
        items=[work_list_item(work, count) for work, count in rows],
        total=total,
        page=page,
        page_size=page_size,
        pages=ceil(total / page_size),
    )


@router.get("/{work_id}", response_model=WorkDetail, summary="Work detail with its characters")
def get_work(work_id: int, db: Session = Depends(get_db)) -> WorkDetail:
    work = db.get(Work, work_id)
    if work is None:
        raise HTTPException(status_code=404, detail="Work not found")

    role_rank = {role: index for index, role in enumerate(CHARACTER_ROLES)}
    links = sorted(
        db.scalars(select(CharacterWork).where(CharacterWork.work_id == work_id)),
        key=lambda link: (role_rank.get(link.role, len(role_rank)), link.character_id),
    )
    characters = load_characters(db, [link.character_id for link in links])
    roles = {link.character_id: link.role for link in links}

    base = work_list_item(work, len(characters))
    return WorkDetail(
        **base.model_dump(),
        characters=[
            WorkCharacter(**character_list_item(c).model_dump(), role=roles[c.id]) for c in characters
        ],
    )
