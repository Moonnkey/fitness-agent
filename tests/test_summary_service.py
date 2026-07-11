from datetime import date

from app.core.db.session import init_db
from app.core.schemas.activity import ActivityEntryInput
from app.core.schemas.meal import MealItemInput, RecordMealInput
from app.core.schemas.profile import UserProfileInput
from app.core.services.activity_service import record_activity
from app.core.services.meal_service import record_meal
from app.core.services.profile_service import update_user_profile
from app.core.services.summary_service import get_daily_summary


def test_empty_day_summary_returns_zero_totals() -> None:
    init_db()

    summary = get_daily_summary(date(2026, 7, 11))

    assert summary.total_calories == 0
    assert summary.meal_count == 0
    assert summary.estimated_item_count == 0


def test_daily_summary_totals_meals_and_targets() -> None:
    init_db()
    update_user_profile(
        UserProfileInput(
            height_cm=180,
            weight_kg=80,
            age=30,
            sex="male",
            activity_level="moderate",
            goal_type="fat_loss",
            target_calories=2200,
            target_protein_g=150,
        )
    )
    record_meal(
        RecordMealInput(
            date=date(2026, 7, 11),
            meal_type="breakfast",
            items=[
                MealItemInput(name="egg", calories=144, protein_g=12, carbs_g=1, fat_g=10),
                MealItemInput(
                    name="rice",
                    calories=260,
                    protein_g=5,
                    carbs_g=58,
                    fat_g=1,
                    is_estimated=True,
                    source="agent_estimate",
                ),
            ],
        )
    )

    summary = get_daily_summary(date(2026, 7, 11))

    assert summary.total_calories == 404
    assert summary.total_protein_g == 17
    assert summary.total_carbs_g == 59
    assert summary.total_fat_g == 11
    assert summary.target_calories == 2200
    assert summary.remaining_calories == 1796
    assert summary.target_protein_g == 150
    assert summary.meal_count == 1
    assert summary.estimated_item_count == 1
    assert summary.meals[0].total_calories == 404


def test_daily_summary_includes_activity_and_net_calories() -> None:
    init_db()
    record_meal(
        RecordMealInput(
            date=date(2026, 7, 11),
            meal_type="breakfast",
            items=[MealItemInput(name="egg", calories=144, protein_g=12)],
        )
    )
    record_activity(
        ActivityEntryInput(
            date=date(2026, 7, 11),
            activity_type="walking",
            calories_burned=80,
            is_estimated=True,
        )
    )

    summary = get_daily_summary(date(2026, 7, 11))

    assert summary.activity_calories == 80
    assert summary.net_calories == 64
    assert summary.activity_count == 1
