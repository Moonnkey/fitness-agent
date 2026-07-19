# Web Chat MVP 设计方案

## 目标

第七阶段目标是做出一个本地局域网可访问的手机聊天版饮食记录助手。

用户可以在手机浏览器打开一个极简聊天页面，用自然语言和饮食记录机器人对话。后端轻量 Agent 调用大模型理解用户意图，再通过 MCP client 调用现有 `fitness-agent` MCP tools，最终由现有 core services 写入 SQLite 或查询总结。

第一版重点跑通文字聊天闭环，不做图片识别、不做公网部署、不做多用户登录。

## 产品形态

当前项目保留两种形态：

```text
Agent 外挂版
  Codex / 其他 Agent
    -> fitness-agent Skill
    -> fitness-agent MCP tools
    -> core services
    -> SQLite

Web Chat 版
  手机浏览器
    -> FastAPI Web Chat
    -> 轻量 Agent
    -> MCP client
    -> fitness-agent MCP tools
    -> core services
    -> SQLite
```

Agent 外挂版不动。Web Chat 版是新增产品形态。

## 为什么 Web Chat 后端也走 MCP

本项目已经有三层：

```text
core services：真正业务逻辑
MCP tools：Agent 调用 core services 的标准接口
Skill：告诉 Agent 什么时候、怎么调用 MCP tools
```

第七阶段选择让 Web Chat 后端通过 MCP client 调用 MCP tools，而不是直接调用 core services。

原因：

- 与 Codex/其他 Agent 的调用方式保持一致。
- 后续替换轻量 Agent 或接入其他 Agent 框架时，工具边界稳定。
- MCP 成为所有 Agent 的统一工具接口。
- core services 仍然是唯一业务逻辑来源，避免重复实现。

代价：

- 比直接调用 core services 多一层 MCP client/server。
- 本地启动和测试链路更复杂。

这个代价可以接受，因为项目目标之一是把 fitness-agent 做成可被各种 Agent 使用的工具能力。

## 轻量 Agent 是什么

轻量 Agent 不是重新实现 Codex，也不是通用编程 Agent。

它只负责：

```text
1. 接收用户聊天消息。
2. 调用大模型理解用户意图。
3. 让模型输出结构化 JSON。
4. 校验 JSON。
5. 通过 MCP client 调用对应 tool。
6. 把工具结果整理成中文回复。
```

它不负责：

- 直接写数据库。
- 自己计算 summary。
- 自己实现热量统计。
- 自己保存 meal、weight、activity。
- 替代 MCP tools 或 core services。

## 第七阶段支持的聊天意图

第一版支持：

- 记录饮食。
- 查询今日总结。
- 查询最近 7 天周报。
- 查询今天后续饮食建议。
- 在用户明确指出记录或 id 时，修改记录。
- 在用户明确指出记录或 id 时，删除记录。

第一版不支持：

- 图片上传和识别。
- 体重秤截图识别。
- 复杂长期聊天记忆。
- 登录和多用户。
- 公网部署。
- 自动生成精确菜单。
- 复杂多轮任务状态机。

## 什么是复杂多轮追问

复杂多轮追问指后端需要长期保存一个未完成任务状态，例如：

```text
用户：早餐吃了两个鸡蛋。
Agent：可能重复了，要保存吗？
用户：保存。
Agent：继续执行刚才那个未完成的 record_meal。
```

或者：

```text
用户：把刚才那条改了。
Agent：你是指早餐 A 还是早餐 B？
用户：第二条。
Agent：继续执行 update_record。
```

第七阶段不做完整 pending-action 状态机。

MVP 规则：

- 如果用户指令明确，直接执行。
- 如果候选不唯一或风险较高，返回候选和提示，让用户下一条消息说清楚。
- 下一条消息需要用户明确给出记录 id 或明确描述，再执行。

这样实现简单，也避免误改、误删。

## 记录饮食是否自动保存

第七阶段采用：

```text
默认自动保存。
不确定时追问。
```

例如用户说：

```text
早餐吃了两个鸡蛋和一杯无糖豆浆。
```

Agent 应：

```text
1. 估算热量和三大营养素。
2. 调用 check_duplicate_meal。
3. 如果没有疑似重复，调用 record_meal。
4. 调用 get_daily_summary。
5. 返回“已记录 + 今日累计”。
```

如果食物或份量不明确，例如：

```text
吃了一大碗面。
```

Agent 应追问或使用明确的估算假设，并把假设写入 `metadata`。

## 大模型和 FakeModelClient

第七阶段后端需要调用大模型。默认按 OpenAI API 设计。

环境变量：

```text
OPENAI_API_KEY
FITNESS_AGENT_MODEL
```

第七阶段只保留两个 model client：

- `OpenAIModelClient`：真实业务 Agent，调用 OpenAI API，把用户自然语言解析成结构化 intent。
- `FakeModelClient`：开发和测试替身，不理解用户输入，只返回预设 intent，用来跑通 Web Chat -> Agent service -> MCP -> DB -> response 全链路。

不做 `RuleBasedModelClient`。

原因：

- 规则解析会让用户感觉“好像能聊”，但实际只能识别少量固定句式，体感容易很差。
- 规则分支容易散落成临时代码，后续难维护。
- 真实产品智能应该来自 `OpenAIModelClient`。
- 当 OpenAI agent 出错时，应该返回清晰错误或要求用户重试，而不是用规则猜测。

`FakeModelClient` 只用于：

- 自动化测试不依赖外部网络。
- 开发前端和 MCP 链路时降低成本。
- 调试时把模型解析问题和 Web/MCP/DB 链路问题解耦。

生产或真实使用时应使用 `OpenAIModelClient`。

用户不需要把 API key 写进代码，也不应该提交到 Git。

如果没有配置 `OPENAI_API_KEY`，真实模式应返回清晰错误。只有显式设置测试/开发模式时，才可以启用 `FakeModelClient`。

## 后端 API

第七阶段计划新增 FastAPI 后端。

初始接口：

```text
GET  /api/health
POST /api/chat
GET  /api/summary/today
GET  /api/weekly-summary
```

`POST /api/chat` 输入：

```json
{
  "message": "早餐吃了两个鸡蛋和一杯无糖豆浆"
}
```

输出：

```json
{
  "reply": "已记录早餐，估算约 224 kcal，蛋白质约 19.6 g。今天目前总摄入 224 kcal。",
  "tool_calls": [
    {
      "name": "check_duplicate_meal",
      "ok": true
    },
    {
      "name": "record_meal",
      "ok": true
    },
    {
      "name": "get_daily_summary",
      "ok": true
    }
  ]
}
```

MVP 不保存聊天消息。

## 前端

第七阶段前端保持极简：

- FastAPI 直接提供静态 HTML/CSS/JS。
- 不引入 React/Vue。
- 手机浏览器优先。
- 一个聊天消息列表。
- 一个输入框。
- 一个发送按钮。
- 显示后端返回的文字回复。

暂不做：

- 精美报表。
- 图表。
- 图片上传。
- 用户登录。
- 聊天历史持久化。

## 局域网访问

本地运行时监听：

```text
0.0.0.0:8000
```

手机访问：

```text
http://电脑局域网IP:8000
```

第七阶段不做登录。默认前提是只在可信局域网内使用。

风险：

- 同一局域网内其他人如果知道地址，也可能访问。
- 不适合直接暴露到公网。

后续公网部署前必须补：

- 登录或访问密码。
- HTTPS。
- 数据备份策略。
- 更明确的隐私策略。

## 图片能力放到第八阶段

第七阶段不做图片。

第八阶段再考虑：

- 饭菜图片识别。
- 体重秤截图 OCR。
- 上传文件接口。
- 图片临时处理。
- 不长期保存原图。
- 识别不确定时让用户确认。

## 验收标准

第七阶段完成时应满足：

```text
1. 可以启动 FastAPI Web Chat 服务。
2. 手机在同一局域网能打开聊天页面。
3. 用户输入文字饮食记录后，后端通过轻量 Agent 调 MCP tools 保存 meal。
4. 保存后返回今日 summary。
5. 用户可以问今日总结、周报、日内建议。
6. 明确的修改/删除指令可以通过 MCP tools 执行。
7. 不保存聊天消息。
8. 没有 API key 时真实模式返回清晰错误；测试/开发模式可显式启用 FakeModelClient。
9. 完整测试、lint 和至少一个 CLI 或 HTTP smoke test 通过。
```
