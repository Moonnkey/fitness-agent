# 第七阶段用户使用手册：Web Chat 最小闭环

## 这一阶段新增了什么

第七阶段新增了一个本地局域网可访问的 Web Chat 形态。

现在你可以在电脑上启动 Web 服务，然后用手机浏览器访问一个极简聊天页面，通过文字和饮食记录助手对话。

新增能力：

- 启动本地 Web Chat 服务。
- 手机在同一局域网访问聊天页面。
- 输入文字消息。
- 后端轻量 Agent 解析消息。
- 轻量 Agent 通过 MCP client 调用已有 `fitness-agent` MCP tools。
- 返回文字回复。
- 查询今日 summary。

新增入口：

```bash
uv run fitness-agent-web
```

新增 HTTP 接口：

- `GET /`
- `GET /api/health`
- `POST /api/chat`
- `GET /api/summary/today`
- `GET /api/weekly-summary`

## 启动方式

安装依赖：

```bash
uv sync --extra dev --extra mcp
```

真实 OpenAI 模式需要配置：

```bash
export OPENAI_API_KEY="你的 OpenAI API key"
export FITNESS_AGENT_MODEL="gpt-4.1-mini"
```

如果使用 OpenAI-compatible 中转站，配置中转站 key、base URL 和该中转站实际支持的模型名：

```bash
export OPENAI_API_KEY="你的中转站 key"
export OPENAI_BASE_URL="https://中转站域名/v1"
export FITNESS_AGENT_MODEL="中转站支持的模型名"
```

可以先用模型列表接口确认模型名：

```bash
curl --noproxy '*' "$OPENAI_BASE_URL/models" \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

启动服务：

```bash
uv run fitness-agent-web
```

默认监听：

```text
0.0.0.0:8000
```

电脑本机访问：

```text
http://127.0.0.1:8000
```

手机访问：

```text
http://电脑局域网IP:8000
```

例如电脑局域网 IP 是 `192.168.1.20`，手机访问：

```text
http://192.168.1.20:8000
```

## 开发和测试模式

第七阶段没有 `RuleBasedModelClient`。

只有两个 model client：

- `OpenAIModelClient`：真实业务使用。
- `FakeModelClient`：测试/开发替身，不理解输入，只返回预设 intent。

真实模式下如果没有 `OPENAI_API_KEY`，聊天接口会返回清晰错误，不会用规则分支猜测用户意图。

显式 fake 模式：

```bash
export FITNESS_AGENT_AGENT_MODE=fake
uv run fitness-agent-web
```

fake 模式主要用于确认页面和 HTTP 服务能启动，不代表真实饮食识别能力。

## 手机聊天怎么用

打开页面后，可以输入：

```text
早餐吃了两个鸡蛋和一杯无糖豆浆
```

真实 OpenAI 模式下，期望流程是：

```text
1. 后端调用 OpenAIModelClient 解析消息。
2. Agent 计划调用 check_duplicate_meal。
3. 没有疑似重复时调用 record_meal。
4. 调用 get_daily_summary。
5. 返回“已记录 + 今日累计”。
```

还可以问：

```text
今天目前吃了多少热量？
```

```text
我最近 7 天执行得怎么样？
```

```text
我今天晚餐应该怎么安排？
```

## 餐别缺失怎么处理

第七阶段采用低摩擦记录原则。

如果用户说：

```text
我吃了两个鸡蛋
```

即使没有说明这是早餐、午餐、晚餐还是加餐，也应该直接记录。系统会默认：

```text
date = today
meal_type = other
```

餐别只是辅助分类，不影响当天总热量、蛋白质、碳水和脂肪汇总。

只有缺失信息会明显影响热量或三大营养素估算时，才应该追问。例如：

```text
我吃了一碗面
```

这种情况里，面条种类、份量、汤底、浇头和油量都可能让热量差异很大，可以追问一句：

```text
这碗面大概是什么类型、份量多大？比如清汤面、牛肉面、拌面，或者有没有明显加油。
```

## 当前可以做什么

Web Chat MVP 当前可以：

- 打开极简聊天页面。
- 发送文字消息。
- 接收后端回复。
- 通过 `/api/chat` 走轻量 Agent。
- 通过 MCP client 调用已有 MCP tools。
- 通过页面右上角“今日”按钮查询今日 summary。

## 响应时间说明

第七阶段优先验证功能闭环，不优先优化响应时间。

一次完整饮食记录通常会经过：

```text
浏览器
-> FastAPI
-> OpenAIModelClient / 中转站 / 模型
-> ChatService
-> MCP stdio client
-> check_duplicate_meal
-> record_meal
-> get_daily_summary
-> 返回前端
```

所以当前体感慢是预期内风险，主要可能来自：

- 模型或中转站响应慢。
- 一次记录需要多个 tool call。
- stdio MCP client 当前每次工具调用都有会话初始化开销。

当前阶段先接受这个性能取舍，继续优先完善功能。后续优化方向包括：

- 复用 MCP session，减少 stdio 初始化开销。
- 减少不必要的 tool call。
- 为 Agent planning 建 eval，降低失败和重试概率。
- 增加流式响应，先让用户看到“正在记录”。

## 当前还不能做什么

这一阶段仍然不能做：

- 图片上传。
- 饭菜图片识别。
- 体重秤截图识别。
- 保存聊天记录。
- 登录和多用户。
- 公网部署。
- 漂亮报表和趋势图。
- 复杂 pending-action 多轮状态机。
- 离线自然语言理解。

## 容易出问题的地方

### 1. 没有 API key

没有 `OPENAI_API_KEY` 时，真实模式不能理解用户消息。系统会返回模型配置错误。

### 2. 中转站模型名不匹配

如果中转站返回 `model_not_found`，说明 `FITNESS_AGENT_MODEL` 不是这个中转站支持的模型名。先查询：

```bash
curl --noproxy '*' "$OPENAI_BASE_URL/models" \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

然后把 `FITNESS_AGENT_MODEL` 设置成返回列表里的 `id`。

### 3. SOCKS 代理缺依赖

如果看到：

```text
Using SOCKS proxy, but the 'socksio' package is not installed
```

说明当前 shell 配置了 SOCKS 代理，例如 `all_proxy=socks5://127.0.0.1:7890`，但环境依赖没同步。运行：

```bash
uv sync --extra dev --extra mcp
```

然后重启 `fitness-agent-web`。

### 4. MCP server 启动失败

Web Chat 通过 MCP client 调用 `fitness-agent-mcp`。如果 MCP server 无法启动，聊天操作会失败。

常见检查：

```bash
uv run fitness-agent-mcp
```

### 5. 手机访问不到电脑

确认：

- 手机和电脑在同一局域网。
- 服务监听 `0.0.0.0:8000`。
- 使用电脑局域网 IP，而不是 `127.0.0.1`。
- 防火墙没有拦截 8000 端口。

### 6. 不能直接暴露公网

第七阶段没有登录和 HTTPS，不适合把端口直接暴露到公网。

## 推荐使用方式

当前最推荐的本地验证流程：

```bash
uv run fitness-agent dev reset-db --yes
uv run fitness-agent profile set --height-cm 180 --weight-kg 80 --age 30 --sex male --activity-level moderate --goal-type fat_loss
export OPENAI_API_KEY="你的 OpenAI API key"
uv run fitness-agent-web
```

然后打开：

```text
http://127.0.0.1:8000
```

或用手机打开：

```text
http://电脑局域网IP:8000
```
