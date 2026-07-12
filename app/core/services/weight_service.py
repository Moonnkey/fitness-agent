from datetime import timedelta

from sqlalchemy import select

from app.core.db.session import session_scope
from app.core.models.weight import WeightEntry
from app.core.schemas.weight import (
    WeightDuplicateWarning,
    WeightEntryInput,
    WeightEntryOutput,
    WeightTrendOutput,
)


def _to_output(entry: WeightEntry) -> WeightEntryOutput:
    return WeightEntryOutput(
        id=entry.id,
        date=entry.date,
        weight_kg=entry.weight_kg,
        raw_text=entry.raw_text,
        metadata=entry.metadata_json,
        note=entry.note,
        updated_at=entry.updated_at,
    )


def record_weight(input_data: WeightEntryInput) -> WeightEntryOutput:
    duplicate_warnings = find_duplicate_weights(input_data)
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
        output = _to_output(entry)
        output.duplicate_warnings = [
            warning.model_dump(mode="json") for warning in duplicate_warnings
        ]
        return output


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


def list_weights_for_date(target_date) -> list[WeightEntryOutput]:
    with session_scope() as session:
        entries = (
            session.execute(
                select(WeightEntry)
                .where(WeightEntry.date == target_date)
                .order_by(WeightEntry.id)
            )
            .scalars()
            .all()
        )
        return [_to_output(entry) for entry in entries]


def find_duplicate_weights(input_data: WeightEntryInput) -> list[WeightDuplicateWarning]:
    with session_scope() as session:
        entries = (
            session.execute(
                select(WeightEntry)
                .where(WeightEntry.date == input_data.date)
                .order_by(WeightEntry.id)
            )
            .scalars()
            .all()
        )

        warnings: list[WeightDuplicateWarning] = []
        for entry in entries:
            output = _to_output(entry)
            reason = _weight_duplicate_reason(input_data, output)
            if reason is None:
                continue
            warnings.append(
                WeightDuplicateWarning(
                    record_id=output.id,
                    reason=reason,
                    message="Possible duplicate weight entry on the same date.",
                    record=output,
                )
            )
        return warnings


def _weight_duplicate_reason(
    input_data: WeightEntryInput,
    existing: WeightEntryOutput,
) -> str | None:
    if input_data.raw_text and existing.raw_text and input_data.raw_text == existing.raw_text:
        return "same_raw_text"
    if abs(input_data.weight_kg - existing.weight_kg) <= 0.05:
        return "same_weight"
    return None
