from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Sex = Literal["male", "female"]
ActivityLevel = Literal["sedentary", "light", "moderate", "active", "very_active"]
GoalType = Literal["fat_loss", "muscle_gain", "maintenance", "recomposition"]


class UserProfileInput(BaseModel):
    height_cm: float | None = Field(default=None, gt=0)
    weight_kg: float | None = Field(default=None, gt=0)
    age: int | None = Field(default=None, gt=0)
    sex: Sex | None = None
    activity_level: ActivityLevel | None = None
    goal_type: GoalType | None = None
    goal_weight_kg: float | None = Field(default=None, gt=0)
    target_calories: float | None = Field(default=None, gt=0)
    target_protein_g: float | None = Field(default=None, gt=0)


class UserProfileOutput(UserProfileInput):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bmr: int | None = None
    tdee: int | None = None
    calculated_target_calories: int | None = None
    calculated_target_protein_g: int | None = None
