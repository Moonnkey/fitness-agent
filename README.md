# Fitness Agent

Fitness Agent 是一个本地优先的 AI 健康减脂助手。它用 Python、SQLite、CLI、MCP tools 和本地 Web Chat 跑通“记录饮食/体重/活动 -> 汇总热量和蛋白质 -> 给出阶段反馈”的最小闭环。

这个项目的重点不是做一个只会聊天的机器人，而是把健康减脂场景里的稳定业务能力沉淀成可复用的 core services，再通过 CLI、MCP、Web Chat 和未来移动端 API 暴露出来。后续独立 Agent 层只负责意图理解、计划、追问、工具调用和结果解释。

> 本项目只提供一般性健康和减脂记录辅助，不提供医疗诊断、治疗建议或极端减重方案。

## 当前能力

- 用户档案：记录身高、体重、年龄、性别、活动水平和目标类型，估算 BMR/TDEE、目标热量和蛋白质。
- 饮食记录：按日期和餐次记录食物、热量、蛋白质、碳水和脂肪，保留原始文本和估算依据。
- 体重记录：保存体重观察，返回最近体重和简单趋势。
- 活动记录：记录走路、跑步、骑车、力量训练等简单活动和估算消耗。
- 每日总结：汇总摄入热量、活动消耗、净热量、蛋白质和剩余目标热量。
- 历史管理：按日期查询记录，按 id 查看、更新或删除饮食、体重和活动记录。
- 重复提醒：记录饮食、体重或活动前可检查疑似重复记录。
- MCP tools：让 Codex 或其他 Agent 通过统一工具契约调用本地能力。
- Web Chat MVP：本地启动 FastAPI 聊天页面，手机可在同一局域网访问，通过轻量 Agent 调用 MCP tools。

## 架构

```text
手机或浏览器
  -> FastAPI Web Chat
  -> app/agent ChatService
  -> ModelClient 生成 tool-call plan
  -> MCP client
  -> app/mcp MCP tools
  -> app/core/services
  -> SQLite
```

另一条本地调试链路：

```text
CLI
  -> app/core/schemas
  -> app/core/services
  -> SQLite
```

核心分层：

- `app/core`：业务逻辑中心，包括 schemas、services、models 和 SQLite session。
- `app/cli`：命令行入口，只做参数解析和输出。
- `app/mcp`：MCP tools，调用同一套 core services。
- `app/agent`：轻量 Agent 编排层，把用户消息转成结构化 MCP tool-call plan。
- `app/web`：FastAPI Web Chat 和静态页面。
- `skill/`：给 Codex/Agent 使用的 skill 说明和工具契约。
- `docs/`：MVP、架构、使用指南、阶段手册和学习复盘。

## 快速开始

### 1. 准备环境

推荐使用 Python 3.11+ 和 `uv`：

```bash
uv sync --extra dev --extra mcp
```

如果需要指定 Python 版本：

```bash
uv sync --extra dev --extra mcp --python python3.12
```

### 2. 运行测试

```bash
uv run pytest
```

如果配置了 ruff：

```bash
uv run ruff check .
```

### 3. 使用 CLI

查看命令：

```bash
uv run fitness-agent --help
```

设置用户档案：

```bash
uv run fitness-agent profile set \
  --height-cm 180 \
  --weight-kg 80 \
  --age 30 \
  --sex male \
  --activity-level moderate \
  --goal-type fat_loss
```

记录一顿饭：

```bash
uv run fitness-agent meal add \
  --date today \
  --type breakfast \
  --item "egg,2,piece,144,12,1,10"
```

查看今日总结：

```bash
uv run fitness-agent summary today
```

### 4. 启动 MCP server

```bash
uv run fitness-agent-mcp
```

MCP tools 会调用 `app/core/services`，不会复制热量、summary 或记录逻辑。

### 5. 启动 Web Chat

真实聊天模式需要 OpenAI API key：

```bash
export OPENAI_API_KEY="你的 OpenAI API key"
export FITNESS_AGENT_MODEL="gpt-4.1-mini"
```

如果使用 OpenAI-compatible 中转站，还可以设置：

```bash
export OPENAI_BASE_URL="https://你的中转站域名/v1"
export FITNESS_AGENT_MODEL="中转站支持的模型名"
```

启动服务：

```bash
uv run fitness-agent-web
```

电脑访问：

```text
http://127.0.0.1:8000
```

手机和电脑在同一局域网时，手机访问：

```text
http://电脑局域网IP:8000
```

显式 fake 模式可以用于检查页面和 HTTP 服务，不代表真实自然语言理解能力：

```bash
FITNESS_AGENT_AGENT_MODE=fake uv run fitness-agent-web
```

## 数据存储

默认 SQLite 数据库位置：

```text
data/fitness-agent.sqlite3
```

可以通过环境变量覆盖：

```bash
FITNESS_AGENT_DB_PATH=/tmp/fitness-agent-test.sqlite3 uv run fitness-agent summary today
```

请不要提交真实健康数据、数据库文件、API key 或其他敏感信息。

## Agent / Harness 设计思路

本项目把 Agent 理解为 `model + harness`：

- 模型负责自然语言理解和计划生成。
- MCP tools 是模型可调用的行动能力。
- Core services 是稳定业务能力。
- SQLite 是业务事实存储，不等同于 Agent memory。
- 工具返回结果是当前对话的 observation 来源。
- 长期提炼出的目标、偏好、习惯和约束，才更接近未来 Agent memory。
- 健康安全规则、隐私规则和高风险操作确认属于 permissions / safety boundary。

当前 Web Chat MVP 已经具备最小 Agent loop：

```text
用户消息 -> 生成 AgentPlan -> 调用 MCP tools -> 观察工具结果 -> 返回中文回复
```

下一阶段会继续补强：

- planning eval：验证自然语言是否生成正确工具调用。
- pending action：支持“发现重复，是否继续保存？”这类多轮确认。
- memory 设计：区分业务记录、用户画像、长期偏好和短期上下文。
- permission 分级：删除、覆盖、健康风险建议等高风险操作需要更严格边界。

## 当前限制

- 不做医疗诊断或治疗建议。
- 不支持图片识别、体重秤截图识别或食物数据库查询。
- Web Chat 不保存聊天记录。
- 暂不支持登录、多用户、云同步、HTTPS 或公网部署。
- 当前 Agent planning 主要依赖 prompt 和 schema，还需要系统化 eval。
- Stdio MCP client 每次调用会有额外初始化开销，Web Chat 响应速度后续还需优化。

## 文档

- [中文使用指南](docs/user-guide.zh.md)
- [中文架构设计](docs/architecture.zh.md)
- [中文 MVP 范围](docs/mvp.zh.md)
- [Web Chat MVP 设计](docs/web-chat-mvp.zh.md)
- [第七阶段用户手册：Web Chat 最小闭环](docs/stage-guides/stage-07-web-chat-mvp.zh.md)
- [AI Agent 学习与秋招提示词库](docs/learning/prompt-library.zh.md)

## 开发定位

这个仓库也是一个 AI Agent 工程学习项目，用来练习：

- tool calling 和 MCP 工具契约设计
- core services 与接口适配层解耦
- Agent loop、observation、context management 和 memory 边界
- 本地优先数据持久化
- 健康安全和隐私边界
- 面向秋招项目讲述的工程复盘
