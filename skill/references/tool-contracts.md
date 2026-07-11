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

## get_daily_summary

Input:

```json
{
  "date_value": "today"
}
```

Use ISO dates such as `2026-07-11` when the user asks for a specific date.
