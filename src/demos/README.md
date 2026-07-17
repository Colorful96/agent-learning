# Demos

This directory contains small command-line entrypoints for learning and manual checks. Run them from the repository root with the project environment activated.

Examples:

```powershell
python -m src.demos.semantic_rag_demo "FastAPI 在这个项目里有什么作用？" --file examples\agent_rag_notes.txt
python -m src.demos.langgraph_research_demo "FastAPI 在这个项目里有什么作用？"
python -m src.demos.mcp_demo
```

The web application does not import demo modules. Shared production logic belongs in `src/`, not in this directory.
