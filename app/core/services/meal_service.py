from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.db.session import session_scope
from app.core.models.meal import Meal, MealItem
from app.core.schemas.meal import (
    MealDuplicateWarning,
    MealItemOutput,
    MealOutput,
    RecordMealInput,
)


def _to_output(meal: Meal) -> MealOutput:
    items = [
        MealItemOutput(
            id=item.id,
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
            updated_at=item.updated_at,
        )
        for item in meal.items
    ]
    return MealOutput(
        id=meal.id,
        date=meal.date,
        meal_type=meal.meal_type,
        raw_text=meal.raw_text,
        metadata=meal.metadata_json,
        note=meal.note,
        updated_at=meal.updated_at,
        items=items,
        total_calories=sum(item.calories for item in items),
        total_protein_g=sum(item.protein_g for item in items),
        total_carbs_g=sum(item.carbs_g for item in items),
        total_fat_g=sum(item.fat_g for item in items),
        estimated_item_count=sum(1 for item in items if item.is_estimated),
    )


def record_meal(input_data: RecordMealInput) -> MealOutput:
    duplicate_warnings = find_duplicate_meals(input_data)
    with session_scope() as session:
        meal = Meal(
            date=input_data.date,
            meal_type=input_data.meal_type,
            raw_text=input_data.raw_text,
            metadata_json=input_data.metadata,
            note=input_data.note,
        )
        meal.items = [
            MealItem(
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
            for item in input_data.items
        ]
        session.add(meal)
        session.flush()
        output = _to_output(meal)
        output.duplicate_warnings = [
            warning.model_dump(mode="json") for warning in duplicate_warnings
        ]
        return output


def list_meals_for_date(target_date: date) -> list[MealOutput]:
    with session_scope() as session:
        meals = (
            session.execute(
                select(Meal)
                .where(Meal.date == target_date)
                .options(selectinload(Meal.items))
                .order_by(Meal.id)
            )
            .scalars()
            .all()
        )
        return [_to_output(meal) for meal in meals]


def find_duplicate_meals(input_data: RecordMealInput) -> list[MealDuplicateWarning]:
    with session_scope() as session:
        existing_meals = (
            session.execute(
                select(Meal)
                .where(Meal.date == input_data.date)
                .where(Meal.meal_type == input_data.meal_type)
                .options(selectinload(Meal.items))
                .order_by(Meal.id)
            )
            .scalars()
            .all()
        )

        warnings: list[MealDuplicateWarning] = []
        for meal in existing_meals:
            output = _to_output(meal)
            reason = _meal_duplicate_reason(input_data, output)
            if reason is None:
                continue
            warnings.append(
                MealDuplicateWarning(
                    record_id=output.id,
                    reason=reason,
                    message="Possible duplicate meal on the same date and meal type.",
                    record=output,
                )
            )
        return warnings


def _meal_duplicate_reason(input_data: RecordMealInput, existing: MealOutput) -> str | None:
    if input_data.raw_text and existing.raw_text and input_data.raw_text == existing.raw_text:
        return "same_raw_text"

    input_names = sorted(item.name.strip().lower() for item in input_data.items)
    existing_names = sorted(item.name.strip().lower() for item in existing.items)
    input_calories = sum(item.calories for item in input_data.items)
    if (
        input_names
        and input_names == existing_names
        and abs(input_calories - existing.total_calories) <= 1
    ):
        return "same_items_and_calories"

    return None
