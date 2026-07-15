# Agent Learning

这是一个用于学习智能体开发的科研文献 Agent 应用 Demo。

项目目标是让 Agent 能够读取 TXT、Word 和 PDF 资料，建立本地知识库，根据用户问题进行检索和分析，生成带引用来源的研究回答，并通过 FastAPI 和 Streamlit 提供可交互的应用界面。

## 当前定位

当前项目已经是一个具备 Agent 特征的科研文献应用 Demo，但还不是生产级智能体平台。

当前主流程如下：

```text
用户问题
    -> FastAPI
    -> LangGraph Research Workflow
    -> Planner
    -> PlanValidator
    -> QueryRewriter
    -> Retriever
    -> Reader
    -> Reviewer
    -> Writer
    -> 返回回答、引用来源和 Markdown 报告
```

## 已实现功能

### 模型与提示词

- 使用 DeepSeek API 调用大语言模型
- 普通文本摘要
- 结构化 JSON 输出
- 多种 Prompt 风格
- Pydantic 结果校验
- 规则评测和语义 RAG 评测

### Agent 工程能力

- 本地工具调用
- 工具注册表
- 多轮工具调用
- Planner 任务计划
- PlanValidator 计划校验
- LangGraph StateGraph 工作流
- Reader、Reviewer、Writer 等角色节点
- 条件路由和 Reviewer 循环
- `current_step`、`completed_steps` 和执行轨迹

### RAG 知识库

- TXT、DOCX、PDF 文档解析
- chunk 切分
- embedding 向量化
- Chroma 本地向量数据库
- 语义检索
- 可选 reranker
- 返回 `chunk_id`、来源文件和文本位置
- 文档上传、列表和删除

### 记忆与应用接口

- Streamlit 页面短期对话
- JSONL 长期记忆 Demo
- SQLite 会话和消息持久化
- 页面刷新后恢复历史会话
- FastAPI 研究接口
- Markdown 报告下载接口
- API 请求日志和统一异常处理
- FastAPI 接口测试

## 当前架构

```text
Streamlit 前端
    -> FastAPI API
        -> LangGraph 工作流
            -> Planner / Retriever / Reader / Reviewer / Writer
                -> 本地工具
                -> Chroma 向量数据库
                -> DeepSeek API
                -> SQLite 会话数据库
```

## 环境准备

创建并激活虚拟环境：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

安装依赖：

```powershell
pip install -r requirements.txt
```

创建环境变量文件：

```powershell
Copy-Item .env.example .env
```

在 `.env` 中填写模型配置：

```text
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_MODEL=deepseek-chat
DEEPSEEK_API_BASE=https://api.deepseek.com
```

## 常用命令

### 文本摘要

```powershell
python -m src.main examples\sample.txt
```

结构化摘要：

```powershell
python -m src.main examples\agent_complex.txt --structured
```

指定 Prompt 风格：

```powershell
python -m src.main examples\agent_complex.txt --structured --style research
```

### 工具调用

```powershell
python -m src.demos.tool_registry_demo
python -m src.demos.model_tool_call_demo
```

### RAG

建立向量索引：

```powershell
python -m src.demos.build_rag_index --file examples\agent_rag_notes.txt
```

查看知识库来源：

```powershell
python -m src.demos.list_rag_sources
```

运行语义检索：

```powershell
python -m src.demos.semantic_rag_demo `
    "FastAPI 在这个项目里有什么作用？" `
    --file examples\agent_rag_notes.txt
```

### LangGraph 研究工作流

```powershell
python -m src.demos.langgraph_research_demo `
    "FastAPI 在这个项目里有什么作用？"
```

查看最终状态和执行轨迹：

```powershell
Get-Content -Encoding UTF8 outputs\langgraph_final_state.json
```

查看 Graph 结构：

```powershell
Get-Content -Encoding UTF8 outputs\langgraph_workflow.mmd
```

### 评测

```powershell
python -m pytest tests -ra
python -m src.rag.semantic_rag_batch_eval
```

## 启动应用

启动 FastAPI：

```powershell
python -m uvicorn src.api.app:app --reload
```

启动 Streamlit：

```powershell
python -m streamlit run frontend\streamlit_app.py
```

浏览器访问：

```text
http://localhost:8501
```

## 主要 API

```text
GET  /health
POST /documents/upload
GET  /documents
DELETE /documents/{filename}
POST /research
GET  /reports/{filename}
GET  /sessions/{session_id}/messages
```

示例：

```powershell
$body = @{
    question = "FastAPI 在这个项目里有什么作用？"
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri http://127.0.0.1:8000/research `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

## 数据目录

```text
data/uploads/       上传的 TXT、DOCX、PDF 文件
data/chroma/        Chroma 向量数据库
data/agent.db       SQLite 会话和消息数据库
outputs/             报告、评测结果和运行轨迹
```

这些运行时数据默认不提交到 Git。

## 项目结构

```text
agent_learning/
├── examples/                  示例资料
├── frontend/
│   └── streamlit_app.py       Streamlit 前端
├── prompts/                   Prompt 文档
├── src/
│   ├── agents/                Agent 角色和状态
│   ├── api/                   FastAPI 接口
│   ├── clients/               大模型客户端
│   ├── core/                  摘要和评测核心逻辑
│   ├── demos/                 命令行 Demo
│   ├── ingestion/             TXT、Word、PDF 解析
│   ├── memory/                长期记忆 Demo
│   ├── rag/                   切分、embedding、检索和向量库
│   ├── storage/               SQLite 存储
│   ├── tools/                 本地工具和工具注册表
│   └── workflows/             LangGraph 工作流
├── tests/                     自动化测试
├── requirements.txt
└── README.md
```

## 后续计划

```text
1. 文档元数据和知识库筛选
2. Planner 动态选择不同工作流分支
3. MCP 外部工具接入
4. Skill 能力模块封装
5. 评测、日志、权限和安全完善
6. 最后再考虑 Docker 部署
```

当前项目的学习重点是理解完整 Agent 应用的工程流程：

```text
需求
    -> 模块设计
    -> 工具和工作流实现
    -> RAG 和记忆
    -> API 和前端
    -> 测试与评测
    -> Git 版本管理
```
