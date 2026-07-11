# History Delete Duplicate Implementation Plan

> Superpowers-style local plan. The installed Codex skills do not currently include
> `superpowers`, so this document keeps the same plan-and-checklist workflow inside
> the repo.

**Goal:** Add history lookup, hard delete, and duplicate warnings for meals, weight
entries, and activity entries. MCP is the primary integration surface for agents;
CLI mirrors the same operations for local debugging.

**Architecture:** Keep business logic in `app/core/services`. Add reusable history
and deletion operations in core services, then expose them through thin CLI and MCP
wrappers. Duplicate warnings are advisory: tools return possible duplicate records,
and the agent decides whether to ask the user or continue based on explicit user
instructions.

**Scope:**

- Query all records for a date.
- Query records by type for a date.
- Delete a meal, meal item, weight entry, or activity entry by id.
- Warn about possible duplicates when recording meals, weights, or activities.
- Update Skill and user guide with the new workflow.

**Out of scope:**

- Soft delete or audit trail.
- Editing records.
- Fuzzy natural language matching.
- Cross-day duplicate detection.
- Cloud sync or multi-user history.

## Duplicate Rules

- Meal: same date and meal type plus matching `raw_text`, or matching item names and
  close total calories.
- Weight: same date plus matching `raw_text`, or same date and same `weight_kg`.
- Activity: same date plus matching `raw_text`, or same date, activity type,
  duration, and calories burned.

## Checklist

- [ ] Add service tests for history lookup and hard delete.
- [ ] Add service tests for duplicate warnings.
- [ ] Implement core schemas and services.
- [ ] Add CLI `history` and delete commands.
- [ ] Add MCP tools for history, delete, and duplicate check.
- [ ] Update Skill contracts and Chinese user guide.
- [ ] Run pytest, ruff, and CLI smoke checks.
