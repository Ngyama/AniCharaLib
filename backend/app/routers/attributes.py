from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Attribute, AttributeCategory, AttributeGroup, CharacterAttribute
from app.schemas import AttributeCategoryOut, AttributeDictionary, AttributeGroupOut, AttributeOut

router = APIRouter(prefix="/api/attributes", tags=["attributes"])


@router.get("", response_model=AttributeDictionary, summary="Full attribute dictionary")
def get_attribute_dictionary(db: Session = Depends(get_db)) -> AttributeDictionary:
    """All categories → groups → attributes in display order, with per-attribute character counts."""
    categories = db.scalars(
        select(AttributeCategory)
        .order_by(AttributeCategory.sort_order, AttributeCategory.id)
        .options(
            selectinload(AttributeCategory.groups)
            .selectinload(AttributeGroup.attributes)
            .selectinload(Attribute.parent)
        )
    ).all()
    counts = dict(
        db.execute(
            select(CharacterAttribute.attribute_id, func.count()).group_by(
                CharacterAttribute.attribute_id
            )
        ).all()
    )

    total = 0
    out: list[AttributeCategoryOut] = []
    for category in categories:
        groups: list[AttributeGroupOut] = []
        for group in category.groups:
            attributes = [
                AttributeOut(
                    id=a.id,
                    key=a.key,
                    name=a.name_zh,
                    name_ja=a.name_ja,
                    name_en=a.name_en,
                    swatch=a.swatch,
                    parent_key=a.parent.key if a.parent else None,
                    character_count=counts.get(a.id, 0),
                )
                for a in group.attributes
            ]
            total += len(attributes)
            groups.append(
                AttributeGroupOut(
                    id=group.id,
                    key=group.key,
                    name=group.name_zh,
                    name_ja=group.name_ja,
                    name_en=group.name_en,
                    featured=group.featured,
                    attributes=attributes,
                )
            )
        out.append(
            AttributeCategoryOut(
                id=category.id,
                key=category.key,
                domain=category.domain,  # type: ignore[arg-type]
                name=category.name_zh,
                name_ja=category.name_ja,
                name_en=category.name_en,
                groups=groups,
            )
        )
    return AttributeDictionary(categories=out, total_attributes=total)
