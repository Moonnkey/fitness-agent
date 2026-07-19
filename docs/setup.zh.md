# 本地开发准备

## 当前选择

项目主体使用 Python。MVP 阶段优先做：

```text
Python core services
SQLite
CLI
pytest
MCP server
Skill
FastAPI Web Chat
```

RAG、embedding 和数据分析也会优先留在 Python 侧。

## 推荐环境

- Python 3.11 或 3.12。
- Git。
- `uv` 作为 Python 包管理和虚拟环境工具。
- VS Code、Cursor 或其他编辑器。

当前项目配置要求 Python `>=3.11`。如果本机只有 Python 3.9，需要先安装新版 Python。

## 建议安装命令

macOS 可以用 Homebrew：

```bash
brew install python@3.12 uv
```

安装后检查：

```bash
python3.12 --version
uv --version
```

## 初始化依赖

安装好 `uv` 后，在项目目录运行：

```bash
uv sync --extra dev --extra mcp
```

后续运行测试：

```bash
uv run pytest
```

## Web Chat 本地启动

真实聊天模式需要 OpenAI API key：

```bash
export OPENAI_API_KEY="你的 OpenAI API key"
export FITNESS_AGENT_MODEL="gpt-4.1-mini"
```

启动 Web Chat：

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

第七阶段没有登录和 HTTPS，只适合可信本地局域网测试，不要直接暴露到公网。

## 远端仓库

本地 Git 可以先初始化。远端 GitHub 仓库可以稍后再建。

建议等以下内容完成后再创建远端仓库：

```text
1. 项目骨架
2. AGENTS.md
3. MVP 文档
4. Python 配置
5. 第一版可运行 CLI
```

如果现在就想创建远端仓库，也可以。仓库名建议：

```text
fitness-agent
```
