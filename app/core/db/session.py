import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.models.base import Base

DEFAULT_DATABASE_PATH = Path("data/fitness-agent.sqlite3")

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_database_path() -> Path:
    override = os.getenv("FITNESS_AGENT_DB_PATH")
    if override:
        return Path(override).expanduser()
    return DEFAULT_DATABASE_PATH


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        db_path = get_database_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        _engine = create_engine(f"sqlite:///{db_path}", future=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), expire_on_commit=False, future=True)
    return _session_factory


def init_db() -> None:
    import app.core.models  # noqa: F401

    engine = get_engine()
    Base.metadata.create_all(engine)
    _ensure_sqlite_schema_updates(engine)


def _ensure_sqlite_schema_updates(engine: Engine) -> None:
    if engine.url.get_backend_name() != "sqlite":
        return

    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    for table_name in ("meal_items", "weight_entries", "activity_entries"):
        if table_name not in table_names:
            continue
        column_names = {column["name"] for column in inspector.get_columns(table_name)}
        if "updated_at" in column_names:
            continue
        with engine.begin() as connection:
            connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN updated_at DATETIME"))


def reset_engine_cache() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


@contextmanager
def session_scope() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
