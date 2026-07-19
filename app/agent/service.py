from app.agent.mcp_client import MCPClient
from app.agent.model_client import ModelClient
from app.agent.schemas import ChatAgentResult, ToolCallResult


class ChatService:
    def __init__(self, model_client: ModelClient, mcp_client: MCPClient) -> None:
        self.model_client = model_client
        self.mcp_client = mcp_client

    async def handle_message(self, message: str) -> ChatAgentResult:
        try:
            plan = await self.model_client.create_plan(message)
        except Exception as exc:
            return ChatAgentResult(reply=f"模型解析失败：{exc}")
        if plan.direct_reply and not plan.tool_calls:
            return ChatAgentResult(reply=plan.direct_reply)

        tool_results: list[ToolCallResult] = []
        for call in plan.tool_calls:
            try:
                result = await self.mcp_client.call_tool(call.name, call.arguments)
            except Exception as exc:
                tool_results.append(
                    ToolCallResult(
                        name=call.name,
                        arguments=call.arguments,
                        ok=False,
                        error=str(exc),
                    )
                )
                return ChatAgentResult(
                    reply=f"执行 {call.name} 时出错：{exc}",
                    tool_calls=tool_results,
                )

            tool_result = ToolCallResult(
                name=call.name,
                arguments=call.arguments,
                ok=True,
                result=result,
            )
            tool_results.append(tool_result)
            if call.name == "check_duplicate_meal" and result.get("duplicates"):
                return ChatAgentResult(
                    reply=_duplicate_reply(result),
                    tool_calls=tool_results,
                )

        return ChatAgentResult(
            reply=_build_reply(tool_results, plan.direct_reply),
            tool_calls=tool_results,
        )


def _duplicate_reply(result: dict) -> str:
    duplicate_count = len(result.get("duplicates", []))
    return (
        f"发现 {duplicate_count} 条疑似重复饮食记录，我先不重复保存。"
        "请确认是否仍要继续保存这一餐。"
    )


def _build_reply(tool_results: list[ToolCallResult], direct_reply: str | None) -> str:
    if direct_reply:
        return direct_reply

    successful_results = [item for item in tool_results if item.ok and item.result is not None]
    for item in reversed(successful_results):
        result = item.result or {}
        report_text = result.get("report_text")
        if isinstance(report_text, str) and report_text:
            return report_text

    summary = _last_result(successful_results, "get_daily_summary")
    meal = _last_result(successful_results, "record_meal")
    if meal is not None:
        meal_text = (
            f"已记录 {meal.get('meal_type', 'meal')}，估算约 "
            f"{meal.get('total_calories', 0):g} kcal，蛋白质约 "
            f"{meal.get('total_protein_g', 0):g} g。"
        )
        if summary is not None:
            meal_text += (
                f"今天目前总摄入 {summary.get('total_calories', 0):g} kcal，"
                f"蛋白质 {summary.get('total_protein_g', 0):g} g，"
                f"剩余目标热量 {summary.get('remaining_calories')} kcal。"
            )
        return meal_text

    summary = _last_result(successful_results, "get_daily_summary")
    if summary is not None:
        return (
            f"今天目前总摄入 {summary.get('total_calories', 0):g} kcal，"
            f"蛋白质 {summary.get('total_protein_g', 0):g} g，"
            f"活动消耗 {summary.get('activity_calories', 0):g} kcal，"
            f"剩余目标热量 {summary.get('remaining_calories')} kcal。"
        )

    update_result = _last_result(successful_results, "update_record")
    if update_result is not None:
        changed_fields = ", ".join(update_result.get("changed_fields", []))
        return (
            f"已更新 {update_result.get('record_type')} "
            f"id={update_result.get('record_id')}。修改字段：{changed_fields}。"
        )

    delete_result = _last_result(successful_results, "delete_record")
    if delete_result is not None:
        return f"已删除 {delete_result.get('record_type')} id={delete_result.get('record_id')}。"

    if successful_results:
        return "操作已完成。"
    return "我还没有执行任何操作。"


def _last_result(tool_results: list[ToolCallResult], name: str) -> dict | None:
    for item in reversed(tool_results):
        if item.name == name:
            return item.result
    return None
