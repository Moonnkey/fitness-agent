from typing import Any, Literal

from pydantic import BaseModel, Field

SupportedToolName = Literal[
    "record_meal",
    "get_daily_summary",
    "get_weekly_summary",
    "get_daily_guidance",
    "get_records_for_date",
    "get_record",
    "update_record",
    "delete_record",
    "check_duplicate_meal",
]


class PlannedToolCall(BaseModel):
    name: SupportedToolName
    arguments: dict[str, Any] = Field(default_factory=dict)


class AgentPlan(BaseModel):
    tool_calls: list[PlannedToolCall] = Field(default_factory=list)
    direct_reply: str | None = None


class ToolCallResult(BaseModel):
    name: str
    arguments: dict[str, Any]
    ok: bool
    result: dict[str, Any] | None = None
    error: str | None = None


class ChatAgentResult(BaseModel):
    reply: str
    tool_calls: list[ToolCallResult] = Field(default_factory=list)
