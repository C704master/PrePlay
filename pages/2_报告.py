"""
PrePlay - 预演伙伴
报告页面
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import streamlit as st
from datetime import datetime
from services.report_service import generate_report
from services.session_service import get_training_stats, get_report_data

# 页面配置
st.set_page_config(
    page_title="PrePlay - 报告",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 隐藏侧边栏菜单
hide_menu_style = """
    <style>
    #MainMenu {visibility: hidden;}
    </style>
    """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# 检查是否有训练数据
if not st.session_state.get("chat_history") and not st.session_state.get("messages_for_report"):
    st.warning("还没有训练记录，请先开始训练")
    if st.button("🚀 去训练"):
        st.switch_page("pages/1_训练.py")
    st.stop()

# 获取会话ID
session_id = st.session_state.get("session_id", "")

# 顶部导航
col1, col2 = st.columns([1, 3])
with col1:
    if st.button("🔙 返回首页"):
        st.switch_page("app.py")
with col2:
    st.subheader("📊 训练报告")

st.divider()

# 获取对话数据
if st.session_state.get("messages_for_report"):
    conversation = st.session_state.messages_for_report
    chat_history = st.session_state.chat_history
else:
    conversation = get_report_data(session_id)
    chat_history = st.session_state.get("chat_history", [])

# 训练摘要
st.markdown("### 📈 训练摘要")

# 统计数据
if chat_history:
    total_messages = len(chat_history)
    red_messages = len([m for m in chat_history if m["role"] == "red"])
    blue_messages = len([m for m in chat_history if m["role"] == "blue"])
    user_messages = len([m for m in chat_history if m["role"] == "user"])
else:
    stats = get_training_stats(session_id)
    total_messages = stats.get("total", 0)
    red_messages = stats.get("red", 0)
    blue_messages = stats.get("blue", 0)
    user_messages = stats.get("user", 0)

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("总消息数", total_messages)
with col2:
    st.metric("🔴 红方提问", red_messages)
with col3:
    st.metric("🔵 蓝方回复", blue_messages)
with col4:
    st.metric("💬 你的回复", user_messages)

# 知识库信息
if st.session_state.get("uploaded_files"):
    file_names = [f.name for f in st.session_state.uploaded_files]
    st.write(f"📚 知识库文件：{', '.join(file_names)}")
st.write(f"🔄 对话轮次：{st.session_state.get('current_round', 0)}")

st.divider()

# KIMI AI 报告生成
st.markdown("### 🤖 AI 训练分析报告")

# 生成报告按钮
if st.button("✨ 生成 AI 报告", type="primary", use_container_width=True):
    with st.spinner("🤖 正在调用 KIMI 生成报告，请稍候..."):
        try:
            report_markdown = generate_report(conversation)
            st.session_state.kimi_report = report_markdown
            st.success("✅ 报告生成成功！")
        except Exception as e:
            st.error(f"❌ 报告生成失败: {str(e)}")

# 显示 KIMI 报告
if st.session_state.get("kimi_report"):
    st.markdown("---")
    st.markdown(st.session_state.kimi_report)
    st.markdown("---")
else:
    st.info("👆 点击上方按钮生成 AI 训练报告")

st.divider()

# 对话记录
st.markdown("### 📝 对话记录")

# 创建表格
data = []
if chat_history:
    for i, msg in enumerate(chat_history, 1):
        role_display = {
            "red": "🔴 红方",
            "blue": "🔵 蓝方",
            "user": "👤 你"
        }
        content_preview = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
        data.append({
            "轮次": i,
            "角色": role_display[msg["role"]],
            "内容": content_preview,
            "时间": msg["timestamp"]
        })
elif conversation:
    for i, msg in enumerate(conversation, 1):
        role = msg.get("role", "")
        source = msg.get("source", "")
        role_display = {"user": "👤 你", "assistant": "🤖 AI回复"}
        display = role_display.get(role, role)
        if source:
            display = f"{display}({source})"

        content_preview = msg["content"][:50] + "..." if len(msg["content"]) > 50 else msg["content"]
        data.append({
            "轮次": i,
            "角色": display,
            "内容": content_preview,
            "时间": msg["timestamp"]
        })

if data:
    st.dataframe(data, use_container_width=True)
else:
    st.info("暂无对话记录")

# 查看完整对话
with st.expander("👁️ 查看完整对话"):
    if chat_history:
        for msg in chat_history:
            role_display = {
                "red": "🔴 红方魔鬼导师",
                "blue": "🔵 蓝方心理教练",
                "user": "👤 你"
            }
            st.markdown(f"""
                <div style='background-color: #F7FAFC; padding: 12px; border-radius: 8px; margin: 10px 0;'>
                    <strong>{role_display[msg["role"]]}</strong> <small>({msg['timestamp']})</small><br/>
                    {msg['content']}
                </div>
            """, unsafe_allow_html=True)
    elif conversation:
        for msg in conversation:
            role = msg.get("role", "")
            source = msg.get("source", "")
            role_display = {"user": "👤 你", "assistant": "🤖 AI回复"}
            display = role_display.get(role, role)
            if source:
                display = f"{display}({source})"

            st.markdown(f"""
                <div style='background-color: #F7FAFC; padding: 12px; border-radius: 8px; margin: 10px 0;'>
                    <strong>{display}</strong> <small>({msg['timestamp']})</small><br/>
                    {msg['content']}
                </div>
            """, unsafe_allow_html=True)

st.divider()

# 导出功能
st.markdown("### 📥 导出报告")

col1, col2 = st.columns(2)

with col1:
    # 导出 KIMI 报告为 Markdown
    if st.session_state.get("kimi_report"):
        st.download_button(
            label="📄 导出 AI 报告 (Markdown)",
            data=st.session_state.kimi_report,
            file_name=f"PrePlay_AI报告_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
            mime="text/markdown",
            use_container_width=True
        )

with col2:
    # 导出对话记录
    def export_dialogue():
        text_content = "PrePlay 训练对话记录\n"
        text_content += f"生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        text_content += "=" * 50 + "\n\n"

        if chat_history:
            for i, msg in enumerate(chat_history, 1):
                role_display = {"red": "[红方]", "blue": "[蓝方]", "user": "[你]"}
                text_content += f"{i}. {role_display[msg['role']]} {msg['timestamp']}\n"
                text_content += f"{msg['content']}\n\n"
        elif conversation:
            for i, msg in enumerate(conversation, 1):
                role = msg.get("role", "")
                source = msg.get("source", "")
                role_display = {"user": "[你]", "assistant": f"[AI-{source}]" if source else "[AI]"}
                display = role_display.get(role, role)
                text_content += f"{i}. {display} {msg['timestamp']}\n"
                text_content += f"{msg['content']}\n\n"

        return text_content

    dialogue_text = export_dialogue()
    st.download_button(
        label="📝 导出对话记录 (TXT)",
        data=dialogue_text,
        file_name=f"PrePlay_对话记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
        use_container_width=True
    )

st.divider()

# 底部操作按钮
col1, col2, col3 = st.columns([1, 2, 1])
with col1:
    if st.button("🔄 新建训练"):
        st.session_state.chat_history = []
        st.session_state.current_round = 0
        st.session_state.session_id = None
        st.session_state.kimi_report = None
        st.session_state.messages_for_report = None
        st.switch_page("pages/1_训练.py")
with col2:
    st.write("")
with col3:
    if st.button("🏠 返回首页"):
        st.switch_page("app.py")
