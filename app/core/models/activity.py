from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class ActivityEntry(Base):
    __tablename__ = "activity_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    activity_type: Mapped[str] = mapped_column(String(100))
    duration_minutes: Mapped[float | None] = mapped_column(Float, nullable=True)
    calories_burned: Mapped[float] = mapped_column(Float, default=0)
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=True)
    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
