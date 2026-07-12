# 第五阶段用户使用手册：单条详情和记录纠错

## 这一阶段新增了什么

第五阶段让 Fitness Agent 从“能记录、能删除”进化到“能查看单条详情、能局部修改”。

现在用户可以让 Agent 做这些事：

- 查看某一条饮食、食物条目、体重或活动记录的详情。
- 修改一条体重记录，比如把 `79.6kg` 改成 `79.2kg`。
- 修改一个食物条目，比如把鸡蛋从 2 个改成 3 个。
- 给已有一顿饭追加食物，比如早餐再加一杯无糖豆浆。
- 替换整顿饭的食物内容，比如“早餐不是鸡蛋，是一个包子”。
- 修改活动记录，比如把快走消耗从 `180 kcal` 改成 `220 kcal`。

新增 MCP tools：

- `get_record`
- `update_record`

对应 CLI 命令：

- `fitness-agent records show`
- `fitness-agent records update`

## 推荐使用方式

日常使用时，优先让 Agent 通过 MCP 工具操作，而不是用户手写 JSON。

推荐流程：

```text
1. 用户用自然语言说明想修改什么。
2. Agent 先调用 get_records_for_date 找候选记录。
3. 如果候选记录不唯一，Agent 先让用户确认。
4. Agent 调用 get_record 查看详情。
5. Agent 构造 patch 并调用 update_record。
6. 如果修改会影响每日热量，Agent 再调用 get_daily_summary 给用户确认结果。
```

## 提示词示例

### 修改体重

```text
我刚才体重记录错了，应该是 79.2kg。请使用 fitness-agent MCP 工具先查询今天的 weight 记录；如果只有一条明显候选，就调用 update_record 把 weight_kg 改成 79.2；最后调用 get_record 返回修改后的记录。
```

### 修改食物数量

```text
我早餐的鸡蛋不是 2 个，是 3 个。请先调用 get_records_for_date 找到今天早餐的 meal 和对应 meal_item。然后按 3 个普通水煮蛋重新估算热量和蛋白质、碳水、脂肪，并调用 update_record 更新这个 meal_item 的 quantity、calories、protein_g、carbs_g、fat_g。后端不会自动重算营养，所以你必须把更新后的营养值一起传入。
```

### 给一顿饭追加食物

```text
我早餐还喝了一杯无糖豆浆。请先找到今天早餐的 meal id，然后调用 update_record，给 meal patch 传 items_append，追加无糖豆浆这一项。请估算豆浆的热量和三大营养素，并把 raw_text 更新成包含豆浆的描述。
```

### 替换整顿饭

```text
我刚才早餐记错了，不是两个鸡蛋，是一个包子。请先查询今天早餐记录并让我确认要修改哪一条，然后调用 update_record，使用 items_replace 把这顿饭的食物条目替换成一个包子，并估算热量和三大营养素。
```

### 修改活动消耗

```text
我今天快走那条活动消耗估低了，应该是 220 kcal。请查询今天的 activity 记录，找到快走那条后调用 update_record，把 calories_burned 改成 220，并返回修改后的记录。
```

### 查看单条详情

```text
请使用 fitness-agent MCP 工具查看今天早餐那条记录的详情。先调用 get_records_for_date 找到 meal id，再调用 get_record 返回完整内容。
```

## CLI 示例

CLI 主要用于开发调试。

查看记录：

```bash
uv run fitness-agent records show meal 1
uv run fitness-agent records show meal_item 1
uv run fitness-agent records show weight 1
uv run fitness-agent records show activity 1
```

修改体重：

```bash
uv run fitness-agent records update weight 1 --json '{"weight_kg": 79.2}'
```

修改食物条目：

```bash
uv run fitness-agent records update meal_item 1 --json '{
  "quantity": 3,
  "calories": 216,
  "protein_g": 18.9,
  "carbs_g": 1.65,
  "fat_g": 14.25
}'
```

给已有 meal 追加食物：

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

替换整顿饭：

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

## 当前还不能做什么

这一阶段仍然不能做：

- 自动识别用户自然语言并直接修改数据库。自然语言理解仍由 Agent 完成。
- 自动重算食物营养。后端不会因为 `quantity` 从 2 改成 3 就自动修改热量和宏量。
- 保留完整修改历史。当前只覆盖原记录并更新 `updated_at`。
- 撤销修改。改错后需要再次调用 `update_record` 或删除后重新记录。
- 复杂训练记录编辑，比如动作、组数、重量、肌群和训练计划。
- 根据长期趋势自动给出完整饮食或训练计划。

## 容易出问题的操作

### 1. 只改数量，不改热量

如果用户说“鸡蛋从 2 个改成 3 个”，Agent 不能只传：

```json
{"quantity": 3}
```

这样后端会只改数量，热量仍然保持旧值。正确做法是同时传入重新估算后的：

```json
{
  "quantity": 3,
  "calories": 216,
  "protein_g": 18.9,
  "carbs_g": 1.65,
  "fat_g": 14.25
}
```

### 2. 误用 `items_replace`

`items_replace` 会替换整顿饭的所有食物条目。只有用户明确表示“整顿饭改成另一组食物”时才应该用。

如果用户只是说“早餐还喝了一杯豆浆”，应该用 `items_append`。

### 3. 候选记录不唯一

如果今天有多条早餐或多条活动记录，Agent 不应该直接修改。应该先列出候选项，让用户确认。

### 4. 修改后 summary 不会自动返回

`update_record` 只返回修改后的记录和 `changed_fields`。如果用户关心当天总热量或剩余热量，Agent 需要再调用 `get_daily_summary`。

## 推荐 Agent 行为

- 不确定要改哪条时，先问用户确认。
- 修改食物数量或种类时，同步更新热量和三大营养素。
- 修改完成后，告诉用户改了哪些字段。
- 如果修改影响当天总摄入或活动消耗，主动调用 `get_daily_summary` 给用户看更新后的结果。
- 把估算假设写入 `metadata`，尤其是食物重量、烹饪方式、品牌或活动强度。
