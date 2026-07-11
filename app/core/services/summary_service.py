from datetime import date

from app.core.schemas.summary import DailySummaryOutput
from app.core.services.meal_service import list_meals_for_date
from app.core.services.profile_service import get_user_profile


def get_daily_summary(target_date: date) -> DailySummaryOutput:
    meals = list_meals_for_date(target_date)
    total_calories = sum(meal.total_calories for meal in meals)
    total_protein_g = sum(meal.total_protein_g for meal in meals)
    total_carbs_g = sum(meal.total_carbs_g for meal in meals)
    total_fat_g = sum(meal.total_fat_g for meal in meals)
    estimated_item_count = sum(meal.estimated_item_count for meal in meals)

    profile = get_user_profile()
    target_calories = None
    target_protein_g = None
    if profile is not None:
        target_calories = profile.target_calories or profile.calculated_target_calories
        target_protein_g = profile.target_protein_g or profile.calculated_target_protein_g

    remaining_calories = None
    if target_calories is not None:
        remaining_calories = target_calories - total_calories

    return DailySummaryOutput(
        date=target_date,
        total_calories=total_calories,
        total_protein_g=total_protein_g,
        total_carbs_g=total_carbs_g,
        total_fat_g=total_fat_g,
        target_calories=target_calories,
        remaining_calories=remaining_calories,
        target_protein_g=target_protein_g,
        meal_count=len(meals),
        estimated_item_count=estimated_item_count,
        meals=meals,
    )
