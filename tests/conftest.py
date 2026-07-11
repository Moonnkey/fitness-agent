from collections.abc import Iterator
from pathlib import Path

import pytest

from app.core.db.session import reset_engine_cache


@pytest.fixture(autouse=True)
def isolated_database(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    db_path = tmp_path / "fitness-agent-test.sqlite3"
    monkeypatch.setenv("FITNESS_AGENT_DB_PATH", str(db_path))
    reset_engine_cache()
    yield db_path
    reset_engine_cache()
