# Research Agent

[![CI](https://github.com/Colorful96/agent-learning/actions/workflows/ci.yml/badge.svg)](https://github.com/Colorful96/agent-learning/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

一个面向科研文献问答的 Agent 应用示例。

项目支持导入 TXT、Word 和 PDF，建立本地知识库，根据问题选择直接回答或检索式研究流程，返回带引用来源的答案，并生成 Markdown 报告。项目同时展示了 LangGraph、RAG、工具调用、MCP、Skill、FastAPI、Streamlit 和 SQLite 的工程化组合方式。

> This repository is an educational but runnable research-agent application. It is designed to make the architecture understandable and easy to extend.

## Features

- 文档导入：支持 TXT、DOCX 和 PDF
- RAG：文本切分、Embedding、Chroma、混合检索和可选重排
- 动态路由：Planner 在 direct_answer 和 research 之间选择
- 研究工作流：Planner -> Validator -> Query Rewriter -> Retriever -> Reader -> Reviewer -> Writer
- 工具系统：本地工具注册表，可选 MCP 后端
- Skill：literature_research 和 direct_qa
- 记忆：SQLite 会话和消息持久化，以及 JSONL 长期记忆示例
- 接口：FastAPI API 和 Streamlit 页面
- 工程能力：请求 ID、日志、API Token、路径校验、评测和测试
- 部署配置：Dockerfile 和 Docker Compose

## Architecture

~~~mermaid
flowchart LR
    User[User] --> UI[Streamlit]
    UI --> API[FastAPI]
    API --> Graph[LangGraph]
    Graph --> Planner[Planner]
    Planner --> Route{Workflow type}
    Route -->|direct_answer| Direct[Direct QA Skill]
    Route -->|research| Research[Literature Research Skill]
    Research --> Retriever[Retriever]
    Retriever --> Vector[(Chroma)]
    Research --> Reader[Reader]
    Reader --> Reviewer[Reviewer]
    Reviewer --> Writer[Writer]
    Writer --> Report[Markdown report]
    Graph --> Tools[Local tools / MCP tools]
    API --> SQLite[(SQLite)]
~~~

## Quick Start

### 1. 创建虚拟环境

~~~powershell
python -m venv .venv
.venv/Scripts/Activate.ps1
pip install -r requirements.txt
~~~

### 2. 配置模型

~~~powershell
Copy-Item .env.example .env
~~~

编辑 .env：

~~~text
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_API_BASE=https://api.deepseek.com
AGENT_API_TOKEN=
AGENT_TOOL_BACKEND=local
~~~

不要提交 .env，也不要在公开环境中暴露 API Key。

### 3. 启动应用

终端 1：

~~~powershell
python -m uvicorn src.api.app:app --reload
~~~

终端 2：

~~~powershell
python -m streamlit run frontend/streamlit_app.py
~~~

打开 http://localhost:8501。

## CLI Examples

建立索引：

~~~powershell
python -m src.demos.build_rag_index --file examples/agent_rag_notes.txt
~~~

运行语义检索：

~~~powershell
python -m src.demos.semantic_rag_demo "FastAPI 在这个项目里有什么作用？" --file examples/agent_rag_notes.txt
~~~

运行 LangGraph 研究工作流：

~~~powershell
python -m src.demos.langgraph_research_demo "FastAPI 在这个项目里有什么作用？"
~~~

查看工作流状态和图：

~~~powershell
Get-Content -Encoding UTF8 outputs/langgraph_final_state.json
Get-Content -Encoding UTF8 outputs/langgraph_workflow.mmd
~~~

运行 MCP 发现示例：

~~~powershell
python -m src.demos.mcp_demo
~~~

使用 MCP 作为工具后端：

~~~powershell
$env:AGENT_TOOL_BACKEND="mcp"
python -m src.demos.tool_registry_demo
Remove-Item Env:AGENT_TOOL_BACKEND
~~~

## API

| Method | Endpoint | Purpose |
|---|---|---|
| GET | /health | 健康检查 |
| POST | /documents/upload | 上传并索引 TXT/DOCX/PDF |
| GET | /documents | 查看已上传文档和元数据 |
| DELETE | /documents/{filename} | 删除文档及其切片 |
| POST | /research | 运行研究 Agent |
| GET | /reports/{filename} | 下载 Markdown 报告 |
| GET | /sessions/{session_id}/messages | 恢复会话历史 |

POST /research 支持可选的 source 字段，用于限制检索范围：

~~~json
{
  "question": "FastAPI 在这个项目里有什么作用？",
  "source": "data/uploads/agent_rag_notes.txt"
}
~~~

配置 AGENT_API_TOKEN 后，受保护接口需要携带 X-API-Key。

## Repository Layout

~~~text
agent-learning/
|-- frontend/                 Streamlit 页面
|-- src/
|   |-- agents/               Planner、角色节点和图状态
|   |-- api/                  FastAPI 路由和中间件
|   |-- clients/              LLM 客户端
|   |-- core/                 摘要和结构化输出逻辑
|   |-- demos/                可运行的学习示例和集成示例
|   |-- evaluation/           工作流评测
|   |-- ingestion/            TXT/DOCX/PDF 加载和索引
|   |-- integrations/         MCP Server 和 Client
|   |-- memory/               JSONL 记忆示例
|   |-- rag/                  切分、Embedding、检索和提示词组装
|   |-- skills/               可复用 Agent 能力
|   |-- storage/              SQLite 持久化
|   |-- tools/                本地工具和注册表
|   |-- workflows/            LangGraph 工作流
|-- docs/                     架构和学习笔记
|-- examples/                 示例资料
|-- tests/                    自动化测试
|-- Dockerfile
|-- docker-compose.yml
+-- README.md
~~~

正式运行链路不依赖 demo 模块。运行时共用的 RAG 提示词组装逻辑位于 src/rag/prompt_builder.py；src/demos/ 中的文件是可执行示例和实验入口。

## Data and Security

运行时数据会被 Git 忽略：

~~~text
data/uploads/       上传的文档
data/chroma/        Chroma 数据库
data/agent.db       SQLite 会话和消息
outputs/            报告、轨迹、日志和评测结果
~~~

本地工具将文件读取限制在 examples/ 和 data/uploads/，将报告写入限制在 outputs/。这是本地开发基线，不等同于完整的生产安全边界。

## Testing and Evaluation

~~~powershell
python -m compileall src frontend
python -m pytest tests -ra
python -m src.evaluation.workflow_evaluator
~~~

测试覆盖 API 校验、会话持久化、source 转发、动态路由、Skill 选择、路径安全和 API Token 保护。

## Docker

Docker 配置不是本地开发的必需项：

~~~powershell
docker compose up --build
~~~

API 暴露在 8000 端口，Streamlit 暴露在 8501 端口。首次构建可能下载较大的 Embedding 和重排模型。

## Contributing

请阅读 CONTRIBUTING.md，了解开发环境、测试要求和 Pull Request 规范。

## License

项目采用 MIT License。
