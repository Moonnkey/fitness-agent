# Fitness Agent 项目规则中文版

## 目标

构建一个本地优先的 AI 健身减脂助手。MVP 阶段通过 Python CLI 和 MCP tools 记录饮食、体重、简单训练或活动，并输出每日热量总结。

## 当前范围

- 主体使用 Python 开发。
- MVP 使用 SQLite，本地优先。
- 先做好可靠的 core services，再增加高级 AI 能力。
- 先支持 CLI，再把相同能力暴露成 MCP tools。
- RAG 等知识库能力要等记录和总结闭环跑通后再加。

## 架构规则

- 业务逻辑放在 `app/core`。
- 数据库模型和持久化代码放在 `app/core/db` 和 `app/core/models`。
- Pydantic 输入输出 schema 放在 `app/core/schemas`。
- 饮食记录、每日总结、目标计算等复用操作放在 `app/core/services`。
- `app/cli` 里的 CLI 命令必须调用 `app/core` services。
- `app/mcp` 里的 MCP tools 必须调用 `app/core` services。
- 未来如果加 API，也必须调用 `app/core` services。
- 不要在 CLI、MCP、未来 API 里重复写热量、营养、目标或总结逻辑。
- 接口层保持薄，核心服务保持可测试。

## 默认技术栈

- Python 3.11 或更新版本。
- SQLite 作为 MVP 数据库。
- Pydantic 做外部输入输出校验。
- Typer 做 CLI。
- pytest 做测试。
- 开始做持久化后，优先考虑 SQLAlchemy 或 SQLModel。
- 开始做 MCP 后，优先考虑 Python MCP SDK 或 FastMCP。

## 产品规则

- 除非来自可靠来源，否则热量、宏量营养素和运动消耗都按估算处理。
- 尽量保存估算依据，比如来源、假设和置信度。
- 如果缺失信息会明显影响结果，优先问一个简短追问。
- 如果使用默认值，要在结果中说明是估算。
- 保护用户隐私。不要提交真实健康数据、数据库文件、API key 或密钥。

## 健康和安全规则

- 不做医疗诊断。
- 不把助手描述成医生、注册营养师或物理治疗师。
- 不推荐极端热量限制、脱水、催吐或危险快速减重。
- 遇到不安全目标、症状、受伤信号或进食障碍风险时，要提示用户寻求专业帮助。
- 健身和营养建议应表达为一般性教练建议，而不是医疗建议。

## MVP 边界

- 在本地 MVP 闭环跑通前，不加 Web UI、移动 App、多用户认证、云同步、支付、模型微调或插件打包。
- 在饮食、体重、活动、总结、CLI、MCP 基础能力跑通前，不加完整 RAG。
- 除非有明确集成边界需要，不引入 TypeScript。

## 验证要求

完成代码改动前：

- 运行相关测试。
- 如果配置了类型检查或 lint，运行对应检查。
- 对用户可见行为，至少手动测试一个 CLI 命令。
- 对 MCP 改动，确认 MCP server 能启动，并且变更的 tool 能被调用或检查。

## 文档规则

- 范围变化时同步更新 `docs/mvp.md` 和 `docs/mvp.zh.md`。
- 影响架构或产品行为的决策，写简短设计说明到 `docs/`。
- 避免写很长的空泛文档，优先记录具体决策、schema、工作流和示例。
