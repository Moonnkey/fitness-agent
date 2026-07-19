# 第六阶段用户使用手册：文字周报、趋势和日内建议

## 这一阶段新增了什么

第六阶段让 Fitness Agent 从“记录工具”开始变成“反馈工具”。它现在可以基于已有饮食、体重和活动记录，输出文字版周报和当天调整建议。

现在用户可以让 Agent 做这些事：

- 总结最近 7 天减脂执行情况。
- 查看平均每日摄入、平均蛋白质、总活动消耗和平均净热量。
- 查看热量目标达标天数和蛋白质目标达标天数。
- 查看周期内体重首末变化。
- 根据今天已摄入、目标热量和蛋白质缺口，给出保守的日内饮食建议。

新增 MCP tools：

- `get_weekly_summary`
- `get_daily_guidance`

新增 CLI 命令：

- `fitness-agent summary week --days 7`
- `fitness-agent guidance today`
- `fitness-agent guidance date 2026-07-19`

## 推荐使用方式

日常使用时，优先让 Agent 调用 MCP 工具，再把 `report_text` 转述给用户。

推荐流程：

```text
1. 用户问一周执行情况时，Agent 调用 get_weekly_summary。
2. 用户问今天还能怎么吃时，Agent 调用 get_daily_guidance。
3. 如果用户想看详细数字，Agent 展示 structured fields 或 daily_points。
4. 如果用户关心图表，当前先解释 daily_points 已支持未来前端画图，但 MVP 暂无图表界面。
```

## 提示词示例

### 总结本周执行情况

```text
请使用 fitness-agent MCP 工具总结我最近 7 天的减脂执行情况。调用 get_weekly_summary，end_date_value 使用 today，days 使用 7。请先用 report_text 总结，再列出平均每日摄入、平均蛋白质、活动总消耗、热量达标天数、蛋白质达标天数和体重变化。
```

### 查看热量和蛋白质趋势

```text
请调用 get_weekly_summary 查看我最近 7 天的 daily_points。帮我判断哪几天热量超过目标，哪几天蛋白质没有达标，并给出保守建议。
```

### 问晚餐怎么吃

```text
请使用 fitness-agent MCP 工具看看我今天晚餐该怎么安排。调用 get_daily_guidance，date_value 使用 today。请告诉我今天已摄入多少热量、还剩多少目标热量、蛋白质还差多少，以及晚餐建议控制在多少 kcal。
```

### 今天已经快超热量了

```text
请调用 get_daily_guidance 看我今天后续饮食怎么调整。如果剩余热量已经很少或为负，请给保守建议，不要推荐极端节食。
```

### 给未来前端看数据

```text
请调用 get_weekly_summary，并把 daily_points 里的日期、总热量、目标热量、蛋白质、活动消耗、净热量和体重整理成表格。这个数据之后要用来做前端趋势图。
```

## CLI 示例

查看最近 7 天周报：

```bash
uv run fitness-agent summary week --days 7
```

查看以指定日期为结束日的周报：

```bash
uv run fitness-agent summary week --days 7 --end-date 2026-07-19
```

查看今天日内建议：

```bash
uv run fitness-agent guidance today
```

查看指定日期建议：

```bash
uv run fitness-agent guidance date 2026-07-19
```

## 返回数据如何理解

`get_weekly_summary` 会返回：

- `report_text`：适合 Agent 直接转述的中文总结。
- `daily_points`：适合未来前端画图的每日数据点。
- `average_daily_calories`：平均每日摄入热量。
- `average_daily_protein_g`：平均每日蛋白质。
- `total_activity_calories`：周期内活动总消耗。
- `average_net_calories`：平均净热量。
- `calorie_target_hit_days`：热量目标达标天数。
- `protein_target_hit_days`：蛋白质目标达标天数。
- `weight_change_kg`：周期内体重变化。

`get_daily_guidance` 会返回：

- `report_text`：当天状态总结。
- `remaining_calories`：目标热量还剩多少。
- `remaining_protein_g`：蛋白质目标还差多少。
- `suggested_dinner_calorie_min` 和 `suggested_dinner_calorie_max`：晚餐建议热量范围。
- `guidance`：一般性建议。
- `cautions`：缺少档案或热量超标等提醒。

## 当前还不能做什么

这一阶段仍然不能做：

- 不能生成可视化图表或前端报表。
- 不能生成精确菜单。
- 不能查询食物数据库。
- 不能做 RAG 知识库问答。
- 不能自动制定完整训练计划。
- 不能替代医生、注册营养师或物理治疗师。

## 容易出问题的操作

### 1. 没有用户档案

如果没有设置身高、体重、年龄、活动水平和目标，系统无法计算目标热量和蛋白质目标。Agent 应先调用 `get_user_profile`，缺失时引导用户补档案。

### 2. 记录太少

如果最近 7 天没有完整饮食或体重记录，周报只能基于已有数据总结，不能代表真实执行情况。

### 3. 活动消耗是估算

活动消耗通常误差较大。周报里的净热量只能作为参考，不能当成精确代谢结果。

### 4. 日内建议不是精确菜单

`get_daily_guidance` 只给热量范围和一般建议。比如“优先高蛋白、低油、蔬菜和适量主食”，不会精确到每克食物。

## 推荐 Agent 行为

- 周报先展示 `report_text`，用户要细节时再展开 `daily_points`。
- 如果目标缺失，先引导用户补档案，而不是强行判断达标。
- 对体重变化保持保守，不用单周数据做医学判断。
- 饮食建议避免极端节食、脱水或惩罚性运动。
- 提醒用户热量、蛋白质和运动消耗都可能是估算。
