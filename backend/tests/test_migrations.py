"""Guards that keep the schema reproducible on every machine.

* the SQLAlchemy models and the Alembic migrations describe the same schema
  (a model change without a migration fails here)
* there is exactly one migration head (two machines adding migrations in parallel fail here)
* every migration can be downgraded and re-applied
"""

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

from app.config import get_settings
from app.manage import alembic_config
from app.models import Base


def config():
    return alembic_config(get_settings().sqlalchemy_test_url)


def test_single_migration_head():
    heads = ScriptDirectory.from_config(config()).get_heads()
    assert len(heads) == 1, (
        f"Multiple Alembic heads {heads}: migrations were created in parallel. "
        "Run `alembic merge heads -m merge` and commit the result."
    )


def test_models_match_migrations(engine: Engine):
    with engine.connect() as conn:
        diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
    assert diff == [], (
        "app/models.py differs from the migrations. Create one with "
        f'`dev.cmd migration "describe the change"`.\n{diff}'
    )


def test_downgrade_and_upgrade_round_trip(engine: Engine):
    try:
        command.downgrade(config(), "base")
        assert set(inspect(engine).get_table_names()) <= {"alembic_version"}
    finally:
        command.upgrade(config(), "head")
    assert {"characters", "attributes", "works"} <= set(inspect(engine).get_table_names())
