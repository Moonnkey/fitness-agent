# Fitness Agent Project Rules

## Goal

Build a local-first AI fitness and fat-loss assistant. The MVP records meals, weight, simple workouts or activities, and daily calorie summaries through a Python CLI and MCP tools.

## Current Scope

- Use Python as the primary implementation language.
- Keep the MVP local-first with SQLite.
- Build reliable core services before adding advanced AI behavior.
- Support CLI usage first, then expose the same capabilities through MCP.
- Add RAG only after the core recording and summary loop works.

## Architecture Rules

- Put business logic in `app/core`.
- Put database models and persistence code under `app/core/db` and `app/core/models`.
- Put Pydantic request/response schemas under `app/core/schemas`.
- Put reusable operations such as meal recording, summaries, and goal calculations under `app/core/services`.
- CLI commands in `app/cli` must call `app/core` services.
- MCP tools in `app/mcp` must call `app/core` services.
- Future API endpoints must also call `app/core` services.
- Do not duplicate calorie, nutrition, goal, or summary logic across CLI, MCP, and future API layers.
- Keep interfaces thin and core services testable.

## Technology Defaults

- Python 3.11 or newer.
- SQLite for MVP persistence.
- Pydantic for external input and output validation.
- Typer for CLI commands.
- pytest for tests.
- Prefer SQLAlchemy or SQLModel for database access once persistence is implemented.
- Prefer the Python MCP SDK or FastMCP when MCP tools are added.

## Product Rules

- Treat calorie, macro, and exercise-burn values as estimates unless they come from a verified source.
- Store enough metadata to explain estimates later, such as source, assumptions, and confidence when practical.
- Prefer asking a short follow-up question when a missing value would materially change the result.
- If a reasonable default is used, surface it as an estimate.
- Preserve user privacy. Do not commit real user health data, database files, API keys, or secrets.

## Health And Safety Rules

- Do not provide medical diagnosis.
- Do not present the assistant as a doctor, dietitian, or physical therapist.
- Do not recommend extreme calorie restriction, dehydration tactics, purging, or unsafe rapid weight loss.
- Flag potentially unsafe goals, symptoms, injury signals, or disordered eating patterns and recommend professional help where appropriate.
- Fitness and nutrition recommendations should be framed as general coaching guidance, not medical advice.

## MVP Boundaries

- Do not add web UI, mobile app, multi-user auth, cloud sync, payments, model fine-tuning, or plugin packaging until the MVP loop works locally.
- Do not add a full RAG system until meal, weight, activity, summary, CLI, and MCP basics are working.
- Do not introduce TypeScript unless it is needed for a clearly scoped integration boundary.

## Verification

Before considering a code change complete:

- Run the relevant tests.
- Run type or lint checks if configured.
- Manually test at least one CLI command for changed user-facing behavior.
- For MCP changes, verify the MCP server starts and the changed tool can be called or inspected.

## Documentation

- Keep `docs/mvp.md` updated when scope changes.
- Add short design notes under `docs/` for decisions that affect architecture or product behavior.
- Avoid long speculative docs. Prefer concrete decisions, schemas, workflows, and examples.
