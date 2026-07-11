from datetime import date

from app.core.db.session import init_db
from app.core.schemas.activity import ActivityEntryInput
from app.core.services.activity_service import (
    find_duplicate_activities,
    list_activities_for_date,
    record_activity,
)


def test_record_activity_preserves_estimate_context() -> None:
    init_db()

    entry = record_activity(
        ActivityEntryInput(
            date=date(2026, 7, 11),
            activity_type="walking",
            duration_minutes=40,
            calories_burned=180,
            is_estimated=True,
            raw_text="今天快走 40 分钟",
            metadata={"estimation_basis": "中等强度快走估算"},
        )
    )

    assert entry.id > 0
    assert entry.calories_burned == 180
    assert entry.is_estimated is True
    assert entry.metadata == {"estimation_basis": "中等强度快走估算"}


def test_list_activities_for_date_filters_by_date() -> None:
    init_db()
    record_activity(
        ActivityEntryInput(
            date=date(2026, 7, 11),
            activity_type="walking",
            calories_burned=180,
        )
    )
    record_activity(
        ActivityEntryInput(
            date=date(2026, 7, 12),
            activity_type="cycling",
            calories_burned=250,
        )
    )

    entries = list_activities_for_date(date(2026, 7, 11))

    assert len(entries) == 1
    assert entries[0].activity_type == "walking"


def test_find_duplicate_activities_matches_same_activity_numbers() -> None:
    init_db()
    record_activity(
        ActivityEntryInput(
            date=date(2026, 7, 11),
            activity_type="walking",
            duration_minutes=40,
            calories_burned=180,
            raw_text="快走 40 分钟",
        )
    )

    duplicates = find_duplicate_activities(
        ActivityEntryInput(
            date=date(2026, 7, 11),
            activity_type="walking",
            duration_minutes=40,
            calories_burned=180,
            raw_text="晚上快走 40 分钟",
        )
    )

    assert len(duplicates) == 1
    assert duplicates[0].reason == "same_activity"
    assert duplicates[0].record.calories_burned == 180
