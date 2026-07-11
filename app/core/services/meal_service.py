from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.db.session import session_scope
from app.core.models.meal import Meal, MealItem
from app.core.schemas.meal import MealItemOutput, MealOutput, RecordMealInput


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
        items=items,
        total_calories=sum(item.calories for item in items),
        total_protein_g=sum(item.protein_g for item in items),
        total_carbs_g=sum(item.carbs_g for item in items),
        total_fat_g=sum(item.fat_g for item in items),
        estimated_item_count=sum(1 for item in items if item.is_estimated),
    )


def record_meal(input_data: RecordMealInput) -> MealOutput:
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
        return _to_output(meal)


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
