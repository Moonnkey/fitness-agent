import os
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
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

    Base.metadata.create_all(get_engine())


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
