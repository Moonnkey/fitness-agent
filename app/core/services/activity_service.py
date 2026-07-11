from datetime import date

from sqlalchemy import select

from app.core.db.session import session_scope
from app.core.models.activity import ActivityEntry
from app.core.schemas.activity import (
    ActivityDuplicateWarning,
    ActivityEntryInput,
    ActivityEntryOutput,
)


def _to_output(entry: ActivityEntry) -> ActivityEntryOutput:
    return ActivityEntryOutput(
        id=entry.id,
        date=entry.date,
        activity_type=entry.activity_type,
        duration_minutes=entry.duration_minutes,
        calories_burned=entry.calories_burned,
        is_estimated=entry.is_estimated,
        raw_text=entry.raw_text,
        metadata=entry.metadata_json,
        note=entry.note,
    )


def record_activity(input_data: ActivityEntryInput) -> ActivityEntryOutput:
    duplicate_warnings = find_duplicate_activities(input_data)
    with session_scope() as session:
        entry = ActivityEntry(
            date=input_data.date,
            activity_type=input_data.activity_type,
            duration_minutes=input_data.duration_minutes,
            calories_burned=input_data.calories_burned,
            is_estimated=input_data.is_estimated,
            raw_text=input_data.raw_text,
            metadata_json=input_data.metadata,
            note=input_data.note,
        )
        session.add(entry)
        session.flush()
        output = _to_output(entry)
        output.duplicate_warnings = [
            warning.model_dump(mode="json") for warning in duplicate_warnings
        ]
        return output


def list_activities_for_date(target_date: date) -> list[ActivityEntryOutput]:
    with session_scope() as session:
        entries = (
            session.execute(
                select(ActivityEntry)
                .where(ActivityEntry.date == target_date)
                .order_by(ActivityEntry.id)
            )
            .scalars()
            .all()
        )
        return [_to_output(entry) for entry in entries]


def find_duplicate_activities(input_data: ActivityEntryInput) -> list[ActivityDuplicateWarning]:
    with session_scope() as session:
        entries = (
            session.execute(
                select(ActivityEntry)
                .where(ActivityEntry.date == input_data.date)
                .order_by(ActivityEntry.id)
            )
            .scalars()
            .all()
        )

        warnings: list[ActivityDuplicateWarning] = []
        for entry in entries:
            output = _to_output(entry)
            reason = _activity_duplicate_reason(input_data, output)
            if reason is None:
                continue
            warnings.append(
                ActivityDuplicateWarning(
                    record_id=output.id,
                    reason=reason,
                    message="Possible duplicate activity entry on the same date.",
                    record=output,
                )
            )
        return warnings


def _activity_duplicate_reason(
    input_data: ActivityEntryInput,
    existing: ActivityEntryOutput,
) -> str | None:
    if input_data.raw_text and existing.raw_text and input_data.raw_text == existing.raw_text:
        return "same_raw_text"
    if (
        input_data.activity_type.strip().lower() == existing.activity_type.strip().lower()
        and input_data.duration_minutes == existing.duration_minutes
        and abs(input_data.calories_burned - existing.calories_burned) <= 1
    ):
        return "same_activity"
    return None
