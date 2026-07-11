import json

from typer.testing import CliRunner

from app.cli.main import app
from app.core.db.session import init_db


def test_profile_set_and_show_commands() -> None:
    runner = CliRunner()

    set_result = runner.invoke(
        app,
        [
            "profile",
            "set",
            "--height-cm",
            "180",
            "--weight-kg",
            "80",
            "--age",
            "30",
            "--sex",
            "male",
            "--activity-level",
            "moderate",
            "--goal-type",
            "fat_loss",
        ],
    )
    show_result = runner.invoke(app, ["profile", "show"])

    assert set_result.exit_code == 0
    assert show_result.exit_code == 0
    assert "fat_loss" in show_result.output
    assert "target calories" in show_result.output.lower()


def test_meal_add_json_and_summary_today() -> None:
    init_db()
    runner = CliRunner()
    payload = {
        "date": "today",
        "meal_type": "breakfast",
        "raw_text": "早餐吃了两个鸡蛋",
        "items": [
            {
                "name": "鸡蛋",
                "quantity": 2,
                "unit": "个",
                "calories": 144,
                "protein_g": 12,
                "carbs_g": 1,
                "fat_g": 10,
                "is_estimated": True,
                "source": "agent_estimate",
                "metadata": {"assumption": "普通水煮蛋"},
            }
        ],
    }

    meal_result = runner.invoke(app, ["meal", "add", "--json", json.dumps(payload)])
    summary_result = runner.invoke(app, ["summary", "today"])

    assert meal_result.exit_code == 0
    assert "144" in meal_result.output
    assert summary_result.exit_code == 0
    assert "144" in summary_result.output
    assert "estimated items" in summary_result.output.lower()


def test_weight_activity_and_summary_commands() -> None:
    init_db()
    runner = CliRunner()
    weight_payload = {
        "date": "today",
        "weight_kg": 79.6,
        "raw_text": "今天早上空腹 79.6kg",
        "metadata": {"timing": "morning fasting"},
    }
    activity_payload = {
        "date": "today",
        "activity_type": "walking",
        "duration_minutes": 40,
        "calories_burned": 180,
        "is_estimated": True,
        "raw_text": "今天快走 40 分钟",
        "metadata": {"estimation_basis": "中等强度快走估算"},
    }

    weight_result = runner.invoke(app, ["weight", "add", "--json", json.dumps(weight_payload)])
    trend_result = runner.invoke(app, ["weight", "trend", "--days", "7"])
    activity_result = runner.invoke(
        app,
        ["activity", "add", "--json", json.dumps(activity_payload)],
    )
    summary_result = runner.invoke(app, ["summary", "today"])

    assert weight_result.exit_code == 0
    assert "79.6" in weight_result.output
    assert trend_result.exit_code == 0
    assert "latest weight" in trend_result.output.lower()
    assert activity_result.exit_code == 0
    assert "180" in activity_result.output
    assert summary_result.exit_code == 0
    assert "activity calories" in summary_result.output.lower()
    assert "net calories" in summary_result.output.lower()


def test_records_list_and_delete_commands() -> None:
    init_db()
    runner = CliRunner()
    payload = {
        "date": "today",
        "meal_type": "breakfast",
        "items": [{"name": "鸡蛋", "calories": 144}],
    }

    meal_result = runner.invoke(app, ["meal", "add", "--json", json.dumps(payload)])
    list_result = runner.invoke(app, ["records", "list", "--date", "today"])
    delete_result = runner.invoke(app, ["records", "delete", "meal", "1"])
    list_after_delete = runner.invoke(app, ["records", "list", "--date", "today"])

    assert meal_result.exit_code == 0
    assert list_result.exit_code == 0
    assert "Meals: 1" in list_result.output
    assert delete_result.exit_code == 0
    assert "Deleted meal: id=1" in delete_result.output
    assert list_after_delete.exit_code == 0
    assert "Total records: 0" in list_after_delete.output


def test_dev_reset_db_requires_yes() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["dev", "reset-db"])

    assert result.exit_code != 0
    assert "--yes" in result.output
