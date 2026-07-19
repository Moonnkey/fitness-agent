import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.agent.mcp_client import MCPClient, StdioFitnessMCPClient
from app.agent.model_client import (
    FakeModelClient,
    ModelClient,
    ModelConfigurationError,
    OpenAIModelClient,
)
from app.agent.schemas import AgentPlan
from app.agent.service import ChatService
from app.web.schemas import ChatRequest, ChatResponse, HealthResponse

STATIC_DIR = Path(__file__).parent / "static"


class UnavailableModelClient:
    def __init__(self, error: str) -> None:
        self.error = error

    async def create_plan(self, message: str) -> AgentPlan:
        raise ModelConfigurationError(self.error)


def create_app(
    chat_service: ChatService | None = None,
    mcp_client: MCPClient | None = None,
) -> FastAPI:
    app = FastAPI(title="Fitness Agent Web Chat")
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    runtime_mcp_client = mcp_client or StdioFitnessMCPClient()
    runtime_chat_service = chat_service or ChatService(
        model_client=_build_model_client(),
        mcp_client=runtime_mcp_client,
    )
    app.state.chat_service = runtime_chat_service
    app.state.mcp_client = runtime_mcp_client

    @app.get("/", include_in_schema=False)
    async def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(ok=True, service="fitness-agent-web")

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest) -> ChatResponse:
        result = await app.state.chat_service.handle_message(request.message)
        return ChatResponse.model_validate(result.model_dump())

    @app.get("/api/summary/today")
    async def summary_today() -> dict:
        return await app.state.mcp_client.call_tool("get_daily_summary", {"date_value": "today"})

    @app.get("/api/weekly-summary")
    async def weekly_summary(days: int = 7) -> dict:
        return await app.state.mcp_client.call_tool(
            "get_weekly_summary",
            {"end_date_value": "today", "days": days},
        )

    return app


def _build_model_client() -> ModelClient:
    mode = os.getenv("FITNESS_AGENT_AGENT_MODE", "openai").strip().lower()
    if mode == "fake":
        return FakeModelClient()
    try:
        return OpenAIModelClient()
    except ModelConfigurationError as exc:
        return UnavailableModelClient(str(exc))


def main() -> None:
    host = os.getenv("FITNESS_AGENT_WEB_HOST", "0.0.0.0")
    port = int(os.getenv("FITNESS_AGENT_WEB_PORT", "8000"))
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
