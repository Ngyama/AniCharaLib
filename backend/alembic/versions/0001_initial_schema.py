"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-10-23 15:49:05.951078
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = '0001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Trigram indexes back the substring (ILIKE) name search.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.create_table('attribute_categories',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=64), nullable=False),
    sa.Column('domain', sa.String(length=16), nullable=False),
    sa.Column('name_zh', sa.String(length=64), nullable=False),
    sa.Column('name_ja', sa.String(length=64), nullable=True),
    sa.Column('name_en', sa.String(length=64), nullable=True),
    sa.Column('sort_order', sa.SmallInteger(), server_default='0', nullable=False),
    sa.CheckConstraint("domain IN ('appearance', 'personality', 'other')", name=op.f('ck_attribute_categories_domain_valid')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_attribute_categories')),
    sa.UniqueConstraint('key', name=op.f('uq_attribute_categories_key'))
    )
    op.create_table('characters',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=64), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('gender', sa.String(length=10), server_default='unknown', nullable=False),
    sa.Column('birth_month', sa.SmallInteger(), nullable=True),
    sa.Column('birth_day', sa.SmallInteger(), nullable=True),
    sa.Column('age', sa.String(length=64), nullable=True),
    sa.Column('height_cm', sa.SmallInteger(), nullable=True),
    sa.Column('blood_type', sa.String(length=8), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('image_url', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("gender IN ('female', 'male', 'other', 'unknown')", name=op.f('ck_characters_gender_valid')),
    sa.CheckConstraint('birth_day BETWEEN 1 AND 31', name=op.f('ck_characters_birth_day_valid')),
    sa.CheckConstraint('birth_month BETWEEN 1 AND 12', name=op.f('ck_characters_birth_month_valid')),
    sa.CheckConstraint('height_cm > 0', name=op.f('ck_characters_height_positive')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_characters')),
    sa.UniqueConstraint('key', name=op.f('uq_characters_key'))
    )
    op.create_index(op.f('ix_characters_gender'), 'characters', ['gender'], unique=False)
    op.create_index(op.f('ix_characters_name'), 'characters', ['name'], unique=False)
    op.create_index('ix_characters_name_trgm', 'characters', ['name'], unique=False, postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
    op.create_table('works',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=64), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('title_original', sa.String(length=200), nullable=True),
    sa.Column('title_en', sa.String(length=200), nullable=True),
    sa.Column('work_type', sa.String(length=20), nullable=False),
    sa.Column('release_year', sa.SmallInteger(), nullable=True),
    sa.Column('summary', sa.Text(), nullable=True),
    sa.Column('image_url', sa.String(length=500), nullable=True),
    sa.CheckConstraint("work_type IN ('anime', 'visual_novel', 'manga', 'light_novel', 'game', 'novel', 'other')", name=op.f('ck_works_work_type_valid')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_works')),
    sa.UniqueConstraint('key', name=op.f('uq_works_key'))
    )
    op.create_index(op.f('ix_works_title'), 'works', ['title'], unique=False)
    op.create_index('ix_works_title_trgm', 'works', ['title'], unique=False, postgresql_using='gin', postgresql_ops={'title': 'gin_trgm_ops'})
    op.create_index(op.f('ix_works_work_type'), 'works', ['work_type'], unique=False)
    op.create_table('attribute_groups',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=64), nullable=False),
    sa.Column('name_zh', sa.String(length=64), nullable=False),
    sa.Column('name_ja', sa.String(length=64), nullable=True),
    sa.Column('name_en', sa.String(length=64), nullable=True),
    sa.Column('sort_order', sa.SmallInteger(), server_default='0', nullable=False),
    sa.Column('featured', sa.Boolean(), server_default='false', nullable=False),
    sa.ForeignKeyConstraint(['category_id'], ['attribute_categories.id'], name=op.f('fk_attribute_groups_category_id_attribute_categories'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_attribute_groups')),
    sa.UniqueConstraint('key', name=op.f('uq_attribute_groups_key'))
    )
    op.create_index(op.f('ix_attribute_groups_category_id'), 'attribute_groups', ['category_id'], unique=False)
    op.create_table('character_names',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('character_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('language', sa.String(length=10), nullable=False),
    sa.Column('name_type', sa.String(length=10), server_default='name', nullable=False),
    sa.CheckConstraint("language IN ('zh', 'ja', 'en', 'romaji', 'other')", name=op.f('ck_character_names_language_valid')),
    sa.CheckConstraint("name_type IN ('name', 'alias')", name=op.f('ck_character_names_name_type_valid')),
    sa.ForeignKeyConstraint(['character_id'], ['characters.id'], name=op.f('fk_character_names_character_id_characters'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_character_names')),
    sa.UniqueConstraint('character_id', 'language', 'name', name='uq_character_names_entry')
    )
    op.create_index(op.f('ix_character_names_character_id'), 'character_names', ['character_id'], unique=False)
    op.create_index('ix_character_names_name_trgm', 'character_names', ['name'], unique=False, postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
    op.create_table('character_works',
    sa.Column('character_id', sa.Integer(), nullable=False),
    sa.Column('work_id', sa.Integer(), nullable=False),
    sa.Column('role', sa.String(length=12), server_default='main', nullable=False),
    sa.Column('sort_order', sa.SmallInteger(), server_default='0', nullable=False),
    sa.CheckConstraint("role IN ('main', 'supporting', 'minor', 'cameo')", name=op.f('ck_character_works_role_valid')),
    sa.ForeignKeyConstraint(['character_id'], ['characters.id'], name=op.f('fk_character_works_character_id_characters'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['work_id'], ['works.id'], name=op.f('fk_character_works_work_id_works'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('character_id', 'work_id', name=op.f('pk_character_works'))
    )
    op.create_index('ix_character_works_work_id', 'character_works', ['work_id'], unique=False)
    op.create_table('attributes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('group_id', sa.Integer(), nullable=False),
    sa.Column('key', sa.String(length=64), nullable=False),
    sa.Column('name_zh', sa.String(length=64), nullable=False),
    sa.Column('name_ja', sa.String(length=64), nullable=True),
    sa.Column('name_en', sa.String(length=64), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('swatch', sa.String(length=7), nullable=True),
    sa.Column('parent_id', sa.Integer(), nullable=True),
    sa.Column('sort_order', sa.SmallInteger(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['group_id'], ['attribute_groups.id'], name=op.f('fk_attributes_group_id_attribute_groups'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['parent_id'], ['attributes.id'], name=op.f('fk_attributes_parent_id_attributes'), ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_attributes')),
    sa.UniqueConstraint('key', name=op.f('uq_attributes_key'))
    )
    op.create_index(op.f('ix_attributes_group_id'), 'attributes', ['group_id'], unique=False)
    op.create_index(op.f('ix_attributes_parent_id'), 'attributes', ['parent_id'], unique=False)
    op.create_table('character_attributes',
    sa.Column('character_id', sa.Integer(), nullable=False),
    sa.Column('attribute_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['attribute_id'], ['attributes.id'], name=op.f('fk_character_attributes_attribute_id_attributes'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['character_id'], ['characters.id'], name=op.f('fk_character_attributes_character_id_characters'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('character_id', 'attribute_id', name=op.f('pk_character_attributes'))
    )
    op.create_index('ix_character_attributes_attribute_id', 'character_attributes', ['attribute_id', 'character_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_character_attributes_attribute_id', table_name='character_attributes')
    op.drop_table('character_attributes')
    op.drop_index(op.f('ix_attributes_parent_id'), table_name='attributes')
    op.drop_index(op.f('ix_attributes_group_id'), table_name='attributes')
    op.drop_table('attributes')
    op.drop_index('ix_character_works_work_id', table_name='character_works')
    op.drop_table('character_works')
    op.drop_index('ix_character_names_name_trgm', table_name='character_names', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
    op.drop_index(op.f('ix_character_names_character_id'), table_name='character_names')
    op.drop_table('character_names')
    op.drop_index(op.f('ix_attribute_groups_category_id'), table_name='attribute_groups')
    op.drop_table('attribute_groups')
    op.drop_index(op.f('ix_works_work_type'), table_name='works')
    op.drop_index('ix_works_title_trgm', table_name='works', postgresql_using='gin', postgresql_ops={'title': 'gin_trgm_ops'})
    op.drop_index(op.f('ix_works_title'), table_name='works')
    op.drop_table('works')
    op.drop_index('ix_characters_name_trgm', table_name='characters', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
    op.drop_index(op.f('ix_characters_name'), table_name='characters')
    op.drop_index(op.f('ix_characters_gender'), table_name='characters')
    op.drop_table('characters')
    op.drop_table('attribute_categories')
