from datetime import date

from pydantic import BaseModel

from app.core.schemas.meal import MealOutput


class DailySummaryOutput(BaseModel):
    date: date
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    activity_calories: float
    net_calories: float
    target_calories: float | None
    remaining_calories: float | None
    target_protein_g: float | None
    meal_count: int
    activity_count: int
    estimated_item_count: int
    meals: list[MealOutput]
