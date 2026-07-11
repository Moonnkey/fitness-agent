from datetime import date

from app.core.db.session import init_db
from app.core.schemas.meal import MealItemInput, RecordMealInput
from app.core.services.meal_service import list_meals_for_date, record_meal


def test_record_meal_preserves_items_raw_text_and_metadata() -> None:
    init_db()

    meal = record_meal(
        RecordMealInput(
            date=date(2026, 7, 11),
            meal_type="breakfast",
            raw_text="早餐吃了两个鸡蛋",
            metadata={"agent": "codex", "confidence": 0.8},
            items=[
                MealItemInput(
                    name="鸡蛋",
                    quantity=2,
                    unit="个",
                    calories=144,
                    protein_g=12,
                    carbs_g=1,
                    fat_g=10,
                    is_estimated=True,
                    source="agent_estimate",
                    raw_text="两个鸡蛋",
                    metadata={"assumption": "普通水煮蛋"},
                )
            ],
        )
    )

    assert meal.id > 0
    assert meal.raw_text == "早餐吃了两个鸡蛋"
    assert meal.metadata == {"agent": "codex", "confidence": 0.8}
    assert meal.total_calories == 144
    assert meal.estimated_item_count == 1
    assert meal.items[0].metadata == {"assumption": "普通水煮蛋"}


def test_list_meals_for_date_filters_by_date() -> None:
    init_db()
    record_meal(
        RecordMealInput(
            date=date(2026, 7, 11),
            meal_type="breakfast",
            items=[MealItemInput(name="egg", calories=100)],
        )
    )
    record_meal(
        RecordMealInput(
            date=date(2026, 7, 12),
            meal_type="lunch",
            items=[MealItemInput(name="rice", calories=200)],
        )
    )

    meals = list_meals_for_date(date(2026, 7, 11))

    assert len(meals) == 1
    assert meals[0].meal_type == "breakfast"
