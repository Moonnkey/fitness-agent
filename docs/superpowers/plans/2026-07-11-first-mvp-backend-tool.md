# First MVP Backend Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first local backend-tool slice: profile storage, meal recording, daily summary, SQLite persistence, and CLI debugging commands.

**Architecture:** CLI commands parse user/debug input into Pydantic schemas, call `app/core/services`, and persist through SQLAlchemy models in SQLite. The backend stores structured nutrition fields plus `raw_text` and `metadata_json` so future Agent/MCP calls can preserve semi-structured context without changing the schema for every new detail.

**Tech Stack:** Python 3.12, Pydantic v2, SQLAlchemy 2, SQLite, Typer, pytest, ruff.

---

## Source Documents

- `AGENTS.md`
- `docs/mvp.md`
- `docs/architecture.md`

## Global Constraints

- Keep business logic in `app/core`.
- CLI must call `app/core/services` and must not contain summary or persistence logic.
- Default database path is `./data/fitness-agent.sqlite3`.
- `FITNESS_AGENT_DB_PATH` overrides the default database path.
- Store meal data as structured fields plus `raw_text` and `metadata_json`.
- Do not implement MCP, Skill, RAG, natural language parsing, weight entries, or activity entries in this slice.
- Use TDD: write the failing test, verify it fails, implement the minimal code, verify it passes.

## Planned File Structure

- Create `app/core/db/session.py`
  - Owns DB path resolution, engine creation, session creation, and table initialization.
- Create `app/core/models/base.py`
  - Defines SQLAlchemy `Base`.
- Create `app/core/models/profile.py`
  - Defines `UserProfile`.
- Create `app/core/models/meal.py`
  - Defines `Meal` and `MealItem`.
- Modify `app/core/models/__init__.py`
  - Imports models so table creation sees them.
- Create `app/core/schemas/common.py`
  - Defines date parsing helpers and reusable literal values.
- Create `app/core/schemas/profile.py`
  - Defines profile input/output schemas and calculated target output.
- Create `app/core/schemas/meal.py`
  - Defines meal item input/output and record meal schemas.
- Create `app/core/schemas/summary.py`
  - Defines daily summary output schemas.
- Create `app/core/services/profile_service.py`
  - Owns profile upsert, read, and target calculations.
- Create `app/core/services/meal_service.py`
  - Owns meal recording and date-based meal listing.
- Create `app/core/services/summary_service.py`
  - Owns daily summary aggregation.
- Modify `app/cli/main.py`
  - Adds `profile`, `meal`, `summary`, and `dev` command groups.
- Create `tests/conftest.py`
  - Provides isolated temp DB setup.
- Create `tests/test_profile_service.py`
  - Tests profile persistence and target calculation.
- Create `tests/test_meal_service.py`
  - Tests meal recording and semi-structured fields.
- Create `tests/test_summary_service.py`
  - Tests daily summary aggregation.
- Create `tests/test_cli_commands.py`
  - Tests CLI wiring for profile, meal JSON, summary, and reset guard.

---

### Task 1: Database Foundation

**Files:**
- Create: `app/core/models/base.py`
- Create: `app/core/db/session.py`
- Modify: `app/core/models/__init__.py`
- Create: `tests/conftest.py`
- Create: `tests/test_db_session.py`

- [ ] **Step 1: Write failing database tests**

Create `tests/test_db_session.py`:

```python
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
```

Create `tests/conftest.py`:

```python
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
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv run pytest tests/test_db_session.py -v
```

Expected: fail because `app.core.db.session` and its functions do not exist.

- [ ] **Step 3: Implement database foundation**

Create `app/core/models/base.py`:

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

Create `app/core/db/session.py`:

```python
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import os

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
```

Modify `app/core/models/__init__.py`:

```python
"""Persistence models for Fitness Agent."""

from app.core.models.base import Base

__all__ = ["Base"]
```

- [ ] **Step 4: Run test to verify pass**

Run:

```bash
uv run pytest tests/test_db_session.py -v
```

Expected: pass.

- [ ] **Step 5: Run lint**

Run:

```bash
uv run ruff check app tests
```

Expected: pass.

- [ ] **Step 6: Commit**

```bash
git add app/core/db/session.py app/core/models/base.py app/core/models/__init__.py tests/conftest.py tests/test_db_session.py
git commit -m "Add SQLite database foundation"
```

---

### Task 2: Profile Model, Schemas, Service, And Target Calculations

**Files:**
- Create: `app/core/models/profile.py`
- Modify: `app/core/models/__init__.py`
- Create: `app/core/schemas/profile.py`
- Create: `app/core/services/profile_service.py`
- Create: `tests/test_profile_service.py`

- [ ] **Step 1: Write failing profile tests**

Create `tests/test_profile_service.py`:

```python
from app.core.db.session import init_db
from app.core.schemas.profile import UserProfileInput
from app.core.services.profile_service import get_user_profile, update_user_profile


def test_update_user_profile_creates_and_updates_single_profile() -> None:
    init_db()

    created = update_user_profile(
        UserProfileInput(
            height_cm=175,
            weight_kg=80,
            age=30,
            sex="male",
            activity_level="moderate",
            goal_type="fat_loss",
            goal_weight_kg=72,
        )
    )
    updated = update_user_profile(
        UserProfileInput(
            height_cm=175,
            weight_kg=78,
            age=30,
            sex="male",
            activity_level="moderate",
            goal_type="fat_loss",
            goal_weight_kg=72,
            target_calories=2100,
            target_protein_g=150,
        )
    )

    assert created.id == updated.id
    assert updated.weight_kg == 78
    assert updated.target_calories == 2100
    assert updated.target_protein_g == 150


def test_get_user_profile_returns_none_when_missing() -> None:
    init_db()

    assert get_user_profile() is None


def test_profile_calculates_bmr_tdee_and_default_targets() -> None:
    init_db()

    profile = update_user_profile(
        UserProfileInput(
            height_cm=180,
            weight_kg=80,
            age=30,
            sex="male",
            activity_level="moderate",
            goal_type="fat_loss",
        )
    )

    assert profile.bmr is not None
    assert profile.tdee is not None
    assert profile.calculated_target_calories is not None
    assert profile.calculated_target_protein_g == 144
    assert profile.bmr == 1780
    assert profile.tdee == 2759
    assert profile.calculated_target_calories == 2309
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv run pytest tests/test_profile_service.py -v
```

Expected: fail because profile model, schemas, and service do not exist.

- [ ] **Step 3: Implement profile model**

Create `app/core/models/profile.py`:

```python
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models.base import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[str | None] = mapped_column(String(20), nullable=True)
    activity_level: Mapped[str | None] = mapped_column(String(30), nullable=True)
    goal_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    goal_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
```

Modify `app/core/models/__init__.py`:

```python
"""Persistence models for Fitness Agent."""

from app.core.models.base import Base
from app.core.models.profile import UserProfile

__all__ = ["Base", "UserProfile"]
```

- [ ] **Step 4: Implement profile schemas**

Create `app/core/schemas/profile.py`:

```python
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Sex = Literal["male", "female"]
ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]
GoalType = Literal["fat_loss", "muscle_gain", "maintenance", "recomposition"]


class UserProfileInput(BaseModel):
    height_cm: float | None = Field(default=None, gt=0)
    weight_kg: float | None = Field(default=None, gt=0)
    age: int | None = Field(default=None, gt=0)
    sex: Sex | None = None
    activity_level: ActivityLevel | None = None
    goal_type: GoalType | None = None
    goal_weight_kg: float | None = Field(default=None, gt=0)
    target_calories: float | None = Field(default=None, gt=0)
    target_protein_g: float | None = Field(default=None, gt=0)


class UserProfileOutput(UserProfileInput):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bmr: int | None = None
    tdee: int | None = None
    calculated_target_calories: int | None = None
    calculated_target_protein_g: int | None = None
```

- [ ] **Step 5: Implement profile service**

Create `app/core/services/profile_service.py`:

```python
from app.core.db.session import session_scope
from app.core.models.profile import UserProfile
from app.core.schemas.profile import UserProfileInput, UserProfileOutput

ACTIVITY_FACTORS = {
    "sedentary": 1.2,
    "light": 1.375,
    "moderate": 1.55,
    "active": 1.725,
    "very_active": 1.9,
}


def _calculate_bmr(input_data: UserProfileInput) -> int | None:
    if (
        input_data.height_cm is None
        or input_data.weight_kg is None
        or input_data.age is None
        or input_data.sex is None
    ):
        return None

    if input_data.sex == "male":
        value = 10 * input_data.weight_kg + 6.25 * input_data.height_cm - 5 * input_data.age + 5
    else:
        value = 10 * input_data.weight_kg + 6.25 * input_data.height_cm - 5 * input_data.age - 161
    return round(value)


def _calculate_tdee(input_data: UserProfileInput, bmr: int | None) -> int | None:
    if bmr is None or input_data.activity_level is None:
        return None
    return round(bmr * ACTIVITY_FACTORS[input_data.activity_level])


def _calculate_target_calories(input_data: UserProfileInput, tdee: int | None) -> int | None:
    if input_data.target_calories is not None:
        return round(input_data.target_calories)
    if tdee is None:
        return None
    if input_data.goal_type == "fat_loss":
        return max(round(tdee - 450), 1200)
    if input_data.goal_type == "muscle_gain":
        return round(tdee + 250)
    return tdee


def _calculate_target_protein(input_data: UserProfileInput) -> int | None:
    if input_data.target_protein_g is not None:
        return round(input_data.target_protein_g)
    if input_data.weight_kg is None:
        return None
    if input_data.goal_type == "muscle_gain":
        return round(input_data.weight_kg * 1.8)
    return round(input_data.weight_kg * 1.8)


def _to_output(profile: UserProfile) -> UserProfileOutput:
    input_data = UserProfileInput.model_validate(profile, from_attributes=True)
    bmr = _calculate_bmr(input_data)
    tdee = _calculate_tdee(input_data, bmr)
    return UserProfileOutput(
        id=profile.id,
        height_cm=profile.height_cm,
        weight_kg=profile.weight_kg,
        age=profile.age,
        sex=profile.sex,
        activity_level=profile.activity_level,
        goal_type=profile.goal_type,
        goal_weight_kg=profile.goal_weight_kg,
        target_calories=profile.target_calories,
        target_protein_g=profile.target_protein_g,
        bmr=bmr,
        tdee=tdee,
        calculated_target_calories=_calculate_target_calories(input_data, tdee),
        calculated_target_protein_g=_calculate_target_protein(input_data),
    )


def get_user_profile() -> UserProfileOutput | None:
    with session_scope() as session:
        profile = session.get(UserProfile, 1)
        if profile is None:
            return None
        return _to_output(profile)


def update_user_profile(input_data: UserProfileInput) -> UserProfileOutput:
    with session_scope() as session:
        profile = session.get(UserProfile, 1)
        if profile is None:
            profile = UserProfile(id=1)
            session.add(profile)

        for field, value in input_data.model_dump().items():
            setattr(profile, field, value)

        session.flush()
        return _to_output(profile)
```

- [ ] **Step 6: Run profile tests**

Run:

```bash
uv run pytest tests/test_profile_service.py -v
```

Expected: pass.

- [ ] **Step 7: Run full tests and lint**

Run:

```bash
uv run pytest
uv run ruff check app tests
```

Expected: pass.

- [ ] **Step 8: Commit**

```bash
git add app/core/models app/core/schemas/profile.py app/core/services/profile_service.py tests/test_profile_service.py
git commit -m "Add user profile service"
```

---

### Task 3: Meal Model, Schemas, And Recording Service

**Files:**
- Create: `app/core/models/meal.py`
- Modify: `app/core/models/__init__.py`
- Create: `app/core/schemas/common.py`
- Create: `app/core/schemas/meal.py`
- Create: `app/core/services/meal_service.py`
- Create: `tests/test_meal_service.py`

- [ ] **Step 1: Write failing meal tests**

Create `tests/test_meal_service.py`:

```python
from datetime import date

from app.core.db.session import init_db
from app.core.schemas.meal import MealItemInput, RecordMealInput
from app.core.services.meal_service import list_meals_for_date, record_meal


def test_record_meal_preserves_items_raw_text_and_metadata() -> None:
    init_db()

    meal = record_meal(
        RecordMealInput(
            date=date(2026, 7, 11),
            meal_type="breakfast",
            raw_text="早餐吃了两个鸡蛋",
            metadata={"agent": "codex", "confidence": 0.8},
            items=[
                MealItemInput(
                    name="鸡蛋",
                    quantity=2,
                    unit="个",
                    calories=144,
                    protein_g=12,
                    carbs_g=1,
                    fat_g=10,
                    is_estimated=True,
                    source="agent_estimate",
                    raw_text="两个鸡蛋",
                    metadata={"assumption": "普通水煮蛋"},
                )
            ],
        )
    )

    assert meal.id > 0
    assert meal.raw_text == "早餐吃了两个鸡蛋"
    assert meal.metadata == {"agent": "codex", "confidence": 0.8}
    assert meal.total_calories == 144
    assert meal.estimated_item_count == 1
    assert meal.items[0].metadata == {"assumption": "普通水煮蛋"}


def test_list_meals_for_date_filters_by_date() -> None:
    init_db()
    record_meal(
        RecordMealInput(
            date=date(2026, 7, 11),
            meal_type="breakfast",
            items=[MealItemInput(name="egg", calories=100)],
        )
    )
    record_meal(
        RecordMealInput(
            date=date(2026, 7, 12),
            meal_type="lunch",
            items=[MealItemInput(name="rice", calories=200)],
        )
    )

    meals = list_meals_for_date(date(2026, 7, 11))

    assert len(meals) == 1
    assert meals[0].meal_type == "breakfast"
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv run pytest tests/test_meal_service.py -v
```

Expected: fail because meal model, schemas, and service do not exist.

- [ ] **Step 3: Implement meal model**

Create `app/core/models/meal.py`:

```python
from datetime import date, datetime
from typing import Any

from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models.base import Base


class Meal(Base):
    __tablename__ = "meals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    meal_type: Mapped[str] = mapped_column(String(30))
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    items: Mapped[list["MealItem"]] = relationship(
        back_populates="meal",
        cascade="all, delete-orphan",
    )


class MealItem(Base):
    __tablename__ = "meal_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    meal_id: Mapped[int] = mapped_column(ForeignKey("meals.id"))
    name: Mapped[str] = mapped_column(String(200))
    quantity: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    grams: Mapped[float | None] = mapped_column(Float, nullable=True)
    calories: Mapped[float] = mapped_column(Float, default=0)
    protein_g: Mapped[float] = mapped_column(Float, default=0)
    carbs_g: Mapped[float] = mapped_column(Float, default=0)
    fat_g: Mapped[float] = mapped_column(Float, default=0)
    source: Mapped[str] = mapped_column(String(50), default="user")
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    meal: Mapped[Meal] = relationship(back_populates="items")
```

Modify `app/core/models/__init__.py`:

```python
"""Persistence models for Fitness Agent."""

from app.core.models.base import Base
from app.core.models.meal import Meal, MealItem
from app.core.models.profile import UserProfile

__all__ = ["Base", "Meal", "MealItem", "UserProfile"]
```

- [ ] **Step 4: Implement meal schemas**

Create `app/core/schemas/common.py`:

```python
from datetime import date


def parse_date_value(value: str | date | None) -> date:
    if value is None or value == "today":
        return date.today()
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)
```

Create `app/core/schemas/meal.py`:

```python
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

MealType = Literal["breakfast", "lunch", "dinner", "snack", "other"]
NutritionSource = Literal["user", "manual_estimate", "food_database", "agent_estimate"]


class MealItemInput(BaseModel):
    name: str
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = None
    grams: float | None = Field(default=None, gt=0)
    calories: float = Field(default=0, ge=0)
    protein_g: float = Field(default=0, ge=0)
    carbs_g: float = Field(default=0, ge=0)
    fat_g: float = Field(default=0, ge=0)
    source: NutritionSource = "user"
    is_estimated: bool = False
    raw_text: str | None = None
    metadata: dict[str, Any] | None = None
    note: str | None = None


class RecordMealInput(BaseModel):
    date: date
    meal_type: MealType
    raw_text: str | None = None
    metadata: dict[str, Any] | None = None
    note: str | None = None
    items: list[MealItemInput] = Field(min_length=1)


class MealItemOutput(MealItemInput):
    model_config = ConfigDict(from_attributes=True)

    id: int


class MealOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    meal_type: MealType
    raw_text: str | None = None
    metadata: dict[str, Any] | None = None
    note: str | None = None
    items: list[MealItemOutput]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    estimated_item_count: int
```

- [ ] **Step 5: Implement meal service**

Create `app/core/services/meal_service.py`:

```python
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.db.session import session_scope
from app.core.models.meal import Meal, MealItem
from app.core.schemas.meal import MealItemOutput, MealOutput, RecordMealInput


def _to_output(meal: Meal) -> MealOutput:
    items = [
        MealItemOutput(
            id=item.id,
            name=item.name,
            quantity=item.quantity,
            unit=item.unit,
            grams=item.grams,
            calories=item.calories,
            protein_g=item.protein_g,
            carbs_g=item.carbs_g,
            fat_g=item.fat_g,
            source=item.source,
            is_estimated=item.is_estimated,
            raw_text=item.raw_text,
            metadata=item.metadata_json,
            note=item.note,
        )
        for item in meal.items
    ]
    return MealOutput(
        id=meal.id,
        date=meal.date,
        meal_type=meal.meal_type,
        raw_text=meal.raw_text,
        metadata=meal.metadata_json,
        note=meal.note,
        items=items,
        total_calories=sum(item.calories for item in items),
        total_protein_g=sum(item.protein_g for item in items),
        total_carbs_g=sum(item.carbs_g for item in items),
        total_fat_g=sum(item.fat_g for item in items),
        estimated_item_count=sum(1 for item in items if item.is_estimated),
    )


def record_meal(input_data: RecordMealInput) -> MealOutput:
    with session_scope() as session:
        meal = Meal(
            date=input_data.date,
            meal_type=input_data.meal_type,
            raw_text=input_data.raw_text,
            metadata_json=input_data.metadata,
            note=input_data.note,
        )
        meal.items = [
            MealItem(
                name=item.name,
                quantity=item.quantity,
                unit=item.unit,
                grams=item.grams,
                calories=item.calories,
                protein_g=item.protein_g,
                carbs_g=item.carbs_g,
                fat_g=item.fat_g,
                source=item.source,
                is_estimated=item.is_estimated,
                raw_text=item.raw_text,
                metadata_json=item.metadata,
                note=item.note,
            )
            for item in input_data.items
        ]
        session.add(meal)
        session.flush()
        return _to_output(meal)


def list_meals_for_date(target_date: date) -> list[MealOutput]:
    with session_scope() as session:
        meals = (
            session.execute(
                select(Meal)
                .where(Meal.date == target_date)
                .options(selectinload(Meal.items))
                .order_by(Meal.id)
            )
            .scalars()
            .all()
        )
        return [_to_output(meal) for meal in meals]
```

- [ ] **Step 6: Run meal tests**

Run:

```bash
uv run pytest tests/test_meal_service.py -v
```

Expected: pass.

- [ ] **Step 7: Run full tests and lint**

Run:

```bash
uv run pytest
uv run ruff check app tests
```

Expected: pass.

- [ ] **Step 8: Commit**

```bash
git add app/core/models app/core/schemas app/core/services/meal_service.py tests/test_meal_service.py
git commit -m "Add meal recording service"
```

---

### Task 4: Daily Summary Service

**Files:**
- Create: `app/core/schemas/summary.py`
- Create: `app/core/services/summary_service.py`
- Create: `tests/test_summary_service.py`

- [ ] **Step 1: Write failing summary tests**

Create `tests/test_summary_service.py`:

```python
from datetime import date

from app.core.db.session import init_db
from app.core.schemas.meal import MealItemInput, RecordMealInput
from app.core.schemas.profile import UserProfileInput
from app.core.services.meal_service import record_meal
from app.core.services.profile_service import update_user_profile
from app.core.services.summary_service import get_daily_summary


def test_empty_day_summary_returns_zero_totals() -> None:
    init_db()

    summary = get_daily_summary(date(2026, 7, 11))

    assert summary.total_calories == 0
    assert summary.meal_count == 0
    assert summary.estimated_item_count == 0


def test_daily_summary_totals_meals_and_targets() -> None:
    init_db()
    update_user_profile(
        UserProfileInput(
            height_cm=180,
            weight_kg=80,
            age=30,
            sex="male",
            activity_level="moderate",
            goal_type="fat_loss",
            target_calories=2200,
            target_protein_g=150,
        )
    )
    record_meal(
        RecordMealInput(
            date=date(2026, 7, 11),
            meal_type="breakfast",
            items=[
                MealItemInput(name="egg", calories=144, protein_g=12, carbs_g=1, fat_g=10),
                MealItemInput(
                    name="rice",
                    calories=260,
                    protein_g=5,
                    carbs_g=58,
                    fat_g=1,
                    is_estimated=True,
                    source="agent_estimate",
                ),
            ],
        )
    )

    summary = get_daily_summary(date(2026, 7, 11))

    assert summary.total_calories == 404
    assert summary.total_protein_g == 17
    assert summary.total_carbs_g == 59
    assert summary.total_fat_g == 11
    assert summary.target_calories == 2200
    assert summary.remaining_calories == 1796
    assert summary.target_protein_g == 150
    assert summary.meal_count == 1
    assert summary.estimated_item_count == 1
    assert summary.meals[0].total_calories == 404
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv run pytest tests/test_summary_service.py -v
```

Expected: fail because summary schema and service do not exist.

- [ ] **Step 3: Implement summary schemas**

Create `app/core/schemas/summary.py`:

```python
from datetime import date

from pydantic import BaseModel

from app.core.schemas.meal import MealOutput


class DailySummaryOutput(BaseModel):
    date: date
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    target_calories: float | None
    remaining_calories: float | None
    target_protein_g: float | None
    meal_count: int
    estimated_item_count: int
    meals: list[MealOutput]
```

- [ ] **Step 4: Implement summary service**

Create `app/core/services/summary_service.py`:

```python
from datetime import date

from app.core.schemas.summary import DailySummaryOutput
from app.core.services.meal_service import list_meals_for_date
from app.core.services.profile_service import get_user_profile


def get_daily_summary(target_date: date) -> DailySummaryOutput:
    meals = list_meals_for_date(target_date)
    total_calories = sum(meal.total_calories for meal in meals)
    total_protein_g = sum(meal.total_protein_g for meal in meals)
    total_carbs_g = sum(meal.total_carbs_g for meal in meals)
    total_fat_g = sum(meal.total_fat_g for meal in meals)
    estimated_item_count = sum(meal.estimated_item_count for meal in meals)

    profile = get_user_profile()
    target_calories = None
    target_protein_g = None
    if profile is not None:
        target_calories = profile.target_calories or profile.calculated_target_calories
        target_protein_g = profile.target_protein_g or profile.calculated_target_protein_g

    remaining_calories = None
    if target_calories is not None:
        remaining_calories = target_calories - total_calories

    return DailySummaryOutput(
        date=target_date,
        total_calories=total_calories,
        total_protein_g=total_protein_g,
        total_carbs_g=total_carbs_g,
        total_fat_g=total_fat_g,
        target_calories=target_calories,
        remaining_calories=remaining_calories,
        target_protein_g=target_protein_g,
        meal_count=len(meals),
        estimated_item_count=estimated_item_count,
        meals=meals,
    )
```

- [ ] **Step 5: Run summary tests**

Run:

```bash
uv run pytest tests/test_summary_service.py -v
```

Expected: pass.

- [ ] **Step 6: Run full tests and lint**

Run:

```bash
uv run pytest
uv run ruff check app tests
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add app/core/schemas/summary.py app/core/services/summary_service.py tests/test_summary_service.py
git commit -m "Add daily summary service"
```

---

### Task 5: CLI Commands For Profile, Meal JSON, Summary, And Reset

**Files:**
- Modify: `app/cli/main.py`
- Create: `tests/test_cli_commands.py`
- Modify: `tests/test_cli.py` if command help expectations need adjustment.
- Modify: `.gitignore` to ignore `data/`.

- [ ] **Step 1: Write failing CLI tests**

Create `tests/test_cli_commands.py`:

```python
import json

from typer.testing import CliRunner

from app.cli.main import app
from app.core.db.session import init_db


def test_profile_set_and_show_commands() -> None:
    runner = CliRunner()

    set_result = runner.invoke(
        app,
        [
            "profile",
            "set",
            "--height-cm",
            "180",
            "--weight-kg",
            "80",
            "--age",
            "30",
            "--sex",
            "male",
            "--activity-level",
            "moderate",
            "--goal-type",
            "fat_loss",
        ],
    )
    show_result = runner.invoke(app, ["profile", "show"])

    assert set_result.exit_code == 0
    assert show_result.exit_code == 0
    assert "fat_loss" in show_result.output
    assert "target calories" in show_result.output.lower()


def test_meal_add_json_and_summary_today() -> None:
    init_db()
    runner = CliRunner()
    payload = {
        "date": "today",
        "meal_type": "breakfast",
        "raw_text": "早餐吃了两个鸡蛋",
        "items": [
            {
                "name": "鸡蛋",
                "quantity": 2,
                "unit": "个",
                "calories": 144,
                "protein_g": 12,
                "carbs_g": 1,
                "fat_g": 10,
                "is_estimated": True,
                "source": "agent_estimate",
                "metadata": {"assumption": "普通水煮蛋"},
            }
        ],
    }

    meal_result = runner.invoke(app, ["meal", "add", "--json", json.dumps(payload)])
    summary_result = runner.invoke(app, ["summary", "today"])

    assert meal_result.exit_code == 0
    assert "144" in meal_result.output
    assert summary_result.exit_code == 0
    assert "144" in summary_result.output
    assert "estimated items" in summary_result.output.lower()


def test_dev_reset_db_requires_yes() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["dev", "reset-db"])

    assert result.exit_code != 0
    assert "--yes" in result.output
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv run pytest tests/test_cli_commands.py -v
```

Expected: fail because command groups do not exist.

- [ ] **Step 3: Implement CLI commands**

Replace `app/cli/main.py` with:

```python
from datetime import date
import json
from pathlib import Path
from typing import Annotated, Any

import typer

from app.core.db.session import get_database_path, init_db, reset_engine_cache
from app.core.schemas.common import parse_date_value
from app.core.schemas.meal import MealItemInput, RecordMealInput
from app.core.schemas.profile import ActivityLevel, GoalType, Sex, UserProfileInput
from app.core.services.meal_service import record_meal
from app.core.services.profile_service import get_user_profile, update_user_profile
from app.core.services.summary_service import get_daily_summary

app = typer.Typer(help="Local-first fitness and fat-loss assistant.")
profile_app = typer.Typer(help="Manage the local user profile.")
meal_app = typer.Typer(help="Record meals.")
summary_app = typer.Typer(help="Show daily summaries.")
dev_app = typer.Typer(help="Development utilities.")

app.add_typer(profile_app, name="profile")
app.add_typer(meal_app, name="meal")
app.add_typer(summary_app, name="summary")
app.add_typer(dev_app, name="dev")


@app.callback()
def main() -> None:
    """Fitness Agent command line interface."""


@profile_app.command("set")
def profile_set(
    height_cm: Annotated[float | None, typer.Option()] = None,
    weight_kg: Annotated[float | None, typer.Option()] = None,
    age: Annotated[int | None, typer.Option()] = None,
    sex: Annotated[Sex | None, typer.Option()] = None,
    activity_level: Annotated[ActivityLevel | None, typer.Option()] = None,
    goal_type: Annotated[GoalType | None, typer.Option()] = None,
    goal_weight_kg: Annotated[float | None, typer.Option()] = None,
    target_calories: Annotated[float | None, typer.Option()] = None,
    target_protein_g: Annotated[float | None, typer.Option()] = None,
) -> None:
    init_db()
    output = update_user_profile(
        UserProfileInput(
            height_cm=height_cm,
            weight_kg=weight_kg,
            age=age,
            sex=sex,
            activity_level=activity_level,
            goal_type=goal_type,
            goal_weight_kg=goal_weight_kg,
            target_calories=target_calories,
            target_protein_g=target_protein_g,
        )
    )
    typer.echo(f"Profile saved: id={output.id}, goal_type={output.goal_type}")
    typer.echo(f"Target calories: {output.target_calories or output.calculated_target_calories}")
    typer.echo(f"Target protein g: {output.target_protein_g or output.calculated_target_protein_g}")


@profile_app.command("show")
def profile_show() -> None:
    init_db()
    output = get_user_profile()
    if output is None:
        typer.echo("No profile found.")
        return
    typer.echo(f"Profile id: {output.id}")
    typer.echo(f"Height cm: {output.height_cm}")
    typer.echo(f"Weight kg: {output.weight_kg}")
    typer.echo(f"Goal type: {output.goal_type}")
    typer.echo(f"BMR: {output.bmr}")
    typer.echo(f"TDEE: {output.tdee}")
    typer.echo(f"Target calories: {output.target_calories or output.calculated_target_calories}")
    typer.echo(f"Target protein g: {output.target_protein_g or output.calculated_target_protein_g}")


def _record_meal_input_from_json(payload: str) -> RecordMealInput:
    data: dict[str, Any] = json.loads(payload)
    data["date"] = parse_date_value(data.get("date"))
    return RecordMealInput.model_validate(data)


def _record_meal_input_from_items(
    date_value: str,
    meal_type: str,
    item_values: list[str],
) -> RecordMealInput:
    items = []
    for value in item_values:
        parts = [part.strip() for part in value.split(",")]
        if len(parts) != 7:
            raise typer.BadParameter(
                "item must use format name,quantity,unit,calories,protein_g,carbs_g,fat_g"
            )
        name, quantity, unit, calories, protein_g, carbs_g, fat_g = parts
        items.append(
            MealItemInput(
                name=name,
                quantity=float(quantity),
                unit=unit,
                calories=float(calories),
                protein_g=float(protein_g),
                carbs_g=float(carbs_g),
                fat_g=float(fat_g),
            )
        )
    return RecordMealInput(date=parse_date_value(date_value), meal_type=meal_type, items=items)


@meal_app.command("add")
def meal_add(
    json_payload: Annotated[str | None, typer.Option("--json")] = None,
    date_value: Annotated[str, typer.Option("--date")] = "today",
    meal_type: Annotated[str, typer.Option("--type")] = "other",
    item: Annotated[list[str] | None, typer.Option("--item")] = None,
) -> None:
    init_db()
    if json_payload is not None:
        input_data = _record_meal_input_from_json(json_payload)
    elif item:
        input_data = _record_meal_input_from_items(date_value, meal_type, item)
    else:
        raise typer.BadParameter("provide --json or at least one --item")

    meal = record_meal(input_data)
    typer.echo(f"Meal recorded: id={meal.id}, type={meal.meal_type}")
    typer.echo(f"Total calories: {meal.total_calories}")
    typer.echo(f"Estimated items: {meal.estimated_item_count}")


def _print_summary(target_date: date) -> None:
    init_db()
    summary = get_daily_summary(target_date)
    typer.echo(f"Date: {summary.date.isoformat()}")
    typer.echo(f"Total calories: {summary.total_calories}")
    typer.echo(f"Protein g: {summary.total_protein_g}")
    typer.echo(f"Carbs g: {summary.total_carbs_g}")
    typer.echo(f"Fat g: {summary.total_fat_g}")
    typer.echo(f"Target calories: {summary.target_calories}")
    typer.echo(f"Remaining calories: {summary.remaining_calories}")
    typer.echo(f"Target protein g: {summary.target_protein_g}")
    typer.echo(f"Meal count: {summary.meal_count}")
    typer.echo(f"Estimated items: {summary.estimated_item_count}")
    for meal in summary.meals:
        typer.echo(f"- {meal.meal_type}: {meal.total_calories} kcal, {len(meal.items)} items")


@summary_app.command("today")
def summary_today() -> None:
    _print_summary(date.today())


@summary_app.command("date")
def summary_date(date_value: str) -> None:
    _print_summary(parse_date_value(date_value))


@dev_app.command("reset-db")
def reset_db(yes: Annotated[bool, typer.Option("--yes")] = False) -> None:
    if not yes:
        raise typer.BadParameter("Refusing to reset database without --yes")
    db_path = get_database_path()
    reset_engine_cache()
    if db_path.exists():
        Path(db_path).unlink()
    init_db()
    typer.echo(f"Database reset: {db_path}")


if __name__ == "__main__":
    app()
```

Modify `.gitignore` to include:

```gitignore
data/
```

- [ ] **Step 4: Run CLI command tests**

Run:

```bash
uv run pytest tests/test_cli_commands.py -v
```

Expected: pass.

- [ ] **Step 5: Manually verify CLI smoke path**

Run:

```bash
FITNESS_AGENT_DB_PATH=/tmp/fitness-agent-plan-smoke.sqlite3 uv run fitness-agent dev reset-db --yes
FITNESS_AGENT_DB_PATH=/tmp/fitness-agent-plan-smoke.sqlite3 uv run fitness-agent profile set --height-cm 180 --weight-kg 80 --age 30 --sex male --activity-level moderate --goal-type fat_loss
FITNESS_AGENT_DB_PATH=/tmp/fitness-agent-plan-smoke.sqlite3 uv run fitness-agent meal add --json '{"date":"today","meal_type":"breakfast","raw_text":"早餐吃了两个鸡蛋","items":[{"name":"鸡蛋","quantity":2,"unit":"个","calories":144,"protein_g":12,"carbs_g":1,"fat_g":10,"is_estimated":true,"source":"agent_estimate","metadata":{"assumption":"普通水煮蛋"}}]}'
FITNESS_AGENT_DB_PATH=/tmp/fitness-agent-plan-smoke.sqlite3 uv run fitness-agent summary today
```

Expected:

- reset command prints database reset.
- profile command prints saved profile and target values.
- meal command prints total calories `144`.
- summary command prints total calories `144` and estimated items `1`.

- [ ] **Step 6: Run full tests and lint**

Run:

```bash
uv run pytest
uv run ruff check app tests
```

Expected: pass.

- [ ] **Step 7: Commit**

```bash
git add app/cli/main.py .gitignore tests/test_cli_commands.py tests/test_cli.py
git commit -m "Add MVP CLI commands"
```

---

### Task 6: Final Verification And Push

**Files:**
- No planned source changes unless verification reveals issues.

- [ ] **Step 1: Run full verification**

Run:

```bash
uv run pytest
uv run ruff check app tests
uv run fitness-agent --help
```

Expected:

- All tests pass.
- Ruff reports no issues.
- CLI help renders.

- [ ] **Step 2: Inspect Git status and commits**

Run:

```bash
git status --branch --short
git log --oneline --decorate --max-count=8
```

Expected:

- Working tree clean.
- `main` has task commits ahead of or aligned with `origin/main`.

- [ ] **Step 3: Push**

Run:

```bash
git push
```

Expected: remote `origin/main` receives the new commits.

---

## Self-Review

### Spec Coverage

- Local-first backend tool: covered by Tasks 1-5.
- SQLite setup and environment override: Task 1.
- Profile with goal type and BMR/TDEE-style target calculation: Task 2.
- Meal and meal item storage with structured fields, `raw_text`, and `metadata_json`: Task 3.
- Daily summary with calories, macros, target, remaining calories, meal count, per-meal totals, and estimated item count: Task 4.
- CLI JSON input and manual item debugging input: Task 5.
- Reset database with required `--yes`: Task 5.
- Tests and lint verification: every task.

### Intentional Deferrals

- MCP tools.
- Skill.
- RAG.
- Natural language parsing.
- Weight entries.
- Activity entries.
- Full coaching advice.

### Placeholder Scan

This plan contains no `TBD`, `TODO`, or "implement later" placeholders in implementation steps. Deferred features are explicitly listed as non-goals for this slice.
