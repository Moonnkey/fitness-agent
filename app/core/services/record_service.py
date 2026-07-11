from datetime import date

from sqlalchemy import select

from app.core.db.session import session_scope
from app.core.models.activity import ActivityEntry
from app.core.models.meal import Meal, MealItem
from app.core.models.weight import WeightEntry
from app.core.schemas.record import (
    DailyRecordsOutput,
    DeletableRecordType,
    DeleteRecordOutput,
    RecordType,
)
from app.core.services.activity_service import list_activities_for_date
from app.core.services.meal_service import list_meals_for_date
from app.core.services.weight_service import list_weights_for_date


class DeleteRecordError(ValueError):
    """Raised when a record cannot be hard-deleted."""


def get_records_for_date(
    target_date: date,
    record_type: RecordType = "all",
) -> DailyRecordsOutput:
    meals = []
    weights = []
    activities = []

    if record_type in ("all", "meal", "meal_item"):
        meals = list_meals_for_date(target_date)
    if record_type in ("all", "weight"):
        weights = list_weights_for_date(target_date)
    if record_type in ("all", "activity"):
        activities = list_activities_for_date(target_date)

    return DailyRecordsOutput(
        date=target_date,
        record_type=record_type,
        meals=meals,
        weights=weights,
        activities=activities,
        total_record_count=len(meals) + len(weights) + len(activities),
    )


def delete_record(record_type: DeletableRecordType, record_id: int) -> DeleteRecordOutput:
    model_by_type = {
        "meal": Meal,
        "meal_item": MealItem,
        "weight": WeightEntry,
        "activity": ActivityEntry,
    }
    model = model_by_type[record_type]

    with session_scope() as session:
        record = session.execute(select(model).where(model.id == record_id)).scalar_one_or_none()
        if record is None:
            raise DeleteRecordError(f"{record_type} record not found: id={record_id}")
        session.delete(record)
        return DeleteRecordOutput(record_type=record_type, record_id=record_id, deleted=True)
