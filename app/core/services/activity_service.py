from datetime import date

from sqlalchemy import select

from app.core.db.session import session_scope
from app.core.models.activity import ActivityEntry
from app.core.schemas.activity import ActivityEntryInput, ActivityEntryOutput


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
        return _to_output(entry)


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
