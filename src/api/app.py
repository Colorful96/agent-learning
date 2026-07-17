from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel, Field

from src.workflows.langgraph_research_workflow import (
    run_langgraph_research_workflow,
)
from typing import Literal
from src.storage.sqlite_store import (
    add_message,
    get_or_create_session,
    get_recent_messages,
)
import logging
from src.ingestion.document_service import (
    delete_uploaded_document,
    list_uploaded_documents,
    save_and_index_document,
)
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.clients.llm_client import LLMClientError
import time
import uuid
from pathlib import Path
import os

from fastapi import HTTPException
from fastapi.responses import FileResponse


class DocumentDeleteResponse(BaseModel):
    """文档删除接口响应模型。"""

    filename: str
    removed_chunks: int
    message: str


class DocumentUploadResponse(BaseModel):
    """文档上传接口响应模型。"""

    filename: str
    source: str
    chunks_count: int
    message: str


class DocumentInfo(BaseModel):
    """已上传文档信息。"""

    filename: str
    source: str
    file_type: str
    size_bytes: int


class HealthResponse(BaseModel):
    """健康检查响应模型。"""

    status: str
    service: str


class SourceInfo(BaseModel):
    """检索资料来源信息。"""

    chunk_id: str
    source: str
    start: int
    end: int


class ConversationMessage(BaseModel):
    """单条对话消息。"""

    role: Literal["user", "assistant"]
    content: str = Field(
        min_length=1,
        max_length=5000,
    )


class ResearchRequest(BaseModel):
    """研究接口请求模型。"""

    session_id: str | None = None
    source: str | None = None
    history: list[ConversationMessage] = Field(
        default_factory=list,
        max_length=10,
    )

    question: str = Field(
        min_length=2,
        max_length=500,
        description="用户要研究的问题。",
    )


class ResearchResponse(BaseModel):
    """研究接口响应模型。"""

    status: str
    answer: str
    report_path: str
    current_step: str
    completed_steps: list[str]
    review_count: int
    sources: list[SourceInfo]
    report_url: str
    session_id: str


app = FastAPI(
    title="Agent Research API",
    version="0.1.0",
)

Path("outputs").mkdir(
    parents=True,
    exist_ok=True,
)

logging.basicConfig(
    level=logging.INFO,
    format=("%(asctime)s " "%(levelname)s " "%(name)s " "%(message)s"),
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(
            "outputs/app.log",
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger("agent_api")

PUBLIC_PATHS = {
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next,
):
    """记录每次请求的 ID、耗时和状态码。"""

    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex

    request.state.request_id = request_id
    start_time = time.perf_counter()

    configured_token = os.getenv("AGENT_API_TOKEN", "").strip()
    request_token = request.headers.get("X-API-Key", "")

    if configured_token and request.url.path not in PUBLIC_PATHS:
        if request_token != configured_token:
            response = JSONResponse(
                status_code=401,
                content={
                    "code": "unauthorized",
                    "message": "缺少有效的 API Token。",
                    "request_id": request_id,
                },
            )
            response.headers["X-Request-ID"] = request_id
            return response

    try:
        response = await call_next(request)
    except Exception as error:
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.error(
            ("request_id=%s method=%s path=%s " "status=500 duration_ms=%.2f error=%s"),
            request_id,
            request.method,
            request.url.path,
            duration_ms,
            str(error),
        )

        raise

    duration_ms = (time.perf_counter() - start_time) * 1000

    response.headers["X-Request-ID"] = request_id

    logger.info(
        ("request_id=%s method=%s path=%s " "status=%s duration_ms=%.2f"),
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    """处理请求参数校验错误。"""

    logger.warning(
        "请求参数校验失败：%s",
        exc.errors(),
    )
    request_id = getattr(
        request.state,
        "request_id",
        "unknown",
    )
    return JSONResponse(
        status_code=422,
        content={
            "code": "validation_error",
            "message": "请求参数不合法。",
            "details": exc.errors(),
            "request_id": request_id,
        },
    )


@app.exception_handler(LLMClientError)
async def llm_exception_handler(
    request: Request,
    exc: LLMClientError,
):
    """处理大模型调用错误。"""

    logger.error(
        "模型调用失败：%s",
        str(exc),
    )

    request_id = getattr(
        request.state,
        "request_id",
        "unknown",
    )

    return JSONResponse(
        status_code=502,
        content={
            "code": "llm_error",
            "message": "模型服务调用失败，请稍后重试。",
            "request_id": request_id,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(
    request: Request,
    exc: Exception,
):
    """处理未预期的服务器异常。"""

    logger.exception(
        "未处理的服务器异常：%s",
        str(exc),
    )
    request_id = getattr(
        request.state,
        "request_id",
        "unknown",
    )
    return JSONResponse(
        status_code=500,
        content={
            "code": "internal_error",
            "message": "服务器内部错误。",
            "request_id": request_id,
        },
    )


@app.get(
    "/health",
    response_model=HealthResponse,
)
def health_check():
    """检查 API 服务是否正常运行。"""

    return HealthResponse(
        status="ok",
        service="agent-research",
    )


@app.post(
    "/documents/upload",
    response_model=DocumentUploadResponse,
)
async def upload_document(
    file: UploadFile = File(...),
):
    """上传 TXT、DOCX 或 PDF，并建立向量索引。"""

    try:
        content = await file.read()

        result = save_and_index_document(
            filename=file.filename or "",
            content=content,
        )

        return DocumentUploadResponse(
            filename=result["filename"],
            source=result["source"],
            chunks_count=result["chunks_count"],
            message="文档上传并建立索引成功。",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error


@app.get(
    "/documents",
    response_model=list[DocumentInfo],
)
def list_documents():
    """返回所有已上传文档。"""

    return [DocumentInfo(**document) for document in list_uploaded_documents()]


@app.delete(
    "/documents/{filename}",
    response_model=DocumentDeleteResponse,
)
def delete_document(filename: str):
    """删除文档和对应的向量切片。"""

    try:
        result = delete_uploaded_document(filename)

        return DocumentDeleteResponse(
            filename=result["filename"],
            removed_chunks=result["removed_chunks"],
            message="文档和向量切片删除成功。",
        )

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error


@app.post(
    "/research",
    response_model=ResearchResponse,
)
def research(request: ResearchRequest):
    """调用 LangGraph 执行科研资料研究。"""

    # 优先使用服务端 SQLite 中保存的历史，避免客户端篡改上下文。
    session_id = get_or_create_session(request.session_id)
    stored_history = get_recent_messages(
        session_id=session_id,
        limit=10,
    )

    # 保留旧 history 参数，兼容之前的命令行和测试请求。
    conversation_history = stored_history or [
        message.model_dump() for message in request.history
    ]

    workflow_arguments = {
        "question": request.question,
        "output_path": "outputs/api_research_report.md",
        "conversation_history": conversation_history,
    }

    if request.source:
        workflow_arguments["source"] = request.source

    result = run_langgraph_research_workflow(**workflow_arguments)

    answer = result.get("answer", "")

    # 工作流成功返回后，按用户、助手的顺序持久化本轮对话。
    add_message(
        session_id=session_id,
        role="user",
        content=request.question,
    )
    if answer:
        add_message(
            session_id=session_id,
            role="assistant",
            content=answer,
        )

    # 把检索结果转换成接口返回的引用来源
    sources = []

    for item in result.get("retrieved_items", []):
        chunk = item.get("chunk", {})

        sources.append(
            SourceInfo(
                chunk_id=str(chunk.get("id", "unknown")),
                source=str(chunk.get("source", "unknown")),
                start=int(chunk.get("start", 0) or 0),
                end=int(chunk.get("end", 0) or 0),
            )
        )

    # 只返回文件名，供下载接口使用
    report_path = result.get("report_path", "")
    report_filename = Path(report_path).name if report_path else ""
    report_url = f"/reports/{report_filename}" if report_filename else ""

    return ResearchResponse(
        status=result.get("status", "unknown"),
        answer=answer,
        report_path=report_path,
        current_step=result.get("current_step", ""),
        completed_steps=result.get("completed_steps", []),
        review_count=result.get("review_count", 0),
        sources=sources,
        report_url=report_url,
        session_id=session_id,
    )


@app.get(
    "/sessions/{session_id}/messages",
    response_model=list[ConversationMessage],
)
def get_session_messages(session_id: str):
    """读取指定会话的历史消息。"""

    messages = get_recent_messages(
        session_id=session_id,
        limit=50,
    )

    return [ConversationMessage(**message) for message in messages]


REPORT_DIR = Path("outputs").resolve()


@app.get("/reports/{filename}")
def download_report(filename: str):
    """下载 outputs 目录中的 Markdown 报告。"""

    file_path = (REPORT_DIR / filename).resolve()

    # 防止通过 ../ 访问 outputs 目录之外的文件
    if REPORT_DIR not in file_path.parents or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail="报告不存在。",
        )

    return FileResponse(
        path=file_path,
        media_type="text/markdown",
        filename=file_path.name,
    )
