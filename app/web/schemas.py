from pydantic import BaseModel, Field

from app.agent.schemas import ToolCallResult


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    reply: str
    tool_calls: list[ToolCallResult] = Field(default_factory=list)


class HealthResponse(BaseModel):
    ok: bool
    service: str

