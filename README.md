# Agent Learning

这是一个智能体开发学习项目，目标是逐步完成一个可展示的科研文献智能体。

当前项目已经覆盖：

- LLM API 调用
- Prompt 与结构化输出
- 本地工具调用
- Agent 工具循环
- 短期记忆与长期记忆
- 关键词版 RAG
- embedding + Chroma 语义检索版 RAG
- 多文档本地知识库问答
- Workflow 与 LangGraph
- Planner、Retriever、Reader、Reviewer、Writer 角色节点
- 条件路由、审核循环和计划校验
- 节点执行状态与运行轨迹保存

## 当前目标

阶段目标是构建一个本地科研资料问答原型：

```text
资料文件
-> chunk 切片
-> embedding 向量化
-> 写入 Chroma 向量数据库
-> 用户提问
-> 语义检索相关 chunk
-> DeepSeek 基于检索内容回答
-> 返回引用来源
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

复制环境变量文件：

```powershell
Copy-Item .env.example .env
```

然后在 `.env` 中填写自己的 DeepSeek API key：

```text
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_API_BASE=https://api.deepseek.com
```

## 常用命令

### 摘要工具

查看命令帮助：

```powershell
python -m src.main --help
```

普通摘要：

```powershell
python -m src.main examples\sample.txt
```

结构化摘要：

```powershell
python -m src.main examples\agent_complex.txt --structured
```

指定 prompt 风格：

```powershell
python -m src.main examples\agent_complex.txt --structured --style research
```

一次生成全部风格：

```powershell
python -m src.main examples\agent_complex.txt --structured --style all
```

评测结构化输出：

```powershell
python -m src.core.evaluator
```

### 工具调用 Agent

直接测试本地工具函数：

```powershell
python -m src.demos.tool_demo
```

测试工具注册表：

```powershell
python -m src.demos.tool_registry_demo
```

运行支持工具调用和记忆的 Agent：

```powershell
python -m src.demos.model_tool_call_demo "请读取 examples/agent_complex.txt，并统计它的字符数、行数和词数"
```

### 关键词版 RAG

运行关键词检索版 RAG：

```powershell
python -m src.demos.rag_demo "我应该先学 LangChain 还是 LangGraph？" --file examples\agent_rag_notes.txt
```

评测最近一次关键词 RAG 结果：

```powershell
python -m src.rag.rag_evaluator
```

### 语义检索版 RAG

先构建向量索引：

```powershell
python -m src.demos.build_rag_index --file examples\agent_rag_notes.txt
python -m src.demos.build_rag_index --file examples\paper_notes.txt
```

查看已经入库的资料：

```powershell
python -m src.demos.list_rag_sources
```

只检索指定文件：

```powershell
python -m src.demos.semantic_rag_demo "FastAPI 在这个项目里有什么作用？" --file examples\agent_rag_notes.txt
```

检索整个知识库：

```powershell
python -m src.demos.semantic_rag_demo "科研文献智能体需要支持哪些资料来源？"
```

指定检索参数：

```powershell
python -m src.demos.semantic_rag_demo "RAG 通常包括哪些步骤？" --top-k 3 --max-distance 0.9
```

评测最近一次语义 RAG 结果：

```powershell
python -m src.rag.semantic_rag_evaluator
```

### LangGraph 研究 Workflow

运行基于 LangGraph 的科研文献研究工作流：

```powershell
python -m src.demos.langgraph_research_demo "FastAPI 在这个项目里有什么作用？"
```

工作流主要经过：

```text
Planner
-> PlanValidator
-> Retriever
-> Reader
-> Reviewer
-> Writer
```

查看 Graph 的 Mermaid 结构：

```powershell
Get-Content -Encoding UTF8 outputs\langgraph_workflow.mmd
```

查看最终状态和执行轨迹：

```powershell
Get-Content -Encoding UTF8 outputs\langgraph_final_state.json
```

最终状态中包含计划、检索结果、回答、当前节点、已完成节点、计划进度和执行轨迹。

## 输出文件

运行过程中会生成一些本地输出：

```text
outputs/
├── summary.md
├── structured_summary_*.md
├── structured_summary_*.json
├── evaluation_report.json
├── tool_agent_trace.json
├── tool_agent_messages.json
├── long_term_memory.jsonl
├── rag_debug_trace.json
├── semantic_rag_debug_trace.json
├── langgraph_workflow.mmd
├── langgraph_final_state.json
└── langgraph_research_report.md
```

这些文件用于调试和学习复盘，不提交到 Git。

Chroma 本地向量数据库保存在：

```text
data/chroma/
```

它可以通过重新运行 `build_rag_index` 生成，也不提交到 Git。

## 项目结构

```text
agent_learning/
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── examples/
│   ├── sample.txt
│   ├── agent_complex.txt
│   ├── agent_rag_notes.txt
│   └── paper_notes.txt
├── prompts/
│   └── structured_summary_prompts.md
├── src/
│   ├── main.py
│   ├── config.py
│   ├── agents/
│   │   ├── planner.py
│   │   ├── research_roles.py
│   │   ├── research_state.py
│   │   └── tool_agent.py
│   ├── clients/
│   │   └── llm_client.py
│   ├── core/
│   │   ├── evaluator.py
│   │   └── summarizer.py
│   ├── demos/
│   │   ├── langgraph_research_demo.py
│   │   ├── langgraph_trace_demo.py
│   │   ├── manual_workflow_demo.py
│   │   ├── model_tool_call_demo.py
│   │   ├── rag_demo.py
│   │   ├── semantic_rag_demo.py
│   │   └── tool_registry_demo.py
│   ├── memory/
│   │   └── long_term_memory.py
│   ├── rag/
│   │   ├── chroma_store.py
│   │   ├── chunker.py
│   │   ├── embedding.py
│   │   ├── hybrid_retriever.py
│   │   ├── reranker.py
│   │   └── semantic_rag_evaluator.py
│   ├── tools/
│   │   ├── local_tools.py
│   │   └── registry.py
│   └── workflows/
│       └── langgraph_research_workflow.py
├── outputs/
└── data/
```
## 当前能力

```text
文本摘要
docx 文件读取
结构化 JSON 输出
Pydantic 校验
多风格 prompt
规则评测
本地工具调用
工具注册表
模型 Tool Calling
多轮工具调用循环
Agent trace
短期记忆 messages
长期记忆 JSONL
关键词 RAG
embedding 语义检索
Chroma 向量数据库
多文档知识库检索
引用来源 chunk_id/source
LangGraph StateGraph
条件边与循环边
Planner 计划生成
PlanValidator 计划校验
Reviewer 结果审核
current_step 与 completed_steps
execution_trace 运行轨迹
```

## 开发节奏

后续开发按这个方式推进：

```text
1. 明确需求
2. 拆分模块
3. 写核心逻辑
4. 写 demo 或测试入口
5. 保存 trace
6. 做简单评测
7. 更新 README
8. Git 提交
```

当前学习进度已经完成第七周的主要内容：

```text
Workflow 与 LangGraph
StateGraph 节点注册
普通边和条件边
Planner 与 PlanValidator
Reader 与 Reviewer 循环
计划进度和运行轨迹
```

第八周将进入应用集成与部署：

```text
FastAPI 接口
请求和响应模型
统一异常处理
API 测试
简单前端调用
README 和部署说明
```
