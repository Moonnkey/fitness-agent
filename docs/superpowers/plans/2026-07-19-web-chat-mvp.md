# Web Chat MVP Implementation Plan

> Superpowers-style local plan. The installed Codex skills do not currently include
> `superpowers`, so this document keeps the same plan-and-checklist workflow inside
> the repo.

**Branch:** `feature/web-chat-mvp`

**Goal:** Add a local-network mobile Web Chat MVP. The Web Chat backend includes a
lightweight agent that calls the existing `fitness-agent` MCP tools through an MCP
client. Agent add-on usage through Codex/Skill/MCP remains unchanged.

## Decisions

- Keep Agent add-on mode intact.
- Add a new Web Chat product mode.
- Web Chat agent calls MCP tools, not core services directly.
- Use FastAPI for HTTP.
- Serve minimal static HTML/CSS/JS from the Python app.
- Use OpenAI API by default through environment variables.
- Provide mock/rule-based mode for tests and local demo without API calls.
- Do not persist chat messages.
- Local-network access only; no login in this stage.
- No image upload in this stage.

## Planned File Structure

- `app/web/server.py`
  - FastAPI app construction, routes, static page serving.
- `app/web/schemas.py`
  - HTTP request/response schemas.
- `app/agent/service.py`
  - Lightweight chat orchestration.
- `app/agent/prompts.py`
  - System/developer prompts for intent extraction.
- `app/agent/schemas.py`
  - Structured model output schemas.
- `app/agent/model_client.py`
  - OpenAI/mock model client boundary.
- `app/agent/mcp_client.py`
  - MCP client wrapper for calling `fitness-agent-mcp`.
- `app/agent/tool_dispatcher.py`
  - Maps structured intents to MCP tool calls.
- `app/web/static/index.html`
- `app/web/static/styles.css`
- `app/web/static/app.js`
- `tests/test_web_chat.py`
- `tests/test_agent_service.py`
- `docs/stage-guides/stage-07-web-chat-mvp.zh.md`

## Initial Chat Intents

- `record_meal`
- `get_daily_summary`
- `get_weekly_summary`
- `get_daily_guidance`
- `update_record`
- `delete_record`
- `clarify`
- `unsupported`

## Risk Controls

- Deletion requires explicit user wording.
- Ambiguous update/delete returns a clarification response, not an action.
- Food estimates must include assumptions in metadata.
- Duplicate meal check runs before record meal when possible.
- Chat messages are not persisted.
- API keys are environment variables only.

## Checklist

- [ ] Add dependencies for FastAPI server and OpenAI client if needed.
- [ ] Add Web Chat design docs and plan.
- [ ] Add model client abstraction with mock mode.
- [ ] Add MCP client wrapper.
- [ ] Add intent schemas and tool dispatcher.
- [ ] Add chat service tests with mock model and mocked MCP calls.
- [ ] Add FastAPI routes and tests.
- [ ] Add minimal mobile-friendly static frontend.
- [ ] Add CLI/script entrypoint for `fitness-agent-web`.
- [ ] Add stage 07 user guide.
- [ ] Run pytest, ruff, and HTTP smoke test.
