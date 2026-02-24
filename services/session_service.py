# coding: utf-8
"""
训练会话管理服务
处理会话创建、消息保存、数据查询
"""
import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional
from database import DatabaseManager, get_db


class SessionService:
    """训练会话服务"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            import os
            # 使用项目根目录下的数据库文件
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(project_root, "preplay.db")
        self.db = get_db(db_path)

    def create_session(self) -> str:
        """
        创建新的训练会话

        Returns:
            session_id: 会话ID
        """
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        success = self.db.create_session(session_id)

        if not success:
            # 如果失败，再试一次
            session_id = f"session_{uuid.uuid4().hex[:12]}"
            self.db.create_session(session_id)

        return session_id

    def save_message(self, session_id: str, role: str, content: str, source: str = "", timestamp: str = None) -> int:
        """
        保存一条消息

        Args:
            session_id: 会话ID
            role: 角色 (user/assistant)
            content: 消息内容
            source: 来源 (红/蓝，assistant角色时使用)
            timestamp: 时间戳（可选）

        Returns:
            消息ID
        """
        return self.db.add_message(session_id, role, content, source, timestamp)

    def get_messages(self, session_id: str) -> List[Dict]:
        """
        获取会话的所有消息

        Args:
            session_id: 会话ID

        Returns:
            消息列表
        """
        return self.db.get_messages(session_id)

    def get_messages_for_report(self, session_id: str) -> List[Dict]:
        """
        获取用于生成报告的消息列表（格式化）

        Args:
            session_id: 会话ID

        Returns:
            格式化后的消息列表
        """
        return self.db.get_messages_for_report(session_id)

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            会话信息字典
        """
        return self.db.get_session(session_id)

    def update_session_sids(self, session_id: str, red_sid: str = None, blue_sid: str = None) -> bool:
        """
        更新会话的红/蓝方sid

        Args:
            session_id: 会话ID
            red_sid: 红方会话ID（可选）
            blue_sid: 蓝方会话ID（可选）

        Returns:
            是否更新成功
        """
        return self.db.update_session_sids(session_id, red_sid, blue_sid)

    def get_session_stats(self, session_id: str) -> Dict:
        """
        获取会话统计信息

        Args:
            session_id: 会话ID

        Returns:
            统计信息字典
        """
        return self.db.get_session_stats(session_id)

    def list_sessions(self, limit: int = 10) -> List[Dict]:
        """
        列出最近的会话

        Args:
            limit: 返回数量限制

        Returns:
            会话列表
        """
        return self.db.list_sessions(limit)

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话及其所有消息

        Args:
            session_id: 会话ID

        Returns:
            是否删除成功
        """
        return self.db.delete_session(session_id)

    # ============================================
    # 知识库文件管理
    # ============================================

    def update_knowledge_file_ids(self, session_id: str, file_ids: List[str]) -> bool:
        """
        更新会话关联的知识库文件 ID 列表

        Args:
            session_id: 会话ID
            file_ids: 知识库文件 ID 列表

        Returns:
            是否更新成功
        """
        return self.db.update_session_knowledge_file_ids(session_id, file_ids)

    def get_knowledge_file_ids(self, session_id: str) -> List[str]:
        """
        获取会话关联的知识库文件 ID 列表

        Args:
            session_id: 会话ID

        Returns:
            文件 ID 列表
        """
        return self.db.get_session_knowledge_file_ids(session_id)

    def add_knowledge_file_id(self, session_id: str, file_id: str) -> bool:
        """
        向会话添加一个知识库文件 ID

        Args:
            session_id: 会话ID
            file_id: 知识库文件 ID

        Returns:
            是否更新成功
        """
        existing_ids = self.get_knowledge_file_ids(session_id)
        if file_id not in existing_ids:
            existing_ids.append(file_id)
            return self.update_knowledge_file_ids(session_id, existing_ids)
        return True


# 全局实例
_session_service = None


def get_session_service(db_path: str = "preplay.db") -> SessionService:
    """获取会话服务实例（单例）"""
    global _session_service
    if _session_service is None:
        _session_service = SessionService(db_path)
    return _session_service


# 便捷函数
def create_training_session() -> str:
    """创建新的训练会话"""
    service = get_session_service()
    return service.create_session()


def save_training_message(session_id: str, role: str, content: str, source: str = "", timestamp: str = None) -> int:
    """保存训练消息"""
    service = get_session_service()
    return service.save_message(session_id, role, content, source, timestamp)


def get_training_messages(session_id: str) -> List[Dict]:
    """获取训练消息"""
    service = get_session_service()
    return service.get_messages(session_id)


def get_training_stats(session_id: str) -> Dict:
    """获取训练统计"""
    service = get_session_service()
    return service.get_session_stats(session_id)


def get_report_data(session_id: str) -> List[Dict]:
    """获取报告数据"""
    service = get_session_service()
    return service.get_messages_for_report(session_id)

# 知识库文件管理便捷函数
def update_session_knowledge_file_ids(session_id: str, file_ids: List[str]) -> bool:
    """更新会话关联的知识库文件 ID 列表"""
    service = get_session_service()
    return service.update_knowledge_file_ids(session_id, file_ids)


def get_session_knowledge_file_ids(session_id: str) -> List[str]:
    """获取会话关联的知识库文件 ID 列表"""
    service = get_session_service()
    return service.get_knowledge_file_ids(session_id)


def add_session_knowledge_file_id(session_id: str, file_id: str) -> bool:
    """向会话添加一个知识库文件 ID"""
    service = get_session_service()
    return service.add_knowledge_file_id(session_id, file_id)
