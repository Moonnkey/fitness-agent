from pathlib import Path

from app.core.db.session import get_database_path, init_db, session_scope


def test_database_path_uses_environment_override(monkeypatch, tmp_path: Path) -> None:
    db_path = tmp_path / "custom.sqlite3"
    monkeypatch.setenv("FITNESS_AGENT_DB_PATH", str(db_path))

    assert get_database_path() == db_path


def test_init_db_creates_sqlite_file(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "fitness.sqlite3"
    monkeypatch.setenv("FITNESS_AGENT_DB_PATH", str(db_path))

    init_db()

    assert db_path.exists()


def test_session_scope_opens_and_closes_session(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "fitness.sqlite3"
    monkeypatch.setenv("FITNESS_AGENT_DB_PATH", str(db_path))
    init_db()

    with session_scope() as session:
        assert session.is_active
