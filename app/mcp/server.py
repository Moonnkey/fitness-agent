from typing import Any

from mcp.server.fastmcp import FastMCP

from app.core.db.session import init_db
from app.core.schemas.activity import ActivityEntryInput
from app.core.schemas.common import parse_date_value
from app.core.schemas.meal import RecordMealInput
from app.core.schemas.profile import UserProfileInput
from app.core.schemas.weight import WeightEntryInput
from app.core.services.activity_service import (
    find_duplicate_activities as find_duplicate_activities_service,
)
from app.core.services.activity_service import (
    record_activity as record_activity_service,
)
from app.core.services.meal_service import (
    find_duplicate_meals as find_duplicate_meals_service,
)
from app.core.services.meal_service import (
    record_meal as record_meal_service,
)
from app.core.services.profile_service import (
    get_user_profile as get_user_profile_service,
)
from app.core.services.profile_service import (
    update_user_profile as update_user_profile_service,
)
from app.core.services.record_service import (
    delete_record as delete_record_service,
)
from app.core.services.record_service import (
    get_record as get_record_service,
)
from app.core.services.record_service import (
    get_records_for_date as get_records_for_date_service,
)
from app.core.services.record_service import (
    update_record as update_record_service,
)
from app.core.services.report_service import (
    get_daily_guidance as get_daily_guidance_service,
)
from app.core.services.report_service import (
    get_weekly_summary as get_weekly_summary_service,
)
from app.core.services.summary_service import get_daily_summary as get_daily_summary_service
from app.core.services.weight_service import (
    find_duplicate_weights as find_duplicate_weights_service,
)
from app.core.services.weight_service import (
    get_weight_trend as get_weight_trend_service,
)
from app.core.services.weight_service import (
    record_weight as record_weight_service,
)

SERVER_INSTRUCTIONS = """
Fitness Agent stores local fitness and fat-loss tracking data.
Use update_user_profile before relying on calorie targets.
Use record_meal only after the agent has parsed or estimated meal items into structured fields.
Use record_weight for body-weight observations and record_activity for exercise calorie records.
Use duplicate check tools or inspect duplicate_warnings before repeating similar records.
Use get_weekly_summary for recent trends and get_daily_guidance for day-level adjustment advice.
Preserve user wording in raw_text and estimation assumptions in metadata.
All calorie and macro values may be estimates unless source says otherwise.
"""


def _dump_model(model: Any) -> dict[str, Any]:
    return model.model_dump(mode="json")


def build_mcp_server() -> FastMCP:
    mcp = FastMCP("fitness-agent", instructions=SERVER_INSTRUCTIONS)

    @mcp.tool()
    def update_user_profile(profile: dict[str, Any]) -> dict[str, Any]:
        """Create or update the single local user profile and return calculated targets."""
        init_db()
        output = update_user_profile_service(UserProfileInput.model_validate(profile))
        return _dump_model(output)

    @mcp.tool()
    def get_user_profile() -> dict[str, Any]:
        """Return the single local user profile, or null in the profile field if missing."""
        init_db()
        output = get_user_profile_service()
        if output is None:
            return {"profile": None}
        return {"profile": _dump_model(output)}

    @mcp.tool()
    def record_meal(meal: dict[str, Any]) -> dict[str, Any]:
        """Record a meal from structured or semi-structured agent-provided data."""
        init_db()
        data = dict(meal)
        data["date"] = parse_date_value(data.get("date"))
        output = record_meal_service(RecordMealInput.model_validate(data))
        return _dump_model(output)

    @mcp.tool()
    def check_duplicate_meal(meal: dict[str, Any]) -> dict[str, Any]:
        """Return possible duplicate meals before recording a new meal."""
        init_db()
        data = dict(meal)
        data["date"] = parse_date_value(data.get("date"))
        warnings = find_duplicate_meals_service(RecordMealInput.model_validate(data))
        return {"duplicates": [_dump_model(warning) for warning in warnings]}

    @mcp.tool()
    def record_weight(weight: dict[str, Any]) -> dict[str, Any]:
        """Record a body-weight observation."""
        init_db()
        data = dict(weight)
        data["date"] = parse_date_value(data.get("date"))
        output = record_weight_service(WeightEntryInput.model_validate(data))
        return _dump_model(output)

    @mcp.tool()
    def check_duplicate_weight(weight: dict[str, Any]) -> dict[str, Any]:
        """Return possible duplicate body-weight entries before recording."""
        init_db()
        data = dict(weight)
        data["date"] = parse_date_value(data.get("date"))
        warnings = find_duplicate_weights_service(WeightEntryInput.model_validate(data))
        return {"duplicates": [_dump_model(warning) for warning in warnings]}

    @mcp.tool()
    def get_weight_trend(days: int = 7) -> dict[str, Any]:
        """Return latest weight and simple average over the recent period."""
        init_db()
        output = get_weight_trend_service(days=days)
        return _dump_model(output)

    @mcp.tool()
    def record_activity(activity: dict[str, Any]) -> dict[str, Any]:
        """Record a simple activity or workout calorie expenditure entry."""
        init_db()
        data = dict(activity)
        data["date"] = parse_date_value(data.get("date"))
        output = record_activity_service(ActivityEntryInput.model_validate(data))
        return _dump_model(output)

    @mcp.tool()
    def check_duplicate_activity(activity: dict[str, Any]) -> dict[str, Any]:
        """Return possible duplicate activity entries before recording."""
        init_db()
        data = dict(activity)
        data["date"] = parse_date_value(data.get("date"))
        warnings = find_duplicate_activities_service(ActivityEntryInput.model_validate(data))
        return {"duplicates": [_dump_model(warning) for warning in warnings]}

    @mcp.tool()
    def get_daily_summary(date_value: str = "today") -> dict[str, Any]:
        """Return calorie and macro totals for a date."""
        init_db()
        output = get_daily_summary_service(parse_date_value(date_value))
        return _dump_model(output)

    @mcp.tool()
    def get_records_for_date(date_value: str = "today", record_type: str = "all") -> dict[str, Any]:
        """Return recorded meals, weights, and activities for a date."""
        init_db()
        output = get_records_for_date_service(parse_date_value(date_value), record_type=record_type)
        return _dump_model(output)

    @mcp.tool()
    def delete_record(record_type: str, record_id: int) -> dict[str, Any]:
        """Hard-delete a meal, meal item, weight entry, or activity entry by id."""
        init_db()
        output = delete_record_service(record_type=record_type, record_id=record_id)
        return _dump_model(output)

    @mcp.tool()
    def get_record(record_type: str, record_id: int) -> dict[str, Any]:
        """Return one meal, meal item, weight entry, or activity entry by id."""
        init_db()
        output = get_record_service(record_type=record_type, record_id=record_id)
        return _dump_model(output)

    @mcp.tool()
    def update_record(record_type: str, record_id: int, patch: dict[str, Any]) -> dict[str, Any]:
        """Partially update one record and return changed fields plus the updated record."""
        init_db()
        output = update_record_service(record_type=record_type, record_id=record_id, patch=patch)
        return _dump_model(output)

    @mcp.tool()
    def get_weekly_summary(end_date_value: str = "today", days: int = 7) -> dict[str, Any]:
        """Return a text weekly report plus structured daily trend points."""
        init_db()
        output = get_weekly_summary_service(end_date=parse_date_value(end_date_value), days=days)
        return _dump_model(output)

    @mcp.tool()
    def get_daily_guidance(date_value: str = "today") -> dict[str, Any]:
        """Return text daily guidance based on current intake, targets, and activity."""
        init_db()
        output = get_daily_guidance_service(parse_date_value(date_value))
        return _dump_model(output)

    return mcp


def main() -> None:
    build_mcp_server().run(transport="stdio")


if __name__ == "__main__":
    main()
