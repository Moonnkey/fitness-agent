import pytest

from app.agent.mcp_client import StdioFitnessMCPClient, _split_args


def test_split_args_preserves_quoted_values() -> None:
    assert _split_args('run fitness-agent-mcp --label "morning meal"') == [
        "run",
        "fitness-agent-mcp",
        "--label",
        "morning meal",
    ]


@pytest.mark.anyio
async def test_stdio_fitness_mcp_client_calls_local_server() -> None:
    client = StdioFitnessMCPClient(command=".venv/bin/fitness-agent-mcp")

    result = await client.call_tool("get_daily_summary", {"date_value": "2026-07-19"})

    assert result["date"] == "2026-07-19"
    assert result["total_calories"] == 0
