import json
from datetime import date
from pathlib import Path
from typing import Annotated, Any

import typer

from app.core.db.session import get_database_path, init_db, reset_engine_cache
from app.core.schemas.activity import ActivityEntryInput
from app.core.schemas.common import parse_date_value
from app.core.schemas.meal import MealItemInput, RecordMealInput
from app.core.schemas.profile import UserProfileInput
from app.core.schemas.weight import WeightEntryInput
from app.core.services.activity_service import record_activity
from app.core.services.meal_service import record_meal
from app.core.services.profile_service import get_user_profile, update_user_profile
from app.core.services.record_service import DeleteRecordError, delete_record, get_records_for_date
from app.core.services.summary_service import get_daily_summary
from app.core.services.weight_service import get_weight_trend, record_weight

app = typer.Typer(help="Local-first fitness and fat-loss assistant.")
profile_app = typer.Typer(help="Manage the local user profile.")
meal_app = typer.Typer(help="Record meals.")
summary_app = typer.Typer(help="Show daily summaries.")
weight_app = typer.Typer(help="Record body weight.")
activity_app = typer.Typer(help="Record activity calories.")
records_app = typer.Typer(help="List and delete recorded data.")
dev_app = typer.Typer(help="Development utilities.")

app.add_typer(profile_app, name="profile")
app.add_typer(meal_app, name="meal")
app.add_typer(summary_app, name="summary")
app.add_typer(weight_app, name="weight")
app.add_typer(activity_app, name="activity")
app.add_typer(records_app, name="records")
app.add_typer(dev_app, name="dev")


@app.callback()
def main() -> None:
    """Fitness Agent command line interface."""


@profile_app.command("set")
def profile_set(
    height_cm: Annotated[float | None, typer.Option()] = None,
    weight_kg: Annotated[float | None, typer.Option()] = None,
    age: Annotated[int | None, typer.Option()] = None,
    sex: Annotated[str | None, typer.Option()] = None,
    activity_level: Annotated[str | None, typer.Option()] = None,
    goal_type: Annotated[str | None, typer.Option()] = None,
    goal_weight_kg: Annotated[float | None, typer.Option()] = None,
    target_calories: Annotated[float | None, typer.Option()] = None,
    target_protein_g: Annotated[float | None, typer.Option()] = None,
) -> None:
    init_db()
    output = update_user_profile(
        UserProfileInput(
            height_cm=height_cm,
            weight_kg=weight_kg,
            age=age,
            sex=sex,
            activity_level=activity_level,
            goal_type=goal_type,
            goal_weight_kg=goal_weight_kg,
            target_calories=target_calories,
            target_protein_g=target_protein_g,
        )
    )
    typer.echo(f"Profile saved: id={output.id}, goal_type={output.goal_type}")
    typer.echo(f"Target calories: {output.target_calories or output.calculated_target_calories}")
    typer.echo(f"Target protein g: {output.target_protein_g or output.calculated_target_protein_g}")


@profile_app.command("show")
def profile_show() -> None:
    init_db()
    output = get_user_profile()
    if output is None:
        typer.echo("No profile found.")
        return
    typer.echo(f"Profile id: {output.id}")
    typer.echo(f"Height cm: {output.height_cm}")
    typer.echo(f"Weight kg: {output.weight_kg}")
    typer.echo(f"Goal type: {output.goal_type}")
    typer.echo(f"BMR: {output.bmr}")
    typer.echo(f"TDEE: {output.tdee}")
    typer.echo(f"Target calories: {output.target_calories or output.calculated_target_calories}")
    typer.echo(f"Target protein g: {output.target_protein_g or output.calculated_target_protein_g}")


def _record_meal_input_from_json(payload: str) -> RecordMealInput:
    data: dict[str, Any] = json.loads(payload)
    data["date"] = parse_date_value(data.get("date"))
    return RecordMealInput.model_validate(data)


def _record_meal_input_from_items(
    date_value: str,
    meal_type: str,
    item_values: list[str],
) -> RecordMealInput:
    items = []
    for value in item_values:
        parts = [part.strip() for part in value.split(",")]
        if len(parts) != 7:
            raise typer.BadParameter(
                "item must use format name,quantity,unit,calories,protein_g,carbs_g,fat_g"
            )
        name, quantity, unit, calories, protein_g, carbs_g, fat_g = parts
        items.append(
            MealItemInput(
                name=name,
                quantity=float(quantity),
                unit=unit,
                calories=float(calories),
                protein_g=float(protein_g),
                carbs_g=float(carbs_g),
                fat_g=float(fat_g),
            )
        )
    return RecordMealInput(date=parse_date_value(date_value), meal_type=meal_type, items=items)


@meal_app.command("add")
def meal_add(
    json_payload: Annotated[str | None, typer.Option("--json")] = None,
    date_value: Annotated[str, typer.Option("--date")] = "today",
    meal_type: Annotated[str, typer.Option("--type")] = "other",
    item: Annotated[list[str] | None, typer.Option("--item")] = None,
) -> None:
    init_db()
    if json_payload is not None:
        input_data = _record_meal_input_from_json(json_payload)
    elif item:
        input_data = _record_meal_input_from_items(date_value, meal_type, item)
    else:
        raise typer.BadParameter("provide --json or at least one --item")

    meal = record_meal(input_data)
    typer.echo(f"Meal recorded: id={meal.id}, type={meal.meal_type}")
    typer.echo(f"Total calories: {meal.total_calories}")
    typer.echo(f"Estimated items: {meal.estimated_item_count}")


def _print_summary(target_date: date) -> None:
    init_db()
    summary = get_daily_summary(target_date)
    typer.echo(f"Date: {summary.date.isoformat()}")
    typer.echo(f"Total calories: {summary.total_calories}")
    typer.echo(f"Protein g: {summary.total_protein_g}")
    typer.echo(f"Carbs g: {summary.total_carbs_g}")
    typer.echo(f"Fat g: {summary.total_fat_g}")
    typer.echo(f"Activity calories: {summary.activity_calories}")
    typer.echo(f"Net calories: {summary.net_calories}")
    typer.echo(f"Target calories: {summary.target_calories}")
    typer.echo(f"Remaining calories: {summary.remaining_calories}")
    typer.echo(f"Target protein g: {summary.target_protein_g}")
    typer.echo(f"Meal count: {summary.meal_count}")
    typer.echo(f"Estimated items: {summary.estimated_item_count}")
    for meal in summary.meals:
        typer.echo(f"- {meal.meal_type}: {meal.total_calories} kcal, {len(meal.items)} items")


@summary_app.command("today")
def summary_today() -> None:
    _print_summary(date.today())


@summary_app.command("date")
def summary_date(date_value: str) -> None:
    _print_summary(parse_date_value(date_value))


def _weight_input_from_json(payload: str) -> WeightEntryInput:
    data: dict[str, Any] = json.loads(payload)
    data["date"] = parse_date_value(data.get("date"))
    return WeightEntryInput.model_validate(data)


@weight_app.command("add")
def weight_add(json_payload: Annotated[str, typer.Option("--json")]) -> None:
    init_db()
    entry = record_weight(_weight_input_from_json(json_payload))
    typer.echo(f"Weight recorded: id={entry.id}, weight_kg={entry.weight_kg}")


@weight_app.command("trend")
def weight_trend(days: Annotated[int, typer.Option("--days")] = 7) -> None:
    init_db()
    trend = get_weight_trend(days=days)
    typer.echo(f"Latest weight: {trend.latest_weight_kg}")
    typer.echo(f"Latest date: {trend.latest_date}")
    typer.echo(f"Average weight kg: {trend.average_weight_kg}")
    typer.echo(f"Entry count: {trend.entry_count}")


def _activity_input_from_json(payload: str) -> ActivityEntryInput:
    data: dict[str, Any] = json.loads(payload)
    data["date"] = parse_date_value(data.get("date"))
    return ActivityEntryInput.model_validate(data)


@activity_app.command("add")
def activity_add(json_payload: Annotated[str, typer.Option("--json")]) -> None:
    init_db()
    entry = record_activity(_activity_input_from_json(json_payload))
    typer.echo(f"Activity recorded: id={entry.id}, type={entry.activity_type}")
    typer.echo(f"Calories burned: {entry.calories_burned}")
    typer.echo(f"Estimated: {entry.is_estimated}")


@records_app.command("list")
def records_list(
    date_value: Annotated[str, typer.Option("--date")] = "today",
    record_type: Annotated[str, typer.Option("--type")] = "all",
) -> None:
    init_db()
    records = get_records_for_date(parse_date_value(date_value), record_type=record_type)
    typer.echo(f"Date: {records.date.isoformat()}")
    typer.echo(f"Type: {records.record_type}")
    typer.echo(f"Total records: {records.total_record_count}")
    typer.echo(f"Meals: {len(records.meals)}")
    for meal in records.meals:
        typer.echo(f"- meal id={meal.id}, type={meal.meal_type}, calories={meal.total_calories}")
    typer.echo(f"Weights: {len(records.weights)}")
    for weight in records.weights:
        typer.echo(f"- weight id={weight.id}, weight_kg={weight.weight_kg}")
    typer.echo(f"Activities: {len(records.activities)}")
    for activity in records.activities:
        typer.echo(
            f"- activity id={activity.id}, type={activity.activity_type}, "
            f"calories={activity.calories_burned}"
        )


@records_app.command("delete")
def records_delete(record_type: str, record_id: int) -> None:
    init_db()
    try:
        output = delete_record(record_type=record_type, record_id=record_id)
    except DeleteRecordError as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(f"Deleted {output.record_type}: id={output.record_id}")


@dev_app.command("reset-db")
def reset_db(yes: Annotated[bool, typer.Option("--yes")] = False) -> None:
    if not yes:
        raise typer.BadParameter("Refusing to reset database without --yes")
    db_path = get_database_path()
    reset_engine_cache()
    if db_path.exists():
        Path(db_path).unlink()
    init_db()
    typer.echo(f"Database reset: {db_path}")


if __name__ == "__main__":
    app()
