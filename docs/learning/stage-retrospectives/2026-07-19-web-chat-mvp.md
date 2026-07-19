# 2026-07-19 第七阶段复盘：Web Chat MVP

## 本次实现了什么功能

第七阶段把 fitness-agent 从“Codex/Skill/MCP 外挂工具”推进到“可用手机浏览器访问的本地 Web Chat 最小闭环”。

新增能力：

- 启动本地 FastAPI Web Chat 服务。
- 提供极简移动端友好的聊天页面。
- 用户可以通过 `/api/chat` 发送自然语言饮食记录请求。
- 后端轻量 Agent 使用 `OpenAIModelClient` 把用户消息解析成 MCP tool-call plan。
- Web Chat 后端通过 MCP client 调用已有 `fitness-agent` MCP tools。
- 支持今日 summary 和 7 天 summary 的 HTTP 查询接口。
- 提供 `FakeModelClient` 作为测试/开发替身，避免测试依赖真实大模型。
- 不保存聊天消息，不做登录，不做公网部署，不做图片上传。

本阶段最重要的结果是：项目开始有了自己的轻量 Agent runtime，但没有破坏原来的 Codex/Skill/MCP 外挂模式。

## 本次功能在整体架构中的位置

第七阶段新增了两层：

- `app/agent`：轻量 Agent 层。
- `app/web`：Web Chat / HTTP interface 层。

新的调用链是：

```text
手机或浏览器
-> FastAPI Web Chat
-> ChatService
-> OpenAIModelClient 生成 tool-call plan
-> StdioFitnessMCPClient 调用 fitness-agent MCP tools
-> app/mcp/server.py
-> app/core/services
-> SQLite
```

这个设计让 Web Chat 成为一个新的 action interface，但仍然复用原来的 MCP 工具契约和 core services。

关键边界：

- Web 层只负责 HTTP 和静态页面。
- Agent 层负责计划、工具调用编排和中文回复。
- MCP 层负责统一工具协议。
- Core services 继续负责饮食、summary、历史、纠错等稳定业务逻辑。

这样避免了把热量计算、summary、记录更新逻辑复制到 Web 或 Agent 层。

## 涉及哪些模块

### Agent 层

- `app/agent/schemas.py`：定义 `AgentPlan`、`PlannedToolCall`、`ToolCallResult`、`ChatAgentResult`。
- `app/agent/prompts.py`：定义模型规划用 system prompt，要求输出 JSON tool-call plan。
- `app/agent/model_client.py`：实现 `OpenAIModelClient` 和 `FakeModelClient`。
- `app/agent/mcp_client.py`：实现 stdio MCP client，调用本地 `fitness-agent-mcp`。
- `app/agent/service.py`：实现 `ChatService`，串联模型计划、MCP 工具调用、重复提醒和中文回复。

### Web 层

- `app/web/server.py`：FastAPI 应用，提供 `/api/chat`、`/api/summary/today`、`/api/weekly-summary`、`/api/health`。
- `app/web/schemas.py`：Web API 请求/响应 schema。
- `app/web/static/index.html`、`styles.css`、`app.js`：极简聊天页面。

### 配置与依赖

- `pyproject.toml`：新增 `fastapi`、`uvicorn`、`openai`、`mcp` 依赖和 `fitness-agent-web` 启动命令。
- `uv.lock`：锁定新增依赖。

### 测试

- `tests/test_agent_service.py`：覆盖 Agent 编排、重复提醒、模型错误、工具错误。
- `tests/test_agent_mcp_client.py`：覆盖 stdio MCP client 和参数解析。
- `tests/test_web_chat.py`：覆盖 Web health、首页、chat、summary HTTP 路由。

### 文档

- `docs/web-chat-mvp.zh.md`：Web Chat MVP 设计。
- `docs/stage-guides/stage-07-web-chat-mvp.zh.md`：第七阶段用户使用手册。
- `docs/setup.zh.md`、`docs/user-guide.zh.md`、`docs/mvp.md`、`docs/mvp.zh.md`、`docs/architecture.md`、`docs/architecture.zh.md`：同步范围、启动方式和架构说明。

## 本次设计决策

### 1. Web Chat 后端调用 MCP tools，而不是直接调用 core services

直接调 core services 会更快、更简单，但这会让内置 Web Chat 和外部 Agent 使用不同接口。

本阶段选择让 Web Chat 也通过 MCP 调工具，原因是：

- Codex、未来外部 Agent、内置 Web Chat Agent 都共享同一套 tool contract。
- MCP tools 已经封装了核心业务能力，Web Chat 不需要重复实现。
- 后续如果把 Agent 换成其他框架，只要能调 MCP，就可以继续复用工具。

代价是本地调用链更长，stdio MCP 每次调用会有额外开销。MVP 阶段这个代价可以接受，后续如果性能不足，可以优化 MCP client 生命周期或在服务内部做长连接。

### 2. 只保留 OpenAIModelClient 和 FakeModelClient

没有加入 `RuleBasedModelClient`。

原因是规则分支很容易让用户误以为系统已经理解自然语言，但实际只是硬编码匹配。健康饮食记录对估算和字段完整性有要求，如果规则误判，用户体验会更差。

最终设计：

- `OpenAIModelClient`：真实业务 agent，用大模型解析用户消息。
- `FakeModelClient`：测试和开发替身，只返回预设计划，不理解输入。
- 如果 API key 缺失或模型输出解析失败，返回清晰错误，不做静默降级。

### 3. Agent 输出结构化计划，不直接写数据库

模型不直接操作数据库，也不直接调用 core services。它只输出：

```text
AgentPlan -> tool_calls -> MCP arguments
```

这样可以把大模型限制在“意图理解和计划生成”范围内，把真正的业务执行交给工具层。

### 4. MVP 不保存聊天消息

第七阶段不做聊天历史持久化，原因是：

- 当前核心目标是跑通手机聊天到 MCP 工具调用的最小闭环。
- 聊天记录涉及隐私、存储策略、删除策略和未来多用户边界。
- 饮食、体重、活动等业务记录已经由 core services 保存，聊天消息本身不是当前必须数据。

### 5. 前端极简

本阶段前端只做移动端可用，不做报表、图表和复杂交互。原因是当前风险主要在 Agent 工具调用链，而不是 UI 表现。

## 如何支撑未来独立 Agent 层

第七阶段已经出现了独立 Agent 层的雏形：

- `ModelClient` 抽象：未来可以替换不同模型或 Agent 框架。
- `AgentPlan` schema：让模型输出变成可验证的结构化计划。
- `ChatService`：承载 agent loop 的最小版本，包括 planning、tool use、observation handling、reply generation。
- `MCPClient` 抽象：让 Agent 不依赖具体 core service 实现，而是依赖稳定工具协议。
- `FakeModelClient`：让 Agent 编排测试和模型质量测试解耦。

未来可以在这个基础上继续演进：

- 增加 clarification pending-action 状态机。
- 增加 memory 提炼和召回。
- 增加 evaluation case，验证用户输入对应的工具调用是否正确。
- 增加图片识别、OCR、食物估算模型，但仍然把最终记录落到同一套 MCP/core services。
- 用更成熟的 Agent 框架替换 `ChatService`，但保留 MCP tool contract。

## 对应的 AI Agent / Harness 工程概念

- Model + Harness：OpenAI 模型只是规划组件；FastAPI、ChatService、MCP client、MCP tools、core services、SQLite 和文档规则共同构成 harness。
- Agent loop：用户输入 -> 生成计划 -> 调工具 -> 观察工具结果 -> 返回用户。
- Tool use：`record_meal`、`get_daily_summary`、`check_duplicate_meal` 等 MCP tools 是 Agent 的行动能力。
- Action Interface：Web Chat 是新的用户入口，MCP 是 Agent 调工具的接口，CLI 是开发调试入口。
- Observation：Agent 调用 summary/history 后得到的结构化数据，是当前对话的观察结果。
- Memory：当前阶段还没有真正 memory。SQLite 保存的是业务记录，只有被查询并注入上下文时才成为 observation 来源。
- Context management：当前只把用户当前消息发给模型；未来需要把用户画像、今日 summary、历史偏好选择性注入。
- Permissions / Safety Boundary：不保存聊天记录、不提交 API key、不做医学诊断、不建议极端减脂。
- Error handling：模型配置失败、模型 JSON 解析失败、MCP 工具失败都返回明确错误，而不是悄悄伪装成功。
- Evaluation：通过 FakeModelClient 和 FakeMCPClient 固定输入输出，验证 agent orchestration，而不是依赖真实模型随机表现。

## 秋招面试怎么讲

可以这样讲：

```text
我在健康减脂助手项目里做了一个 Web Chat MVP。这个阶段的目标不是简单做一个网页，而是把项目从 Codex 外挂工具推进到自带轻量 Agent runtime。

架构上，我没有让 Web 后端直接写数据库，也没有把热量和 summary 逻辑复制到接口层。Web Chat 的调用链是：用户在手机网页发消息，FastAPI 接收请求，ChatService 调 OpenAIModelClient 生成结构化 tool-call plan，然后通过 MCP client 调已有的 fitness-agent MCP tools，最后工具再调用 app/core/services 和 SQLite。

这样做的好处是，Codex、未来外部 Agent 和我自己的 Web Chat Agent 都使用同一套 MCP 工具契约。core services 仍然是稳定业务能力，MCP 是 action interface，Web Chat 是用户入口，Agent 层负责意图理解、计划、工具调用和结果解释。

我还特意没有做 RuleBasedModelClient。因为规则分支看起来可用，但会掩盖模型理解失败。真实业务只用 OpenAIModelClient，测试用 FakeModelClient 固定计划，这样可以把 Agent 编排测试和模型能力测试解耦。

这个阶段让我更清楚地理解 Agent 不是一个 prompt，而是 model + harness。模型负责理解和计划，harness 负责工具、状态、接口、安全边界、错误处理和测试。
```

## 面试官可能追问

### Q1：为什么 Web Chat 要通过 MCP 调工具，而不是直接调 core services？

推荐回答：

```text
直接调 core services 更短，但会让内置 Web Chat 和外部 Agent 走不同接口。我选择通过 MCP，是为了让 Codex、未来外部 Agent 和内置 Agent 都复用同一套 tool contract。这样工具能力、参数 schema、错误边界都更统一。代价是本地调用链变长，后续可以通过复用 MCP session 或优化 client 生命周期解决性能问题。
```

### Q2：FakeModelClient 和 RuleBasedModelClient 有什么区别？为什么只保留 Fake？

推荐回答：

```text
FakeModelClient 不理解输入，只返回测试里预设的 AgentPlan，用来测试编排链路。RuleBasedModelClient 会在主程序里用规则猜用户意图，容易让人误以为系统具备自然语言理解能力。饮食记录如果误判，会直接写入错误数据。所以我宁愿模型失败时返回明确错误，也不在生产路径里做脆弱规则降级。
```

### Q3：这个阶段的 Agent loop 在哪里？

推荐回答：

```text
最小 Agent loop 在 ChatService 里：先让 ModelClient 根据用户消息生成 AgentPlan，然后按顺序调用 MCP tools，拿到工具结果后构造中文回复。如果发现重复记录，会中断后续 record_meal 并让用户确认。这是一个很轻量的 loop，未来可以扩展成多轮追问、pending action 和 memory 注入。
```

### Q4：你怎么测试 Agent 功能？真实模型输出不稳定怎么办？

推荐回答：

```text
我把模型客户端抽象成 ModelClient。测试时用 FakeModelClient 返回固定 AgentPlan，用 FakeMCPClient 返回固定工具结果，这样能稳定测试 ChatService 的编排逻辑、错误处理和重复提醒。真实模型质量需要另一类 eval case 来测，比如输入自然语言后期望生成哪些工具调用，但不应该让单元测试依赖真实 API。
```

### Q5：SQLite 是不是 Agent memory？

推荐回答：

```text
当前不是。SQLite 保存饮食、体重、活动和用户画像这些业务事实。Agent 调用工具查询这些数据，并把结果放进当前上下文时，它们是 observation。真正的 memory 更接近从长期交互中提炼出的目标、偏好、习惯和约束，并且能在未来对话中被选择性召回。
```

### Q6：这个设计的主要风险是什么？

推荐回答：

```text
第一是性能，Web Chat 每次通过 stdio MCP 调工具，链路比直接调 core services 更长。第二是模型规划质量，OpenAI 输出 JSON plan 如果字段不完整，会影响工具调用。第三是当前没有多轮 pending-action 状态机，复杂澄清和确认还不够好。第四是没有登录和 HTTPS，只适合本地可信局域网。
```

## 当前限制、风险和下一步

当前限制：

- 只支持文本输入，不支持饭菜图片或体重秤截图。
- 不保存聊天消息。
- 没有登录、多用户、HTTPS 或公网部署能力。
- 复杂多轮追问和 pending-action 还没有实现。
- 当前模型规划只靠 prompt 和 schema 约束，还没有系统化 eval。
- 第七阶段先接受响应较慢的体感；主要风险来自模型/中转站响应，以及 stdio MCP client 每次调用工具的初始化开销。

下一步：

- 为 Agent planning 建立 eval case：用户输入、期望工具序列、期望关键参数。
- 增强澄清流程：餐别缺失不追问，默认 `other`；数量、份量、做法等会显著影响估算的信息缺失时，再生成 pending action。
- 引入图片识别/OCR 前，先定义图片分析结果如何转成现有 `record_meal` 或体重记录 schema。
- 评估 MCP client session 复用、减少工具调用次数和流式响应，降低 Web Chat 响应延迟。
- 设计真正的 memory：从用户目标、偏好、过敏/忌口、常吃食物中提炼长期可复用信息。
