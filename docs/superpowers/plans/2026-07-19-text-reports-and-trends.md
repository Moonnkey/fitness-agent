# Text Reports And Trends Implementation Plan

> Superpowers-style local plan. The installed Codex skills do not currently include
> `superpowers`, so this document keeps the same plan-and-checklist workflow inside
> the repo.

**Goal:** Add text-based weekly summaries, trend points, and daily guidance. MCP
returns structured data for future front-end charts plus Chinese `report_text` for
current agent responses.

## Decisions

- Default weekly range is the latest 7 days including the end date.
- Current phase is text-first; no web UI or chart rendering yet.
- Preserve structured `daily_points` so a future frontend can plot calories,
  protein, activity, net calories, and weight.
- Guidance is conservative general coaching guidance, not medical advice.
- No food database, exact meal planning engine, RAG, or training plan generation.

## New Core Outputs

- `get_weekly_summary(end_date, days=7)`
- `get_daily_guidance(target_date)`

## New MCP Tools

- `get_weekly_summary`
- `get_daily_guidance`

## New CLI Commands

- `fitness-agent summary week --days 7`
- `fitness-agent guidance today`
- `fitness-agent guidance date 2026-07-19`

## Checklist

- [ ] Add report schemas with `daily_points` and `report_text`.
- [ ] Add report service tests for weekly summary.
- [ ] Add guidance service tests for daily guidance.
- [ ] Implement report service using existing summary/profile/weight services.
- [ ] Add CLI commands.
- [ ] Add MCP tools.
- [ ] Update Skill contracts and user-facing stage guide.
- [ ] Run pytest, ruff, and CLI smoke checks.
