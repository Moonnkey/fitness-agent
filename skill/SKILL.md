---
name: fitness-agent
description: Use when the user wants to record, inspect, edit, or delete meals, body weight, activity, update fitness or fat-loss profile data, ask for daily calorie and macro summaries, weekly reports, trends, or day-level guidance through the local Fitness Agent MCP tools. This skill guides agents to call update_user_profile, get_user_profile, record_meal, record_weight, get_weight_trend, record_activity, get_records_for_date, get_record, update_record, delete_record, duplicate-check tools, get_daily_summary, get_weekly_summary, and get_daily_guidance with structured or semi-structured payloads while preserving raw user text and uncertainty metadata.
---

# Fitness Agent

Use the local Fitness Agent MCP tools as the source of truth for profile, meal, weight,
activity, history, editing, deletion, daily summary, weekly report, and guidance data.

## Workflow

1. Identify whether the user is updating their profile, recording a meal, recording body weight, recording activity, or asking for a summary.
2. For profile changes, call `update_user_profile`.
3. For meal records, parse the user's description into structured meal items before calling `record_meal`.
4. Before recording data that looks similar to an existing entry, call the matching duplicate-check tool or inspect `duplicate_warnings`.
5. If a duplicate warning appears and the user did not explicitly say to save anyway, ask a short confirmation question before recording another copy.
6. For body weight observations, call `record_weight`; do not infer trends from a single weigh-in.
7. For simple exercise or activity calorie records, call `record_activity`.
8. For history questions, call `get_records_for_date`; use `record_type` to narrow to meals, weights, or activities when the user asks for one category.
9. For detail questions, call `get_record` after identifying the record type and id.
10. For correction requests, first identify candidate records with `get_records_for_date`; if more than one plausible candidate exists, ask the user to confirm before calling `update_record` or `delete_record`.
11. Use `update_record` for partial edits. The backend does not automatically recalculate nutrition, so if quantity or food identity changes, provide updated calories, protein, carbs, and fat in the patch.
12. For meal-level edits, use `items_append` to add food items and `items_replace` to replace all items in a meal.
13. For deletion requests such as "删掉刚才那条", identify the record id first, then call `delete_record`.
14. Preserve the original user wording in `raw_text`.
15. Put estimation assumptions, confidence, cooking method, brand, activity intensity, or missing context in `metadata`.
16. For recent body-weight questions, call `get_weight_trend`.
17. For daily totals or remaining calories, call `get_daily_summary`.
18. For weekly performance, trend, or "this week" questions, call `get_weekly_summary`.
19. For "what should I eat later today" or day-level adjustment questions, call `get_daily_guidance`.
20. Use `report_text` for direct user-facing summaries, and use structured fields such as `daily_points` when the user asks for detailed numbers.
21. Mark calories, macros, and activity burn as estimates unless the source is user-provided or database-derived.

## Tool Contracts

Read `references/tool-contracts.md` before constructing unfamiliar payloads.

## Safety

Do not provide medical diagnosis. Do not recommend extreme restriction, dehydration, purging, or unsafe rapid weight loss. Encourage professional help for symptoms, injuries, eating disorder signals, or medical conditions.
