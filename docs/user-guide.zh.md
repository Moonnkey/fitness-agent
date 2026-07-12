# Fitness Agent 使用指南

## 当前项目状态

Fitness Agent 现在是一个本地优先的减脂健身记录工具。它已经可以通过 CLI 或 MCP 工具记录和查询：

- 用户档案：身高、体重、年龄、性别、活动水平、目标类型。
- 饮食记录：餐次、食物、热量、蛋白质、碳水、脂肪、估算来源。
- 体重记录：单次体重、最近体重、简单 7 日均重。
- 活动记录：活动类型、时长、估算消耗。
- 每日总结：摄入热量、活动消耗、净热量、蛋白质、目标热量、剩余热量。
- 历史管理：按日期查询记录、按类型筛选、按 id 硬删除误记记录。
- 记录编辑：按 id 查看单条记录，局部更新饮食、体重、活动和食物条目。
- 重复提醒：记录饮食、体重或活动时返回疑似重复记录，方便 Agent 追问确认。

它还不是完整 AI 教练。当前版本不做：

- 食物数据库查询。
- 图片识别。
- 自动训练计划。
- 肌群恢复分析。
- RAG 知识库问答。
- 云同步或多用户账号。

## 阶段使用手册

每个开发阶段完成后，都会补一份面向用户的阶段使用手册，说明这一阶段新增能力、提示词示例、CLI 示例、限制和风险。

当前阶段手册：

- [第五阶段：单条详情和记录纠错](stage-guides/stage-05-record-detail-update.zh.md)

## 数据保存在哪里

默认 SQLite 数据库位置：

```bash
data/fitness-agent.sqlite3
```

可以用环境变量临时指定数据库：

```bash
FITNESS_AGENT_DB_PATH=/tmp/fitness-agent-test.sqlite3 uv run fitness-agent summary today
```

本地数据库和 `.uv-cache/` 都已被 `.gitignore` 忽略，不会提交到 Git。

## 准备环境

安装依赖：

```bash
uv sync --extra dev --extra mcp --python python3.12
```

如果你的环境不允许 `uv` 写入默认缓存，可以使用项目内缓存：

```bash
uv --cache-dir .uv-cache sync --extra dev --extra mcp --python python3.12
```

检查 CLI 是否可用：

```bash
uv run fitness-agent --help
```

当前应该能看到这些命令：

```text
profile
meal
summary
weight
activity
records
dev
```

## CLI 使用

CLI 主要用于本地调试。真实使用时，更推荐让 Codex/Agent 通过 MCP 工具调用。

### 1. 重置本地数据库

开发测试时可以重置数据库：

```bash
uv run fitness-agent dev reset-db --yes
```

没有 `--yes` 时不会执行，避免误删。

### 2. 设置用户档案

```bash
uv run fitness-agent profile set \
  --height-cm 180 \
  --weight-kg 80 \
  --age 30 \
  --sex male \
  --activity-level moderate \
  --goal-type fat_loss
```

查看档案：

```bash
uv run fitness-agent profile show
```

当前会根据档案估算：

- BMR。
- TDEE。
- 目标热量。
- 目标蛋白质。

手动传入的 `target_calories` 和 `target_protein_g` 会优先于系统估算。

### 3. 记录饮食

推荐用 JSON，因为这和未来 Agent/MCP payload 一致：

```bash
uv run fitness-agent meal add --json '{
  "date": "today",
  "meal_type": "breakfast",
  "raw_text": "今天早餐吃了两个鸡蛋",
  "metadata": {
    "estimation_basis": "按2个普通水煮鸡蛋估算，每个约50g可食部"
  },
  "items": [
    {
      "name": "水煮鸡蛋",
      "quantity": 2,
      "unit": "个",
      "grams": 100,
      "calories": 144,
      "protein_g": 12.6,
      "carbs_g": 1.1,
      "fat_g": 9.5,
      "is_estimated": true,
      "source": "agent_estimate",
      "raw_text": "两个鸡蛋",
      "metadata": {
        "assumption": "普通水煮蛋，按每个约50g可食部估算"
      }
    }
  ]
}'
```

也支持简单 `--item` 调试格式：

```bash
uv run fitness-agent meal add \
  --date today \
  --type breakfast \
  --item "egg,2,piece,144,12,1,10"
```

`--item` 格式是：

```text
name,quantity,unit,calories,protein_g,carbs_g,fat_g
```

### 4. 记录体重

```bash
uv run fitness-agent weight add --json '{
  "date": "today",
  "weight_kg": 79.6,
  "raw_text": "今天早上空腹 79.6kg",
  "metadata": {
    "timing": "morning fasting"
  }
}'
```

查看体重趋势：

```bash
uv run fitness-agent weight trend --days 7
```

当前趋势只是简单计算最近记录和指定天数内平均体重，不做复杂趋势判断。

### 5. 记录活动

```bash
uv run fitness-agent activity add --json '{
  "date": "today",
  "activity_type": "walking",
  "duration_minutes": 40,
  "calories_burned": 180,
  "is_estimated": true,
  "raw_text": "今天快走 40 分钟",
  "metadata": {
    "estimation_basis": "中等强度快走估算"
  }
}'
```

活动记录只用于简单热量消耗统计。当前不记录动作、组数、重量、肌群或训练计划质量。

### 6. 查看每日总结

查看今天：

```bash
uv run fitness-agent summary today
```

查看指定日期：

```bash
uv run fitness-agent summary date 2026-07-11
```

summary 当前包含：

- 总摄入热量。
- 蛋白质、碳水、脂肪。
- 活动消耗。
- 净热量：摄入热量减活动消耗。
- 目标热量。
- 剩余热量。
- 目标蛋白质。
- 餐次数量。
- 估算条目数量。

### 7. 查询和删除历史记录

查询今天所有记录：

```bash
uv run fitness-agent records list --date today
```

只查某一类记录：

```bash
uv run fitness-agent records list --date today --type meal
uv run fitness-agent records list --date today --type weight
uv run fitness-agent records list --date today --type activity
```

删除误记记录：

```bash
uv run fitness-agent records delete meal 1
uv run fitness-agent records delete meal_item 1
uv run fitness-agent records delete weight 1
uv run fitness-agent records delete activity 1
```

删除是硬删除，不会保留回收站或审计记录。删除前建议先用 `records list` 找到正确 id。

查看单条记录详情：

```bash
uv run fitness-agent records show meal 1
uv run fitness-agent records show meal_item 1
uv run fitness-agent records show weight 1
uv run fitness-agent records show activity 1
```

局部更新记录：

```bash
uv run fitness-agent records update weight 1 --json '{"weight_kg": 79.2}'
```

修改食物条目时，后端不会自动重算热量和三大营养素。如果数量或食物发生变化，需要同时传入更新后的营养值：

```bash
uv run fitness-agent records update meal_item 1 --json '{
  "quantity": 3,
  "calories": 216,
  "protein_g": 18.9,
  "carbs_g": 1.65,
  "fat_g": 14.25
}'
```

给已有一顿饭追加食物：

```bash
uv run fitness-agent records update meal 1 --json '{
  "raw_text": "早餐两个鸡蛋和一杯无糖豆浆",
  "items_append": [
    {
      "name": "无糖豆浆",
      "quantity": 1,
      "unit": "杯",
      "calories": 80,
      "protein_g": 7,
      "carbs_g": 4,
      "fat_g": 4,
      "is_estimated": true
    }
  ]
}'
```

替换整顿饭的食物条目：

```bash
uv run fitness-agent records update meal 1 --json '{
  "raw_text": "早餐改成一个包子",
  "items_replace": [
    {
      "name": "包子",
      "quantity": 1,
      "unit": "个",
      "calories": 250,
      "protein_g": 8,
      "carbs_g": 35,
      "fat_g": 8,
      "is_estimated": true
    }
  ]
}'
```

## MCP 使用

项目已经提供本地 MCP server：

```bash
uv run fitness-agent-mcp
```

Codex 中可注册为 stdio MCP server：

```bash
codex mcp add fitness-agent -- zsh -lc 'cd /Users/houshufeng/fitness-agent && .venv/bin/fitness-agent-mcp'
```

查看配置：

```bash
codex mcp list
codex mcp get fitness-agent
```

注册后通常需要重启 Codex 或开启新会话，Agent 才能发现新工具。

当前 MCP tools：

- `update_user_profile`
- `get_user_profile`
- `record_meal`
- `record_weight`
- `get_weight_trend`
- `record_activity`
- `get_daily_summary`
- `get_records_for_date`
- `get_record`
- `update_record`
- `delete_record`
- `check_duplicate_meal`
- `check_duplicate_weight`
- `check_duplicate_activity`

## 给 Agent 的提示词示例

### 记录档案、饮食并总结

```text
请使用 fitness-agent MCP 工具帮我记录和总结。

我的档案是：男，30岁，身高180cm，体重80kg，活动水平 moderate，目标是减脂。

今天早餐我吃了两个鸡蛋。请你先估算这顿饭的热量、蛋白质、碳水和脂肪，然后调用 record_meal 保存。保存时 raw_text 使用我的原话，metadata 里写明你的估算假设。最后调用 get_daily_summary，告诉我今天目前摄入了多少热量和蛋白质，还剩多少目标热量。
```

### 记录体重

```text
使用 fitness-agent MCP 工具记录体重：今天早上空腹 79.6kg。请调用 record_weight 保存，raw_text 保留我的原话，metadata 里标注 morning fasting。然后调用 get_weight_trend 查看最近 7 天趋势。
```

### 记录活动并查询净热量

```text
使用 fitness-agent MCP 工具记录活动：今天快走 40 分钟，估算消耗 180 kcal。请调用 record_activity 保存，raw_text 保留我的原话，metadata 写明这是中等强度快走估算。最后调用 get_daily_summary 查看今天的摄入、活动消耗和净热量。
```

### 一次性记录多件事

```text
使用 fitness-agent MCP 工具处理下面的信息，不要只在对话里估算，请实际保存。

我的信息：
- 今天早上空腹体重 79.6kg
- 早餐吃了两个鸡蛋和一杯无糖豆浆
- 晚上快走 40 分钟，估算消耗 180 kcal

请你：
1. 调用 record_weight 保存体重。
2. 估算早餐营养后调用 record_meal 保存。
3. 调用 record_activity 保存活动。
4. 调用 get_daily_summary 输出今天 summary。
```

### 查询历史记录

```text
使用 fitness-agent MCP 工具查询我今天记录过什么。请调用 get_records_for_date，record_type 使用 all，然后按饮食、体重、活动分组告诉我。
```

```text
使用 fitness-agent MCP 工具查询今天的饮食记录。请调用 get_records_for_date，record_type 使用 meal，告诉我每条 meal id、餐次和总热量。
```

### 删除误记记录

```text
我刚才早餐记录错了。请先调用 get_records_for_date 查询今天的 meal 记录，找到最可能是刚才那条的记录后告诉我 id 和内容，等我确认后再调用 delete_record 删除。
```

如果你已经知道要删除的 id：

```text
使用 fitness-agent MCP 工具删除 meal id=3，这是我刚才重复记录的一顿早餐。请调用 delete_record，然后再调用 get_records_for_date 确认今天记录里已经没有这条。
```

### 修改记录

```text
我刚才体重记录错了，应该是 79.2kg。请使用 fitness-agent MCP 工具先调用 get_records_for_date 查询今天的 weight 记录；如果只有一条明显候选，就调用 update_record 把 weight_kg 改成 79.2；最后调用 get_record 返回修改后的记录。
```

```text
我早餐的鸡蛋不是 2 个，是 3 个。请先调用 get_records_for_date 找到今天早餐的 meal 和对应 meal_item。然后按 3 个普通水煮蛋重新估算热量和三大营养素，并调用 update_record 更新这个 meal_item 的 quantity、calories、protein_g、carbs_g、fat_g。后端不会自动重算营养，所以你必须把更新后的营养值一起传入。
```

```text
我早餐还喝了一杯无糖豆浆。请先找到今天早餐的 meal id，然后调用 update_record，给 meal patch 传 items_append，追加无糖豆浆这一项，并把 raw_text 更新成包含豆浆的原始描述。
```

### 处理重复提醒

```text
使用 fitness-agent MCP 工具记录早餐：今天早餐吃了两个鸡蛋。请先估算营养并调用 check_duplicate_meal 检查是否疑似重复；如果发现重复，先告诉我疑似重复记录并问我要不要继续保存；如果没有重复，再调用 record_meal 保存。
```

## 当前限制和注意事项

- 后端不解析自然语言。自然语言解析和估算由 Agent 完成，然后传结构化数据给工具。
- 热量、宏量营养素和活动消耗大多是估算值，除非用户明确提供或后续接入可靠数据源。
- 当前有重复提醒，但不会自动拦截保存。Agent 应根据 `duplicate_warnings` 或 `check_duplicate_*` 结果向用户确认。
- 当前支持按 id 局部编辑和硬删除记录，但还不保留完整修改历史。
- 修改食物数量时，后端不会自动重算营养；Agent 需要把更新后的热量和三大营养素一起传入。
- 当前 summary 的 `remaining_calories` 是目标热量减摄入热量；`net_calories` 是摄入热量减活动消耗。
- 当前体重趋势只是简单均值，不代表医学判断。

## 推荐使用方式

日常使用时，推荐流程是：

```text
1. 先让 Agent 调用 get_user_profile 检查档案。
2. 档案缺失时调用 update_user_profile。
3. 每次吃饭让 Agent 估算后调用 record_meal。
4. 每次称重调用 record_weight。
5. 每次运动调用 record_activity。
6. 每天任意时间调用 get_daily_summary 查看当天状态。
7. 如果怀疑重复或误记，让 Agent 调用 get_records_for_date 和 delete_record 处理。
8. 如果需要纠错，让 Agent 先定位记录，再调用 get_record 或 update_record。
```

开发调试时，推荐流程是：

```bash
uv run fitness-agent dev reset-db --yes
uv run fitness-agent profile set --height-cm 180 --weight-kg 80 --age 30 --sex male --activity-level moderate --goal-type fat_loss
uv run fitness-agent summary today
```
