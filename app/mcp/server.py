from typing import Any

from mcp.server.fastmcp import FastMCP

from app.core.db.session import init_db
from app.core.schemas.activity import ActivityEntryInput
from app.core.schemas.common import parse_date_value
from app.core.schemas.meal import RecordMealInput
from app.core.schemas.profile import UserProfileInput
from app.core.schemas.weight import WeightEntryInput
from app.core.services.activity_service import record_activity as record_activity_service
from app.core.services.meal_service import record_meal as record_meal_service
from app.core.services.profile_service import get_user_profile as get_user_profile_service
from app.core.services.profile_service import update_user_profile as update_user_profile_service
from app.core.services.summary_service import get_daily_summary as get_daily_summary_service
from app.core.services.weight_service import get_weight_trend as get_weight_trend_service
from app.core.services.weight_service import record_weight as record_weight_service

SERVER_INSTRUCTIONS = """
Fitness Agent stores local fitness and fat-loss tracking data.
Use update_user_profile before relying on calorie targets.
Use record_meal only after the agent has parsed or estimated meal items into structured fields.
Use record_weight for body-weight observations and record_activity for exercise calorie records.
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
    def record_weight(weight: dict[str, Any]) -> dict[str, Any]:
        """Record a body-weight observation."""
        init_db()
        data = dict(weight)
        data["date"] = parse_date_value(data.get("date"))
        output = record_weight_service(WeightEntryInput.model_validate(data))
        return _dump_model(output)

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
    def get_daily_summary(date_value: str = "today") -> dict[str, Any]:
        """Return calorie and macro totals for a date."""
        init_db()
        output = get_daily_summary_service(parse_date_value(date_value))
        return _dump_model(output)

    return mcp


def main() -> None:
    build_mcp_server().run(transport="stdio")


if __name__ == "__main__":
    main()
