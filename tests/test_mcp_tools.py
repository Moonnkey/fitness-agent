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
        "record_weight",
        "get_weight_trend",
        "record_activity",
        "get_records_for_date",
        "delete_record",
        "check_duplicate_meal",
        "check_duplicate_weight",
        "check_duplicate_activity",
        "get_record",
        "update_record",
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


@pytest.mark.anyio
async def test_mcp_tools_record_weight_activity_and_summary() -> None:
    server = build_mcp_server()

    weight_result = await server.call_tool(
        "record_weight",
        {
            "weight": {
                "date": "2026-07-11",
                "weight_kg": 79.6,
                "raw_text": "今天早上空腹 79.6kg",
                "metadata": {"timing": "morning fasting"},
            }
        },
    )
    trend_result = await server.call_tool("get_weight_trend", {"days": 7})
    activity_result = await server.call_tool(
        "record_activity",
        {
            "activity": {
                "date": "2026-07-11",
                "activity_type": "walking",
                "duration_minutes": 40,
                "calories_burned": 180,
                "is_estimated": True,
                "raw_text": "今天快走 40 分钟",
                "metadata": {"estimation_basis": "中等强度快走估算"},
            }
        },
    )
    summary_result = await server.call_tool("get_daily_summary", {"date_value": "2026-07-11"})

    weight_payload = _payload(weight_result)
    trend_payload = _payload(trend_result)
    activity_payload = _payload(activity_result)
    summary_payload = _payload(summary_result)

    assert weight_payload["weight_kg"] == 79.6
    assert trend_payload["latest_weight_kg"] == 79.6
    assert activity_payload["calories_burned"] == 180
    assert summary_payload["activity_calories"] == 180
    assert summary_payload["net_calories"] == -180


@pytest.mark.anyio
async def test_mcp_tools_history_delete_and_duplicate_check() -> None:
    server = build_mcp_server()

    meal = {
        "date": "2026-07-11",
        "meal_type": "breakfast",
        "raw_text": "早餐两个鸡蛋",
        "items": [{"name": "鸡蛋", "quantity": 2, "unit": "个", "calories": 144}],
    }
    recorded_result = await server.call_tool("record_meal", {"meal": meal})
    duplicate_result = await server.call_tool("check_duplicate_meal", {"meal": meal})
    history_result = await server.call_tool(
        "get_records_for_date",
        {"date_value": "2026-07-11", "record_type": "all"},
    )
    delete_result = await server.call_tool(
        "delete_record",
        {"record_type": "meal", "record_id": _payload(recorded_result)["id"]},
    )
    history_after_delete = await server.call_tool(
        "get_records_for_date",
        {"date_value": "2026-07-11", "record_type": "all"},
    )

    duplicate_payload = _payload(duplicate_result)
    history_payload = _payload(history_result)
    delete_payload = _payload(delete_result)
    history_after_delete_payload = _payload(history_after_delete)

    assert len(duplicate_payload["duplicates"]) == 1
    assert duplicate_payload["duplicates"][0]["reason"] == "same_raw_text"
    assert history_payload["total_record_count"] == 1
    assert delete_payload == {"record_type": "meal", "record_id": 1, "deleted": True}
    assert history_after_delete_payload["total_record_count"] == 0


@pytest.mark.anyio
async def test_mcp_tools_get_and_update_record() -> None:
    server = build_mcp_server()

    weight_result = await server.call_tool(
        "record_weight",
        {"weight": {"date": "2026-07-11", "weight_kg": 79.6}},
    )
    weight_id = _payload(weight_result)["id"]
    detail_result = await server.call_tool(
        "get_record",
        {"record_type": "weight", "record_id": weight_id},
    )
    update_result = await server.call_tool(
        "update_record",
        {
            "record_type": "weight",
            "record_id": weight_id,
            "patch": {"weight_kg": 79.2},
        },
    )

    detail_payload = _payload(detail_result)
    update_payload = _payload(update_result)

    assert detail_payload["record"]["weight_kg"] == 79.6
    assert update_payload["changed_fields"] == ["weight_kg"]
    assert update_payload["record"]["weight_kg"] == 79.2
    assert update_payload["record"]["updated_at"] is not None


def _payload(result: object) -> object:
    if isinstance(result, tuple):
        return result[1]
    raise AssertionError(f"unexpected MCP result shape: {result!r}")
