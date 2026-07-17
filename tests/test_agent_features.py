import pytest

import src.api.app as app_module
import src.agents.research_roles as research_roles
from fastapi.testclient import TestClient
from src.agents.planner import PlanStep, TaskPlan, validate_plan
from src.skills.registry import get_skill
from src.tools.local_tools import (
    read_text_file,
    save_markdown_report,
)


client = TestClient(app_module.app)


def test_retriever_forwards_source_filter(monkeypatch):
    """Retriever 应该把来源筛选条件传给知识库工具。"""

    captured = {}

    def fake_execute_tool(name, arguments):
        captured["name"] = name
        captured["arguments"] = arguments
        return {"items": []}

    monkeypatch.setattr(
        research_roles,
        "execute_tool",
        fake_execute_tool,
    )

    research_roles.retriever_node(
        {
            "question": "FastAPI 有什么作用？",
            "retrieval_question": "FastAPI 有什么作用？",
            "source": "data/uploads/notes.pdf",
        }
    )

    assert captured["name"] == "search_knowledge_base"
    assert captured["arguments"]["source"] == "data/uploads/notes.pdf"


def test_api_forwards_source_filter(monkeypatch):
    """FastAPI 应该把请求中的 source 传给研究工作流。"""

    captured = {}

    def fake_workflow(
        question,
        output_path,
        conversation_history=None,
        source=None,
    ):
        captured["source"] = source
        return {
            "status": "direct_answer_completed",
            "answer": "测试回答",
            "report_path": "",
            "current_step": "direct_answer",
            "completed_steps": ["direct_answer"],
            "review_count": 0,
            "retrieved_items": [],
        }

    monkeypatch.setattr(
        app_module,
        "run_langgraph_research_workflow",
        fake_workflow,
    )

    response = client.post(
        "/research",
        json={
            "question": "测试来源筛选",
            "source": "data/uploads/notes.pdf",
        },
    )

    assert response.status_code == 200
    assert captured["source"] == "data/uploads/notes.pdf"


def test_direct_answer_plan_routes_without_tools():
    """direct_answer 计划不需要检索和报告工具。"""

    plan = TaskPlan(
        goal="解释 FastAPI 的基本概念",
        workflow_type="direct_answer",
        skill_name="direct_qa",
        steps=[
            PlanStep(
                step_id="step-1",
                action="生成回答",
                description="直接回答用户问题",
            )
        ],
    )

    assert validate_plan(plan).workflow_type == "direct_answer"

    state = {
        "workflow_type": "direct_answer",
        "planned_tools": [],
    }
    result = research_roles.plan_validator_node(state)

    assert result["plan_valid"] is True
    assert research_roles.route_after_plan_validation(
        {**state, **result}
    ) == "direct_answer"


def test_skill_registry_returns_specialized_prompts():
    """不同 Skill 应该提供不同的任务配置。"""

    research_skill = get_skill("literature_research")
    direct_skill = get_skill("direct_qa")

    assert research_skill.workflow_type == "research"
    assert direct_skill.workflow_type == "direct_answer"
    assert research_skill.system_prompt != direct_skill.system_prompt


def test_local_tools_reject_unsafe_paths(tmp_path):
    """本地工具不允许访问项目目录之外的文件。"""

    with pytest.raises(ValueError):
        read_text_file("..\\.env")

    with pytest.raises(ValueError):
        save_markdown_report(
            title="unsafe",
            content="content",
            output_path=str(tmp_path / "unsafe.md"),
        )


def test_api_token_protects_sensitive_routes(monkeypatch):
    """配置 API Token 后，敏感接口需要 X-API-Key。"""

    monkeypatch.setenv("AGENT_API_TOKEN", "test-token")

    assert client.get("/health").status_code == 200
    assert client.get("/documents").status_code == 401
    assert client.get(
        "/documents",
        headers={"X-API-Key": "test-token"},
    ).status_code == 200
