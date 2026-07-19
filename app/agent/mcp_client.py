import json
import os
import shlex
from typing import Any, Protocol

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPClient(Protocol):
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Call an MCP tool and return a JSON-like payload."""


class StdioFitnessMCPClient:
    def __init__(
        self,
        command: str | None = None,
        args: list[str] | None = None,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
    ) -> None:
        self.command = command or os.getenv("FITNESS_AGENT_MCP_COMMAND") or "fitness-agent-mcp"
        self.args = args or _split_args(os.getenv("FITNESS_AGENT_MCP_ARGS"))
        self.cwd = cwd or os.getenv("FITNESS_AGENT_MCP_CWD")
        self.env = env or dict(os.environ)

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        server_params = StdioServerParameters(
            command=self.command,
            args=self.args,
            cwd=self.cwd,
            env=self.env,
        )
        async with stdio_client(server_params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool(name, arguments)
        if result.isError:
            raise RuntimeError(_extract_text_result(result.content) or f"MCP tool failed: {name}")
        return _extract_json_result(result.content)


def _split_args(raw_args: str | None) -> list[str]:
    if not raw_args:
        return []
    return shlex.split(raw_args)


def _extract_json_result(content: list[Any]) -> dict[str, Any]:
    text = _extract_text_result(content)
    if text is None:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return {"text": text}
    if isinstance(payload, dict):
        return payload
    return {"value": payload}


def _extract_text_result(content: list[Any]) -> str | None:
    for item in content:
        text = getattr(item, "text", None)
        if text is not None:
            return text
    return None
