from typing import Any

import pytest

from app.agent.model_client import FakeModelClient
from app.agent.schemas import AgentPlan, PlannedToolCall
from app.agent.service import ChatService


class FakeMCPClient:
    def __init__(self, results: dict[str, dict[str, Any]]) -> None:
        self.results = results
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((name, arguments))
        result = self.results.get(name)
        if result is None:
            raise RuntimeError(f"missing fake result: {name}")
        return result


class BrokenModelClient:
    async def create_plan(self, message: str) -> AgentPlan:
        raise RuntimeError("missing api key")


@pytest.mark.anyio
async def test_chat_service_records_meal_and_returns_summary_reply() -> None:
    plan = AgentPlan(
        tool_calls=[
            PlannedToolCall(
                name="check_duplicate_meal",
                arguments={"meal": {"date": "today", "meal_type": "breakfast", "items": []}},
            ),
            PlannedToolCall(
                name="record_meal",
                arguments={"meal": {"date": "today", "meal_type": "breakfast", "items": []}},
            ),
            PlannedToolCall(name="get_daily_summary", arguments={"date_value": "today"}),
        ]
    )
    mcp_client = FakeMCPClient(
        {
            "check_duplicate_meal": {"duplicates": []},
            "record_meal": {
                "meal_type": "breakfast",
                "total_calories": 224,
                "total_protein_g": 20,
            },
            "get_daily_summary": {
                "total_calories": 224,
                "total_protein_g": 20,
                "activity_calories": 0,
                "remaining_calories": 1776,
            },
        }
    )
    service = ChatService(model_client=FakeModelClient(plan), mcp_client=mcp_client)

    result = await service.handle_message("早餐吃了两个鸡蛋和一杯无糖豆浆")

    assert [call[0] for call in mcp_client.calls] == [
        "check_duplicate_meal",
        "record_meal",
        "get_daily_summary",
    ]
    assert "已记录 breakfast" in result.reply
    assert "今天目前总摄入 224 kcal" in result.reply


@pytest.mark.anyio
async def test_chat_service_defaults_missing_meal_type_to_other() -> None:
    plan = AgentPlan(
        tool_calls=[
            PlannedToolCall(
                name="check_duplicate_meal",
                arguments={
                    "meal": {
                        "date": "today",
                        "raw_text": "我吃了两个鸡蛋",
                        "items": [
                            {
                                "name": "鸡蛋",
                                "quantity": 2,
                                "unit": "个",
                                "calories": 144,
                                "protein_g": 12,
                                "carbs_g": 1,
                                "fat_g": 10,
                                "source": "agent_estimate",
                                "is_estimated": True,
                            }
                        ],
                    }
                },
            )
        ]
    )
    mcp_client = FakeMCPClient({"check_duplicate_meal": {"duplicates": []}})
    service = ChatService(model_client=FakeModelClient(plan), mcp_client=mcp_client)

    await service.handle_message("我吃了两个鸡蛋")

    meal_payload = mcp_client.calls[0][1]["meal"]
    assert meal_payload["meal_type"] == "other"
    assert meal_payload["metadata"]["agent_defaults"] == [
        "meal_type defaulted to other because user did not specify meal time"
    ]


@pytest.mark.anyio
async def test_chat_service_stops_when_duplicate_meal_found() -> None:
    plan = AgentPlan(
        tool_calls=[
            PlannedToolCall(name="check_duplicate_meal", arguments={"meal": {}}),
            PlannedToolCall(name="record_meal", arguments={"meal": {}}),
        ]
    )
    mcp_client = FakeMCPClient({"check_duplicate_meal": {"duplicates": [{"record_id": 1}]}})
    service = ChatService(model_client=FakeModelClient(plan), mcp_client=mcp_client)

    result = await service.handle_message("早餐吃了两个鸡蛋")

    assert [call[0] for call in mcp_client.calls] == ["check_duplicate_meal"]
    assert "疑似重复" in result.reply


@pytest.mark.anyio
async def test_chat_service_returns_tool_error() -> None:
    plan = AgentPlan(tool_calls=[PlannedToolCall(name="get_daily_summary", arguments={})])
    service = ChatService(model_client=FakeModelClient(plan), mcp_client=FakeMCPClient({}))

    result = await service.handle_message("查今天总结")

    assert "执行 get_daily_summary 时出错" in result.reply
    assert result.tool_calls[0].ok is False


@pytest.mark.anyio
async def test_chat_service_returns_model_error_as_reply() -> None:
    service = ChatService(model_client=BrokenModelClient(), mcp_client=FakeMCPClient({}))

    result = await service.handle_message("早餐吃了两个鸡蛋")

    assert result.reply == "模型解析失败：missing api key"
    assert result.tool_calls == []
