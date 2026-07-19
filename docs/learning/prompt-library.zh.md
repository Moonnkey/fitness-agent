# AI Agent 学习与秋招提示词库

这个文档保存本项目常用提示词。使用方式很简单：根据场景复制对应模板，发给负责开发的 Codex session，或者发给负责复盘和面试训练的 session。

## 使用建议

- 开发类提示词发给负责写代码的 Codex session。
- 复盘、讲解、面试训练类提示词发给负责学习辅导的 Codex session。
- 每次开发完成后，优先让开发 session 把变更沉淀到 `docs/learning/stage-retrospectives/`，再让学习 session 基于文档和代码做训练。
- 不要在复盘中记录真实健康数据、API key、数据库文件、私人联系方式或其他敏感信息。

## 让开发 Session 写入长期规则

适用场景：第一次建立“开发后自动复盘”的项目规则时使用。

```text
请修改本仓库的 AGENTS.md，在保持现有项目规则不变的前提下，新增一个“Learning And Interview Retrospective Rules”章节。

目标：
我正在用这个健康减脂助手项目学习 AI Agent / Harness 工程，并准备秋招找 AI Agent 开发相关工作。之后每完成一个非平凡开发阶段，都需要把本次工程实践沉淀成学习材料和面试材料。

请加入以下规则：

1. 每完成一个非平凡开发阶段后，更新或新增一篇复盘文档：
   docs/learning/stage-retrospectives/YYYY-MM-DD-<short-topic>.md

2. 复盘文档必须包含：
   - 本次实现了什么功能
   - 涉及哪些核心模块、CLI、MCP、schema、service、model 或 docs
   - 本次设计决策是什么，为什么这样设计
   - 这次工作对应哪些 AI Agent / Harness 工程概念
   - 如何用秋招面试语言讲这个项目
   - 面试官可能追问的问题和推荐回答
   - 当前限制、风险和下一步

3. 复盘时要结合 learn-claude-code 这套教程的思想，尤其是：
   - Agent 产品 = 模型 + Harness
   - Harness 包括 Tools、Knowledge、Observation、Action Interfaces、Permissions
   - Agent loop、tool use、permission、skill loading、memory、context management、MCP、multi-agent、task system 等概念
   - 不要机械照搬教程，要结合本项目的健康减脂助手场景解释

4. 本项目的对应关系可以这样理解：
   - app/core/services 是稳定业务能力
   - CLI、MCP、未来移动端 API 是 action interface / tool surface
   - SQLite 数据库是业务事实和用户记录的持久化存储，不等同于 Agent memory；当 Agent 通过 core services 查询并注入当前上下文时，这些数据才成为 observation 的来源；经过提炼并在后续对话中长期复用的目标、偏好、习惯和约束才更接近 Agent memory
   - docs、stage guides、schema 说明是 knowledge
   - 健康安全规则、隐私规则、审批边界是 permissions / safety boundary
   - 未来独立 Agent 层负责意图理解、计划、追问、工具调用和结果解释

5. 不要为了写复盘而影响小修小补的效率。只有功能开发、架构调整、接口变化、数据模型变化、Agent/MCP/CLI 能力变化时才需要写阶段复盘。

6. 复盘中不要记录真实个人健康数据、API key、数据库文件路径中的隐私信息或任何敏感信息。

同时请创建 docs/learning/README.md，简要说明这个目录用于沉淀 AI Agent 工程学习、项目复盘和秋招面试材料。
```

## 每次开发任务后的复盘要求

适用场景：给开发 session 派发具体开发任务时，把这段追加在任务末尾。

```text
开发完成后，请按 AGENTS.md 中的 Learning And Interview Retrospective Rules 更新本阶段复盘文档。

复盘重点：
1. 本次功能在健康减脂助手整体架构中的位置
2. 本次变更涉及的 core service、schema、model、CLI、MCP 或 docs
3. 本次设计如何支撑未来独立 Agent 层
4. 本次实践对应哪些 AI Agent / Harness 工程概念
5. 秋招面试时我应该如何讲这个功能
6. 面试官可能追问什么，以及推荐回答
```

## 请求学习 Session 做秋招训练

适用场景：开发 session 已经完成代码和复盘后，把这段发给学习 session。

```text
请阅读最近一次 docs/learning/stage-retrospectives/ 复盘和相关代码，结合 learn-claude-code 教程，给我做一次 AI Agent 秋招训练。

重点讲：
1. 本次开发对应哪些 Harness 工程概念
2. 这个功能在我的健康减脂助手 Agent 架构中处于什么位置
3. 它和 tool calling、MCP、memory、context management、permissions、evaluation 的关系
4. 面试官可能怎么追问
5. 我应该如何回答，给出可以直接背诵但不僵硬的回答模板
6. 下一阶段我应该学习和补强什么
```

## 请求学习 Session 做项目讲述稿

适用场景：准备简历、面试自我介绍、项目介绍时使用。

```text
请基于当前 fitness-agent 项目，帮我整理一版 AI Agent 方向秋招项目讲述稿。

要求：
1. 用 1 分钟、3 分钟、5 分钟三个版本分别讲
2. 突出我是如何从 CLI/MCP 工具层演进到独立 Agent 架构的
3. 突出 app/core 业务服务复用、SQLite 本地优先、MCP 工具暴露、未来移动端 API 的架构思路
4. 解释为什么不能把业务规则全部写进 prompt
5. 给出面试官可能追问的问题和回答
6. 指出当前项目短板，以及我应该如何诚实但有工程判断地回答
```

## 请求学习 Session 对比 Agent 框架

适用场景：你想学习 LangGraph、OpenAI Agents SDK、Claude Code、AutoGen、CrewAI 等框架和项目的关系时使用。

```text
请结合我的 fitness-agent 项目，讲解 LangGraph、OpenAI Agents SDK、Claude Code / learn-claude-code 中的 Harness 思想、MCP、AutoGen、CrewAI 这些 Agent 开发方式的差异。

请不要泛泛介绍框架。请围绕我的项目回答：
1. 如果我现在要做独立 Agent 层，哪些部分适合自己写，哪些部分适合交给框架
2. 我的 app/core/services、CLI、MCP、SQLite、未来移动端 API 分别对应 Agent 架构中的什么组件
3. LangGraph 适合解决我项目中的什么问题，不适合解决什么问题
4. MCP 在这里是工具协议、集成层还是 Agent 框架
5. 秋招面试时如何讲清楚“我理解 Agent 不是只有 prompt，而是模型加 Harness”
```

## 请求开发 Session 做某阶段架构设计

适用场景：开始一个较大功能前使用，比如独立 Agent 层、移动端 API、memory、RAG、evaluation。

```text
请先不要直接写代码。请基于当前仓库代码和 AGENTS.md，给出这个阶段的实现计划。

阶段目标：
<在这里写你的目标，例如：设计独立 Agent 层，让它能理解用户自然语言、调用已有 core services、必要时追问，并为未来手机端 API 复用。>

要求：
1. 先阅读相关代码和文档
2. 说明本阶段应该修改哪些模块
3. 说明哪些逻辑应该放在 app/core，哪些应该放在 Agent 编排层，哪些属于 CLI/MCP/API 适配层
4. 给出数据流和调用链
5. 给出测试策略
6. 指出风险、限制和不应该做的事情
7. 最后给出一个小步可执行的开发计划
```

## 请求开发 Session 实现功能

适用场景：计划已经明确后，让开发 session 真正改代码。

```text
请按刚才的计划实现这个阶段的功能。

要求：
1. 遵守 AGENTS.md 中的项目规则
2. 保持 app/core 作为业务逻辑中心，CLI/MCP/API 只做薄适配
3. 不要引入不必要的新框架
4. 为核心服务补充或更新 pytest
5. 如果改变用户可见行为，请手动测试至少一个 CLI 命令
6. 如果改变 MCP 工具，请验证 MCP server 能启动，且相关工具可以被检查或调用
7. 开发完成后，更新相关 docs 和 docs/learning/stage-retrospectives/ 复盘
8. 最后总结修改文件、测试结果、未解决问题
```

## 请求代码审查

适用场景：开发 session 改完后，你想让另一个 session 帮你找问题。

```text
请以代码审查的方式检查最近一次变更。

重点关注：
1. 是否违反 AGENTS.md 中的架构规则
2. 是否把业务逻辑泄漏到了 CLI、MCP 或未来 API 适配层
3. 是否存在重复的 calorie、nutrition、goal 或 summary 逻辑
4. Pydantic schema、SQLAlchemy/SQLModel model、service 之间边界是否清楚
5. 测试是否覆盖核心行为和失败场景
6. 是否有隐私、健康安全或极端减脂建议风险
7. 这些变更在未来独立 Agent 层中是否容易被工具调用

请先列出问题，按严重程度排序，带上文件和行号；如果没有明显问题，也请说明剩余风险和测试缺口。
```

## 请求面试追问训练

适用场景：你想围绕某个已实现功能做模拟面试。

```text
请围绕最近一次开发内容，模拟 AI Agent 开发岗位面试。

流程：
1. 先问我 5 个由浅入深的问题
2. 等我回答后，逐题点评
3. 指出我的回答哪里不够工程化
4. 给出更好的回答版本
5. 把相关知识点映射到我的 fitness-agent 项目

题目请覆盖：
- Agent 和普通聊天机器人的区别
- tool calling / MCP / action interface
- memory / observation / context management
- 为什么要有 app/core 服务层
- 如何做 Agent 行为测试和安全边界
```

## 请求阶段学习路线

适用场景：你想知道下一阶段该学什么、做什么。

```text
请基于当前 fitness-agent 项目的状态，为我制定下一阶段 AI Agent 开发学习路线。

要求：
1. 路线必须和项目开发绑定，不要只列课程名
2. 每个学习点都要对应一个可以落地到项目里的功能或测试
3. 覆盖 tool calling、MCP、memory、context management、planning、evaluation、safety、mobile API
4. 标出哪些内容适合秋招前优先掌握，哪些可以以后再深入
5. 给出 2 周版本和 6 周版本两个计划
```
