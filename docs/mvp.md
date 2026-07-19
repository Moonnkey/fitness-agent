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
- Initial commands should cover profile setup, meal recording, weight recording, activity recording, history lookup, deletion, and daily summary.

### MCP Tools

- Expose core capabilities as MCP tools after the CLI and services work.
- Initial MCP tools:
  - `record_meal`
  - `record_weight`
  - `record_activity`
  - `get_daily_summary`
  - `get_user_profile`
  - `update_user_profile`
  - `get_records_for_date`
  - `delete_record`
  - `check_duplicate_meal`
  - `check_duplicate_weight`
  - `check_duplicate_activity`

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

## Suggested Third Milestone

The third milestone is complete when:

```text
1. Record one weight entry through CLI and MCP.
2. Return latest weight and a simple 7-day average when enough data exists.
3. Record one activity entry through CLI and MCP.
4. Daily summary includes activity calories and net calories.
5. Skill tool contracts document weight and activity tools.
```

## Suggested Fourth Milestone

The fourth milestone is complete when:

```text
1. Query meals, weight entries, and activities for a date through CLI and MCP.
2. Filter history by record type when the user asks for one category.
3. Hard-delete meals, meal items, weight entries, and activity entries by id.
4. Return duplicate warnings for meals, weight entries, and activities.
5. Skill and user guide explain how agents should confirm before saving likely duplicates.
```

## Suggested Fifth Milestone

The fifth milestone is complete when:

```text
1. Fetch one meal, meal item, weight entry, or activity entry by id.
2. Partially update one record by id through CLI and MCP.
3. Update meal outer fields, append meal items, and replace all meal items when requested.
4. Return updated records with changed_fields.
5. Preserve updated_at for edited records.
6. Skill and user guide explain that nutrition is not automatically recalculated on quantity edits.
```

## Suggested Sixth Milestone

The sixth milestone is complete when:

```text
1. Return a 7-day text weekly report through CLI and MCP.
2. Return structured daily trend points for future chart/front-end use.
3. Return day-level guidance based on current intake, targets, protein, and activity.
4. Include Chinese report_text for direct agent responses.
5. Document limitations: no exact meal planning, food database, RAG, or frontend charts yet.
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
- Add weekly trend analysis beyond the simple 7-day weight average.
- Add structured strength training logs with exercise and muscle-group mapping.
- Add RAG for nutrition and training knowledge.
- Add an installable plugin package.
- Add a web or mobile interface if the local assistant proves useful.
