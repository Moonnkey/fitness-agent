---
name: fitness-agent
description: Use when the user wants to record, inspect, or delete meals, body weight, activity, update fitness or fat-loss profile data, or ask for daily calorie and macro summaries through the local Fitness Agent MCP tools. This skill guides agents to call update_user_profile, get_user_profile, record_meal, record_weight, get_weight_trend, record_activity, get_records_for_date, delete_record, duplicate-check tools, and get_daily_summary with structured or semi-structured payloads while preserving raw user text and uncertainty metadata.
---

# Fitness Agent

Use the local Fitness Agent MCP tools as the source of truth for profile, meal, weight,
activity, history, deletion, and daily summary data.

## Workflow

1. Identify whether the user is updating their profile, recording a meal, recording body weight, recording activity, or asking for a summary.
2. For profile changes, call `update_user_profile`.
3. For meal records, parse the user's description into structured meal items before calling `record_meal`.
4. Before recording data that looks similar to an existing entry, call the matching duplicate-check tool or inspect `duplicate_warnings`.
5. If a duplicate warning appears and the user did not explicitly say to save anyway, ask a short confirmation question before recording another copy.
6. For body weight observations, call `record_weight`; do not infer trends from a single weigh-in.
7. For simple exercise or activity calorie records, call `record_activity`.
8. For history questions, call `get_records_for_date`; use `record_type` to narrow to meals, weights, or activities when the user asks for one category.
9. For correction requests such as "删掉刚才那条", first identify the record id with `get_records_for_date`, then call `delete_record`.
10. Preserve the original user wording in `raw_text`.
11. Put estimation assumptions, confidence, cooking method, brand, activity intensity, or missing context in `metadata`.
12. For recent body-weight questions, call `get_weight_trend`.
13. For daily totals or remaining calories, call `get_daily_summary`.
14. Mark calories, macros, and activity burn as estimates unless the source is user-provided or database-derived.

## Tool Contracts

Read `references/tool-contracts.md` before constructing unfamiliar payloads.

## Safety

Do not provide medical diagnosis. Do not recommend extreme restriction, dehydration, purging, or unsafe rapid weight loss. Encourage professional help for symptoms, injuries, eating disorder signals, or medical conditions.
