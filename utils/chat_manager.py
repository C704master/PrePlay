"""
对话管理工具
用于管理训练对话历史
"""
from datetime import datetime
import streamlit as st


def add_message(role, content, target=None):
    """添加一条消息到对话历史"""
    message = {
        "role": role,              # "user", "red", "blue"
        "content": content,
        "timestamp": datetime.now().strftime("%H:%M:%S"),
        "target": target           # 仅用户消息使用，"red" 或 "blue"
    }
    st.session_state.chat_history.append(message)
    return message


def get_red_context():
    """获取红方上下文（只包含用户对话）"""
    user_messages = [msg for msg in st.session_state.chat_history if msg["role"] == "user"]
    # 过滤出发给红方的用户消息
    red_context = [
        msg for msg in user_messages
        if msg.get("target") == "red" or msg.get("target") is None
    ]
    return red_context


def get_blue_context():
    """获取蓝方上下文（包含完整对话历史）"""
    return st.session_state.chat_history


def get_last_user_message_to_red():
    """获取最后一条发给红方的用户消息"""
    user_messages = [
        msg for msg in st.session_state.chat_history
        if msg["role"] == "user" and msg.get("target") == "red"
    ]
    return user_messages[-1] if user_messages else None


def clear_chat_history():
    """清空对话历史"""
    st.session_state.chat_history = []
    st.session_state.current_round = 0
