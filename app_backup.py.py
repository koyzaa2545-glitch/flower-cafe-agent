import os
import sqlite3
from datetime import datetime
from pathlib import Path

import streamlit as st
from openai import OpenAI
from pypdf import PdfReader

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "research_assistant.db"

st.set_page_config(page_title="实验室科研辅助 Agent", page_icon="🔬", layout="wide")

SYSTEM_PROMPT = """你是一名严谨的科研辅助助手。请使用清晰、自然的中文回答。
帮助用户理解研究问题、研究设计、文献内容和学术写作。
不要编造论文、作者、DOI、数据或参考文献。信息不足时明确说明。
总结文献时区分原文明确陈述、合理推断和无法从文本确认的内容。
你提供的是研究辅助，不替代研究者核验原始文献。"""

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                task TEXT NOT NULL,
                due_date TEXT,
                status TEXT NOT NULL DEFAULT '未完成'
            )
        """)

def get_client(api_key):
    return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")

def ask_ai(client, messages, model):
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.3,
    )
    return response.choices[0].message.content or "模型没有返回文本。"

def extract_pdf_text(uploaded_file, max_chars=45000):
    reader = PdfReader(uploaded_file)
    pages = []
    for i, page in enumerate(reader.pages):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if text.strip():
            pages.append(f"\n[第 {i + 1} 页]\n{text}")
        if sum(len(x) for x in pages) >= max_chars:
            break
    return "\n".join(pages)[:max_chars], len(reader.pages)

init_db()

st.title("🔬 实验室科研辅助 Agent")
st.caption("AI 研究助手 · 文献总结 · 研究笔记 · 任务管理")
st.info("此应用在本机运行。调用 AI 时，所提交的聊天内容或 PDF 文本会发送到你选择的 AI 服务商。请勿上传含有机密或个人敏感信息的文件。")

with st.sidebar:
    st.header("⚙️ 模型设置")
    st.markdown("默认使用 DeepSeek API（OpenAI 兼容接口）。")
    api_key = st.text_input(
        "DeepSeek API Key",
        value=os.getenv("DEEPSEEK_API_KEY", ""),
        type="password",
        help="从 DeepSeek 开放平台获取 API Key；不要把密钥写进代码或分享给别人。"
    )
    model = st.text_input("模型名称", value="deepseek-flash")
    st.caption("API 调用可能产生费用，具体以服务商价格和账户额度为准。")
    st.divider()
    st.markdown("**功能导航**\n\n左侧选择页面：AI 对话、文献总结、研究笔记或任务管理。")

page = st.sidebar.radio(
    "选择功能",
    ["AI 研究助手", "文献总结", "研究笔记", "任务管理"],
    label_visibility="collapsed"
)

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

if page == "AI 研究助手":
    st.subheader("💬 AI 研究助手")
    st.write("可以询问研究问题、理论概念、研究设计、问卷思路或学术写作。")
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    prompt = st.chat_input("请输入你的研究问题……")
    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        if not api_key:
            st.warning("请先在左侧填写 DeepSeek API Key。")
        else:
            with st.chat_message("assistant"):
                with st.spinner("AI 正在思考……"):
                    try:
                        client = get_client(api_key)
                        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                        messages.extend(st.session_state.chat_messages[-12:])
                        answer = ask_ai(client, messages, model)
                        st.markdown(answer)
                        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
                    except Exception as e:
                        st.error(f"调用 API 失败：{e}")
    if st.button("清空本次对话"):
        st.session_state.chat_messages = []
        st.rerun()

elif page == "文献总结":
    st.subheader("📚 文献总结")
    st.write("上传可读取文字的 PDF。扫描版 PDF 可能需要先进行 OCR 文字识别。")
    uploaded_pdf = st.file_uploader("上传论文 PDF", type=["pdf"])
    focus = st.text_area(
        "希望重点分析什么？（可选）",
        placeholder="例如：研究问题、理论基础、变量定义、样本、方法、主要发现、局限性"
    )
    if uploaded_pdf and st.button("开始总结", type="primary"):
        if not api_key:
            st.warning("请先在左侧填写 DeepSeek API Key。")
        else:
            with st.spinner("正在读取 PDF 并生成总结……"):
                try:
                    text, total_pages = extract_pdf_text(uploaded_pdf)
                    if not text.strip():
                        st.error("没有提取到可用文字。该 PDF 可能是扫描图片，请先进行 OCR。")
                    else:
                        client = get_client(api_key)
                        request = f"""请根据以下论文文本，用中文整理文献阅读笔记。
请按以下结构输出：
1. 研究目的与研究问题
2. 理论基础与核心概念
3. 研究模型/假设（仅在文本明确提及时列出）
4. 数据、样本与研究方法
5. 主要结果
6. 理论贡献与实践启示
7. 研究局限
8. 值得进一步核对的问题
要求：不要凭空补充文献没有提供的信息；缺失的部分写“原文未明确说明”。
用户特别关注：{focus or "无额外要求"}
PDF 文件名：{uploaded_pdf.name}
PDF 总页数：{total_pages}
以下为提取到的文本（可能因 PDF 排版而不完整）：
{text}"""
                        result = ask_ai(
                            client,
                            [
                                {"role": "system", "content": SYSTEM_PROMPT},
                                {"role": "user", "content": request},
                            ],
                            model,
                        )
                        st.markdown(result)
                        st.download_button(
                            "下载总结为 TXT",
                            data=result.encode("utf-8"),
                            file_name="文献总结.txt",
                            mime="text/plain",
                        )
                        st.caption("提醒：请对照原文核实页码、数据、引用与结论。")
                except Exception as e:
                    st.error(f"处理失败：{e}")

elif page == "研究笔记":
    st.subheader("📝 研究笔记")
    with st.form("note_form", clear_on_submit=True):
        title = st.text_input("笔记标题")
        content = st.text_area("笔记内容", height=180)
        submitted = st.form_submit_button("保存笔记")
    if submitted:
        if title.strip() and content.strip():
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO notes (created_at, title, content) VALUES (?, ?, ?)",
                    (datetime.now().strftime("%Y-%m-%d %H:%M"), title.strip(), content.strip())
                )
            st.success("笔记已保存到本机数据库。")
        else:
            st.warning("请填写标题和内容。")

    with sqlite3.connect(DB_PATH) as conn:
        notes = conn.execute(
            "SELECT id, created_at, title, content FROM notes ORDER BY id DESC"
        ).fetchall()
    st.markdown("### 已保存的笔记")
    if not notes:
        st.caption("还没有笔记。")
    for note_id, created_at, title, content in notes:
        with st.expander(f"{title} · {created_at}"):
            st.write(content)
            if st.button("删除此笔记", key=f"delete_note_{note_id}"):
                with sqlite3.connect(DB_PATH) as conn:
                    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
                st.rerun()

elif page == "任务管理":
    st.subheader("✅ 研究任务管理")
    with st.form("task_form", clear_on_submit=True):
        task = st.text_input("任务内容")
        due = st.date_input("截止日期", value=None)
        submitted = st.form_submit_button("添加任务")
    if submitted:
        if task.strip():
            due_text = due.isoformat() if due else ""
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute(
                    "INSERT INTO tasks (created_at, task, due_date, status) VALUES (?, ?, ?, ?)",
                    (datetime.now().strftime("%Y-%m-%d %H:%M"), task.strip(), due_text, "未完成")
                )
            st.success("任务已添加。")
            st.rerun()
        else:
            st.warning("请先填写任务内容。")

    with sqlite3.connect(DB_PATH) as conn:
        tasks = conn.execute(
            "SELECT id, created_at, task, due_date, status FROM tasks ORDER BY status, due_date, id DESC"
        ).fetchall()
    if not tasks:
        st.caption("目前没有任务。")
    for task_id, created_at, task_text, due_date, status in tasks:
        with st.container(border=True):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{task_text}**")
                st.caption(f"创建时间：{created_at} · 截止日期：{due_date or '未设置'} · 状态：{status}")
            with col2:
                if status == "未完成":
                    if st.button("标记完成", key=f"done_{task_id}"):
                        with sqlite3.connect(DB_PATH) as conn:
                            conn.execute("UPDATE tasks SET status='已完成' WHERE id=?", (task_id,))
                        st.rerun()
                if st.button("删除", key=f"delete_task_{task_id}"):
                    with sqlite3.connect(DB_PATH) as conn:
                        conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
                    st.rerun()

st.divider()
st.caption("实验室科研辅助 Agent · 本地原型版")
