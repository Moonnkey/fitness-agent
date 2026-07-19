# Fitness Agent Architecture

## Purpose

This document defines the MVP architecture for Fitness Agent. It should guide the first implementation phase without over-designing future features.

The MVP should prove a local-first backend-tool loop:

```text
Agent-shaped structured or semi-structured input
  -> Pydantic schema validation
  -> core service
  -> SQLAlchemy persistence
  -> SQLite
  -> summary output
```

The CLI is a development and debugging interface. The long-term primary caller is an agent such as Codex through MCP tools. MCP tools will later call the same schemas and core services.

## Design Principles

- Keep business logic in `app/core`.
- Keep interface layers thin.
- Make CLI and MCP share the same core services.
- Prefer explicit structured input at service boundaries.
- Preserve semi-structured context with `raw_text` and `metadata_json`.
- Store estimates with enough metadata to explain uncertainty.
- Keep the first database schema small and useful.
- Add RAG only after local records and summaries work.

## Layers

### CLI Layer

Location: `app/cli`

Responsibilities:

- Parse command-line arguments.
- Convert arguments into Pydantic schemas.
- Call core services.
- Render concise human-readable output.

The CLI must not contain calorie calculation, summary, or persistence logic. For MVP debugging, prefer JSON input because it mirrors future agent/MCP payloads. Simple item flags can also exist for manual testing.

### MCP Layer

Location: `app/mcp`

Responsibilities:

- Expose tools for agents.
- Validate tool inputs using Pydantic schemas.
- Call core services.
- Return structured tool results.

MCP should be added after the CLI and core services are working.

### Core Schemas

Location: `app/core/schemas`

Responsibilities:

- Define external input and output contracts.
- Reuse schemas across CLI, MCP, tests, and future API endpoints.

Initial schemas:

- `UserProfileInput`
- `UserProfileOutput`
- `MealItemInput`
- `RecordMealInput`
- `MealOutput`
- `DailySummaryOutput`
- `WeightEntryInput`
- `ActivityEntryInput`

### Core Services

Location: `app/core/services`

Responsibilities:

- Own business behavior.
- Validate business rules that are not simple type validation.
- Coordinate persistence.
- Return Pydantic outputs or simple domain results.

Initial services:

- `profile_service.py`
- `meal_service.py`
- `summary_service.py`
- `weight_service.py`
- `activity_service.py`
- `record_service.py`
- `report_service.py`

`record_service.py` owns cross-record history lookup, single-record detail lookup,
partial updates, and hard deletion. Type-specific duplicate checks stay near the
type-specific recording services:

- `meal_service.py` checks likely duplicate meals.
- `weight_service.py` checks likely duplicate weight entries.
- `activity_service.py` checks likely duplicate activities.

Duplicate checks are advisory. The backend returns warnings but does not silently
block recording; the agent should ask the user when intent is unclear.

Update behavior:

- `get_record(record_type, record_id)` returns one meal, meal item, weight entry, or activity entry.
- `update_record(record_type, record_id, patch)` applies partial updates and returns `changed_fields`.
- Updating meal item quantity does not automatically recalculate calories or macros.
- Meal updates may use `items_append` to add food or `items_replace` to replace all meal items.
- Edited records keep `updated_at`; full audit logs are out of scope for the MVP.

Report behavior:

- `get_weekly_summary(end_date, days=7)` returns a Chinese `report_text` and structured `daily_points`.
- `get_daily_guidance(date)` returns day-level text guidance plus remaining calorie/protein fields.
- `daily_points` are intentionally chart-friendly for a future frontend, but the MVP does not render charts.
- Guidance remains general coaching advice and does not generate medical advice or precise meal plans.

### Persistence Layer

Location: `app/core/db` and `app/core/models`

Responsibilities:

- Configure SQLite engine and sessions.
- Define SQLAlchemy models.
- Create tables for local MVP.
- Keep database code out of CLI and MCP.

## Database Choice

Use SQLite for the MVP.

Default database path:

```text
./data/fitness-agent.sqlite3
```

The database path can be overridden with:

```text
FITNESS_AGENT_DB_PATH=/tmp/fitness-agent-test.sqlite3
```

The `data/` directory should be ignored by Git. Tests should use temporary SQLite files or in-memory databases.

Because the MVP does not use Alembic yet, `init_db()` may apply small SQLite-only
compatibility upgrades for local schema additions, such as adding missing `updated_at`
columns to existing local tables.

## Initial Database Models

### UserProfile

Purpose: store local user settings and goal information.

Fields:

- `id`
- `height_cm`
- `weight_kg`
- `age`
- `sex`
- `activity_level`
- `goal_type`
- `goal_weight_kg`
- `target_calories`
- `target_protein_g`
- `created_at`
- `updated_at`

MVP assumption: single local user. Store one profile row and update it.

Allowed `goal_type` values:

- `fat_loss`
- `muscle_gain`
- `maintenance`
- `recomposition`

Target calculation rules:

- Manual `target_calories` and `target_protein_g` take precedence.
- If profile data is sufficient, calculate BMR with Mifflin-St Jeor.
- Calculate TDEE as `BMR * activity_factor`.
- For MVP, expose calculated values but do not generate a full diet plan.

### Meal

Purpose: group meal items by date and meal type.

Fields:

- `id`
- `date`
- `meal_type`
- `raw_text`
- `metadata_json`
- `note`
- `created_at`
- `updated_at`

Allowed `meal_type` values:

- `breakfast`
- `lunch`
- `dinner`
- `snack`
- `other`

### MealItem

Purpose: store food item nutrition values.

Fields:

- `id`
- `meal_id`
- `name`
- `quantity`
- `unit`
- `grams`
- `calories`
- `protein_g`
- `carbs_g`
- `fat_g`
- `source`
- `is_estimated`
- `raw_text`
- `metadata_json`
- `note`
- `created_at`
- `updated_at`

Source examples:

- `user`
- `manual_estimate`
- `food_database`
- `agent_estimate`

Meal storage should be both structured and semi-structured:

- Structured fields support totals and summaries.
- `raw_text` preserves the user's original wording or the agent's source text.
- `metadata_json` preserves assumptions, confidence, cooking method, brand, prompt context, or any future fields that do not deserve first-class columns yet.

The backend does not parse natural language in the first slice. An agent may parse and estimate values, then send structured fields plus `raw_text` and `metadata_json`.

### WeightEntry

Purpose: store body weight observations.

Fields:

- `id`
- `date`
- `weight_kg`
- `raw_text`
- `metadata_json`
- `note`
- `created_at`

Third-stage scope: implement weight recording and a simple trend summary with latest weight and 7-day average.

### ActivityEntry

Purpose: store simple activity or workout calorie expenditure.

Fields:

- `id`
- `date`
- `activity_type`
- `duration_minutes`
- `calories_burned`
- `is_estimated`
- `raw_text`
- `metadata_json`
- `note`
- `created_at`

Third-stage scope: implement simple activity recording. Do not implement structured strength programming, exercise libraries, muscle groups, or periodization yet.

## First Implementation Slice

Implement only:

- SQLite setup.
- `UserProfile`.
- `Meal`.
- `MealItem`.
- `profile_service`.
- `meal_service`.
- `summary_service`.
- CLI commands for profile, meal, and summary.
- Tests for profile, meal recording, and daily summary.

Defer:

- Weight entries.
- Activity entries.
- MCP tools.
- RAG.
- Skill.

## Third Implementation Slice

Implement:

- `WeightEntry`.
- `ActivityEntry`.
- `weight_service`.
- `activity_service`.
- Summary activity calories and net calories.
- CLI commands for weight and activity.
- MCP tools for weight and activity.
- Skill contract updates for weight and activity.

Keep out of scope:

- Structured exercise library.
- Muscle-group mapping.
- Training plan optimization.
- RAG.
- Food database lookup.

## Service API Draft

### Profile Service

```python
def update_user_profile(input: UserProfileInput) -> UserProfileOutput:
    ...

def get_user_profile() -> UserProfileOutput | None:
    ...

def calculate_profile_targets(input: UserProfileInput) -> ProfileTargets:
    ...
```

### Meal Service

```python
def record_meal(input: RecordMealInput) -> MealOutput:
    ...

def list_meals_for_date(date: date) -> list[MealOutput]:
    ...
```

### Summary Service

```python
def get_daily_summary(date: date) -> DailySummaryOutput:
    ...
```

### Weight Service

```python
def record_weight(input: WeightEntryInput) -> WeightEntryOutput:
    ...

def get_weight_trend(days: int = 7) -> WeightTrendOutput:
    ...
```

### Activity Service

```python
def record_activity(input: ActivityEntryInput) -> ActivityEntryOutput:
    ...

def list_activities_for_date(date: date) -> list[ActivityEntryOutput]:
    ...
```

## CLI Draft

### Profile

```bash
uv run fitness-agent profile set \
  --height-cm 175 \
  --weight-kg 75 \
  --age 30 \
  --sex male \
  --activity-level moderate \
  --goal-weight-kg 70
```

```bash
uv run fitness-agent profile show
```

### Meal

Prefer JSON input for MVP because it mirrors future MCP tool payloads.

```bash
uv run fitness-agent meal add --json '{
  "date": "today",
  "meal_type": "breakfast",
  "raw_text": "Breakfast was two eggs and one bowl of rice",
  "items": [
    {
      "name": "egg",
      "quantity": 2,
      "unit": "piece",
      "calories": 144,
      "protein_g": 12,
      "carbs_g": 1,
      "fat_g": 10,
      "is_estimated": true,
      "source": "agent_estimate",
      "metadata": {
        "assumption": "regular boiled eggs"
      }
    }
  ]
}'
```

Also support repeatable `--item` values for manual debugging.

Format:

```text
name,quantity,unit,calories,protein_g,carbs_g,fat_g
```

Example:

```bash
uv run fitness-agent meal add \
  --date today \
  --type breakfast \
  --item "egg,2,piece,144,12,1,10" \
  --item "soy milk,1,cup,120,7,10,4"
```

### Summary

```bash
uv run fitness-agent summary today
```

```bash
uv run fitness-agent summary date 2026-07-08
```

Minimum summary output:

- Date.
- Total calories.
- Activity calories, when recorded.
- Net calories, calculated as intake minus activity calories.
- Total protein, carbs, and fat.
- Target calories, if available.
- Remaining calories, if available.
- Meal count.
- Per-meal subtotals.
- Estimated item count.

### Dev

```bash
uv run fitness-agent dev reset-db --yes
```

The reset command must require `--yes` and must not run by default.

### Weight

Prefer JSON input:

```bash
uv run fitness-agent weight add --json '{
  "date": "today",
  "weight_kg": 79.6,
  "raw_text": "今天早上空腹 79.6kg",
  "metadata": {
    "timing": "morning fasting"
  }
}'
```

Show trend:

```bash
uv run fitness-agent weight trend --days 7
```

### Activity

Prefer JSON input:

```bash
uv run fitness-agent activity add --json '{
  "date": "today",
  "activity_type": "walking",
  "duration_minutes": 40,
  "calories_burned": 180,
  "is_estimated": true,
  "raw_text": "今天快走 40 分钟",
  "metadata": {
    "estimation_basis": "moderate brisk walk estimate"
  }
}'
```

## MCP Strategy

Add MCP after the first CLI slice works.

Initial MCP tools:

- `update_user_profile`
- `get_user_profile`
- `record_meal`
- `get_daily_summary`
- Third-stage additions:
  - `record_weight`
  - `get_weight_trend`
  - `record_activity`

MCP tool inputs should mirror Pydantic schemas. MCP tools should not implement business logic directly.

The first MCP payloads should follow the same JSON shape accepted by the CLI.

## Skill Strategy

Create `skill/SKILL.md` after MCP tools exist.

The Skill should explain:

- When to call `record_meal`.
- When to call `get_daily_summary`.
- When to ask follow-up questions.
- When estimates are acceptable.
- How to mark uncertainty in user-facing replies.
- How to record weight and activity without over-interpreting training data.

## Testing Strategy

Initial tests:

- Profile can be created and updated.
- Profile target calculations produce BMR/TDEE-style values when inputs are sufficient.
- Meal can be recorded with multiple items.
- Meal recording preserves `raw_text` and `metadata_json`.
- Daily summary totals calories and macros correctly.
- Daily summary reports estimated item count.
- Empty day summary returns zero totals.
- CLI help works.
- Weight can be recorded and trend output returns latest and average values.
- Activity can be recorded and daily summary includes activity calories.
- MCP tools expose weight and activity operations.

Testing rules:

- Core services should be tested without invoking CLI where possible.
- CLI tests should cover command wiring and output.
- Tests should not write to real local user data.

## Non-Goals

Do not implement these in the first slice:

- Full food database lookup.
- Natural language parsing.
- RAG.
- MCP server.
- Skill.
- Web UI.
- Authentication.
- Cloud sync.
- Multi-user support.
- Model fine-tuning.

Third-stage non-goals:

- Full workout programming.
- Exercise library.
- Muscle-group recovery analysis.
- Wearable import.

## Open Decisions

- Whether to use SQLAlchemy declarative models directly or SQLModel.
- Whether to support database migrations before public release.
- Whether nutrition fields should be floats or decimals for all values.
- How much default calorie estimation should happen before a food database exists.
