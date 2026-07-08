# Fitness Agent MVP

## Objective

Create a local-first AI fitness and fat-loss assistant that can record daily meals, weight, and simple exercise data, then summarize calorie intake, estimated expenditure, and progress toward a user's goal.

The first version should prove the core loop:

```text
User describes data
  -> Agent or CLI sends structured input
  -> Core service validates and records it
  -> SQLite stores it locally
  -> Summary service returns useful daily totals
```

## Target User

The initial target user is a single local user who wants help tracking fat-loss behavior and receiving basic daily guidance. Multi-user support and cloud sync are intentionally out of scope for the MVP.

## In Scope

### User Profile

- Create or update a local user profile.
- Store height, weight, age, sex, activity level, and goal weight.
- Estimate BMR and TDEE from profile data.
- Store target daily calories and protein target when available.

### Meal Tracking

- Record meals by date and meal type.
- Store food items, quantity, unit, estimated grams when available, calories, protein, carbs, and fat.
- Allow manually supplied nutrition values.
- Support estimated values when exact data is unavailable.
- Return per-meal and per-day totals.

### Weight Tracking

- Record body weight by date.
- Return latest weight.
- Return simple 7-day average once enough data exists.

### Activity And Workout Tracking

- Record simple activities such as walking, running, cycling, or strength training.
- Store duration and estimated calories burned when available.
- Record basic strength workouts as free-form or simple structured entries in the MVP.

### Daily Summary

- Show total calorie intake for a date.
- Show estimated activity calories for a date.
- Show target calories when profile and goal data exist.
- Show remaining calories relative to target.
- Show protein total and protein target when available.
- Mark estimated values clearly.

### CLI

- Provide a Python CLI for local usage and testing.
- Initial commands should cover profile setup, meal recording, weight recording, activity recording, and daily summary.

### MCP Tools

- Expose core capabilities as MCP tools after the CLI and services work.
- Initial MCP tools:
  - `record_meal`
  - `record_weight`
  - `record_activity`
  - `get_daily_summary`
  - `get_user_profile`
  - `update_user_profile`

### Skill

- Create a Codex/Agent Skill after the MCP tools exist.
- The Skill should explain when to record data, when to ask follow-up questions, when to estimate, and how to summarize uncertainty.

## Out Of Scope

- Web UI.
- Mobile app.
- Multi-user accounts.
- Authentication.
- Cloud sync.
- Payment or subscription features.
- Full workout programming engine.
- Full RAG knowledge base.
- Model fine-tuning or distillation.
- Automated meal photo recognition.
- Wearable device integrations.
- Public plugin distribution.

## Suggested First Milestone

The first milestone is complete when all of the following work locally:

```text
1. Initialize a profile.
2. Record one meal.
3. Record one weight entry.
4. Record one activity.
5. Ask for today's summary through the CLI.
6. Persist data in SQLite.
7. Run tests for core summary logic.
```

## Suggested Second Milestone

The second milestone is complete when:

```text
1. MCP server starts locally.
2. MCP tools can call the same core services used by the CLI.
3. Agent can record a meal through MCP.
4. Agent can query the daily summary through MCP.
5. Basic Skill instructions exist.
```

## Data Quality Principles

- Prefer structured values over free text once data reaches core services.
- Keep original user text where useful for later audit.
- Store whether values are user-provided, database-derived, or estimated.
- Do not hide uncertainty. Estimated values should be visible in summaries.

## Safety Principles

- Avoid unsafe weight-loss guidance.
- Avoid medical diagnosis.
- Encourage professional consultation for symptoms, injuries, eating disorder signals, or medical conditions.
- Keep advice practical and conservative.

## Future Directions

After the MVP works:

- Add a food knowledge source or nutrition database.
- Add weekly trend analysis.
- Add structured strength training logs with exercise and muscle-group mapping.
- Add RAG for nutrition and training knowledge.
- Add an installable plugin package.
- Add a web or mobile interface if the local assistant proves useful.
