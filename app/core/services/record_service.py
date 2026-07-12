from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.db.session import session_scope
from app.core.models.activity import ActivityEntry
from app.core.models.meal import Meal, MealItem
from app.core.models.weight import WeightEntry
from app.core.schemas.activity import ActivityEntryInput
from app.core.schemas.common import parse_date_value
from app.core.schemas.meal import MealItemInput
from app.core.schemas.record import (
    DailyRecordsOutput,
    DeletableRecordType,
    DeleteRecordOutput,
    RecordDetailOutput,
    RecordType,
    UpdateRecordOutput,
)
from app.core.schemas.weight import WeightEntryInput
from app.core.services.activity_service import _to_output as _activity_to_output
from app.core.services.activity_service import list_activities_for_date
from app.core.services.meal_service import _to_output as _meal_to_output
from app.core.services.meal_service import list_meals_for_date
from app.core.services.weight_service import _to_output as _weight_to_output
from app.core.services.weight_service import list_weights_for_date


class DeleteRecordError(ValueError):
    """Raised when a record cannot be hard-deleted."""


class RecordNotFoundError(ValueError):
    """Raised when a record cannot be found."""


class UpdateRecordError(ValueError):
    """Raised when a record cannot be updated."""


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _dump_model(model: Any) -> dict[str, Any]:
    return model.model_dump(mode="json")


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


def get_record(record_type: DeletableRecordType, record_id: int) -> RecordDetailOutput:
    with session_scope() as session:
        record = _get_model_record(session, record_type, record_id)
        return RecordDetailOutput(
            record_type=record_type,
            record_id=record_id,
            record=_dump_record(record_type, record),
        )


def update_record(
    record_type: DeletableRecordType,
    record_id: int,
    patch: dict[str, Any],
) -> UpdateRecordOutput:
    with session_scope() as session:
        record = _get_model_record(session, record_type, record_id)
        if not patch:
            return UpdateRecordOutput(
                record_type=record_type,
                record_id=record_id,
                changed_fields=[],
                record=_dump_record(record_type, record),
            )

        if record_type == "meal":
            changed_fields = _update_meal(record, patch)
        elif record_type == "meal_item":
            changed_fields = _update_meal_item(record, patch)
        elif record_type == "weight":
            changed_fields = _update_weight(record, patch)
        elif record_type == "activity":
            changed_fields = _update_activity(record, patch)
        else:
            raise UpdateRecordError(f"unsupported record type: {record_type}")

        session.flush()
        return UpdateRecordOutput(
            record_type=record_type,
            record_id=record_id,
            changed_fields=changed_fields,
            record=_dump_record(record_type, record),
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


def _get_model_record(session, record_type: DeletableRecordType, record_id: int):
    if record_type == "meal":
        record = (
            session.execute(
                select(Meal)
                .where(Meal.id == record_id)
                .options(selectinload(Meal.items))
            )
            .scalars()
            .first()
        )
    elif record_type == "meal_item":
        record = (
            session.execute(select(MealItem).where(MealItem.id == record_id))
            .scalars()
            .first()
        )
    elif record_type == "weight":
        record = (
            session.execute(select(WeightEntry).where(WeightEntry.id == record_id))
            .scalars()
            .first()
        )
    elif record_type == "activity":
        record = (
            session.execute(select(ActivityEntry).where(ActivityEntry.id == record_id))
            .scalars()
            .first()
        )
    else:
        raise RecordNotFoundError(f"unsupported record type: {record_type}")

    if record is None:
        raise RecordNotFoundError(f"{record_type} record not found: id={record_id}")
    return record


def _dump_record(record_type: DeletableRecordType, record) -> dict[str, Any]:
    if record_type == "meal":
        return _dump_model(_meal_to_output(record))
    if record_type == "meal_item":
        return _dump_meal_item(record)
    if record_type == "weight":
        return _dump_model(_weight_to_output(record))
    if record_type == "activity":
        return _dump_model(_activity_to_output(record))
    raise RecordNotFoundError(f"unsupported record type: {record_type}")


def _dump_meal_item(item: MealItem) -> dict[str, Any]:
    return _dump_model(
        MealItemInput(
            name=item.name,
            quantity=item.quantity,
            unit=item.unit,
            grams=item.grams,
            calories=item.calories,
            protein_g=item.protein_g,
            carbs_g=item.carbs_g,
            fat_g=item.fat_g,
            source=item.source,
            is_estimated=item.is_estimated,
            raw_text=item.raw_text,
            metadata=item.metadata_json,
            note=item.note,
        )
    ) | {"id": item.id, "updated_at": item.updated_at.isoformat() if item.updated_at else None}


def _update_meal(meal: Meal, patch: dict[str, Any]) -> list[str]:
    changed_fields: list[str] = []
    field_map = {
        "date": "date",
        "meal_type": "meal_type",
        "raw_text": "raw_text",
        "metadata": "metadata_json",
        "note": "note",
    }
    for patch_field, model_field in field_map.items():
        if patch_field not in patch:
            continue
        value = patch[patch_field]
        if patch_field == "date":
            value = parse_date_value(value)
        setattr(meal, model_field, value)
        changed_fields.append(patch_field)

    if "items_replace" in patch:
        meal.items = [_meal_item_from_input(item) for item in patch["items_replace"]]
        changed_fields.append("items_replace")

    if "items_append" in patch:
        meal.items.extend(_meal_item_from_input(item) for item in patch["items_append"])
        changed_fields.append("items_append")

    if changed_fields:
        meal.updated_at = _utc_now()
    return changed_fields


def _update_meal_item(item: MealItem, patch: dict[str, Any]) -> list[str]:
    current = {
        "name": item.name,
        "quantity": item.quantity,
        "unit": item.unit,
        "grams": item.grams,
        "calories": item.calories,
        "protein_g": item.protein_g,
        "carbs_g": item.carbs_g,
        "fat_g": item.fat_g,
        "source": item.source,
        "is_estimated": item.is_estimated,
        "raw_text": item.raw_text,
        "metadata": item.metadata_json,
        "note": item.note,
    }
    merged = current | patch
    validated = MealItemInput.model_validate(merged)
    field_map = {"metadata": "metadata_json"}
    for field in patch:
        setattr(item, field_map.get(field, field), getattr(validated, field))
    if patch:
        item.updated_at = _utc_now()
    return list(patch.keys())


def _update_weight(entry: WeightEntry, patch: dict[str, Any]) -> list[str]:
    current = {
        "date": entry.date,
        "weight_kg": entry.weight_kg,
        "raw_text": entry.raw_text,
        "metadata": entry.metadata_json,
        "note": entry.note,
    }
    normalized_patch = _normalize_date_patch(patch)
    validated = WeightEntryInput.model_validate(current | normalized_patch)
    field_map = {"metadata": "metadata_json"}
    for field in patch:
        setattr(entry, field_map.get(field, field), getattr(validated, field))
    if patch:
        entry.updated_at = _utc_now()
    return list(patch.keys())


def _update_activity(entry: ActivityEntry, patch: dict[str, Any]) -> list[str]:
    current = {
        "date": entry.date,
        "activity_type": entry.activity_type,
        "duration_minutes": entry.duration_minutes,
        "calories_burned": entry.calories_burned,
        "is_estimated": entry.is_estimated,
        "raw_text": entry.raw_text,
        "metadata": entry.metadata_json,
        "note": entry.note,
    }
    normalized_patch = _normalize_date_patch(patch)
    validated = ActivityEntryInput.model_validate(current | normalized_patch)
    field_map = {"metadata": "metadata_json"}
    for field in patch:
        setattr(entry, field_map.get(field, field), getattr(validated, field))
    if patch:
        entry.updated_at = _utc_now()
    return list(patch.keys())


def _normalize_date_patch(patch: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(patch)
    if "date" in normalized:
        normalized["date"] = parse_date_value(normalized["date"])
    return normalized


def _meal_item_from_input(data: dict[str, Any]) -> MealItem:
    item = MealItemInput.model_validate(data)
    return MealItem(
        name=item.name,
        quantity=item.quantity,
        unit=item.unit,
        grams=item.grams,
        calories=item.calories,
        protein_g=item.protein_g,
        carbs_g=item.carbs_g,
        fat_g=item.fat_g,
        source=item.source,
        is_estimated=item.is_estimated,
        raw_text=item.raw_text,
        metadata_json=item.metadata,
        note=item.note,
    )
