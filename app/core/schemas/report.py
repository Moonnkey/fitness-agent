from datetime import date

from pydantic import BaseModel


class TrendDailyPoint(BaseModel):
    date: date
    total_calories: float
    target_calories: float | None
    remaining_calories: float | None
    total_protein_g: float
    target_protein_g: float | None
    activity_calories: float
    net_calories: float
    weight_kg: float | None
    meal_count: int
    activity_count: int


class WeeklySummaryOutput(BaseModel):
    start_date: date
    end_date: date
    days: int
    daily_points: list[TrendDailyPoint]
    total_calories: float
    average_daily_calories: float
    average_daily_protein_g: float
    total_activity_calories: float
    average_net_calories: float
    calorie_target_hit_days: int | None
    protein_target_hit_days: int | None
    days_over_calorie_target: int | None
    days_under_calorie_target: int | None
    weight_start_kg: float | None
    weight_end_kg: float | None
    weight_change_kg: float | None
    notes: list[str]
    report_text: str


class DailyGuidanceOutput(BaseModel):
    date: date
    total_calories: float
    target_calories: float | None
    remaining_calories: float | None
    total_protein_g: float
    target_protein_g: float | None
    remaining_protein_g: float | None
    activity_calories: float
    net_calories: float
    suggested_dinner_calorie_min: int | None
    suggested_dinner_calorie_max: int | None
    guidance: list[str]
    cautions: list[str]
    report_text: str
