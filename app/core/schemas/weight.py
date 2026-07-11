from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class WeightEntryInput(BaseModel):
    date: date
    weight_kg: float = Field(gt=0)
    raw_text: str | None = None
    metadata: dict[str, Any] | None = None
    note: str | None = None


class WeightEntryOutput(WeightEntryInput):
    model_config = ConfigDict(from_attributes=True)

    id: int
    duplicate_warnings: list[dict[str, Any]] = Field(default_factory=list)


class WeightDuplicateWarning(BaseModel):
    record_type: Literal["weight"] = "weight"
    record_id: int
    reason: str
    message: str
    record: WeightEntryOutput


class WeightTrendOutput(BaseModel):
    latest_weight_kg: float | None
    latest_date: date | None
    average_weight_kg: float | None
    days: int
    entry_count: int
    entries: list[WeightEntryOutput]
