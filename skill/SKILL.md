---
name: fitness-agent
description: Use when the user wants to record meals, update fitness or fat-loss profile data, or ask for daily calorie and macro summaries through the local Fitness Agent MCP tools. This skill guides agents to call update_user_profile, get_user_profile, record_meal, and get_daily_summary with structured or semi-structured payloads while preserving raw user text and uncertainty metadata.
---

# Fitness Agent

Use the local Fitness Agent MCP tools as the source of truth for profile, meal, and daily summary data.

## Workflow

1. Identify whether the user is updating their profile, recording a meal, or asking for a summary.
2. For profile changes, call `update_user_profile`.
3. For meal records, parse the user's description into structured meal items before calling `record_meal`.
4. Preserve the original user wording in `raw_text`.
5. Put estimation assumptions, confidence, cooking method, brand, or missing context in `metadata`.
6. For daily totals or remaining calories, call `get_daily_summary`.
7. Mark calories and macros as estimates unless the source is user-provided or database-derived.

## Tool Contracts

Read `references/tool-contracts.md` before constructing unfamiliar payloads.

## Safety

Do not provide medical diagnosis. Do not recommend extreme restriction, dehydration, purging, or unsafe rapid weight loss. Encourage professional help for symptoms, injuries, eating disorder signals, or medical conditions.
