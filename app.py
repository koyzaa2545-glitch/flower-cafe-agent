import streamlit as st
import streamlit.components.v1 as components
import time
import pandas as pd
import os
from datetime import datetime
from openai import OpenAI
from pypdf import PdfReader

# ==========================================
# 1. ตั้งค่าหน้าเว็บ
# ==========================================
st.set_page_config(page_title="花香研究室 · 虚拟咖啡馆", page_icon="🌸", layout="wide")

st.markdown("""
<style>
    .stButton>button { background-color: #FFB7B2; color: white; border-radius: 20px; border: none; padding: 10px 24px; width: 100%; font-weight: 600; transition: 0.3s; }
    .stButton>button:hover { background-color: #E5989B; color: white; }
    .stTextInput>div>div>input, .stTextArea>div>div>textarea { border-radius: 15px; border: 1px solid #FADADD; }
    .cute-card { background: white; border-radius: 15px; padding: 15px; border: 2px dashed #FADADD; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. หน้าจอคาเฟ่จำลอง
# ==========================================
cafe_room_html = """
<!DOCTYPE html>
<html>
<head>
<style>
    @import url('https://fonts.googleapis.com/css2?family=Mali:wght@600&display=swap');
    .cafe-room { position: relative; width: 100%; height: 350px; background-color: #FFF0F5; background-image: repeating-linear-gradient(90deg, transparent, transparent 40px, rgba(255,255,255,0.5) 40px, rgba(255,255,255,0.5) 80px); border: 6px solid #8B4513; border-radius: 20px; overflow: hidden; font-family: 'Mali', sans-serif; box-shadow: inset 0 0 50px rgba(0,0,0,0.1); }
    .floor { position: absolute; bottom: 0; width: 100%; height: 150px; background: repeating-linear-gradient(90deg, #DEB887, #DEB887 40px, #D2B48C 40px, #D2B48C 80px); border-top: 4px solid #A0522D; }
    .window { position: absolute; top: 30px; right: 50px; width: 150px; height: 100px; background: linear-gradient(to bottom, #87CEEB, #E0FFFF); border: 8px solid #FFF; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
    .bakery-case { position: absolute; bottom: 150px; left: 40px; width: 120px; height: 150px; background: rgba(255, 255, 255, 0.4); border: 6px solid #8B4513; border-radius: 10px 10px 0 0; display: flex; flex-direction: column; justify-content: space-around; padding: 10px; z-index: 5; }
    .shelf { border-bottom: 4px solid #A0522D; display: flex; justify-content: space-around; padding-bottom: 5px; font-size: 24px; }
    .plant { position: absolute; bottom: 10px; font-size: 40px; z-index: 5; }
    .p1 { right: 30px; } .p2 { left: 180px; }
    .table-spot { position: absolute; text-align: center; z-index: 10; }
    .t1 { top: 40%; left: 30%; } .t2 { top: 20%; left: 50%; } .t3 { top: 45%; left: 70%; }
    .table-top { width: 80px; height: 30px; background-color: #8B4513; border-radius: 50%; border: 4px solid #5C2E0B; display: flex; justify-content: center; align-items: center; }
    .table-top .snack { position: absolute; font-size: 20px; top: -15px; }
    .table-leg { width: 10px; height: 30px; background-color: #5C2E0B; margin: 0 auto; margin-top: -5px; }
    .customer { position: absolute; top: -40px; left: 20px; font-size: 35px; animation: sit-bob 2s ease-in-out infinite; }
    @keyframes sit-bob { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-5px); } }
    .chef { position: absolute; bottom: 10px; font-size: 50px; z-index: 20; animation: chef-walk 10s infinite alternate ease-in-out; }
    @keyframes chef-walk { 0% { left: 20%; transform: scaleX(1); } 49% { left: 75%; transform: scaleX(1); } 50% { left: 75%; transform: scaleX(-1); } 100% { left: 20%; transform: scaleX(-1); } }
</style>
</head>
<body>
<div class="cafe-room">
    <div class="window"></div>
    <div class="bakery-case"><div class="shelf">🍰 🧁</div><div class="shelf">🥐 🍩</div><div class="shelf">🍪 🍬</div></div>
    <div class="floor"></div>
    <div class="plant p1">🪴</div><div class="plant p2">🌿</div>
    <div class="table-spot t1"><div class="table-top"><div class="customer">👩‍💻</div><div class="snack">🍰</div></div><div class="table-leg"></div></div>
    <div class="table-spot t2"><div class="table-top"><div class="customer">👨‍🔬</div><div class="snack">🍬</div></div><div class="table-leg"></div></div>
    <div class="table-spot t3"><div class="table-top"><div class="customer">🧑‍🎓</div><div class="snack">🥐</div></div><div class="table-leg"></div></div>
    <div class="chef">👩‍🍳</div>
</div>
</body>
</html>
"""
st.markdown("<h2 style='text-align: center; color: #E5989B;'>🌸 花香研究室 · 虚拟咖啡馆 🌸</h2>", unsafe_allow_html=True)
components.html(cafe_room_html, height=370)

st.markdown("---")
st.markdown("<h3 style='text-align: center; color: #8B4513;'>👇 请在下方选择您的工作台 👇</h3>", unsafe_allow_html=True)

# ==========================================
# 3. ระบบหลังบ้าน (State & Excel)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "你好！我是你的科研小助手 Flora，今天想喝点什么？🌸"}]
if "rewards" not in st.session_state:
    st.session_state.rewards = []

EXCEL_FILE = "cafe_records.xlsx"
CATEGORIES = ["📝 毕业论文", "📚 理论框架", "🔬 自变量", "⚙️ 中介变量", "🎯 因变量", "💡 其他"]

# ฟังก์ชันเซฟแบบดักจับ Error
def save_to_excel(category, action, summary, note, dessert_name):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_data = pd.DataFrame({"时间": [now], "分类": [category], "活动": [action], "摘要": [summary], "笔记": [note], "获得甜点": [dessert_name]})
    
    try:
        if os.path.exists(EXCEL_FILE):
            df_existing = pd.read_excel(EXCEL_FILE)
            # ลบคอลัมน์แปลกปลอมที่อาจจะติดมาจากเวอร์ชันเก่า
            expected_cols = ["时间", "分类", "活动", "摘要", "笔记", "获得甜点"]
            df_existing = df_existing[[c for c in expected_cols if c in df_existing.columns]]
            
            df_combined = pd.concat([df_existing, new_data], ignore_index=True)
            df_combined.to_excel(EXCEL_FILE, index=False)
        else: 
            new_data.to_excel(EXCEL_FILE, index=False)
        return True
    except PermissionError:
        return "PermissionError"
    except Exception as e: 
        return str(e)

def get_dessert_by_time(seconds):
    minutes = seconds / 60
    if minutes < 1: return "🍪 黄油曲奇"
    elif minutes <= 3: return "🍰 草莓蛋糕"
    else: return "🎂 玫瑰特级蛋糕"

def extract_text_from_pdf(pdf_file):
    try:
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            if page.extract_text(): text += page.extract_text() + "\n"
        return text[:12000]
    except Exception as e:
        return f"Error: {e}"

def ask_flora_ai(text, mode):
    try:
        client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
        
        if mode == "translate":
            system_msg = "你是一位专业的学术翻译。"
            prompt = f"请将以下提取自 PDF 的学术文本翻译成专业、流畅的中文：\n\n{text}"
        elif mode == "pdf":
            system_msg = "你是一位专业的科研助手，擅长总结文献。"
            prompt = f"请阅读以下文献内容，提取核心观点、研究方法，并写一段 300 字以内的中文摘要：\n\n{text}"
            
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"AI 处理失败，请检查 API Key: {e}"

def serve_dessert(action_name, category, summary, note, key_prefix):
    start_time = st.session_state.get(f'timer_{key_prefix}', time.time())
    time_spent = time.time() - start_time
    dessert = get_dessert_by_time(time_spent)
    
    result = save_to_excel(category, action_name, summary, note, dessert)
    
    if result is True:
        st.toast(f"🔔 获得 {dessert}！", icon="👩‍🍳")
        st.session_state.rewards.append(dessert)
        st.balloons()
        time.sleep(1) 
        st.rerun()
    elif result == "PermissionError":
        st.error("❌ บันทึกไม่สำเร็จ! **กรุณาปิดไฟล์ Excel (cafe_records.xlsx) ก่อนกดรับขนมครับ** (เพราะโปรแกรม Excel กำลังล็อกไฟล์อยู่)")
        st.stop()
    else:
        st.error(f"❌ เกิดข้อผิดพลาด: {result}")
        st.stop()

def render_task(col, title, emoji, desc, action_name, key_prefix, mode="text"):
    with col:
        st.markdown(f"<div class='cute-card'><span style='font-size: 40px;'>{emoji}</span><h3 style='color: #E5989B; margin: 5px 0;'>{title}</h3><p style='font-size: 12px; color: #888;'>{desc}</p></div>", unsafe_allow_html=True)
        
        uploaded_file = None
        user_input = ""
        
        if mode in ["pdf", "translate"]:
            uploaded_file = st.file_uploader("上传 PDF 文件", type=["pdf"], key=f"file_{key_prefix}", label_visibility="collapsed")
            if uploaded_file: user_input = uploaded_file.name
        else:
            user_input = st.text_input("输入内容", key=f"in_{key_prefix}", label_visibility="collapsed", placeholder="在此输入...")
            
        cat = st.selectbox("选择分类", CATEGORIES, key=f"cat_{key_prefix}", label_visibility="collapsed")
        note = st.text_area("补充笔记", key=f"nt_{key_prefix}", placeholder="记录你的灵感...", height=68)
        
        timer_key = f"timer_{key_prefix}"
        if timer_key not in st.session_state: st.session_state[timer_key] = None
            
        if st.session_state[timer_key] is None:
            if st.button("⏱️ 开始工作", key=f"st_{key_prefix}"):
                st.session_state[timer_key] = time.time()
                st.rerun()
        else:
            st.success("⏳ 计时中... 请专注！")
            if st.button("🔔 完成 & 领取甜点", key=f"fn_{key_prefix}"):
                
                if mode in ["pdf", "translate"] and not uploaded_file:
                    st.warning("请先上传 PDF 文件哦")
                    return
                if mode == "text" and not user_input and not note:
                    st.warning("请先填写内容或笔记哦")
                    return

                if mode in ["pdf", "translate"]:
                    with st.spinner("Flora 正在努力处理中..."):
                        raw_text = extract_text_from_pdf(uploaded_file)
                        ai_summary = ask_flora_ai(raw_text, mode=mode)
                    serve_dessert(action_name, cat, ai_summary, note, key_prefix)
                else: 
                    serve_dessert(action_name, cat, user_input, note, key_prefix)
                
                st.session_state[timer_key] = None

# ==========================================
# 4. Sidebar
# ==========================================
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #E5989B;'>👩‍🍳 Flora</h2>", unsafe_allow_html=True)
    st.markdown('<div style="text-align:center; font-size: 80px;">👩‍🍳</div>', unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 14px; color: #888;'>工作时间越长，甜点越精美！</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("<p style='text-align: center; font-size: 14px; color: #A3B18A;'>🎵 背景音乐</p>", unsafe_allow_html=True)
    audio_url = "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3?filename=lofi-study-112191.mp3"
    st.markdown(f"""<audio controls autoplay loop style="width: 100%; height: 40px;"><source src="{audio_url}" type="audio/mpeg"></audio>""", unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("🎁 我的甜点收集")
    if st.session_state.rewards:
        for r in st.session_state.rewards: st.write(f"✨ {r}")
    else: st.caption("还没有甜点哦，快去工作吧！")

# ==========================================
# 5. Tabs
# ==========================================
tab1, tab2, tab3 = st.tabs(["☕ 工作台 (Tools)", "💬 与 Flora 聊天 (AI)", "📊 Excel 记录"])

with tab1:
    r1, r2, r3 = st.columns(3)
    render_task(r1, "总结 PDF", "🍰", "上传 PDF 并总结", "总结 PDF", "pdf", mode="pdf")
    render_task(r2, "翻译文献", "🍩", "上传 PDF 并翻译", "翻译文献", "trans", mode="translate")
    render_task(r3, "任务管理", "☕", "记录任务（直接保存）", "任务管理", "task", mode="text")

with tab2:
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]): st.write(msg["content"])
            
        if prompt := st.chat_input("输入你的科研问题..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"): st.write(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Flora 正在思考..."):
                    try:
                        client = OpenAI(api_key=st.secrets["DEEPSEEK_API_KEY"], base_url="https://api.deepseek.com")
                        msgs = [{"role": "system", "content": "你是一位名叫 Flora 的可爱咖啡师，帮助用户解答科研问题。请用温柔、礼貌的中文回答。"}] + st.session_state.messages
                        resp = client.chat.completions.create(model="deepseek-chat", messages=msgs)
                        ans = resp.choices[0].message.content
                        st.write(ans)
                    except Exception as e:
                        ans = f"❌ 连接错误: {e}"
                        st.error(ans)
            st.session_state.messages.append({"role": "assistant", "content": ans})

# ---------- แท็บ 3: ตาราง Excel ----------
with tab3:
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE)
            
            df = df.fillna("") 
            df["笔记"] = df["笔记"].astype(str) 
            df["摘要"] = df["摘要"].astype(str) 

            # ใช้ num_rows="dynamic" จะมีรูปถังขยะให้กดลบแถวได้เลย
            edited_df = st.data_editor(
                df, use_container_width=True, hide_index=True, num_rows="dynamic",
                column_config={
                    "摘要": st.column_config.TextColumn("摘要", width="large"),
                    "笔记": st.column_config.TextColumn("笔记", width="medium")
                }
            )

            if st.button("💾 บันทึกการแก้ไข / ลบข้อมูล", use_container_width=True):
                edited_df.to_excel(EXCEL_FILE, index=False)
                st.toast("✅ บันทึกข้อมูลลง Excel เรียบร้อยแล้ว!", icon="💾")
                time.sleep(1)
                st.rerun()

            st.markdown("---")
            with open(EXCEL_FILE, "rb") as file:
                st.download_button("📥 下载 Excel 记录", data=file, file_name="cafe_records.xlsx")
        except Exception as e:
            st.error(f"ไม่สามารถอ่านไฟล์ Excel ได้: {e}")
    else:
        st.info("暂无记录，请先去工作台赚取甜点吧！")