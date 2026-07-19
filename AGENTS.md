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
- After each development stage, add or update a user-facing stage guide under `docs/stage-guides/`.
- Each stage guide must explain what the user can do now, example agent prompts, CLI examples when relevant, current limitations, and risky/uncertain operations.
- Avoid long speculative docs. Prefer concrete decisions, schemas, workflows, and examples.

## Learning And Interview Retrospective Rules

The project is also used to learn AI Agent / Harness engineering and prepare for AI Agent engineering interviews. After each non-trivial development stage, preserve the engineering practice as learning and interview material.

- After each non-trivial development stage, update or add one retrospective document under `docs/learning/stage-retrospectives/YYYY-MM-DD-<short-topic>.md`.
- A retrospective must cover:
  - What was implemented in this stage.
  - Which core modules, CLI, MCP, schemas, services, models, or docs changed.
  - Which design decisions were made and why.
  - Which AI Agent / Harness engineering concepts this work maps to.
  - How to explain this project in interview language.
  - Likely interviewer follow-up questions and recommended answers.
  - Current limitations, risks, and next steps.
- Retrospectives should use the ideas from the learn-claude-code material, especially:
  - Agent product = model + harness.
  - Harness includes tools, knowledge, observation, action interfaces, and permissions.
  - Relevant concepts include agent loop, tool use, permission, skill loading, memory, context management, MCP, multi-agent patterns, and task systems.
  - Do not mechanically copy the tutorial. Explain these ideas through this health and fat-loss assistant.
- In this project, use these mappings:
  - `app/core/services` is the stable business capability layer.
  - CLI, MCP, and future mobile APIs are action interfaces / tool surfaces.
  - The SQLite database is persistent storage for business facts and user records. It is not the same as Agent memory. These records become observation sources when an Agent queries them through core services and injects them into current context. Long-term reusable goals, preferences, habits, and constraints extracted from interaction are closer to Agent memory.
  - `docs`, stage guides, and schema notes are knowledge.
  - Health safety rules, privacy rules, and approval boundaries are permissions / safety boundaries.
  - The future independent Agent layer handles intent understanding, planning, clarification, tool calling, and result explanation.
- Do not let retrospectives slow down small fixes. Only write stage retrospectives for feature work, architecture changes, interface changes, data model changes, or Agent/MCP/CLI capability changes.
- Do not record real personal health data, API keys, private database paths, or any sensitive information in retrospectives.
