from datetime import date

from app.core.db.session import init_db
from app.core.schemas.weight import WeightEntryInput
from app.core.services.weight_service import find_duplicate_weights, get_weight_trend, record_weight


def test_record_weight_preserves_raw_text_and_metadata() -> None:
    init_db()

    entry = record_weight(
        WeightEntryInput(
            date=date(2026, 7, 11),
            weight_kg=79.6,
            raw_text="今天早上空腹 79.6kg",
            metadata={"timing": "morning fasting"},
        )
    )

    assert entry.id > 0
    assert entry.weight_kg == 79.6
    assert entry.raw_text == "今天早上空腹 79.6kg"
    assert entry.metadata == {"timing": "morning fasting"}


def test_weight_trend_returns_latest_and_average() -> None:
    init_db()
    for day, weight in [(5, 80.0), (6, 79.8), (7, 79.7), (8, 79.6)]:
        record_weight(WeightEntryInput(date=date(2026, 7, day), weight_kg=weight))

    trend = get_weight_trend(days=7)

    assert trend.latest_weight_kg == 79.6
    assert trend.latest_date == date(2026, 7, 8)
    assert trend.average_weight_kg == 79.775
    assert trend.entry_count == 4


def test_find_duplicate_weights_matches_same_date_and_weight() -> None:
    init_db()
    record_weight(
        WeightEntryInput(
            date=date(2026, 7, 11),
            weight_kg=79.6,
            raw_text="今天早上空腹 79.6kg",
        )
    )

    duplicates = find_duplicate_weights(
        WeightEntryInput(
            date=date(2026, 7, 11),
            weight_kg=79.6,
            raw_text="早上称重 79.6kg",
        )
    )

    assert len(duplicates) == 1
    assert duplicates[0].reason == "same_weight"
    assert duplicates[0].record.weight_kg == 79.6
