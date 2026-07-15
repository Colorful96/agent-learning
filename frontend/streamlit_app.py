import os
from urllib.parse import quote
import requests
import streamlit as st
from dotenv import load_dotenv

# 加载项目根目录中的 .env 文件
load_dotenv()

# 优先读取环境变量，没有配置时使用本地地址
API_BASE_URL = os.getenv(
    "AGENT_API_BASE_URL",
    "http://127.0.0.1:8000",
)

API_URL = f"{API_BASE_URL}/research"
UPLOAD_URL = f"{API_BASE_URL}/documents/upload"
DOCUMENTS_URL = f"{API_BASE_URL}/documents"

st.set_page_config(
    page_title="科研文献智能体",
    page_icon="📚",
    layout="wide",
)
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "session_id" not in st.session_state:
    st.session_state.session_id = st.query_params.get("session_id")
if "history_loaded" not in st.session_state:
    st.session_state.history_loaded = False

# 页面刷新后，根据 URL 中的会话 ID 从 FastAPI 恢复历史消息。
if (
    st.session_state.session_id
    and not st.session_state.history_loaded
):
    try:
        history_response = requests.get(
            f"{API_BASE_URL}/sessions/"
            f"{st.session_state.session_id}/messages",
            timeout=30,
        )

        if history_response.ok:
            st.session_state.chat_history = history_response.json()
            st.session_state.history_loaded = True
    except requests.RequestException:
        pass

st.title("科研文献智能体")
st.write("输入问题，让 Agent 基于本地资料进行研究。")

st.subheader("导入科研资料")

# 使用表单，只有点击按钮后才上传文件
with st.form("document_upload_form"):
    uploaded_file = st.file_uploader(
        "选择 TXT、DOCX 或 PDF 文件",
        type=["txt", "docx", "pdf"],
    )

    upload_submitted = st.form_submit_button(
        "导入知识库",
        type="primary",
    )

if upload_submitted:
    if uploaded_file is None:
        st.warning("请先选择一个文件。")
    else:
        try:
            with st.spinner("正在解析文件并建立索引..."):
                upload_response = requests.post(
                    UPLOAD_URL,
                    files={
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            uploaded_file.type or "application/octet-stream",
                        )
                    },
                    timeout=180,
                )

            if upload_response.status_code >= 400:
                error_data = upload_response.json()

                st.error(
                    error_data.get(
                        "detail",
                        "文件上传失败。",
                    )
                )
            else:
                upload_result = upload_response.json()

                st.success("文件上传并建立索引成功：" + upload_result["filename"])

                st.write(
                    "生成切片数量：",
                    upload_result["chunks_count"],
                )

        except requests.RequestException as error:
            st.error("无法连接 FastAPI 服务。")
            st.caption(str(error))
st.subheader("已上传文档")

try:
    documents_response = requests.get(
        DOCUMENTS_URL,
        timeout=30,
    )

    if documents_response.ok:
        documents = documents_response.json()

        if documents:
            st.dataframe(
                documents,
                hide_index=True,
            )
            document_names = [document["filename"] for document in documents]

            selected_filename = st.selectbox(
                "选择要删除的文档",
                document_names,
                key="selected_document",
            )

            if st.button(
                "删除选中文档",
                key="delete_document",
            ):
                try:
                    delete_response = requests.delete(
                        f"{DOCUMENTS_URL}/" f"{quote(selected_filename, safe='')}",
                        timeout=30,
                    )

                    if delete_response.ok:
                        delete_result = delete_response.json()

                        st.success(
                            "文档删除成功，删除向量切片数量："
                            + str(delete_result["removed_chunks"])
                        )

                        # 删除成功后刷新文档列表
                        st.rerun()
                    else:
                        error_data = delete_response.json()

                        st.error(
                            error_data.get(
                                "detail",
                                "文档删除失败。",
                            )
                        )

                except requests.RequestException as error:
                    st.error("无法连接 FastAPI 删除文档。")
                    st.caption(str(error))
        else:
            st.info("当前还没有上传文档。")
    else:
        st.warning("无法获取文档列表。")

except requests.RequestException as error:
    st.warning("无法连接 FastAPI 获取文档列表。")
    st.caption(str(error))

st.subheader("对话历史")

for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if st.button("清空对话", key="clear_chat"):
    st.session_state.chat_history = []
    st.session_state.session_id = None
    st.session_state.history_loaded = False
    st.query_params.pop("session_id", None)
    st.rerun()

question = st.text_area(
    "研究问题",
    placeholder="例如：FastAPI 在这个项目里有什么作用？",
    height=120,
)


if st.button("开始研究", type="primary"):
    if not question.strip():
        st.warning("请输入研究问题。")
    else:
        try:
            with st.spinner("Agent 正在检索和分析资料..."):
                response = requests.post(
                    API_URL,
                    json={
                        "question": question,
                        "session_id": st.session_state.session_id,
                    },
                    timeout=180,
                )

            if response.status_code >= 400:
                error_data = response.json()

                st.error(
                    error_data.get(
                        "message",
                        "API 请求失败。",
                    )
                )

            else:
                result = response.json()

                # 保存服务端返回的会话 ID，下一轮据此读取 SQLite 历史。
                st.session_state.session_id = result.get("session_id")
                st.session_state.history_loaded = True

                if st.session_state.session_id:
                    st.query_params["session_id"] = (
                        st.session_state.session_id
                    )

                answer = result.get("answer", "")

                # 保存本轮用户问题和 Agent 回答
                st.session_state.chat_history.extend(
                    [
                        {
                            "role": "user",
                            "content": question,
                        },
                        {
                            "role": "assistant",
                            "content": answer,
                        },
                    ]
                )

                # 只保留最近 10 条消息
                st.session_state.chat_history = st.session_state.chat_history[-10:]

                st.subheader("研究回答")
                st.markdown(answer)

                st.subheader("执行信息")

                col1, col2 = st.columns(2)

                with col1:
                    st.write(
                        "当前步骤：",
                        result.get("current_step"),
                    )

                with col2:
                    st.write(
                        "审核次数：",
                        result.get("review_count"),
                    )

                st.write(
                    "已完成节点：",
                    " → ".join(result.get("completed_steps", [])),
                )

                st.success("报告已保存到：" + result.get("report_path", ""))

                st.subheader("引用来源")

                for index, source in enumerate(
                    result.get("sources", []),
                    start=1,
                ):
                    st.write(
                        f"资料 {index}："
                        f"{source['source']} "
                        f"（chunk_id：{source['chunk_id']}，"
                        f"位置：{source['start']}-{source['end']}）"
                    )

                report_url = result.get("report_url", "")

                if report_url:
                    report_response = requests.get(
                        f"{API_BASE_URL}{report_url}",
                        timeout=30,
                    )

                    if report_response.ok:
                        st.download_button(
                            label="下载 Markdown 报告",
                            data=report_response.content,
                            file_name="api_research_report.md",
                            mime="text/markdown",
                        )
                    else:
                        st.warning("报告下载失败。")

        except requests.RequestException as error:
            st.error("无法连接 FastAPI 服务，请确认后端已经启动。")
            st.caption(str(error))
