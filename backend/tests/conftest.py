"""Test fixtures.

Tests run against a real PostgreSQL database (TEST_DATABASE_URL, default ``<POSTGRES_DB>_test``).
The schema is rebuilt with the Alembic migrations once per session and every table is
truncated before each test.
"""

import copy
from collections.abc import Callable, Iterator
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.config import BACKEND_DIR, get_settings
from app.db import get_db
from app.main import app
from app.models import Base
from app.seed import SeedData, SeedStats, run_seed


def _ensure_database(url: str) -> None:
    target = make_url(url)
    admin = create_engine(target.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": target.database}
        )
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{target.database}"'))
    admin.dispose()


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    url = get_settings().sqlalchemy_test_url
    _ensure_database(url)
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))

    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    command.upgrade(config, "head")

    yield engine
    engine.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as session:
        yield session


@pytest.fixture
def client(engine: Engine, db: Session) -> Iterator[TestClient]:
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override() -> Iterator[Session]:
        with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


# ── a small, hand-crafted dataset for exact search assertions ────────────────

MINI_DICTIONARY: list[dict[str, Any]] = [
    {
        "key": "hair",
        "domain": "appearance",
        "zh": "头发",
        "groups": [
            {
                "key": "hair-color",
                "zh": "发色",
                "featured": True,
                "attributes": [
                    {"key": "pink-hair", "zh": "粉发", "swatch": "#eda3bf"},
                    {"key": "red-hair", "zh": "红发", "swatch": "#c4453f"},
                    {"key": "black-hair", "zh": "黑发", "swatch": "#2c2c33"},
                    # Exists in the dictionary but nobody is tagged with it.
                    {"key": "blue-hair", "zh": "蓝发"},
                ],
            },
            {
                "key": "hairstyle",
                "zh": "发型",
                "featured": True,
                "attributes": [
                    {"key": "twin-tails", "zh": "双马尾"},
                    {"key": "ponytail", "zh": "单马尾"},
                ],
            },
        ],
    },
    {
        "key": "personality",
        "domain": "personality",
        "zh": "性格",
        "groups": [
            {
                "key": "personality-traits",
                "zh": "性格特征",
                "attributes": [
                    {"key": "weak-willed", "zh": "弱气"},
                    {"key": "gentle", "zh": "温柔"},
                ],
            },
            {
                "key": "archetypes",
                "zh": "ACG 人物属性",
                "featured": True,
                "attributes": [{"key": "tsundere", "zh": "傲娇"}],
            },
        ],
    },
    {
        "key": "other",
        "domain": "other",
        "zh": "其他属性",
        "groups": [
            {"key": "occupation", "zh": "身份与职业", "attributes": [{"key": "student", "zh": "学生"}]}
        ],
    },
]

MINI_WORKS: list[dict[str, Any]] = [
    {"key": "work-one", "title": "作品一", "title_en": "Work One", "work_type": "anime"},
    {"key": "work-two", "title": "作品二", "work_type": "manga"},
]

MINI_CHARACTERS: list[dict[str, Any]] = [
    {
        "key": "alpha",
        "name": "阿尔法",
        "names": {"ja": "アルファ", "en": "Alpha Example", "romaji": "Aruufa"},
        "aliases": [{"name": "小A", "language": "zh"}, {"name": "あーちゃん", "language": "ja"}],
        "gender": "female",
        "birthday": "04-03",
        "works": [{"work": "work-one", "role": "main"}, {"work": "work-two", "role": "cameo"}],
        "attributes": ["pink-hair", "twin-tails", "weak-willed", "student"],
    },
    {
        "key": "bravo",
        "name": "布拉沃",
        "names": {"en": "Bravo"},
        "gender": "female",
        "works": [{"work": "work-one", "role": "supporting"}],
        "attributes": ["red-hair", "twin-tails", "weak-willed"],
    },
    {
        "key": "charlie",
        "name": "查理",
        "gender": "female",
        "works": [{"work": "work-one"}],
        "attributes": ["pink-hair", "twin-tails", "tsundere"],
    },
    {
        "key": "delta",
        "name": "德尔塔",
        "gender": "female",
        "works": [{"work": "work-two"}],
        "attributes": ["pink-hair", "ponytail", "weak-willed"],
    },
    {
        "key": "echo",
        "name": "回声",
        "names": {"en": "Echo"},
        "gender": "male",
        "works": [{"work": "work-two"}],
        "attributes": ["black-hair", "twin-tails", "weak-willed", "gentle"],
    },
    {
        "key": "zeta",
        "name": "泽塔",
        "names": {"en": "Zeta 100%"},
        "gender": "unknown",
        "works": [{"work": "work-two", "role": "minor"}],
        "attributes": [],
    },
]


def mini_data() -> SeedData:
    return SeedData(
        categories=copy.deepcopy(MINI_DICTIONARY),
        works=copy.deepcopy(MINI_WORKS),
        characters=copy.deepcopy(MINI_CHARACTERS),
    )


@pytest.fixture
def seed(db: Session) -> Callable[[SeedData | None], SeedStats]:
    def _seed(data: SeedData | None = None) -> SeedStats:
        return run_seed(db, data or mini_data())

    return _seed


@pytest.fixture
def mini(seed: Callable[[SeedData | None], SeedStats]) -> None:
    seed(None)
