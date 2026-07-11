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

## get_daily_summary

Input:

```json
{
  "date_value": "today"
}
```

Use ISO dates such as `2026-07-11` when the user asks for a specific date.
