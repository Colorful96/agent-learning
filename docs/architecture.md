# Architecture

## Overview

Research Agent is a runnable reference project for a document question-answering agent. The current production path is:

```text
Streamlit or HTTP client
        |
     FastAPI
        |
    LangGraph
        |
Planner -> PlanValidator -> QueryRewriter -> Retriever
                                      |
                               Reader -> Reviewer -> Writer
```

The planner chooses one of two routes:

- `direct_answer`: answer a simple question from the current conversation.
- `research`: retrieve local documents, read the evidence, review the draft, and write a cited Markdown report.

## Runtime Modules

| Layer | Location | Responsibility |
| --- | --- | --- |
| API | `src/api/` | Request validation, session persistence, upload and report download |
| Workflow | `src/workflows/` | Build and invoke the LangGraph state machine |
| Agents | `src/agents/` | Planner and role-based node implementations |
| RAG | `src/rag/` | Loading, chunking, embedding, retrieval and prompt construction |
| Tools | `src/tools/` | Tool definitions, registry and local execution |
| Integrations | `src/integrations/` | Optional MCP client/server integration |
| Skills | `src/skills/` | Reusable domain-level capabilities |
| Memory | `src/memory/` | SQLite conversation history and long-term-memory examples |
| Frontend | `frontend/` | Streamlit user interface |

## State and Persistence

LangGraph nodes share a typed state object. It contains the question, plan, current step, retrieved evidence, answer, report path, completed steps and execution trace.

SQLite stores sessions and messages. Chroma stores document embeddings. Runtime data is intentionally ignored by Git; only source code, examples and evaluation cases belong in the repository.

## Production Code and Demos

`src/demos/` contains small command-line entrypoints used during learning and manual verification. They are not imported by the API runtime. Historical implementations such as the fixed workflow and manual workflow are kept as learning references, while the current application uses `src/workflows/langgraph_research_workflow.py`.

Prompt assembly shared by runtime and demos lives in `src/rag/prompt_builder.py`, so the production path does not depend on a demo module.

## Extension Points

1. Add a document parser in `src/ingestion/document_service.py`.
2. Add a retrieval strategy under `src/rag/`.
3. Add a tool to `src/tools/` and expose it through the registry.
4. Add a reusable capability under `src/skills/`.
5. Add a LangGraph node or route in the workflow module.
6. Add tests under `tests/` and an evaluation case under `data/eval/`.
