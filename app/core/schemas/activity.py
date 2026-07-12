from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ActivityEntryInput(BaseModel):
    date: date
    activity_type: str
    duration_minutes: float | None = Field(default=None, ge=0)
    calories_burned: float = Field(default=0, ge=0)
    is_estimated: bool = True
    raw_text: str | None = None
    metadata: dict[str, Any] | None = None
    note: str | None = None


class ActivityEntryOutput(ActivityEntryInput):
    model_config = ConfigDict(from_attributes=True)

    id: int
    updated_at: datetime | None = None
    duplicate_warnings: list[dict[str, Any]] = Field(default_factory=list)


class ActivityDuplicateWarning(BaseModel):
    record_type: Literal["activity"] = "activity"
    record_id: int
    reason: str
    message: str
    record: ActivityEntryOutput
