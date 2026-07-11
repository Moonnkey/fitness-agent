"""Persistence models for Fitness Agent."""

from app.core.models.base import Base
from app.core.models.meal import Meal, MealItem
from app.core.models.profile import UserProfile
from app.core.models.weight import WeightEntry

__all__ = ["Base", "Meal", "MealItem", "UserProfile", "WeightEntry"]
