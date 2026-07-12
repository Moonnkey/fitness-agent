# Fitness Agent Tool Contracts

## update_user_profile

Input:

```json
{
  "profile": {
    "height_cm": 180,
    "weight_kg": 80,
    "age": 30,
    "sex": "male",
    "activity_level": "moderate",
    "goal_type": "fat_loss",
    "goal_weight_kg": 72,
    "target_calories": 2200,
    "target_protein_g": 150
  }
}
```

Manual `target_calories` and `target_protein_g` are optional and take precedence over calculated values.

## get_user_profile

Input:

```json
{}
```

Returns an object with a `profile` field:

```json
{
  "profile": null
}
```

When a profile exists, `profile` contains the same fields returned by `update_user_profile`.

## record_meal

Input:

```json
{
  "meal": {
    "date": "today",
    "meal_type": "breakfast",
    "raw_text": "早餐吃了两个鸡蛋",
    "metadata": {
      "agent": "codex",
      "confidence": 0.8
    },
    "items": [
      {
        "name": "鸡蛋",
        "quantity": 2,
        "unit": "个",
        "calories": 144,
        "protein_g": 12,
        "carbs_g": 1,
        "fat_g": 10,
        "is_estimated": true,
        "source": "agent_estimate",
        "raw_text": "两个鸡蛋",
        "metadata": {
          "assumption": "普通水煮蛋"
        }
      }
    ]
  }
}
```

The backend does not parse natural language. The agent should parse or estimate fields before calling `record_meal`.
The response may include `duplicate_warnings`; if present and the user did not explicitly request another copy, ask for confirmation before saving more duplicate records.

## check_duplicate_meal

Input uses the same `meal` payload as `record_meal`:

```json
{
  "meal": {
    "date": "today",
    "meal_type": "breakfast",
    "raw_text": "早餐吃了两个鸡蛋",
    "items": [
      {
        "name": "鸡蛋",
        "quantity": 2,
        "unit": "个",
        "calories": 144
      }
    ]
  }
}
```

Returns:

```json
{
  "duplicates": []
}
```

## record_weight

Input:

```json
{
  "weight": {
    "date": "today",
    "weight_kg": 79.6,
    "raw_text": "今天早上空腹 79.6kg",
    "metadata": {
      "timing": "morning fasting"
    }
  }
}
```

Use this for body-weight observations. Do not treat one entry as a trend.
The response may include `duplicate_warnings`.

## check_duplicate_weight

Input uses the same `weight` payload as `record_weight`.

## get_weight_trend

Input:

```json
{
  "days": 7
}
```

Returns latest weight, latest date, simple average weight, entry count, and included entries.

## record_activity

Input:

```json
{
  "activity": {
    "date": "today",
    "activity_type": "walking",
    "duration_minutes": 40,
    "calories_burned": 180,
    "is_estimated": true,
    "raw_text": "今天快走 40 分钟",
    "metadata": {
      "estimation_basis": "中等强度快走估算"
    }
  }
}
```

Use this for simple activity or workout calorie expenditure. It does not model exercise sets, muscle groups, recovery, or training-plan quality.
The response may include `duplicate_warnings`.

## check_duplicate_activity

Input uses the same `activity` payload as `record_activity`.

## get_daily_summary

Input:

```json
{
  "date_value": "today"
}
```

Use ISO dates such as `2026-07-11` when the user asks for a specific date.

## get_records_for_date

Input:

```json
{
  "date_value": "today",
  "record_type": "all"
}
```

Allowed `record_type` values:

- `all`
- `meal`
- `meal_item`
- `weight`
- `activity`

Use this before deletion when the user refers to a record indirectly, such as "delete the breakfast I just added".

## delete_record

Input:

```json
{
  "record_type": "meal",
  "record_id": 1
}
```

Allowed `record_type` values:

- `meal`
- `meal_item`
- `weight`
- `activity`

This is a hard delete. Confirm intent when the user has not clearly requested deletion.

## get_record

Input:

```json
{
  "record_type": "meal",
  "record_id": 1
}
```

Allowed `record_type` values:

- `meal`
- `meal_item`
- `weight`
- `activity`

Use this when the user asks for one record's details or before applying a precise edit.

## update_record

Input:

```json
{
  "record_type": "weight",
  "record_id": 1,
  "patch": {
    "weight_kg": 79.2
  }
}
```

Returns the updated full record and `changed_fields`.

For `meal_item`, partial patches are supported:

```json
{
  "record_type": "meal_item",
  "record_id": 1,
  "patch": {
    "quantity": 3,
    "calories": 216,
    "protein_g": 18.9,
    "carbs_g": 1.65,
    "fat_g": 14.25
  }
}
```

The backend does not automatically recalculate calories or macros when quantity changes. If the edit affects nutrition, the agent must estimate or otherwise provide updated nutrition fields in the patch.

For `meal`, update outer fields directly and use `items_append` or `items_replace` for food items:

```json
{
  "record_type": "meal",
  "record_id": 1,
  "patch": {
    "raw_text": "早餐两个鸡蛋和一杯无糖豆浆",
    "items_append": [
      {
        "name": "无糖豆浆",
        "quantity": 1,
        "unit": "杯",
        "calories": 80,
        "protein_g": 7,
        "carbs_g": 4,
        "fat_g": 4,
        "is_estimated": true
      }
    ]
  }
}
```

Use `items_replace` only when the user clearly wants to replace the whole meal contents.
