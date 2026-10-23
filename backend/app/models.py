"""Database models.

The schema is character-centric:

    Character ─< CharacterName
    Character >─< Work                (character_works)
    Character >─< Attribute           (character_attributes)
    AttributeCategory ─< AttributeGroup ─< Attribute

Every searchable trait (hair colour, outfit, personality, occupation ...) is a row in
``attributes``; adding categories or tags never requires a schema change.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    MetaData,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

DOMAINS = ("appearance", "personality", "other")
GENDERS = ("female", "male", "other", "unknown")
NAME_LANGUAGES = ("zh", "ja", "en", "romaji", "other")
NAME_TYPES = ("name", "alias")
WORK_TYPES = ("anime", "visual_novel", "manga", "light_novel", "game", "novel", "other")
CHARACTER_ROLES = ("main", "supporting", "minor", "cameo")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(table_name)s_%(column_0_N_name)s",
            "uq": "uq_%(table_name)s_%(column_0_N_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class AttributeCategory(Base):
    """First-level attribute category, e.g. 头发 / 眼睛 / 性格."""

    __tablename__ = "attribute_categories"
    __table_args__ = (CheckConstraint(_in("domain", DOMAINS), name="domain_valid"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    domain: Mapped[str] = mapped_column(String(16))
    name_zh: Mapped[str] = mapped_column(String(64))
    name_ja: Mapped[str | None] = mapped_column(String(64))
    name_en: Mapped[str | None] = mapped_column(String(64))
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")

    groups: Mapped[list["AttributeGroup"]] = relationship(
        back_populates="category",
        order_by="AttributeGroup.sort_order",
        cascade="all, delete-orphan",
    )


class AttributeGroup(Base):
    """Second-level category, e.g. 发色 / 发型. Mainly used for navigation and OR-grouping in search."""

    __tablename__ = "attribute_groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("attribute_categories.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(64), unique=True)
    name_zh: Mapped[str] = mapped_column(String(64))
    name_ja: Mapped[str | None] = mapped_column(String(64))
    name_en: Mapped[str | None] = mapped_column(String(64))
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    # Attributes of featured groups are shown on character cards.
    featured: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")

    category: Mapped[AttributeCategory] = relationship(back_populates="groups")
    attributes: Mapped[list["Attribute"]] = relationship(
        back_populates="group",
        order_by="Attribute.sort_order",
        cascade="all, delete-orphan",
    )


class Attribute(Base):
    """A single searchable tag, e.g. 粉发 / 双马尾 / 弱气."""

    __tablename__ = "attributes"

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(
        ForeignKey("attribute_groups.id", ondelete="CASCADE"), index=True
    )
    key: Mapped[str] = mapped_column(String(64), unique=True)
    name_zh: Mapped[str] = mapped_column(String(64))
    name_ja: Mapped[str | None] = mapped_column(String(64))
    name_en: Mapped[str | None] = mapped_column(String(64))
    description: Mapped[str | None] = mapped_column(Text)
    # Optional display colour for colour attributes (hair / eye colour), e.g. "#e7a3b9".
    swatch: Mapped[str | None] = mapped_column(String(7))
    # Informational hierarchy (猫耳 → 兽耳). Search does not expand parents to children.
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("attributes.id", ondelete="SET NULL"), index=True
    )
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")

    group: Mapped[AttributeGroup] = relationship(back_populates="attributes")
    parent: Mapped["Attribute | None"] = relationship(remote_side="Attribute.id")


class Work(Base):
    __tablename__ = "works"
    __table_args__ = (
        CheckConstraint(_in("work_type", WORK_TYPES), name="work_type_valid"),
        Index(
            "ix_works_title_trgm",
            "title",
            postgresql_using="gin",
            postgresql_ops={"title": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True)
    title: Mapped[str] = mapped_column(String(200), index=True)
    title_original: Mapped[str | None] = mapped_column(String(200))
    title_en: Mapped[str | None] = mapped_column(String(200))
    work_type: Mapped[str] = mapped_column(String(20), index=True)
    release_year: Mapped[int | None] = mapped_column(SmallInteger)
    summary: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))

    character_links: Mapped[list["CharacterWork"]] = relationship(
        back_populates="work", cascade="all, delete-orphan"
    )


class Character(Base):
    __tablename__ = "characters"
    __table_args__ = (
        CheckConstraint(_in("gender", GENDERS), name="gender_valid"),
        CheckConstraint("birth_month BETWEEN 1 AND 12", name="birth_month_valid"),
        CheckConstraint("birth_day BETWEEN 1 AND 31", name="birth_day_valid"),
        CheckConstraint("height_cm > 0", name="height_positive"),
        Index(
            "ix_characters_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Stable identifier used by the seed files; never shown as the display name.
    key: Mapped[str] = mapped_column(String(64), unique=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    gender: Mapped[str] = mapped_column(
        String(10), default="unknown", server_default="unknown", index=True
    )
    birth_month: Mapped[int | None] = mapped_column(SmallInteger)
    birth_day: Mapped[int | None] = mapped_column(SmallInteger)
    # Free text because ACG ages are often "17", "外表 12 / 实际 400" or unknown.
    age: Mapped[str | None] = mapped_column(String(64))
    height_cm: Mapped[int | None] = mapped_column(SmallInteger)
    blood_type: Mapped[str | None] = mapped_column(String(8))
    summary: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    names: Mapped[list["CharacterName"]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
        order_by="CharacterName.id",
    )
    work_links: Mapped[list["CharacterWork"]] = relationship(
        back_populates="character",
        cascade="all, delete-orphan",
        order_by="CharacterWork.sort_order",
    )
    attribute_links: Mapped[list["CharacterAttribute"]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )


class CharacterName(Base):
    """Names and aliases in different languages."""

    __tablename__ = "character_names"
    __table_args__ = (
        UniqueConstraint("character_id", "language", "name", name="uq_character_names_entry"),
        CheckConstraint(_in("language", NAME_LANGUAGES), name="language_valid"),
        CheckConstraint(_in("name_type", NAME_TYPES), name="name_type_valid"),
        Index(
            "ix_character_names_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    character_id: Mapped[int] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    language: Mapped[str] = mapped_column(String(10))
    name_type: Mapped[str] = mapped_column(String(10), default="name", server_default="name")

    character: Mapped[Character] = relationship(back_populates="names")


class CharacterWork(Base):
    __tablename__ = "character_works"
    __table_args__ = (
        CheckConstraint(_in("role", CHARACTER_ROLES), name="role_valid"),
        Index("ix_character_works_work_id", "work_id"),
    )

    character_id: Mapped[int] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True
    )
    work_id: Mapped[int] = mapped_column(
        ForeignKey("works.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(12), default="main", server_default="main")
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")

    character: Mapped[Character] = relationship(back_populates="work_links")
    work: Mapped[Work] = relationship(back_populates="character_links")


class CharacterAttribute(Base):
    __tablename__ = "character_attributes"
    # (character_id, attribute_id) is the PK; the reverse index serves attribute → characters lookups.
    __table_args__ = (Index("ix_character_attributes_attribute_id", "attribute_id", "character_id"),)

    character_id: Mapped[int] = mapped_column(
        ForeignKey("characters.id", ondelete="CASCADE"), primary_key=True
    )
    attribute_id: Mapped[int] = mapped_column(
        ForeignKey("attributes.id", ondelete="CASCADE"), primary_key=True
    )

    character: Mapped[Character] = relationship(back_populates="attribute_links")
    attribute: Mapped[Attribute] = relationship()
