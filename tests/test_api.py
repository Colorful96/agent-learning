from fastapi.testclient import TestClient

import src.api.app as app_module
import src.agents.research_roles as research_roles

client = TestClient(app_module.app)


def test_health_check():
    """测试健康检查接口。"""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "agent-research",
    }


def test_research_validation_error():
    """测试研究问题为空时的参数校验。"""

    response = client.post(
        "/research",
        json={
            "question": "",
        },
    )

    assert response.status_code == 422

    data = response.json()

    assert data["code"] == "validation_error"


def test_research_success(monkeypatch):
    """测试研究接口成功响应。"""

    def fake_workflow(question, output_path, conversation_history=None):
        """模拟 LangGraph，避免测试时调用真实模型。"""

        return {
            "status": "writer_completed",
            "answer": "测试回答",
            "report_path": "outputs/test_report.md",
            "current_step": "writer",
            "completed_steps": [
                "planner",
                "retriever",
                "reader",
                "reviewer",
                "writer",
            ],
            "review_count": 1,
            "retrieved_items": [
                {
                    "chunk": {
                        "id": "test-chunk-1",
                        "source": "examples/test.txt",
                        "start": 0,
                        "end": 100,
                        "content": "测试内容",
                    }
                }
            ],
        }

    # 将真实 Workflow 替换成模拟函数
    monkeypatch.setattr(
        app_module,
        "run_langgraph_research_workflow",
        fake_workflow,
    )

    response = client.post(
        "/research",
        json={
            "question": "测试问题",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "writer_completed"
    assert data["answer"] == "测试回答"
    assert data["current_step"] == "writer"
    assert data["review_count"] == 1
    # 验证接口正确返回引用来源
    assert data["sources"] == [
        {
            "chunk_id": "test-chunk-1",
            "source": "examples/test.txt",
            "start": 0,
            "end": 100,
        }
    ]

    # 验证接口正确生成报告下载地址
    assert data["report_url"] == "/reports/test_report.md"


def test_download_report(tmp_path, monkeypatch):
    """测试 Markdown 报告下载接口。"""

    # 创建临时 Markdown 报告
    report_file = tmp_path / "test_report.md"
    report_file.write_text(
        "# 测试报告\n\n这是测试内容。",
        encoding="utf-8",
    )

    # 让接口从临时目录读取报告
    monkeypatch.setattr(
        app_module,
        "REPORT_DIR",
        tmp_path,
    )

    response = client.get("/reports/test_report.md")

    assert response.status_code == 200
    # 统一 Windows 和 Linux 的换行符后再比较
    actual_content = response.text.replace("\r\n", "\n")
    expected_content = "# 测试报告\n\n这是测试内容。"

    assert actual_content == expected_content


def test_query_rewriter_without_history():
    """没有历史时，直接使用当前问题。"""

    result = research_roles.query_rewriter_node(
        {
            "question": "FastAPI 有什么作用？",
            "conversation_history": [],
        }
    )

    assert result["retrieval_question"] == ("FastAPI 有什么作用？")
    assert result["status"] == "query_rewrite_skipped"


def test_query_rewriter_uses_history(monkeypatch):
    """有历史时，测试模型是否生成完整检索问题。"""

    captured = {}

    def fake_load_config():
        """返回测试所需的模型配置。"""

        return {
            "deepseek_api_key": "test-key",
            "deepseek_model": "test-model",
            "deepseek_api_base": "http://test-api",
        }

    def fake_generate_text(**kwargs):
        """模拟 Query Rewriter 的模型输出。"""

        captured["user_input"] = kwargs["user_input"]

        return "FastAPI 适合部署吗？"

    monkeypatch.setattr(
        research_roles,
        "load_config",
        fake_load_config,
    )

    monkeypatch.setattr(
        research_roles,
        "generate_text",
        fake_generate_text,
    )

    result = research_roles.query_rewriter_node(
        {
            "question": "它适合部署吗？",
            "conversation_history": [
                {
                    "role": "user",
                    "content": "FastAPI 在这个项目里有什么作用？",
                },
                {
                    "role": "assistant",
                    "content": "FastAPI 可以提供 HTTP 接口。",
                },
            ],
        }
    )

    assert "FastAPI 在这个项目里有什么作用？" in (captured["user_input"])

    assert result["retrieval_question"] == ("FastAPI 适合部署吗？")

    assert result["status"] == ("query_rewrite_completed")


def test_research_forwards_history(monkeypatch):
    """测试 FastAPI 将历史对话传给 LangGraph。"""

    captured = {}

    def fake_workflow(
        question,
        output_path,
        conversation_history=None,
    ):
        """模拟研究工作流并记录历史消息。"""

        captured["conversation_history"] = conversation_history

        return {
            "status": "writer_completed",
            "answer": "测试回答",
            "report_path": "outputs/test_report.md",
            "current_step": "writer",
            "completed_steps": ["writer"],
            "review_count": 1,
            "retrieved_items": [],
        }

    monkeypatch.setattr(
        app_module,
        "run_langgraph_research_workflow",
        fake_workflow,
    )

    history = [
        {
            "role": "user",
            "content": "FastAPI 有什么作用？",
        },
        {
            "role": "assistant",
            "content": "FastAPI 可以提供 HTTP 接口。",
        },
    ]

    response = client.post(
        "/research",
        json={
            "question": "它适合部署吗？",
            "history": history,
        },
    )

    assert response.status_code == 200
    assert captured["conversation_history"] == history
