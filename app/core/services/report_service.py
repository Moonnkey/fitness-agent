from datetime import date, timedelta

from app.core.schemas.report import DailyGuidanceOutput, TrendDailyPoint, WeeklySummaryOutput
from app.core.services.summary_service import get_daily_summary
from app.core.services.weight_service import list_weights_for_date


def get_weekly_summary(end_date: date, days: int = 7) -> WeeklySummaryOutput:
    if days <= 0:
        raise ValueError("days must be greater than 0")

    start_date = end_date - timedelta(days=days - 1)
    daily_points = [
        _build_daily_point(start_date + timedelta(days=offset)) for offset in range(days)
    ]

    total_calories = sum(point.total_calories for point in daily_points)
    total_protein = sum(point.total_protein_g for point in daily_points)
    total_activity = sum(point.activity_calories for point in daily_points)
    total_net = sum(point.net_calories for point in daily_points)

    calorie_target_hit_days = _count_calorie_target_hits(daily_points)
    protein_target_hit_days = _count_protein_target_hits(daily_points)
    days_over_calorie_target = _count_days_over_calorie_target(daily_points)
    days_under_calorie_target = _count_days_under_calorie_target(daily_points)
    weight_start, weight_end = _first_and_last_weight(daily_points)
    weight_change = None
    if weight_start is not None and weight_end is not None:
        weight_change = round(weight_end - weight_start, 2)

    notes = _weekly_notes(
        daily_points=daily_points,
        calorie_target_hit_days=calorie_target_hit_days,
        protein_target_hit_days=protein_target_hit_days,
        weight_change=weight_change,
    )
    output = WeeklySummaryOutput(
        start_date=start_date,
        end_date=end_date,
        days=days,
        daily_points=daily_points,
        total_calories=round(total_calories, 2),
        average_daily_calories=round(total_calories / days, 2),
        average_daily_protein_g=round(total_protein / days, 2),
        total_activity_calories=round(total_activity, 2),
        average_net_calories=round(total_net / days, 2),
        calorie_target_hit_days=calorie_target_hit_days,
        protein_target_hit_days=protein_target_hit_days,
        days_over_calorie_target=days_over_calorie_target,
        days_under_calorie_target=days_under_calorie_target,
        weight_start_kg=weight_start,
        weight_end_kg=weight_end,
        weight_change_kg=weight_change,
        notes=notes,
        report_text="",
    )
    output.report_text = _weekly_report_text(output)
    return output


def get_daily_guidance(target_date: date) -> DailyGuidanceOutput:
    summary = get_daily_summary(target_date)
    remaining_protein = None
    if summary.target_protein_g is not None:
        remaining_protein = max(round(summary.target_protein_g - summary.total_protein_g, 2), 0)

    dinner_min = None
    dinner_max = None
    if summary.remaining_calories is not None:
        dinner_max = max(round(summary.remaining_calories), 0)
        dinner_min = max(dinner_max - 200, 0)

    cautions = []
    guidance = []
    if summary.target_calories is None or summary.target_protein_g is None:
        cautions.append("还没有用户档案，无法计算目标热量和蛋白质目标。")
        guidance.append("先完善身高、体重、年龄、活动水平和目标，再让 Agent 计算当天建议。")
    else:
        if summary.remaining_calories is not None and summary.remaining_calories <= 0:
            cautions.append("今天摄入已经达到或超过目标热量，后续饮食建议保守处理。")
            guidance.append("如果还需要进食，优先选择低油、高蛋白、蔬菜为主的轻量食物。")
        else:
            guidance.append(
                f"今天目标热量还剩约 {round(summary.remaining_calories or 0)} kcal，"
                "晚餐建议控制在这个范围内。"
            )

        if remaining_protein is not None and remaining_protein > 0:
            guidance.append(
                f"蛋白质还差约 {remaining_protein:g} g，晚餐优先补充瘦肉、鱼、蛋、奶或豆制品。"
            )
        else:
            guidance.append("蛋白质目标目前已经达到或接近达到，晚餐注意控制总热量和烹饪油脂。")
        guidance.append("这只是一般减脂记录建议，不替代医生或注册营养师的个性化建议。")

    output = DailyGuidanceOutput(
        date=target_date,
        total_calories=summary.total_calories,
        target_calories=summary.target_calories,
        remaining_calories=summary.remaining_calories,
        total_protein_g=summary.total_protein_g,
        target_protein_g=summary.target_protein_g,
        remaining_protein_g=remaining_protein,
        activity_calories=summary.activity_calories,
        net_calories=summary.net_calories,
        suggested_dinner_calorie_min=dinner_min,
        suggested_dinner_calorie_max=dinner_max,
        guidance=guidance,
        cautions=cautions,
        report_text="",
    )
    output.report_text = _daily_guidance_text(output)
    return output


def _build_daily_point(target_date: date) -> TrendDailyPoint:
    summary = get_daily_summary(target_date)
    weights = list_weights_for_date(target_date)
    latest_weight = weights[-1].weight_kg if weights else None
    return TrendDailyPoint(
        date=target_date,
        total_calories=summary.total_calories,
        target_calories=summary.target_calories,
        remaining_calories=summary.remaining_calories,
        total_protein_g=summary.total_protein_g,
        target_protein_g=summary.target_protein_g,
        activity_calories=summary.activity_calories,
        net_calories=summary.net_calories,
        weight_kg=latest_weight,
        meal_count=summary.meal_count,
        activity_count=summary.activity_count,
    )


def _count_calorie_target_hits(points: list[TrendDailyPoint]) -> int | None:
    target_days = [point for point in points if point.target_calories is not None]
    if not target_days:
        return None
    return sum(1 for point in target_days if point.total_calories <= (point.target_calories or 0))


def _count_protein_target_hits(points: list[TrendDailyPoint]) -> int | None:
    target_days = [point for point in points if point.target_protein_g is not None]
    if not target_days:
        return None
    return sum(1 for point in target_days if point.total_protein_g >= (point.target_protein_g or 0))


def _count_days_over_calorie_target(points: list[TrendDailyPoint]) -> int | None:
    target_days = [point for point in points if point.target_calories is not None]
    if not target_days:
        return None
    return sum(1 for point in target_days if point.total_calories > (point.target_calories or 0))


def _count_days_under_calorie_target(points: list[TrendDailyPoint]) -> int | None:
    target_days = [point for point in points if point.target_calories is not None]
    if not target_days:
        return None
    return sum(1 for point in target_days if point.total_calories <= (point.target_calories or 0))


def _first_and_last_weight(points: list[TrendDailyPoint]) -> tuple[float | None, float | None]:
    weights = [point.weight_kg for point in points if point.weight_kg is not None]
    if not weights:
        return None, None
    return weights[0], weights[-1]


def _weekly_notes(
    daily_points: list[TrendDailyPoint],
    calorie_target_hit_days: int | None,
    protein_target_hit_days: int | None,
    weight_change: float | None,
) -> list[str]:
    notes = []
    if calorie_target_hit_days is None:
        notes.append("缺少用户热量目标，无法判断热量达标天数。")
    else:
        notes.append(f"热量目标达标 {calorie_target_hit_days}/{len(daily_points)} 天。")
    if protein_target_hit_days is None:
        notes.append("缺少蛋白质目标，无法判断蛋白质达标天数。")
    else:
        notes.append(f"蛋白质目标达标 {protein_target_hit_days}/{len(daily_points)} 天。")
    if weight_change is None:
        notes.append("本周期体重记录不足，无法判断体重变化。")
    elif weight_change < 0:
        notes.append(f"周期内体重下降 {abs(weight_change):g} kg。")
    elif weight_change > 0:
        notes.append(f"周期内体重上升 {weight_change:g} kg。")
    else:
        notes.append("周期内体重基本持平。")
    return notes


def _weekly_report_text(output: WeeklySummaryOutput) -> str:
    weight_text = "体重记录不足，暂不判断体重变化。"
    if output.weight_change_kg is not None:
        direction = "下降" if output.weight_change_kg < 0 else "上升"
        if output.weight_change_kg == 0:
            weight_text = "体重基本持平。"
        else:
            weight_text = f"体重{direction} {abs(output.weight_change_kg):g} kg。"

    return (
        f"过去 {output.days} 天（{output.start_date.isoformat()} 至 "
        f"{output.end_date.isoformat()}）平均每日摄入 "
        f"{output.average_daily_calories:g} kcal，平均蛋白质 "
        f"{output.average_daily_protein_g:g} g，总活动消耗 "
        f"{output.total_activity_calories:g} kcal，平均净热量 "
        f"{output.average_net_calories:g} kcal。"
        f"热量达标 {output.calorie_target_hit_days} 天，"
        f"蛋白质达标 {output.protein_target_hit_days} 天。{weight_text}"
    )


def _daily_guidance_text(output: DailyGuidanceOutput) -> str:
    target_text = "目标热量未知"
    if output.target_calories is not None:
        target_text = f"目标 {output.target_calories:g} kcal"
    remaining_text = "剩余热量未知"
    if output.remaining_calories is not None:
        remaining_text = f"还剩约 {output.remaining_calories:g} kcal"
    protein_text = "蛋白质目标未知"
    if output.remaining_protein_g is not None:
        protein_text = f"蛋白质还差约 {output.remaining_protein_g:g} g"
    return (
        f"今天目前摄入 {output.total_calories:g} kcal，{target_text}，"
        f"{remaining_text}；目前蛋白质 {output.total_protein_g:g} g，"
        f"{protein_text}。"
    )
