"""
PrePlay - 预演伙伴
训练页面
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
from utils.chat_manager import add_message, get_red_context, get_blue_context
from services.red_assistant import chat_with_red
from services.blue_assistant import chat_with_blue
from services.session_service import (
    create_training_session,
    save_training_message,
    get_training_messages,
    update_session_knowledge_file_ids,
    get_session_knowledge_file_ids
)
from services.knowledge_service import search_document

# 页面配置
st.set_page_config(
    page_title="PrePlay - 训练",
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

# 初始化 session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "current_round" not in st.session_state:
    st.session_state.current_round = 0
if "input_key_count" not in st.session_state:
    st.session_state.input_key_count = 0
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "persisted_session_id" not in st.session_state:
    st.session_state.persisted_session_id = None
if "knowledge_file_ids" not in st.session_state:
    st.session_state.knowledge_file_ids = []

# 加载历史训练记录
if st.session_state.get("current_training_id"):
    # 从首页点击了"继续"，加载历史会话
    session_id = st.session_state.current_training_id

    # 从数据库加载消息
    messages = get_training_messages(session_id)

    # 转换消息格式并添加到 chat_history
    st.session_state.chat_history = []
    st.session_state.current_round = 0

    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        source = msg.get("source", "")
        timestamp = msg["timestamp"]

        # 转换时间格式
        if isinstance(timestamp, str):
            # SQLite 返回的是类似 "2025-02-23 18:40:15" 的字符串
            # 只取时间部分 HH:MM:SS
            parts = timestamp.split()
            if len(parts) > 1:
                time_str = parts[1][:8]  # 取 "18:40:15"
            else:
                time_str = "00:00:00"
        else:
            # 如果是 datetime 对象，转换
            time_str = timestamp.strftime("%H:%M:%S")

        # 转换角色
        if role == "user":
            display_role = "user"
        elif role == "assistant":
            if "红" in source:
                display_role = "red"
            elif "蓝" in source:
                display_role = "blue"
            else:
                display_role = "blue"
        else:
            display_role = role

        # 添加到历史
        st.session_state.chat_history.append({
            "role": display_role,
            "content": content,
            "timestamp": time_str
        })

        # 更新轮次计数
        if role == "user":
            st.session_state.current_round += 1

    # 使用现有会话ID
    st.session_state.session_id = session_id
    # 标记为持久化，避免重新创建会话
    st.session_state.persisted_session_id = session_id

    # 获取知识库文件 IDs
    knowledge_file_ids = get_session_knowledge_file_ids(session_id)
    st.session_state.knowledge_file_ids = knowledge_file_ids if knowledge_file_ids else []

    # 清除 current_training_id 避免重复加载
    st.session_state.current_training_id = None

    st.success(f"已加载历史训练记录 ({len([m for m in messages if m['role'] == 'user'])} 轮对话)")

# 创建新会话 - 只在没有持久化会话时创建
elif st.session_state.session_id is None:
    st.session_state.session_id = create_training_session()
    st.session_state.persisted_session_id = st.session_state.session_id

    # 如果有从首页传来的 knowledge_file_ids，保存到数据库
    if st.session_state.get("training_file_ids"):
        st.session_state.knowledge_file_ids = st.session_state.training_file_ids
        update_session_knowledge_file_ids(st.session_state.session_id, st.session_state.training_file_ids)
        # 清理临时变量
        del st.session_state.training_file_ids

    st.info(f"已创建新的训练会话: {st.session_state.session_id}")

# 顶部导航栏
col1, col2, col3, col4 = st.columns([1, 2, 1, 1])
with col1:
    if st.button("🔙 返回首页"):
        st.switch_page("app.py")

with col2:
    st.subheader("🔴 红方(魔鬼导师)  |  🔵 蓝方(心理教练)")

with col3:
    if st.button("🔄 清空对话"):
        st.session_state.chat_history = []
        st.session_state.current_round = 0
        st.session_state.input_key_count += 1
        st.rerun()

with col4:
    if st.button("📊 查看报告"):
        st.switch_page("pages/2_报告.py")

st.divider()

# 知识库信息
if st.session_state.knowledge_file_ids:
    file_count = len(st.session_state.knowledge_file_ids)
    st.caption(f"📚 当前知识库：{file_count} 个文件（已激活）")
    st.caption(f"💬 对话轮次：{st.session_state.current_round}")

st.divider()

# 对话历史区域
def render_message(role, content, timestamp):
    """渲染单条消息"""
    if role == "red":
        st.markdown(f"""
            <div style='background-color: #FFF5F5; padding: 12px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #E53E3E;'>
                <strong>🔴 红方魔鬼导师</strong> <small>({timestamp})</small><br/>
                {content}
            </div>
        """, unsafe_allow_html=True)
    elif role == "blue":
        st.markdown(f"""
            <div style='background-color: #EBF8FF; padding: 12px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #3182CE;'>
                <strong>🔵 蓝方心理教练</strong> <small>({timestamp})</small><br/>
                {content}
            </div>
        """, unsafe_allow_html=True)
    else:  # user
        st.markdown(f"""
            <div style='background-color: #F7FAFC; padding: 12px; border-radius: 8px; margin: 10px 0; border-left: 4px solid #718096;'>
                <strong>👤 你</strong> <small>({timestamp})</small><br/>
                {content}
            </div>
        """, unsafe_allow_html=True)

# 创建一个容器来显示对话历史
chat_container = st.container()

with chat_container:
    # 渲染历史消息
    if st.session_state.chat_history:
        for msg in st.session_state.chat_history:
            render_message(msg["role"], msg["content"], msg["timestamp"])
    else:
        st.info("👋 训练开始！你可以直接输入内容发送给红方或蓝方")

st.divider()

# 底部输入区域
col1, col2 = st.columns([3, 1])

with col1:
    user_input = st.text_area(
        "输入你的回答或问题...",
        placeholder="输入你想说的话...",
        height=100,
        key=f"user_input_{st.session_state.input_key_count}"
    )

with col2:
    st.write("")
    st.write("")
    send_to_red = st.button("🔴 发送给红方", use_container_width=True)
    send_to_blue = st.button("🔵 发送给蓝方", use_container_width=True)

# 发送消息逻辑
if user_input and (send_to_red or send_to_blue):
    target = None
    if send_to_red:
        target = "red"
    elif send_to_blue:
        target = "blue"

    if target:
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 添加用户消息到界面
        add_message("user", user_input, target)

        # 保存到数据库 - 立即保存！
        try:
            save_training_message(st.session_state.session_id, "user", user_input, "", timestamp)
        except Exception as e:
            print(f"保存用户消息失败: {str(e)}")

        # 更新轮次计数
        st.session_state.current_round += 1

        # 改变 key 来清空输入框
        st.session_state.input_key_count += 1

        # 获取AI回复
        with st.spinner(f"{'红方' if target == 'red' else '蓝方'}正在思考..."):
            try:
                # 检查是否有知识库文件
                has_knowledge = bool(st.session_state.knowledge_file_ids)

                if target == "red":
                    # 红方只需要用户发给自己的对话
                    red_context = get_red_context()

                    if has_knowledge:
                        # 先进行知识库检索
                        try:
                            kb_answer = search_document(
                                st.session_state.knowledge_file_ids,
                                user_input,
                                wiki_filter_score=0.83,
                                temperature=0.8
                            )
                            # 将知识库检索结果作为用户消息发送给红方
                            user_input = f"[知识库参考]\n{kb_answer}\n\n[用户问题]\n{user_input}"
                            st.caption("📚 已基于知识库内容生成问题")
                        except Exception as e:
                            st.warning(f"知识库检索失败，使用常规对话：{str(e)}")

                    # 转换为 API 格式
                    api_history = [
                        {"role": "user", "content": msg["content"]}
                        for msg in red_context
                    ]
                    response, sid = chat_with_red(user_input, api_history)
                    source = "红方魔鬼导师"
                    role = "red"
                else:
                    # 蓝方需要完整对话历史
                    blue_context = get_blue_context()

                    if has_knowledge:
                        # 先进行知识库检索
                        try:
                            kb_answer = search_document(
                                st.session_state.knowledge_file_ids,
                                user_input,
                                wiki_filter_score=0.83,
                                temperature=0.7
                            )
                            # 将知识库检索结果作为上下文
                            user_input = f"[知识库参考]\n{kb_answer}\n\n[用户问题]\n{user_input}"
                            st.caption("📚 已基于知识库内容生成建议")
                        except Exception as e:
                            st.warning(f"知识库检索失败，使用常规对话：{str(e)}")

                    # 转换为 API 格式
                    api_history = []
                    for msg in blue_context:
                        role_map = {"user": "user", "red": "assistant", "blue": "assistant"}
                        api_role = role_map.get(msg["role"], "user")
                        source_text = f" ({msg['role']})" if msg.get("target") else ""
                        api_history.append({
                            "role": api_role,
                            "content": msg["content"]
                        })
                    response, sid = chat_with_blue(user_input, api_history)
                    source = "蓝方心理教练"
                    role = "blue"

                # 添加AI回复到界面
                add_message(role, response)

                # 保存到数据库 - 立即保存！
                try:
                    save_training_message(st.session_state.session_id, "assistant", response, source, timestamp)
                except Exception as e:
                    print(f"保存AI消息失败: {str(e)}")

            except Exception as e:
                st.error(f"回复失败: {str(e)}")

        st.rerun()

st.divider()

# 结束训练按钮
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("✅ 结束训练", type="primary", use_container_width=True):
        st.session_state.report_generated = True
        # 显示加载动画
        with st.spinner("正在生成训练报告..."):
            st.session_state.messages_for_report = get_training_messages(st.session_state.session_id)
            # 更新首页训练记录
            import app
            app.refresh_training_history()
        st.switch_page("pages/2_报告.py")
