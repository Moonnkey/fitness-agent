# MCP Tools And Basic Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expose the existing profile, meal, and summary core services as local MCP tools, then add a basic Agent Skill that teaches an agent when and how to call those tools.

**Architecture:** The MCP layer remains a thin interface over existing Pydantic schemas and `app/core/services`. Tool payloads mirror the JSON shape already accepted by the CLI, preserving `raw_text` and `metadata` for agent-estimated records. The Skill is documentation only and depends on the MCP tools rather than duplicating business logic.

**Tech Stack:** Python 3.12, MCP Python SDK FastMCP, Pydantic v2, SQLAlchemy 2, SQLite, pytest, ruff.

---

## Source Documents

- `AGENTS.md`
- `docs/mvp.md`
- `docs/architecture.md`
- `docs/superpowers/plans/2026-07-11-first-mvp-backend-tool.md`

## Global Constraints

- Do not duplicate profile, meal, summary, or database logic in `app/mcp`.
- MCP tools must call existing `app/core/services`.
- MCP tool inputs should mirror Pydantic schemas where practical.
- The MCP server must default to stdio transport so Codex can launch it as a local MCP server.
- Keep CLI behavior unchanged.
- Add a basic Skill only after MCP tools are implemented and tested.
- Do not add RAG, food database lookup, weight/activity tools, or natural language parsing in this phase.

## Planned File Structure

- Create `app/mcp/server.py`
  - Owns FastMCP app construction, tool registration, and `main()`.
- Create `tests/test_mcp_tools.py`
  - Verifies tool list and direct FastMCP tool calls.
- Modify `pyproject.toml`
  - Add `fitness-agent-mcp = "app.mcp.server:main"` script.
- Create `skill/SKILL.md`
  - Basic Agent Skill instructions for using the local MCP tools.
- Create `skill/references/tool-contracts.md`
  - Tool payload examples and response expectations.
- Optionally modify `docs/setup.zh.md`
  - Add local MCP command notes if needed.

---

### Task 1: MCP Server With Profile, Meal, And Summary Tools

**Files:**
- Create: `app/mcp/server.py`
- Modify: `pyproject.toml`
- Create: `tests/test_mcp_tools.py`

- [ ] **Step 1: Write failing MCP tests**

Create `tests/test_mcp_tools.py`:

```python
from datetime import date
import json

import pytest

from app.mcp.server import build_mcp_server


@pytest.mark.anyio
async def test_mcp_server_lists_expected_tools() -> None:
    server = build_mcp_server()

    tools = await server.list_tools()

    assert {tool.name for tool in tools} >= {
        "update_user_profile",
        "get_user_profile",
        "record_meal",
        "get_daily_summary",
    }


@pytest.mark.anyio
async def test_mcp_tools_record_profile_meal_and_summary() -> None:
    server = build_mcp_server()

    profile_result = await server.call_tool(
        "update_user_profile",
        {
            "profile": {
                "height_cm": 180,
                "weight_kg": 80,
                "age": 30,
                "sex": "male",
                "activity_level": "moderate",
                "goal_type": "fat_loss",
            }
        },
    )
    meal_result = await server.call_tool(
        "record_meal",
        {
            "meal": {
                "date": "2026-07-11",
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
        },
    )
    summary_result = await server.call_tool(
        "get_daily_summary",
        {"date_value": "2026-07-11"},
    )

    profile_payload = _payload(profile_result)
    meal_payload = _payload(meal_result)
    summary_payload = _payload(summary_result)

    assert profile_payload["goal_type"] == "fat_loss"
    assert meal_payload["total_calories"] == 144
    assert summary_payload["total_calories"] == 144
    assert summary_payload["estimated_item_count"] == 1
    assert summary_payload["target_calories"] == 2309


@pytest.mark.anyio
async def test_get_user_profile_returns_none_when_missing() -> None:
    server = build_mcp_server()

    result = await server.call_tool("get_user_profile", {})

    assert _payload(result) is None


def _payload(result: object) -> object:
    if isinstance(result, tuple):
        return result[1]
    raise AssertionError(f"unexpected MCP result shape: {result!r}")
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv run pytest tests/test_mcp_tools.py -v
```

Expected: fail because `app.mcp.server` does not exist.

- [ ] **Step 3: Implement MCP server**

Create `app/mcp/server.py`:

```python
from typing import Any

from mcp.server.fastmcp import FastMCP

from app.core.db.session import init_db
from app.core.schemas.common import parse_date_value
from app.core.schemas.meal import RecordMealInput
from app.core.schemas.profile import UserProfileInput
from app.core.services.meal_service import record_meal as record_meal_service
from app.core.services.profile_service import get_user_profile as get_user_profile_service
from app.core.services.profile_service import update_user_profile as update_user_profile_service
from app.core.services.summary_service import get_daily_summary as get_daily_summary_service

SERVER_INSTRUCTIONS = """
Fitness Agent stores local fitness and fat-loss tracking data.
Use update_user_profile before relying on calorie targets.
Use record_meal only after the agent has parsed or estimated meal items into structured fields.
Preserve user wording in raw_text and estimation assumptions in metadata.
All calorie and macro values may be estimates unless source says otherwise.
"""


def _dump_model(model: Any) -> dict[str, Any]:
    return model.model_dump(mode="json")


def build_mcp_server() -> FastMCP:
    mcp = FastMCP("fitness-agent", instructions=SERVER_INSTRUCTIONS)

    @mcp.tool()
    def update_user_profile(profile: dict[str, Any]) -> dict[str, Any]:
        """Create or update the single local user profile and return calculated targets."""
        init_db()
        output = update_user_profile_service(UserProfileInput.model_validate(profile))
        return _dump_model(output)

    @mcp.tool()
    def get_user_profile() -> dict[str, Any] | None:
        """Return the single local user profile, or null if no profile exists."""
        init_db()
        output = get_user_profile_service()
        if output is None:
            return None
        return _dump_model(output)

    @mcp.tool()
    def record_meal(meal: dict[str, Any]) -> dict[str, Any]:
        """Record a meal from structured or semi-structured agent-provided data."""
        init_db()
        data = dict(meal)
        data["date"] = parse_date_value(data.get("date"))
        output = record_meal_service(RecordMealInput.model_validate(data))
        return _dump_model(output)

    @mcp.tool()
    def get_daily_summary(date_value: str = "today") -> dict[str, Any]:
        """Return calorie and macro totals for a date."""
        init_db()
        output = get_daily_summary_service(parse_date_value(date_value))
        return _dump_model(output)

    return mcp


def main() -> None:
    build_mcp_server().run(transport="stdio")


if __name__ == "__main__":
    main()
```

Modify `pyproject.toml`:

```toml
[project.scripts]
fitness-agent = "app.cli.main:app"
fitness-agent-mcp = "app.mcp.server:main"
```

- [ ] **Step 4: Run MCP tests**

Run:

```bash
uv run pytest tests/test_mcp_tools.py -v
```

Expected: pass.

- [ ] **Step 5: Run full verification**

Run:

```bash
uv run pytest
uv run ruff check app tests
uv sync --extra dev --extra mcp --python python3.12
uv run fitness-agent-mcp --help
```

Expected:

- All tests pass.
- Ruff reports no issues.
- `uv sync` succeeds and installs the new script.
- `fitness-agent-mcp --help` may start stdio server instead of printing help; if it blocks, stop and instead verify import with `uv run python -c "from app.mcp.server import build_mcp_server; print(build_mcp_server().name)"`.

- [ ] **Step 6: Commit**

```bash
git add app/mcp/server.py pyproject.toml tests/test_mcp_tools.py uv.lock
git commit -m "Add MCP tools for profile meals and summary"
```

---

### Task 2: Basic Agent Skill For Fitness MCP Tools

**Files:**
- Create: `skill/SKILL.md`
- Create: `skill/references/tool-contracts.md`
- Create: `tests/test_skill_files.py`

- [ ] **Step 1: Write failing skill file tests**

Create `tests/test_skill_files.py`:

```python
from pathlib import Path


def test_skill_file_exists_with_required_frontmatter() -> None:
    text = Path("skill/SKILL.md").read_text()

    assert text.startswith("---")
    assert "name: fitness-agent" in text
    assert "description:" in text
    assert "record_meal" in text
    assert "get_daily_summary" in text


def test_tool_contracts_reference_exists() -> None:
    text = Path("skill/references/tool-contracts.md").read_text()

    assert "update_user_profile" in text
    assert "record_meal" in text
    assert "get_daily_summary" in text
```

- [ ] **Step 2: Run test to verify failure**

Run:

```bash
uv run pytest tests/test_skill_files.py -v
```

Expected: fail because `skill/SKILL.md` and `tool-contracts.md` do not exist.

- [ ] **Step 3: Create basic Skill**

Create `skill/SKILL.md`:

```markdown
---
name: fitness-agent
description: Use when the user wants to record meals, update fitness or fat-loss profile data, or ask for daily calorie and macro summaries through the local Fitness Agent MCP tools. This skill guides agents to call update_user_profile, get_user_profile, record_meal, and get_daily_summary with structured or semi-structured payloads while preserving raw user text and uncertainty metadata.
---

# Fitness Agent

Use the local Fitness Agent MCP tools as the source of truth for profile, meal, and daily summary data.

## Workflow

1. Identify whether the user is updating their profile, recording a meal, or asking for a summary.
2. For profile changes, call `update_user_profile`.
3. For meal records, parse the user's description into structured meal items before calling `record_meal`.
4. Preserve the original user wording in `raw_text`.
5. Put estimation assumptions, confidence, cooking method, brand, or missing context in `metadata`.
6. For daily totals or remaining calories, call `get_daily_summary`.
7. Mark calories and macros as estimates unless the source is user-provided or database-derived.

## Tool Contracts

Read `references/tool-contracts.md` before constructing unfamiliar payloads.

## Safety

Do not provide medical diagnosis. Do not recommend extreme restriction, dehydration, purging, or unsafe rapid weight loss. Encourage professional help for symptoms, injuries, eating disorder signals, or medical conditions.
```

- [ ] **Step 4: Create tool contracts reference**

Create `skill/references/tool-contracts.md`:

```markdown
# Fitness Agent Tool Contracts

## update_user_profile

Input:

```json
{
  "profile": {
    "height_cm": 180,
    "weight_kg": 80,
    "age": 30,
    "sex": "male",
    "activity_level": "moderate",
    "goal_type": "fat_loss",
    "goal_weight_kg": 72,
    "target_calories": 2200,
    "target_protein_g": 150
  }
}
```

Manual `target_calories` and `target_protein_g` are optional and take precedence over calculated values.

## get_user_profile

Input:

```json
{}
```

Returns the local profile or `null`.

## record_meal

Input:

```json
{
  "meal": {
    "date": "today",
    "meal_type": "breakfast",
    "raw_text": "早餐吃了两个鸡蛋",
    "metadata": {
      "agent": "codex",
      "confidence": 0.8
    },
    "items": [
      {
        "name": "鸡蛋",
        "quantity": 2,
        "unit": "个",
        "calories": 144,
        "protein_g": 12,
        "carbs_g": 1,
        "fat_g": 10,
        "is_estimated": true,
        "source": "agent_estimate",
        "raw_text": "两个鸡蛋",
        "metadata": {
          "assumption": "普通水煮蛋"
        }
      }
    ]
  }
}
```

The backend does not parse natural language. The agent should parse or estimate fields before calling `record_meal`.

## get_daily_summary

Input:

```json
{
  "date_value": "today"
}
```

Use ISO dates such as `2026-07-11` when the user asks for a specific date.
```

- [ ] **Step 5: Run skill tests**

Run:

```bash
uv run pytest tests/test_skill_files.py -v
```

Expected: pass.

- [ ] **Step 6: Run full verification and commit**

Run:

```bash
uv run pytest
uv run ruff check app tests
```

Expected: pass.

Commit:

```bash
git add skill/SKILL.md skill/references/tool-contracts.md tests/test_skill_files.py
git commit -m "Add basic Fitness Agent skill"
```

---

### Task 3: Final Verification And Push

**Files:**
- No planned source changes unless verification reveals issues.

- [ ] **Step 1: Run full verification**

Run:

```bash
uv run pytest
uv run ruff check app tests
uv run python -c "from app.mcp.server import build_mcp_server; print(build_mcp_server().name)"
```

Expected:

- All tests pass.
- Ruff reports no issues.
- Python import prints `fitness-agent`.

- [ ] **Step 2: Inspect Git status and commits**

Run:

```bash
git status --branch --short
git log --oneline --decorate --max-count=10
```

Expected:

- Working tree clean.
- `main` has the MCP and Skill commits.

- [ ] **Step 3: Push**

Run:

```bash
git push
```

Expected: remote `origin/main` receives the new commits.

---

## Self-Review

### Spec Coverage

- MCP server starts locally: Task 1 provides `fitness-agent-mcp`.
- MCP tools call existing core services: Task 1.
- Agent can record a meal through MCP: Task 1 tests `record_meal`.
- Agent can query daily summary through MCP: Task 1 tests `get_daily_summary`.
- Basic Skill instructions exist: Task 2.

### Intentional Deferrals

- Weight MCP tool.
- Activity MCP tool.
- RAG knowledge search.
- Food database lookup.
- Natural language parsing inside backend.
- Public plugin packaging.

### Placeholder Scan

This plan contains no implementation placeholders. Any deferred features are explicitly listed as intentional deferrals.
