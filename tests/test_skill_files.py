from pathlib import Path


def test_skill_file_exists_with_required_frontmatter() -> None:
    text = Path("skill/SKILL.md").read_text()

    assert text.startswith("---")
    assert "name: fitness-agent" in text
    assert "description:" in text
    assert "record_meal" in text
    assert "record_weight" in text
    assert "record_activity" in text
    assert "get_records_for_date" in text
    assert "get_record" in text
    assert "update_record" in text
    assert "delete_record" in text
    assert "get_weekly_summary" in text
    assert "get_daily_guidance" in text
    assert "get_daily_summary" in text


def test_tool_contracts_reference_exists() -> None:
    text = Path("skill/references/tool-contracts.md").read_text()

    assert "update_user_profile" in text
    assert "record_meal" in text
    assert "record_weight" in text
    assert "get_weight_trend" in text
    assert "record_activity" in text
    assert "get_records_for_date" in text
    assert "get_record" in text
    assert "update_record" in text
    assert "delete_record" in text
    assert "get_weekly_summary" in text
    assert "get_daily_guidance" in text
    assert "check_duplicate_meal" in text
    assert "get_daily_summary" in text
