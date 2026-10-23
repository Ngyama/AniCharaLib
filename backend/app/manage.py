"""Development database commands.

    python -m app.manage wait            # wait until PostgreSQL accepts connections
    python -m app.manage init            # wait, create the database if missing, migrate, seed
    python -m app.manage migrate         # alembic upgrade head
    python -m app.manage reset           # DROP everything, migrate, seed (asks for confirmation)
    python -m app.manage reset --yes     # same, without the prompt
    python -m app.manage status          # show connection target and migration revision

Every command reads the connection settings from .env / environment variables.
"""

import argparse
import sys
import time

from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import OperationalError

from app.config import BACKEND_DIR, get_settings

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "db", "postgres"}


def alembic_config(url: str) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return config


def describe(url: URL) -> str:
    return f"{url.username}@{url.host}:{url.port or 5432}/{url.database}"


def wait_for_server(url: URL, timeout: float = 60) -> None:
    """Block until the server answers (via the always-present 'postgres' database)."""
    admin = create_engine(url.set(database="postgres"))
    deadline = time.monotonic() + timeout
    try:
        while True:
            try:
                with admin.connect():
                    return
            except OperationalError as exc:
                if time.monotonic() > deadline:
                    raise SystemExit(
                        f"PostgreSQL at {url.host}:{url.port or 5432} is not reachable after "
                        f"{timeout:.0f}s.\nIs it running? Try: dev.cmd db\n\n{exc.orig}"
                    ) from exc
                time.sleep(1)
    finally:
        admin.dispose()


def ensure_database(url: URL) -> bool:
    """Create the target database if it does not exist. Returns True when it was created."""
    admin = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            exists = conn.scalar(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": url.database}
            )
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{url.database}"'))
                return True
            return False
    finally:
        admin.dispose()


def current_revision(url: URL) -> str | None:
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            return MigrationContext.configure(conn).get_current_revision()
    finally:
        engine.dispose()


def migrate(url_str: str) -> None:
    command.upgrade(alembic_config(url_str), "head")


def seed() -> None:
    from app.seed import main as seed_main

    if seed_main([]) != 0:
        raise SystemExit(1)


def drop_all(url: URL) -> None:
    engine = create_engine(url)
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP SCHEMA public CASCADE"))
            conn.execute(text("CREATE SCHEMA public"))
    finally:
        engine.dispose()


def cmd_init(url_str: str, url: URL) -> None:
    print(f"Database: {describe(url)}")
    wait_for_server(url)
    if ensure_database(url):
        print(f"Created database {url.database!r}")
    migrate(url_str)
    seed()


def cmd_reset(url_str: str, url: URL, yes: bool, allow_remote: bool) -> None:
    if url.host not in LOCAL_HOSTS and not allow_remote:
        raise SystemExit(
            f"Refusing to reset non-local database host {url.host!r}. "
            "Pass --allow-remote if you really mean it."
        )
    print(f"This will DELETE ALL DATA in {describe(url)} and rebuild it from migrations + seed files.")
    if not yes:
        answer = input(f"Type the database name ({url.database}) to confirm: ").strip()
        if answer != url.database:
            raise SystemExit("Aborted, nothing was changed.")
    wait_for_server(url)
    ensure_database(url)
    drop_all(url)
    print("Dropped all tables.")
    migrate(url_str)
    seed()


def cmd_status(url_str: str, url: URL) -> None:
    head = ScriptDirectory.from_config(alembic_config(url_str)).get_current_head()
    print(f"Database:          {describe(url)}")
    try:
        revision = current_revision(url)
    except OperationalError as exc:
        print(f"Connection:        FAILED ({str(exc.orig).strip().splitlines()[0]})")
        raise SystemExit(1) from exc
    print(f"Current revision:  {revision or '(empty database)'}")
    print(f"Latest migration:  {head}")
    if revision != head:
        print("Database is behind the code. Run: dev.cmd migrate")
        raise SystemExit(1)
    print("Up to date.")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("wait")
    sub.add_parser("init")
    sub.add_parser("migrate")
    sub.add_parser("status")
    reset = sub.add_parser("reset")
    reset.add_argument("--yes", action="store_true", help="skip the confirmation prompt")
    reset.add_argument("--allow-remote", action="store_true", help="allow a non-local host")
    args = parser.parse_args(argv)

    url_str = get_settings().sqlalchemy_url
    url = make_url(url_str)
    if args.command == "wait":
        wait_for_server(url)
        print("PostgreSQL is ready.")
    elif args.command == "init":
        cmd_init(url_str, url)
    elif args.command == "migrate":
        migrate(url_str)
    elif args.command == "status":
        cmd_status(url_str, url)
    elif args.command == "reset":
        cmd_reset(url_str, url, args.yes, args.allow_remote)


if __name__ == "__main__":
    sys.stdout.reconfigure(errors="backslashreplace")  # type: ignore[union-attr]
    main()
