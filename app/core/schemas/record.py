from datetime import date
from typing import Literal

from pydantic import BaseModel, Field

from app.core.schemas.activity import ActivityEntryOutput
from app.core.schemas.meal import MealOutput
from app.core.schemas.weight import WeightEntryOutput

RecordType = Literal["all", "meal", "meal_item", "weight", "activity"]
DeletableRecordType = Literal["meal", "meal_item", "weight", "activity"]


class DailyRecordsOutput(BaseModel):
    date: date
    record_type: RecordType
    meals: list[MealOutput] = Field(default_factory=list)
    weights: list[WeightEntryOutput] = Field(default_factory=list)
    activities: list[ActivityEntryOutput] = Field(default_factory=list)
    total_record_count: int


class DeleteRecordOutput(BaseModel):
    record_type: DeletableRecordType
    record_id: int
    deleted: bool
