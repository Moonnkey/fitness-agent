import sqlite3
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


def test_init_db_adds_updated_at_to_existing_sqlite_tables(
    tmp_path: Path,
    monkeypatch,
) -> None:
    db_path = tmp_path / "fitness.sqlite3"
    monkeypatch.setenv("FITNESS_AGENT_DB_PATH", str(db_path))
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE meal_items (id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE weight_entries (id INTEGER PRIMARY KEY)")
        connection.execute("CREATE TABLE activity_entries (id INTEGER PRIMARY KEY)")

    init_db()

    with sqlite3.connect(db_path) as connection:
        for table_name in ("meal_items", "weight_entries", "activity_entries"):
            columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")}
            assert "updated_at" in columns
