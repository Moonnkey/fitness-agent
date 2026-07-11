from datetime import timedelta

from sqlalchemy import select

from app.core.db.session import session_scope
from app.core.models.weight import WeightEntry
from app.core.schemas.weight import WeightEntryInput, WeightEntryOutput, WeightTrendOutput


def _to_output(entry: WeightEntry) -> WeightEntryOutput:
    return WeightEntryOutput(
        id=entry.id,
        date=entry.date,
        weight_kg=entry.weight_kg,
        raw_text=entry.raw_text,
        metadata=entry.metadata_json,
        note=entry.note,
    )


def record_weight(input_data: WeightEntryInput) -> WeightEntryOutput:
    with session_scope() as session:
        entry = WeightEntry(
            date=input_data.date,
            weight_kg=input_data.weight_kg,
            raw_text=input_data.raw_text,
            metadata_json=input_data.metadata,
            note=input_data.note,
        )
        session.add(entry)
        session.flush()
        return _to_output(entry)


def get_weight_trend(days: int = 7) -> WeightTrendOutput:
    with session_scope() as session:
        latest = (
            session.execute(
                select(WeightEntry).order_by(WeightEntry.date.desc(), WeightEntry.id.desc())
            )
            .scalars()
            .first()
        )
        if latest is None:
            return WeightTrendOutput(
                latest_weight_kg=None,
                latest_date=None,
                average_weight_kg=None,
                days=days,
                entry_count=0,
                entries=[],
            )

        start_date = latest.date - timedelta(days=days - 1)
        entries = (
            session.execute(
                select(WeightEntry)
                .where(WeightEntry.date >= start_date)
                .where(WeightEntry.date <= latest.date)
                .order_by(WeightEntry.date, WeightEntry.id)
            )
            .scalars()
            .all()
        )
        outputs = [_to_output(entry) for entry in entries]
        average = sum(entry.weight_kg for entry in outputs) / len(outputs)
        return WeightTrendOutput(
            latest_weight_kg=latest.weight_kg,
            latest_date=latest.date,
            average_weight_kg=average,
            days=days,
            entry_count=len(outputs),
            entries=outputs,
        )
