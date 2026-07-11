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

    assert _payload(result) == {"profile": None}


def _payload(result: object) -> object:
    if isinstance(result, tuple):
        return result[1]
    raise AssertionError(f"unexpected MCP result shape: {result!r}")
