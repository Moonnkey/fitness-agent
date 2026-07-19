from datetime import date

from app.core.db.session import init_db
from app.core.schemas.activity import ActivityEntryInput
from app.core.schemas.meal import MealItemInput, RecordMealInput
from app.core.schemas.profile import UserProfileInput
from app.core.schemas.weight import WeightEntryInput
from app.core.services.activity_service import record_activity
from app.core.services.meal_service import record_meal
from app.core.services.profile_service import update_user_profile
from app.core.services.report_service import get_daily_guidance, get_weekly_summary
from app.core.services.weight_service import record_weight


def test_weekly_summary_returns_structured_points_and_report_text() -> None:
    init_db()
    update_user_profile(
        UserProfileInput(
            height_cm=180,
            weight_kg=80,
            age=30,
            sex="male",
            activity_level="moderate",
            goal_type="fat_loss",
            target_calories=2000,
            target_protein_g=150,
        )
    )
    record_meal(
        RecordMealInput(
            date=date(2026, 7, 18),
            meal_type="breakfast",
            items=[MealItemInput(name="egg", calories=500, protein_g=40)],
        )
    )
    record_meal(
        RecordMealInput(
            date=date(2026, 7, 19),
            meal_type="lunch",
            items=[MealItemInput(name="chicken", calories=2100, protein_g=160)],
        )
    )
    record_activity(
        ActivityEntryInput(
            date=date(2026, 7, 19),
            activity_type="walking",
            calories_burned=200,
        )
    )
    record_weight(WeightEntryInput(date=date(2026, 7, 13), weight_kg=80.0))
    record_weight(WeightEntryInput(date=date(2026, 7, 19), weight_kg=79.2))

    summary = get_weekly_summary(end_date=date(2026, 7, 19), days=7)

    assert summary.start_date == date(2026, 7, 13)
    assert summary.end_date == date(2026, 7, 19)
    assert len(summary.daily_points) == 7
    assert summary.total_calories == 2600
    assert summary.average_daily_calories == 371.43
    assert summary.average_daily_protein_g == 28.57
    assert summary.total_activity_calories == 200
    assert summary.average_net_calories == 342.86
    assert summary.calorie_target_hit_days == 6
    assert summary.protein_target_hit_days == 1
    assert summary.days_over_calorie_target == 1
    assert summary.weight_start_kg == 80.0
    assert summary.weight_end_kg == 79.2
    assert summary.weight_change_kg == -0.8
    assert summary.daily_points[-1].date == date(2026, 7, 19)
    assert summary.daily_points[-1].weight_kg == 79.2
    assert "过去 7 天" in summary.report_text


def test_daily_guidance_returns_remaining_targets_and_text() -> None:
    init_db()
    update_user_profile(
        UserProfileInput(
            height_cm=180,
            weight_kg=80,
            age=30,
            sex="male",
            activity_level="moderate",
            goal_type="fat_loss",
            target_calories=2000,
            target_protein_g=150,
        )
    )
    record_meal(
        RecordMealInput(
            date=date(2026, 7, 19),
            meal_type="breakfast",
            items=[MealItemInput(name="egg", calories=1200, protein_g=70)],
        )
    )

    guidance = get_daily_guidance(date(2026, 7, 19))

    assert guidance.date == date(2026, 7, 19)
    assert guidance.remaining_calories == 800
    assert guidance.remaining_protein_g == 80
    assert guidance.suggested_dinner_calorie_min == 600
    assert guidance.suggested_dinner_calorie_max == 800
    assert guidance.guidance
    assert "今天目前摄入" in guidance.report_text


def test_daily_guidance_without_profile_surfaces_missing_targets() -> None:
    init_db()

    guidance = get_daily_guidance(date(2026, 7, 19))

    assert guidance.target_calories is None
    assert guidance.remaining_calories is None
    assert guidance.suggested_dinner_calorie_min is None
    assert guidance.cautions == ["还没有用户档案，无法计算目标热量和蛋白质目标。"]
