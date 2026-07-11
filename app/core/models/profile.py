from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.models.base import Base


def utc_now() -> datetime:
    return datetime.now(UTC)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sex: Mapped[str | None] = mapped_column(String(20), nullable=True)
    activity_level: Mapped[str | None] = mapped_column(String(30), nullable=True)
    goal_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    goal_weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
    )
