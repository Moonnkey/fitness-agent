# Weight Activity Summary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add basic weight and activity recording, include activity calories and net calories in daily summaries, expose the new operations through CLI and MCP tools, and update the Agent Skill contracts.

**Architecture:** Add `WeightEntry` and `ActivityEntry` SQLAlchemy models with Pydantic schemas and core services. Extend `summary_service` to aggregate activity calories without changing meal logic. Keep CLI and MCP as thin wrappers over `app/core/services`.

**Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2, SQLite, Typer, MCP Python SDK FastMCP, pytest, ruff.

---

## Source Documents

- `AGENTS.md`
- `docs/mvp.md`
- `docs/architecture.md`
- `skill/SKILL.md`
- `skill/references/tool-contracts.md`

## Global Constraints

- Keep all business logic in `app/core/services`.
- Preserve `raw_text` and `metadata` for weight and activity entries.
- Do not add training programming, exercise libraries, muscle-group mapping, wearable import, RAG, or food database lookup.
- Activity calories are estimates unless `is_estimated` is false.
- Daily summary net calories means `total_calories - activity_calories`.
- Use TDD for each feature slice.

## Planned File Structure

- Create `app/core/models/weight.py`
- Create `app/core/models/activity.py`
- Modify `app/core/models/__init__.py`
- Create `app/core/schemas/weight.py`
- Create `app/core/schemas/activity.py`
- Modify `app/core/schemas/summary.py`
- Create `app/core/services/weight_service.py`
- Create `app/core/services/activity_service.py`
- Modify `app/core/services/summary_service.py`
- Modify `app/cli/main.py`
- Modify `app/mcp/server.py`
- Modify `skill/SKILL.md`
- Modify `skill/references/tool-contracts.md`
- Add tests for weight, activity, summary, CLI, MCP, and skill contracts.

---

### Task 1: Commit Third-Stage Documentation Updates

**Files:**
- Modify: `docs/mvp.md`
- Modify: `docs/mvp.zh.md`
- Modify: `docs/architecture.md`
- Modify: `docs/architecture.zh.md`
- Create: `docs/superpowers/plans/2026-07-11-weight-activity-summary.md`

- [ ] **Step 1: Run verification**

Run:

```bash
uv --cache-dir .uv-cache run pytest
uv --cache-dir .uv-cache run ruff check app tests
```

Expected: pass.

- [ ] **Step 2: Commit docs and plan**

```bash
git add docs/mvp.md docs/mvp.zh.md docs/architecture.md docs/architecture.zh.md docs/superpowers/plans/2026-07-11-weight-activity-summary.md
git commit -m "Document weight and activity milestone"
```

---

### Task 2: Weight Model, Schema, Service, And Trend

**Files:**
- Create: `app/core/models/weight.py`
- Modify: `app/core/models/__init__.py`
- Create: `app/core/schemas/weight.py`
- Create: `app/core/services/weight_service.py`
- Create: `tests/test_weight_service.py`

- [ ] **Step 1: Write failing weight tests**

Create `tests/test_weight_service.py`:

```python
from datetime import date

from app.core.db.session import init_db
from app.core.schemas.weight import WeightEntryInput
from app.core.services.weight_service import get_weight_trend, record_weight


def test_record_weight_preserves_raw_text_and_metadata() -> None:
    init_db()

    entry = record_weight(
        WeightEntryInput(
            date=date(2026, 7, 11),
            weight_kg=79.6,
            raw_text="今天早上空腹 79.6kg",
            metadata={"timing": "morning fasting"},
        )
    )

    assert entry.id > 0
    assert entry.weight_kg == 79.6
    assert entry.raw_text == "今天早上空腹 79.6kg"
    assert entry.metadata == {"timing": "morning fasting"}


def test_weight_trend_returns_latest_and_average() -> None:
    init_db()
    for day, weight in [(5, 80.0), (6, 79.8), (7, 79.7), (8, 79.6)]:
        record_weight(WeightEntryInput(date=date(2026, 7, day), weight_kg=weight))

    trend = get_weight_trend(days=7)

    assert trend.latest_weight_kg == 79.6
    assert trend.latest_date == date(2026, 7, 8)
    assert trend.average_weight_kg == 79.775
    assert trend.entry_count == 4
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv --cache-dir .uv-cache run pytest tests/test_weight_service.py -v
```

Expected: fail because weight modules do not exist.

- [ ] **Step 3: Implement weight model**

Create `app/core/models/weight.py`:

```python
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import Date, DateTime, Float, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class WeightEntry(Base):
    __tablename__ = "weight_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    weight_kg: Mapped[float] = mapped_column(Float)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
```

Modify `app/core/models/__init__.py` to import and export `WeightEntry`.

- [ ] **Step 4: Implement weight schemas**

Create `app/core/schemas/weight.py`:

```python
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class WeightEntryInput(BaseModel):
    date: date
    weight_kg: float = Field(gt=0)
    raw_text: str | None = None
    metadata: dict[str, Any] | None = None
    note: str | None = None


class WeightEntryOutput(WeightEntryInput):
    model_config = ConfigDict(from_attributes=True)

    id: int


class WeightTrendOutput(BaseModel):
    latest_weight_kg: float | None
    latest_date: date | None
    average_weight_kg: float | None
    days: int
    entry_count: int
    entries: list[WeightEntryOutput]
```

- [ ] **Step 5: Implement weight service**

Create `app/core/services/weight_service.py`:

```python
from datetime import date, timedelta

from sqlalchemy import select

from app.core.db.session import session_scope
from app.core.models.weight import WeightEntry
from app.core.schemas.weight import WeightEntryInput, WeightEntryOutput, WeightTrendOutput


def _to_output(entry: WeightEntry) -> WeightEntryOutput:
    return WeightEntryOutput(
        id=entry.id,
        date=entry.date,
        weight_kg=entry.weight_kg,
        raw_text=entry.raw_text,
        metadata=entry.metadata_json,
        note=entry.note,
    )


def record_weight(input_data: WeightEntryInput) -> WeightEntryOutput:
    with session_scope() as session:
        entry = WeightEntry(
            date=input_data.date,
            weight_kg=input_data.weight_kg,
            raw_text=input_data.raw_text,
            metadata_json=input_data.metadata,
            note=input_data.note,
        )
        session.add(entry)
        session.flush()
        return _to_output(entry)


def get_weight_trend(days: int = 7) -> WeightTrendOutput:
    with session_scope() as session:
        latest = (
            session.execute(select(WeightEntry).order_by(WeightEntry.date.desc(), WeightEntry.id.desc()))
            .scalars()
            .first()
        )
        if latest is None:
            return WeightTrendOutput(
                latest_weight_kg=None,
                latest_date=None,
                average_weight_kg=None,
                days=days,
                entry_count=0,
                entries=[],
            )

        start_date = latest.date - timedelta(days=days - 1)
        entries = (
            session.execute(
                select(WeightEntry)
                .where(WeightEntry.date >= start_date)
                .where(WeightEntry.date <= latest.date)
                .order_by(WeightEntry.date, WeightEntry.id)
            )
            .scalars()
            .all()
        )
        outputs = [_to_output(entry) for entry in entries]
        average = sum(entry.weight_kg for entry in outputs) / len(outputs)
        return WeightTrendOutput(
            latest_weight_kg=latest.weight_kg,
            latest_date=latest.date,
            average_weight_kg=average,
            days=days,
            entry_count=len(outputs),
            entries=outputs,
        )
```

- [ ] **Step 6: Run weight tests and full verification**

Run:

```bash
uv --cache-dir .uv-cache run pytest tests/test_weight_service.py -v
uv --cache-dir .uv-cache run pytest
uv --cache-dir .uv-cache run ruff check app tests
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add app/core/models app/core/schemas/weight.py app/core/services/weight_service.py tests/test_weight_service.py
git commit -m "Add weight tracking service"
```

---

### Task 3: Activity Model, Schema, Service

**Files:**
- Create: `app/core/models/activity.py`
- Modify: `app/core/models/__init__.py`
- Create: `app/core/schemas/activity.py`
- Create: `app/core/services/activity_service.py`
- Create: `tests/test_activity_service.py`

- [ ] **Step 1: Write failing activity tests**

Create `tests/test_activity_service.py`:

```python
from datetime import date

from app.core.db.session import init_db
from app.core.schemas.activity import ActivityEntryInput
from app.core.services.activity_service import list_activities_for_date, record_activity


def test_record_activity_preserves_estimate_context() -> None:
    init_db()

    entry = record_activity(
        ActivityEntryInput(
            date=date(2026, 7, 11),
            activity_type="walking",
            duration_minutes=40,
            calories_burned=180,
            is_estimated=True,
            raw_text="今天快走 40 分钟",
            metadata={"estimation_basis": "中等强度快走估算"},
        )
    )

    assert entry.id > 0
    assert entry.calories_burned == 180
    assert entry.is_estimated is True
    assert entry.metadata == {"estimation_basis": "中等强度快走估算"}


def test_list_activities_for_date_filters_by_date() -> None:
    init_db()
    record_activity(
        ActivityEntryInput(
            date=date(2026, 7, 11),
            activity_type="walking",
            calories_burned=180,
        )
    )
    record_activity(
        ActivityEntryInput(
            date=date(2026, 7, 12),
            activity_type="cycling",
            calories_burned=250,
        )
    )

    entries = list_activities_for_date(date(2026, 7, 11))

    assert len(entries) == 1
    assert entries[0].activity_type == "walking"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv --cache-dir .uv-cache run pytest tests/test_activity_service.py -v
```

Expected: fail because activity modules do not exist.

- [ ] **Step 3: Implement activity model, schema, and service**

Create `app/core/models/activity.py`, `app/core/schemas/activity.py`, and `app/core/services/activity_service.py` mirroring the weight pattern with these fields:

```text
date
activity_type
duration_minutes
calories_burned
is_estimated
raw_text
metadata
note
```

Use `ge=0` for `duration_minutes` and `calories_burned`.

- [ ] **Step 4: Run activity tests and full verification**

Run:

```bash
uv --cache-dir .uv-cache run pytest tests/test_activity_service.py -v
uv --cache-dir .uv-cache run pytest
uv --cache-dir .uv-cache run ruff check app tests
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add app/core/models app/core/schemas/activity.py app/core/services/activity_service.py tests/test_activity_service.py
git commit -m "Add activity tracking service"
```

---

### Task 4: Daily Summary Includes Activity Calories And Net Calories

**Files:**
- Modify: `app/core/schemas/summary.py`
- Modify: `app/core/services/summary_service.py`
- Modify: `tests/test_summary_service.py`

- [ ] **Step 1: Update failing summary test**

Add this test to `tests/test_summary_service.py`:

```python
from app.core.schemas.activity import ActivityEntryInput
from app.core.services.activity_service import record_activity


def test_daily_summary_includes_activity_and_net_calories() -> None:
    init_db()
    record_meal(
        RecordMealInput(
            date=date(2026, 7, 11),
            meal_type="breakfast",
            items=[MealItemInput(name="egg", calories=144, protein_g=12)],
        )
    )
    record_activity(
        ActivityEntryInput(
            date=date(2026, 7, 11),
            activity_type="walking",
            calories_burned=80,
            is_estimated=True,
        )
    )

    summary = get_daily_summary(date(2026, 7, 11))

    assert summary.activity_calories == 80
    assert summary.net_calories == 64
    assert summary.activity_count == 1
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv --cache-dir .uv-cache run pytest tests/test_summary_service.py -v
```

Expected: fail because summary output does not include activity fields.

- [ ] **Step 3: Update summary schema and service**

Add fields to `DailySummaryOutput`:

```python
activity_calories: float
net_calories: float
activity_count: int
```

Update `get_daily_summary()` to call `list_activities_for_date()` and calculate:

```python
activity_calories = sum(activity.calories_burned for activity in activities)
net_calories = total_calories - activity_calories
activity_count = len(activities)
```

- [ ] **Step 4: Run summary tests and full verification**

Run:

```bash
uv --cache-dir .uv-cache run pytest tests/test_summary_service.py -v
uv --cache-dir .uv-cache run pytest
uv --cache-dir .uv-cache run ruff check app tests
```

Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add app/core/schemas/summary.py app/core/services/summary_service.py tests/test_summary_service.py
git commit -m "Include activity calories in daily summary"
```

---

### Task 5: CLI Commands For Weight And Activity

**Files:**
- Modify: `app/cli/main.py`
- Modify: `tests/test_cli_commands.py`

- [ ] **Step 1: Add failing CLI tests**

Add tests for:

```bash
fitness-agent weight add --json '{"date":"today","weight_kg":79.6}'
fitness-agent weight trend --days 7
fitness-agent activity add --json '{"date":"today","activity_type":"walking","calories_burned":180,"is_estimated":true}'
fitness-agent summary today
```

Expected assertions:

- weight add output includes `79.6`.
- trend output includes `Latest weight`.
- activity add output includes `180`.
- summary output includes `Activity calories` and `Net calories`.

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv --cache-dir .uv-cache run pytest tests/test_cli_commands.py -v
```

Expected: fail because weight/activity CLI groups do not exist.

- [ ] **Step 3: Implement CLI groups**

Add Typer groups:

```python
weight_app = typer.Typer(help="Record body weight.")
activity_app = typer.Typer(help="Record activity calories.")
app.add_typer(weight_app, name="weight")
app.add_typer(activity_app, name="activity")
```

Implement:

- `weight add --json`
- `weight trend --days`
- `activity add --json`

Update summary output with activity and net calories.

- [ ] **Step 4: Run CLI tests and smoke commands**

Run:

```bash
uv --cache-dir .uv-cache run pytest tests/test_cli_commands.py -v
FITNESS_AGENT_DB_PATH=/tmp/fitness-agent-weight-activity.sqlite3 uv --cache-dir .uv-cache run fitness-agent dev reset-db --yes
FITNESS_AGENT_DB_PATH=/tmp/fitness-agent-weight-activity.sqlite3 uv --cache-dir .uv-cache run fitness-agent weight add --json '{"date":"today","weight_kg":79.6,"raw_text":"今天早上空腹 79.6kg"}'
FITNESS_AGENT_DB_PATH=/tmp/fitness-agent-weight-activity.sqlite3 uv --cache-dir .uv-cache run fitness-agent activity add --json '{"date":"today","activity_type":"walking","duration_minutes":40,"calories_burned":180,"is_estimated":true,"raw_text":"今天快走 40 分钟"}'
FITNESS_AGENT_DB_PATH=/tmp/fitness-agent-weight-activity.sqlite3 uv --cache-dir .uv-cache run fitness-agent summary today
```

Expected: all commands succeed.

- [ ] **Step 5: Full verification and commit**

Run:

```bash
uv --cache-dir .uv-cache run pytest
uv --cache-dir .uv-cache run ruff check app tests
```

Commit:

```bash
git add app/cli/main.py tests/test_cli_commands.py
git commit -m "Add weight and activity CLI commands"
```

---

### Task 6: MCP Tools And Skill Contracts For Weight And Activity

**Files:**
- Modify: `app/mcp/server.py`
- Modify: `tests/test_mcp_tools.py`
- Modify: `skill/SKILL.md`
- Modify: `skill/references/tool-contracts.md`
- Modify: `tests/test_skill_files.py`

- [ ] **Step 1: Add failing MCP and skill tests**

Update `tests/test_mcp_tools.py` to assert tools include:

```text
record_weight
get_weight_trend
record_activity
```

Add a test that calls:

- `record_weight`
- `get_weight_trend`
- `record_activity`
- `get_daily_summary`

and asserts summary has activity and net calories.

Update `tests/test_skill_files.py` to assert `record_weight`, `get_weight_trend`, and `record_activity` appear in skill files.

- [ ] **Step 2: Run tests to verify failure**

Run:

```bash
uv --cache-dir .uv-cache run pytest tests/test_mcp_tools.py tests/test_skill_files.py -v
```

Expected: fail because tools/contracts are missing.

- [ ] **Step 3: Implement MCP tools**

Add tools to `app/mcp/server.py`:

- `record_weight(weight: dict[str, Any])`
- `get_weight_trend(days: int = 7)`
- `record_activity(activity: dict[str, Any])`

Use existing schemas and services only.

- [ ] **Step 4: Update Skill and contracts**

Update `skill/SKILL.md` workflow to include:

- record body weight with `record_weight`
- record exercise/activity with `record_activity`
- use `get_weight_trend` for recent trend questions

Update `skill/references/tool-contracts.md` with JSON examples for the three new tools.

- [ ] **Step 5: Full verification and commit**

Run:

```bash
uv --cache-dir .uv-cache run pytest
uv --cache-dir .uv-cache run ruff check app tests
uv --cache-dir .uv-cache run python -c "from app.mcp.server import build_mcp_server; print([tool.name for tool in __import__('anyio').run(build_mcp_server().list_tools)])"
```

Expected: pass and tool list includes the new tools.

Commit:

```bash
git add app/mcp/server.py tests/test_mcp_tools.py skill/SKILL.md skill/references/tool-contracts.md tests/test_skill_files.py
git commit -m "Add weight and activity MCP tools"
```

---

### Task 7: Final Verification And Push

**Files:**
- No planned source changes unless verification reveals issues.

- [ ] **Step 1: Run full verification**

Run:

```bash
uv --cache-dir .uv-cache run pytest
uv --cache-dir .uv-cache run ruff check app tests
uv --cache-dir .uv-cache run fitness-agent --help
uv --cache-dir .uv-cache run python -c "from app.mcp.server import build_mcp_server; print(build_mcp_server().name)"
```

Expected:

- All tests pass.
- Ruff reports no issues.
- CLI help renders.
- MCP server builds.

- [ ] **Step 2: Push**

Run:

```bash
git status --branch --short
git push
```

Expected: remote `origin/main` receives all new commits.

---

## Self-Review

### Spec Coverage

- Weight recording through CLI/MCP: Tasks 2, 5, 6.
- Weight trend with latest and 7-day average: Tasks 2, 5, 6.
- Activity recording through CLI/MCP: Tasks 3, 5, 6.
- Daily summary activity and net calories: Task 4.
- Skill contracts update: Task 6.

### Intentional Deferrals

- Full workout programming.
- Exercise library and muscle-group mapping.
- Wearable device import.
- RAG.
- Food database lookup.
- Advanced weekly trend analysis beyond simple 7-day average.
