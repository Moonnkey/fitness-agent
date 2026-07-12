from datetime import date

import pytest

from app.core.db.session import init_db
from app.core.schemas.activity import ActivityEntryInput
from app.core.schemas.meal import MealItemInput, RecordMealInput
from app.core.schemas.weight import WeightEntryInput
from app.core.services.activity_service import record_activity
from app.core.services.meal_service import record_meal
from app.core.services.record_service import (
    DeleteRecordError,
    delete_record,
    get_record,
    get_records_for_date,
    update_record,
)
from app.core.services.weight_service import record_weight


def test_get_records_for_date_returns_all_record_types() -> None:
    init_db()
    record_meal(
        RecordMealInput(
            date=date(2026, 7, 11),
            meal_type="breakfast",
            raw_text="早餐两个鸡蛋",
            items=[MealItemInput(name="egg", calories=144, protein_g=12)],
        )
    )
    record_weight(
        WeightEntryInput(
            date=date(2026, 7, 11),
            weight_kg=79.6,
            raw_text="早上空腹 79.6kg",
        )
    )
    record_activity(
        ActivityEntryInput(
            date=date(2026, 7, 11),
            activity_type="walking",
            duration_minutes=40,
            calories_burned=180,
            raw_text="快走 40 分钟",
        )
    )
    record_meal(
        RecordMealInput(
            date=date(2026, 7, 12),
            meal_type="lunch",
            items=[MealItemInput(name="rice", calories=200)],
        )
    )

    records = get_records_for_date(date(2026, 7, 11))

    assert len(records.meals) == 1
    assert len(records.weights) == 1
    assert len(records.activities) == 1
    assert records.total_record_count == 3


def test_get_records_for_date_filters_record_type() -> None:
    init_db()
    record_meal(
        RecordMealInput(
            date=date(2026, 7, 11),
            meal_type="breakfast",
            items=[MealItemInput(name="egg", calories=144)],
        )
    )
    record_weight(WeightEntryInput(date=date(2026, 7, 11), weight_kg=79.6))

    records = get_records_for_date(date(2026, 7, 11), record_type="meal")

    assert len(records.meals) == 1
    assert records.weights == []
    assert records.activities == []
    assert records.total_record_count == 1


def test_delete_record_hard_deletes_supported_record_types() -> None:
    init_db()
    meal = record_meal(
        RecordMealInput(
            date=date(2026, 7, 11),
            meal_type="breakfast",
            items=[MealItemInput(name="egg", calories=144)],
        )
    )
    item_id = meal.items[0].id
    weight = record_weight(WeightEntryInput(date=date(2026, 7, 11), weight_kg=79.6))
    activity = record_activity(
        ActivityEntryInput(
            date=date(2026, 7, 11),
            activity_type="walking",
            calories_burned=180,
        )
    )

    deleted_item = delete_record("meal_item", item_id)
    deleted_weight = delete_record("weight", weight.id)
    deleted_activity = delete_record("activity", activity.id)
    deleted_meal = delete_record("meal", meal.id)
    records = get_records_for_date(date(2026, 7, 11))

    assert deleted_item.record_type == "meal_item"
    assert deleted_item.deleted is True
    assert deleted_weight.record_type == "weight"
    assert deleted_activity.record_type == "activity"
    assert deleted_meal.record_type == "meal"
    assert records.total_record_count == 0


def test_delete_record_raises_for_missing_id() -> None:
    init_db()

    with pytest.raises(DeleteRecordError):
        delete_record("meal", 999)


def test_get_record_returns_single_record_detail() -> None:
    init_db()
    meal = record_meal(
        RecordMealInput(
            date=date(2026, 7, 11),
            meal_type="breakfast",
            raw_text="早餐两个鸡蛋",
            items=[MealItemInput(name="egg", calories=144, protein_g=12)],
        )
    )

    detail = get_record("meal", meal.id)

    assert detail.record_type == "meal"
    assert detail.record_id == meal.id
    assert detail.record["raw_text"] == "早餐两个鸡蛋"
    assert detail.record["total_calories"] == 144


def test_update_record_partially_updates_weight() -> None:
    init_db()
    weight = record_weight(WeightEntryInput(date=date(2026, 7, 11), weight_kg=79.6))

    updated = update_record("weight", weight.id, {"weight_kg": 79.2})

    assert updated.record_type == "weight"
    assert updated.changed_fields == ["weight_kg"]
    assert updated.record["weight_kg"] == 79.2
    assert updated.record["updated_at"] is not None


def test_update_meal_item_quantity_does_not_recalculate_nutrition() -> None:
    init_db()
    meal = record_meal(
        RecordMealInput(
            date=date(2026, 7, 11),
            meal_type="breakfast",
            items=[
                MealItemInput(
                    name="鸡蛋",
                    quantity=2,
                    unit="个",
                    calories=144,
                    protein_g=12.6,
                    carbs_g=1.1,
                    fat_g=9.5,
                )
            ],
        )
    )

    updated = update_record("meal_item", meal.items[0].id, {"quantity": 3})

    assert updated.changed_fields == ["quantity"]
    assert updated.record["quantity"] == 3
    assert updated.record["calories"] == 144
    assert updated.record["protein_g"] == 12.6


def test_update_meal_can_append_and_replace_items() -> None:
    init_db()
    meal = record_meal(
        RecordMealInput(
            date=date(2026, 7, 11),
            meal_type="breakfast",
            raw_text="早餐两个鸡蛋",
            items=[MealItemInput(name="鸡蛋", quantity=2, unit="个", calories=144)],
        )
    )

    appended = update_record(
        "meal",
        meal.id,
        {
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
                    "is_estimated": True,
                }
            ],
        },
    )

    replaced = update_record(
        "meal",
        meal.id,
        {
            "raw_text": "早餐改成一个包子",
            "items_replace": [
                {
                    "name": "包子",
                    "quantity": 1,
                    "unit": "个",
                    "calories": 250,
                    "protein_g": 8,
                    "carbs_g": 35,
                    "fat_g": 8,
                    "is_estimated": True,
                }
            ],
        },
    )

    assert appended.changed_fields == ["raw_text", "items_append"]
    assert len(appended.record["items"]) == 2
    assert appended.record["total_calories"] == 224
    assert replaced.changed_fields == ["raw_text", "items_replace"]
    assert len(replaced.record["items"]) == 1
    assert replaced.record["items"][0]["name"] == "包子"
    assert replaced.record["total_calories"] == 250
