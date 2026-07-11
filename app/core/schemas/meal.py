from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

MealType = Literal["breakfast", "lunch", "dinner", "snack", "other"]
NutritionSource = Literal["user", "manual_estimate", "food_database", "agent_estimate"]


class MealItemInput(BaseModel):
    name: str
    quantity: float | None = Field(default=None, gt=0)
    unit: str | None = None
    grams: float | None = Field(default=None, gt=0)
    calories: float = Field(default=0, ge=0)
    protein_g: float = Field(default=0, ge=0)
    carbs_g: float = Field(default=0, ge=0)
    fat_g: float = Field(default=0, ge=0)
    source: NutritionSource = "user"
    is_estimated: bool = False
    raw_text: str | None = None
    metadata: dict[str, Any] | None = None
    note: str | None = None


class RecordMealInput(BaseModel):
    date: date
    meal_type: MealType
    raw_text: str | None = None
    metadata: dict[str, Any] | None = None
    note: str | None = None
    items: list[MealItemInput] = Field(min_length=1)


class MealItemOutput(MealItemInput):
    model_config = ConfigDict(from_attributes=True)

    id: int


class MealOutput(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    meal_type: MealType
    raw_text: str | None = None
    metadata: dict[str, Any] | None = None
    note: str | None = None
    items: list[MealItemOutput]
    total_calories: float
    total_protein_g: float
    total_carbs_g: float
    total_fat_g: float
    estimated_item_count: int
    duplicate_warnings: list[dict[str, Any]] = Field(default_factory=list)


class MealDuplicateWarning(BaseModel):
    record_type: Literal["meal"] = "meal"
    record_id: int
    reason: str
    message: str
    record: MealOutput
