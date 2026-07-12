# Record Detail Update Implementation Plan

> Superpowers-style local plan. The installed Codex skills do not currently include
> `superpowers`, so this document keeps the same plan-and-checklist workflow inside
> the repo.

**Goal:** Add single-record lookup and partial update support for meals, meal items,
weight entries, and activity entries. MCP remains the primary agent-facing surface;
CLI mirrors the same operations for local debugging.

## Decisions

- Use unified tools:
  - `get_record(record_type, record_id)`
  - `update_record(record_type, record_id, patch)`
- Support partial updates.
- The backend does not automatically recalculate nutrition when quantity changes.
  Agents must provide updated calories and macros when a correction changes them.
- For `meal`, support:
  - updating outer fields such as `date`, `meal_type`, `raw_text`, `metadata`, `note`
  - `items_replace` to replace all meal items
  - `items_append` to add new meal items
- For `meal_item`, support partial field updates.
- Editing overwrites the current record and updates `updated_at`; no full audit log yet.
- Update tools return the updated full record plus `changed_fields`.
- When user intent is ambiguous, agents must identify candidates and ask for confirmation
  before updating.

## Compatibility

Existing local SQLite databases may not have `updated_at` columns on `meal_items`,
`weight_entries`, or `activity_entries`. Add a small local schema upgrade in
`init_db()` so existing MVP databases keep working without Alembic.

## Checklist

- [ ] Add schemas for record detail and update results.
- [ ] Add `updated_at` to meal items, weight entries, and activity entries.
- [ ] Add SQLite compatibility upgrade for missing `updated_at` columns.
- [ ] Add service tests for `get_record`.
- [ ] Add service tests for `update_record` partial updates.
- [ ] Add service tests for `items_replace` and `items_append`.
- [ ] Add CLI `records show` and `records update`.
- [ ] Add MCP `get_record` and `update_record`.
- [ ] Update Skill contracts and Chinese user guide.
- [ ] Run pytest, ruff, and CLI smoke checks.
