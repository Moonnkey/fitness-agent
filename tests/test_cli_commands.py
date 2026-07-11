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


def test_dev_reset_db_requires_yes() -> None:
    runner = CliRunner()

    result = runner.invoke(app, ["dev", "reset-db"])

    assert result.exit_code != 0
    assert "--yes" in result.output
