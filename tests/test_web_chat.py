from typing import Any

from fastapi.testclient import TestClient

from app.agent.model_client import FakeModelClient
from app.agent.schemas import AgentPlan, PlannedToolCall
from app.agent.service import ChatService
from app.web.server import create_app


class FakeMCPClient:
    def __init__(self, results: dict[str, dict[str, Any]]) -> None:
        self.results = results
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((name, arguments))
        return self.results[name]


def test_web_health_and_index() -> None:
    client = TestClient(create_app(chat_service=_chat_service(), mcp_client=FakeMCPClient({})))

    health = client.get("/api/health")
    index = client.get("/")

    assert health.status_code == 200
    assert health.json() == {"ok": True, "service": "fitness-agent-web"}
    assert index.status_code == 200
    assert "Fitness Agent" in index.text


def test_web_chat_records_meal_via_agent_service() -> None:
    plan = AgentPlan(
        tool_calls=[
            PlannedToolCall(name="check_duplicate_meal", arguments={"meal": {}}),
            PlannedToolCall(name="record_meal", arguments={"meal": {}}),
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
    chat_service = ChatService(model_client=FakeModelClient(plan), mcp_client=mcp_client)
    client = TestClient(create_app(chat_service=chat_service, mcp_client=mcp_client))

    response = client.post("/api/chat", json={"message": "早餐吃了两个鸡蛋"})

    assert response.status_code == 200
    payload = response.json()
    assert "今天目前总摄入 224 kcal" in payload["reply"]
    assert [call["name"] for call in payload["tool_calls"]] == [
        "check_duplicate_meal",
        "record_meal",
        "get_daily_summary",
    ]


def test_web_summary_today_uses_mcp_client() -> None:
    mcp_client = FakeMCPClient(
        {
            "get_daily_summary": {
                "total_calories": 500,
                "total_protein_g": 40,
                "remaining_calories": 1500,
            }
        }
    )
    client = TestClient(create_app(chat_service=_chat_service(), mcp_client=mcp_client))

    response = client.get("/api/summary/today")

    assert response.status_code == 200
    assert response.json()["total_calories"] == 500
    assert mcp_client.calls == [("get_daily_summary", {"date_value": "today"})]


def _chat_service() -> ChatService:
    return ChatService(
        model_client=FakeModelClient(AgentPlan(direct_reply="ok")),
        mcp_client=FakeMCPClient({}),
    )
