import json
import os
from typing import Protocol

from app.agent.prompts import AGENT_SYSTEM_PROMPT
from app.agent.schemas import AgentPlan

DEFAULT_MODEL = "gpt-4.1-mini"


class ModelConfigurationError(RuntimeError):
    """Raised when the configured model client cannot run."""


class ModelClient(Protocol):
    async def create_plan(self, message: str) -> AgentPlan:
        """Return a structured MCP tool-call plan for a user message."""


class FakeModelClient:
    def __init__(self, plan: AgentPlan | None = None) -> None:
        self.plan = plan or AgentPlan(direct_reply="FakeModelClient 已收到消息。")

    async def create_plan(self, message: str) -> AgentPlan:
        return self.plan


class OpenAIModelClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("FITNESS_AGENT_MODEL") or DEFAULT_MODEL
        if not self.api_key:
            raise ModelConfigurationError(
                "OPENAI_API_KEY is required for OpenAIModelClient. "
                "Set FITNESS_AGENT_AGENT_MODE=fake for explicit development mode."
            )

    async def create_plan(self, message: str) -> AgentPlan:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ModelConfigurationError(
                "openai package is required for OpenAIModelClient."
            ) from exc

        client = AsyncOpenAI(api_key=self.api_key)
        response = await client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": AGENT_SYSTEM_PROMPT},
                {"role": "user", "content": message},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
        )
        content = response.choices[0].message.content
        if not content:
            raise ModelConfigurationError("OpenAI returned an empty planning response.")
        try:
            payload = json.loads(content)
        except json.JSONDecodeError as exc:
            raise ModelConfigurationError("OpenAI returned invalid JSON planning output.") from exc
        return AgentPlan.model_validate(payload)
