# coding: utf-8
"""
PrePlay 数据库管理
使用 SQLite 存储训练会话和对话记录
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional


class DatabaseManager:
    """数据库管理类"""

    def __init__(self, db_path: str = "preplay.db"):
        self.db_path = db_path
        self.conn = None
        self._init_db()

    def connect(self):
        """建立数据库连接"""
        if self.conn is None:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # 返回字典格式
        return self.conn

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _init_db(self):
        """初始化数据库表结构"""
        conn = self.connect()
        cursor = conn.cursor()

        # 创建训练会话表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                red_sid TEXT,
                blue_sid TEXT,
                knowledge_file_ids TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 兼容旧数据库：添加 knowledge_file_ids 列表（如果不存在）
        try:
            cursor.execute("ALTER TABLE sessions ADD COLUMN knowledge_file_ids TEXT")
        except sqlite3.OperationalError:
            # 列已存在，忽略
            pass

        # 创建知识库文件表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS knowledge_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT NOT NULL UNIQUE,
                file_name TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER,
                content TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建消息表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                source TEXT,
                content TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
            )
        """)

        # 创建索引，提高查询性能
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_session
            ON messages(session_id)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_timestamp
            ON messages(timestamp)
        """)

        conn.commit()

    # ============================================
    # 会话操作
    # ============================================

    def create_session(self, session_id: str) -> bool:
        """
        创建新的训练会话

        Args:
            session_id: 会话ID，可以是UUID或自定义ID

        Returns:
            是否创建成功
        """
        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO sessions (id) VALUES (?)",
                (session_id,)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # 会话ID已存在
            return False

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
        conn = self.connect()
        cursor = conn.cursor()

        updates = []
        params = []

        if red_sid:
            updates.append("red_sid = ?")
            params.append(red_sid)
        if blue_sid:
            updates.append("blue_sid = ?")
            params.append(blue_sid)

        if not updates:
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(session_id)

        sql = f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?"

        cursor.execute(sql, params)
        conn.commit()
        return cursor.rowcount > 0

    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            会话信息字典，不存在返回None
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM sessions WHERE id = ?",
            (session_id,)
        )

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def list_sessions(self, limit: int = 10) -> List[Dict]:
        """
        列出最近的会话

        Args:
            limit: 返回数量限制

        Returns:
            会话列表
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM sessions ORDER BY created_at DESC LIMIT ?",
            (limit,)
        )

        return [dict(row) for row in cursor.fetchall()]

    def update_session_knowledge_file_ids(self, session_id: str, file_ids: List[str]) -> bool:
        """
        更新会话关联的知识库文件 ID 列表

        Args:
            session_id: 会话ID
            file_ids: 知识库文件 ID 列表

        Returns:
            是否更新成功
        """
        conn = self.connect()
        cursor = conn.cursor()

        # 将列表转换为 JSON 字符串存储
        file_ids_json = json.dumps(file_ids)

        cursor.execute(
            """
            UPDATE sessions
            SET knowledge_file_ids = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (file_ids_json, session_id)
        )
        conn.commit()
        return cursor.rowcount > 0

    def get_session_knowledge_file_ids(self, session_id: str) -> List[str]:
        """
        获取会话关联的知识库文件 ID 列表

        Args:
            session_id: 会话ID

        Returns:
            文件 ID 列表
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT knowledge_file_ids FROM sessions WHERE id = ?",
            (session_id,)
        )

        row = cursor.fetchone()
        if row and row["knowledge_file_ids"]:
            try:
                return json.loads(row["knowledge_file_ids"])
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    # ============================================
    # 消息操作
    # ============================================

    def add_message(self, session_id: str, role: str, content: str, source: str = "", timestamp: str = None) -> int:
        """
        添加一条消息

        Args:
            session_id: 会话ID
            role: 角色 (user/assistant)
            content: 消息内容
            source: 来源 (红/蓝，assistant角色时使用)
            timestamp: 时间戳（可选，不传则使用当前本地时间）

        Returns:
            消息ID
        """
        conn = self.connect()
        cursor = conn.cursor()

        # 使用本地时间而不是 UTC
        if timestamp is None:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute(
            """
            INSERT INTO messages (session_id, role, content, source, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (session_id, role, content, source, timestamp)
        )

        conn.commit()
        return cursor.lastrowid

    def get_messages(self, session_id: str) -> List[Dict]:
        """
        获取会话的所有消息（按时间排序）

        Args:
            session_id: 会话ID

        Returns:
            消息列表
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, session_id, role, source, content, timestamp
            FROM messages
            WHERE session_id = ?
            ORDER BY timestamp ASC
            """,
            (session_id,)
        )

        return [dict(row) for row in cursor.fetchall()]

    def get_messages_for_report(self, session_id: str) -> List[Dict]:
        """
        获取用于生成报告的消息列表（格式化）

        Args:
            session_id: 会话ID

        Returns:
            消息列表，格式与报告生成器兼容
        """
        messages = self.get_messages(session_id)

        # 转换格式
        result = []
        for msg in messages:
            result.append({
                "role": msg["role"],
                "content": msg["content"],
                "source": msg["source"] or "",
                "timestamp": msg["timestamp"]
            })

        return result

    def delete_session(self, session_id: str) -> bool:
        """
        删除会话及其所有消息

        Args:
            session_id: 会话ID

        Returns:
            是否删除成功
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        return cursor.rowcount > 0

    # ============================================
    # 知识库文件管理
    # ============================================

    def add_knowledge_file(self, file_id: str, file_name: str, file_type: str, file_size: int = None, content: str = None) -> int:
        """
        添加知识库文件记录

        Args:
            file_id: 知识库返回的文件ID
            file_name: 文件名
            file_type: 文件类型（txt/docx）
            file_size: 文件大小（字节）
            content: 文件内容

        Returns:
            记录ID
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO knowledge_files (file_id, file_name, file_type, file_size, content)
            VALUES (?, ?, ?, ?, ?)
            """,
            (file_id, file_name, file_type, file_size, content)
        )
        conn.commit()
        return cursor.lastrowid

    def get_knowledge_files(self) -> List[Dict]:
        """
        获取所有知识库文件列表

        Returns:
            文件列表
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, file_id, file_name, file_type, file_size, content, uploaded_at
            FROM knowledge_files
            ORDER BY uploaded_at DESC
            """
        )

        return [dict(row) for row in cursor.fetchall()]

    def delete_knowledge_file(self, file_id: str) -> bool:
        """
        删除知识库文件记录

        Args:
            file_id: 知识库文件ID

        Returns:
            是否删除成功
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM knowledge_files WHERE file_id = ?", (file_id,))
        conn.commit()
        return cursor.rowcount > 0

    def delete_all_knowledge_files(self) -> bool:
        """
        删除所有知识库文件记录

        Returns:
            是否删除成功
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM knowledge_files")
        conn.commit()
        return True

    def get_knowledge_file_by_id(self, file_id: str) -> Optional[Dict]:
        """
        通过file_id获取知识库文件

        Args:
            file_id: 知识库文件ID

        Returns:
            文件信息，不存在返回None
        """
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM knowledge_files WHERE file_id = ?",
            (file_id,)
        )

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    # ============================================
    # 统计信息
    # ============================================

    def get_session_stats(self, session_id: str) -> Dict:
        """
        获取会话统计信息

        Args:
            session_id: 会话ID

        Returns:
            统计信息字典
        """
        conn = self.connect()
        cursor = conn.cursor()

        # 获取消息统计
        cursor.execute(
            """
            SELECT
                role,
                source,
                COUNT(*) as count
            FROM messages
            WHERE session_id = ?
            GROUP BY role, source
            """,
            (session_id,)
        )

        stats = {"total": 0, "user": 0, "assistant": 0, "red": 0, "blue": 0}

        for row in cursor.fetchall():
            role = row["role"]
            source = row["source"]
            count = row["count"]

            stats["total"] += count
            if role == "user":
                stats["user"] += count
            elif role == "assistant":
                stats["assistant"] += count
                if "红" in source:
                    stats["red"] += count
                elif "蓝" in source:
                    stats["blue"] += count

        return stats


# ============================================
# 便捷函数
# ============================================

# 全局数据库实例
_db_manager = None


def get_db(db_path: str = "preplay.db") -> DatabaseManager:
    """
    获取数据库管理器实例（单例模式）

    Args:
        db_path: 数据库文件路径

    Returns:
        DatabaseManager 实例
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(db_path)
    return _db_manager


# 知识库文件管理便捷函数
def add_knowledge_file(file_id: str, file_name: str, file_type: str, file_size: int = None, content: str = None) -> int:
    """添加知识库文件记录"""
    db = get_db()
    return db.add_knowledge_file(file_id, file_name, file_type, file_size, content)


def get_all_knowledge_files() -> List[Dict]:
    """获取所有知识库文件列表"""
    db = get_db()
    return db.get_knowledge_files()


def delete_knowledge_file(file_id: str) -> bool:
    """删除知识库文件记录"""
    db = get_db()
    return db.delete_knowledge_file(file_id)


def delete_all_knowledge_files() -> bool:
    """删除所有知识库文件记录"""
    db = get_db()
    return db.delete_all_knowledge_files()


def get_knowledge_file_by_id(file_id: str) -> Optional[Dict]:
    """通过file_id获取知识库文件"""
    db = get_db()
    return db.get_knowledge_file_by_id(file_id)


if __name__ == '__main__':
    # 测试数据库功能
    db = get_db("test_preplay.db")

    print("=" * 60)
    print("测试数据库功能")
    print("=" * 60)

    # 创建会话
    session_id = "test_session_001"
    print(f"\n1. 创建会话: {session_id}")
    success = db.create_session(session_id)
    print(f"   结果: {'成功' if success else '失败/已存在'}")

    # 更新会话sid
    print("\n2. 更新会话sid")
    db.update_session_sids(session_id, red_sid="red_123", blue_sid="blue_456")
    session = db.get_session(session_id)
    print(f"   会话信息: {session}")

    # 添加消息
    print("\n3. 添加消息")
    db.add_message(session_id, "user", "你好，我想要提高编程能力")
    db.add_message(session_id, "assistant", "多练习，多看代码", source="红方魔鬼导师")
    db.add_message(session_id, "user", "学不会怎么办")
    db.add_message(session_id, "assistant", "保持耐心，慢慢来", source="蓝方心理教练")

    # 查询消息
    print("\n4. 查询消息")
    messages = db.get_messages(session_id)
    for msg in messages:
        role = msg["role"]
        source = msg["source"] or ""
        content = msg["content"][:30] + "..." if len(msg["content"]) > 30 else msg["content"]
        print(f"   [{msg['timestamp']}] {role}({source}): {content}")

    # 获取统计信息
    print("\n5. 统计信息")
    stats = db.get_session_stats(session_id)
    print(f"   {stats}")

    # 获取用于报告的消息
    print("\n6. 用于报告的消息")
    report_messages = db.get_messages_for_report(session_id)
    print(f"   共 {len(report_messages)} 条消息")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

    # 关闭连接
    db.close()

    # 清理测试数据库
    if os.path.exists("test_preplay.db"):
        os.remove("test_preplay.db")
        print("\n已删除测试数据库文件")
