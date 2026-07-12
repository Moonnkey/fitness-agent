# Fitness Agent 架构设计中文版

## 目的

这份文档定义 Fitness Agent 的 MVP 架构。它的目标是指导第一阶段实现，而不是提前设计所有未来功能。

MVP 先跑通本地后端工具闭环：

```text
Agent 形态的结构化或半结构化输入
  -> Pydantic schema 校验
  -> core service
  -> SQLAlchemy 持久化
  -> SQLite
  -> summary 输出
```

CLI 是开发和调试入口。长期主要调用者是 Codex 这类 Agent，后续通过 MCP tools 调用同一套 schemas 和 core services。

## 设计原则

- 业务逻辑放在 `app/core`。
- CLI 和 MCP 只做薄接口层。
- CLI 和 MCP 共用同一套 core services。
- service 边界尽量使用明确的结构化输入。
- 用 `raw_text` 和 `metadata_json` 保留半结构化上下文。
- 对估算值保留来源和不确定性信息。
- 第一版数据库 schema 保持小而实用。
- 本地记录和总结跑通前，不加 RAG。

## 分层

### CLI 层

位置：`app/cli`

职责：

- 解析命令行参数。
- 把参数转成 Pydantic schemas。
- 调用 core services。
- 输出简洁的人类可读结果。

CLI 不应该包含热量计算、summary 或数据库逻辑。

MVP 调试优先支持 JSON 输入，因为它更接近未来 Agent/MCP payload。也可以保留简单 item 参数，方便手动测试。

### MCP 层

位置：`app/mcp`

职责：

- 给 Agent 暴露 tools。
- 用 Pydantic schemas 校验 tool 输入。
- 调用 core services。
- 返回结构化 tool 结果。

MCP 应该等 CLI 和 core services 跑通后再加。

### Core Schemas

位置：`app/core/schemas`

职责：

- 定义外部输入输出结构。
- 被 CLI、MCP、测试和未来 API 复用。

初始 schemas：

- `UserProfileInput`
- `UserProfileOutput`
- `MealItemInput`
- `RecordMealInput`
- `MealOutput`
- `DailySummaryOutput`
- `WeightEntryInput`
- `ActivityEntryInput`

### Core Services

位置：`app/core/services`

职责：

- 承载业务行为。
- 做类型校验之外的业务规则校验。
- 协调数据库持久化。
- 返回 Pydantic outputs 或简单领域结果。

初始 services：

- `profile_service.py`
- `meal_service.py`
- `summary_service.py`
- `weight_service.py`
- `activity_service.py`
- `record_service.py`

`record_service.py` 负责跨类型的历史查询、单条详情查询、局部更新和硬删除。类型相关的重复判断保留在对应记录服务附近：

- `meal_service.py` 判断疑似重复饮食记录。
- `weight_service.py` 判断疑似重复体重记录。
- `activity_service.py` 判断疑似重复活动记录。

重复判断只做提醒，不会静默阻止保存。Agent 看到疑似重复但用户意图不明确时，应该先向用户确认。

更新行为：

- `get_record(record_type, record_id)` 返回一条 meal、meal_item、weight 或 activity 详情。
- `update_record(record_type, record_id, patch)` 做局部更新，并返回 `changed_fields`。
- 修改 meal item 数量时，后端不会自动重算热量和三大营养素。
- meal 更新可以用 `items_append` 追加食物，也可以用 `items_replace` 替换整顿饭的所有食物条目。
- 编辑后的记录保留 `updated_at`；完整 audit log 暂不属于 MVP 范围。

### 持久化层

位置：`app/core/db` 和 `app/core/models`

职责：

- 配置 SQLite engine 和 session。
- 定义 SQLAlchemy models。
- 为本地 MVP 创建数据表。
- 避免数据库代码散落在 CLI 和 MCP 里。

## 数据库选择

MVP 使用 SQLite。

默认数据库路径：

```text
./data/fitness-agent.sqlite3
```

数据库路径可以用环境变量覆盖：

```text
FITNESS_AGENT_DB_PATH=/tmp/fitness-agent-test.sqlite3
```

`data/` 目录应该被 Git 忽略。测试应该使用临时 SQLite 文件或内存数据库。

因为 MVP 暂不引入 Alembic，`init_db()` 可以执行少量 SQLite-only 的兼容升级，比如给已有本地表补充缺失的 `updated_at` 列。

## 初始数据模型

### UserProfile

用途：保存本地用户设置和目标信息。

字段：

- `id`
- `height_cm`
- `weight_kg`
- `age`
- `sex`
- `activity_level`
- `goal_type`
- `goal_weight_kg`
- `target_calories`
- `target_protein_g`
- `created_at`
- `updated_at`

MVP 假设：单个本地用户。只保存一条 profile 记录，后续更新它。

允许的 `goal_type`：

- `fat_loss`
- `muscle_gain`
- `maintenance`
- `recomposition`

目标计算规则：

- 手动传入的 `target_calories` 和 `target_protein_g` 优先。
- 如果用户档案数据足够，用 Mifflin-St Jeor 公式计算 BMR。
- TDEE 按 `BMR * activity_factor` 计算。
- MVP 阶段只暴露基础目标计算结果，不生成完整饮食计划。

### Meal

用途：按日期和餐次归组饮食条目。

字段：

- `id`
- `date`
- `meal_type`
- `raw_text`
- `metadata_json`
- `note`
- `created_at`
- `updated_at`

允许的 `meal_type`：

- `breakfast`
- `lunch`
- `dinner`
- `snack`
- `other`

### MealItem

用途：保存单个食物条目的营养值。

字段：

- `id`
- `meal_id`
- `name`
- `quantity`
- `unit`
- `grams`
- `calories`
- `protein_g`
- `carbs_g`
- `fat_g`
- `source`
- `is_estimated`
- `raw_text`
- `metadata_json`
- `note`
- `created_at`

`source` 示例：

- `user`
- `manual_estimate`
- `food_database`
- `agent_estimate`

饮食数据同时保存结构化和半结构化内容：

- 结构化字段用于统计和 summary。
- `raw_text` 保存用户原始描述或 Agent 解析来源文本。
- `metadata_json` 保存估算假设、置信度、烹饪方式、品牌、prompt 上下文，或暂时不值得单独建字段的未来扩展信息。

第一阶段后端不解析自然语言。Agent 可以负责解析和估算，然后把结构化字段、`raw_text` 和 `metadata_json` 一起传给后端。

### WeightEntry

用途：保存体重记录。

字段：

- `id`
- `date`
- `weight_kg`
- `raw_text`
- `metadata_json`
- `note`
- `created_at`

第三阶段范围：实现体重记录，并提供最近体重和简单 7 日均重。

### ActivityEntry

用途：保存简单活动或训练消耗。

字段：

- `id`
- `date`
- `activity_type`
- `duration_minutes`
- `calories_burned`
- `is_estimated`
- `raw_text`
- `metadata_json`
- `note`
- `created_at`

第三阶段范围：实现简单活动记录。暂不做结构化力量训练编程、动作库、肌群映射或周期计划。

## 第一阶段实现切片

只实现：

- SQLite 初始化。
- `UserProfile`。
- `Meal`。
- `MealItem`。
- `profile_service`。
- `meal_service`。
- `summary_service`。
- profile、meal、summary 的 CLI 命令。
- profile、meal 记录、daily summary 测试。

暂缓：

- 体重记录。
- 活动记录。
- MCP tools。
- RAG。
- Skill。

## 第三阶段实现切片

实现：

- `WeightEntry`。
- `ActivityEntry`。
- `weight_service`。
- `activity_service`。
- summary 中加入活动消耗和净热量。
- weight 和 activity 的 CLI 命令。
- weight 和 activity 的 MCP tools。
- Skill 工具契约更新。

不做：

- 结构化动作库。
- 肌群映射。
- 训练计划优化。
- RAG。
- 食物数据库查询。

## Service API 草案

### Profile Service

```python
def update_user_profile(input: UserProfileInput) -> UserProfileOutput:
    ...

def get_user_profile() -> UserProfileOutput | None:
    ...

def calculate_profile_targets(input: UserProfileInput) -> ProfileTargets:
    ...
```

### Meal Service

```python
def record_meal(input: RecordMealInput) -> MealOutput:
    ...

def list_meals_for_date(date: date) -> list[MealOutput]:
    ...
```

### Summary Service

```python
def get_daily_summary(date: date) -> DailySummaryOutput:
    ...
```

### Weight Service

```python
def record_weight(input: WeightEntryInput) -> WeightEntryOutput:
    ...

def get_weight_trend(days: int = 7) -> WeightTrendOutput:
    ...
```

### Activity Service

```python
def record_activity(input: ActivityEntryInput) -> ActivityEntryOutput:
    ...

def list_activities_for_date(date: date) -> list[ActivityEntryOutput]:
    ...
```

## CLI 草案

### 用户档案

```bash
uv run fitness-agent profile set \
  --height-cm 175 \
  --weight-kg 75 \
  --age 30 \
  --sex male \
  --activity-level moderate \
  --goal-weight-kg 70
```

```bash
uv run fitness-agent profile show
```

### 饮食

MVP 优先支持 JSON 输入，因为它更接近未来 MCP tool payload。

```bash
uv run fitness-agent meal add --json '{
  "date": "today",
  "meal_type": "breakfast",
  "raw_text": "早餐吃了两个鸡蛋一碗米饭",
  "items": [
    {
      "name": "鸡蛋",
      "quantity": 2,
      "unit": "个",
      "calories": 144,
      "protein_g": 12,
      "carbs_g": 1,
      "fat_g": 10,
      "is_estimated": true,
      "source": "agent_estimate",
      "metadata": {
        "assumption": "按普通水煮蛋估算"
      }
    }
  ]
}'
```

同时支持可重复的 `--item` 参数，方便手动调试。

格式：

```text
name,quantity,unit,calories,protein_g,carbs_g,fat_g
```

示例：

```bash
uv run fitness-agent meal add \
  --date today \
  --type breakfast \
  --item "egg,2,piece,144,12,1,10" \
  --item "soy milk,1,cup,120,7,10,4"
```

### 总结

```bash
uv run fitness-agent summary today
```

```bash
uv run fitness-agent summary date 2026-07-08
```

最小 summary 输出：

- 日期。
- 今日总热量。
- 活动消耗，如果有记录。
- 净热量，按摄入减活动消耗计算。
- 蛋白质、碳水、脂肪总量。
- 目标热量，如果有。
- 剩余热量，如果有。
- 餐次数量。
- 每餐小计。
- 估算条目数量。

### 开发命令

```bash
uv run fitness-agent dev reset-db --yes
```

重置数据库必须要求 `--yes`，默认不能执行。

### 体重

优先支持 JSON 输入：

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

查看趋势：

```bash
uv run fitness-agent weight trend --days 7
```

### 活动

优先支持 JSON 输入：

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

## MCP 策略

等第一版 CLI 切片跑通后，再加 MCP。

初始 MCP tools：

- `update_user_profile`
- `get_user_profile`
- `record_meal`
- `get_daily_summary`
- 第三阶段新增：
  - `record_weight`
  - `get_weight_trend`
  - `record_activity`

MCP tool 输入应该尽量和 Pydantic schemas 保持一致。MCP tools 不直接写业务逻辑。

第一批 MCP payload 应该和 CLI 接受的 JSON 形态一致。

## Skill 策略

等 MCP tools 存在后，再创建 `skill/SKILL.md`。

Skill 需要说明：

- 什么时候调用 `record_meal`。
- 什么时候调用 `get_daily_summary`。
- 什么时候追问。
- 什么时候可以估算。
- 如何在回复中标注不确定性。
- 如何记录体重和活动，同时避免过度解读训练数据。

## 测试策略

初始测试：

- Profile 可以创建和更新。
- Profile 在信息足够时能计算 BMR/TDEE 风格的目标值。
- Meal 可以记录多个 items。
- Meal 记录能保留 `raw_text` 和 `metadata_json`。
- Daily summary 能正确汇总热量和宏量营养素。
- Daily summary 能返回估算条目数量。
- 空日期 summary 返回 0。
- CLI help 正常。
- 可以记录体重，trend 输出最近体重和均值。
- 可以记录活动，daily summary 包含活动消耗。
- MCP tools 暴露体重和活动操作。

测试规则：

- core services 尽量不通过 CLI 测试。
- CLI 测试只覆盖命令 wiring 和输出。
- 测试不能写入真实本地用户数据。

## 非目标

第一阶段不实现：

- 完整食物数据库查询。
- 自然语言解析。
- RAG。
- MCP server。
- Skill。
- Web UI。
- 登录认证。
- 云同步。
- 多用户。
- 模型微调。

## 待定问题

- 使用 SQLAlchemy declarative models 还是 SQLModel。
- 公开发布前是否需要数据库 migration。
- 营养数值统一用 float 还是 decimal。
- 在没有食物数据库前，应该做多少默认热量估算。
