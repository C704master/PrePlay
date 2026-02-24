# coding: utf-8
"""
讯飞星火知识库服务
封装文档上传、删除、列表查询、检索功能
"""
import hashlib
import hmac
import base64
import time
import json
import sys
import os
import _thread as thread
import ssl
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import CHATDOC_CONFIG
import requests
import websocket


class ChatDocAuth:
    """ChatDoc 认证类"""

    def __init__(self, app_id, api_secret):
        self.app_id = app_id
        self.api_secret = api_secret

    def get_signature(self, timestamp=None):
        """
        生成签名

        Args:
            timestamp: 时间戳，不传则使用当前时间

        Returns:
            signature: 签名字符串
        """
        if timestamp is None:
            timestamp = str(int(time.time()))

        # MD5(APPID + timestamp)
        m2 = hashlib.md5()
        data = bytes(self.app_id + timestamp, encoding="utf-8")
        m2.update(data)
        check_sum = m2.hexdigest()

        # HMAC-SHA1
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            check_sum.encode('utf-8'),
            digestmod=hashlib.sha1
        ).digest()

        # Base64 编码
        return base64.b64encode(signature).decode(encoding='utf-8')

    def get_headers(self, timestamp=None, content_type="application/json"):
        """
        获取请求头

        Args:
            timestamp: 时间戳
            content_type: Content-Type

        Returns:
            请求头字典
        """
        if timestamp is None:
            timestamp = str(int(time.time()))

        signature = self.get_signature(timestamp)

        headers = {
            "appId": self.app_id,
            "timestamp": timestamp,
            "signature": signature
        }

        if content_type:
            headers["Content-Type"] = content_type

        return headers


class KnowledgeService:
    """知识库服务类"""

    def __init__(self, config=None):
        self.config = config or CHATDOC_CONFIG
        self.app_id = self.config["app_id"]
        self.api_secret = self.config["api_secret"]
        self.base_url = self.config["base_url"]
        self.ws_url = self.config["ws_url"]
        self.auth = ChatDocAuth(self.app_id, self.api_secret)

    # ============================================
    # 1. 上传文档
    # ============================================

    def upload_document(self, file_path, file_name=None, file_type="wiki"):
        """
        上传文档到知识库

        Args:
            file_path: 本地文件路径
            file_name: 文件名（可选，默认使用原文件名）
            file_type: 文件类型，默认为 "wiki"

        Returns:
            dict: 包含 fileId, sid 等信息
        """
        timestamp = str(int(time.time()))
        headers = self.auth.get_headers(timestamp, None)  # multipart 不设置 Content-Type

        url = f"{self.base_url}/openapi/v1/file/upload"

        if file_name is None:
            file_name = os.path.basename(file_path)

        # 构建 multipart/form-data
        files = {'file': open(file_path, 'rb')}
        data = {
            "fileName": file_name,
            "fileType": file_type,
        }

        try:
            response = requests.post(url, files=files, data=data, headers=headers)
            response.raise_for_status()

            result = response.json()

            if result.get("code") == 0:
                return {
                    "success": True,
                    "file_id": result.get("data", {}).get("fileId"),
                    "sid": result.get("sid"),
                    "file_name": file_name,
                    "raw": result
                }
            else:
                return {
                    "success": False,
                    "error": result.get("desc", "上传失败"),
                    "code": result.get("code"),
                    "raw": result
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }

    # ============================================
    # 2. 删除文档
    # ============================================

    def delete_document(self, file_ids):
        """
        删除文档

        Args:
            file_ids: 文件ID或文件ID列表（支持单个字符串或列表）

        Returns:
            dict: 删除结果
        """
        timestamp = str(int(time.time()))
        headers = self.auth.get_headers(timestamp, None)  # form-data 不设置 Content-Type

        url = f"{self.base_url}/openapi/v1/file/del"

        # 统一处理 file_ids 格式
        if isinstance(file_ids, list):
            file_ids_str = ",".join(file_ids)
        else:
            file_ids_str = str(file_ids)

        data = {"fileIds": file_ids_str}

        try:
            response = requests.post(url, data=data, headers=headers)
            response.raise_for_status()

            result = response.json()

            if result.get("code") == 0:
                return {
                    "success": True,
                    "sid": result.get("sid"),
                    "raw": result
                }
            else:
                return {
                    "success": False,
                    "error": result.get("desc", "删除失败"),
                    "code": result.get("code"),
                    "raw": result
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }

    # ============================================
    # 3. 获取文档列表
    # ============================================

    def get_document_list(self, file_name=None, ext_name=None, current_page=1, page_size=10):
        """
        获取文档列表

        Args:
            file_name: 文件名称模糊查询（可选）
            ext_name: 文件后缀（可选）
            current_page: 页码，默认1
            page_size: 每页数量，默认10

        Returns:
            dict: 包含文档列表和总数
        """
        timestamp = str(int(time.time()))
        headers = self.auth.get_headers(timestamp, "application/json")

        url = f"{self.base_url}/openapi/v1/file/list"

        data = {
            "currentPage": current_page,
            "pageSize": page_size
        }

        if file_name:
            data["fileName"] = file_name
        if ext_name:
            data["extName"] = ext_name

        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            result = response.json()

            if result.get("code") == 0:
                data_obj = result.get("data", {})
                return {
                    "success": True,
                    "total": data_obj.get("total", 0),
                    "files": data_obj.get("rows", []),
                    "sid": result.get("sid"),
                    "raw": result
                }
            else:
                return {
                    "success": False,
                    "error": result.get("desc", "获取列表失败"),
                    "code": result.get("code"),
                    "raw": result
                }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": str(e)
            }

    # ============================================
    # 4. 检索文档（问答）
    # ============================================

    def search_document(self, file_ids, question, messages=None, wiki_filter_score=0.83, temperature=0.5):
        """
        检索文档并进行问答

        Args:
            file_ids: 文件ID或文件ID列表
            question: 用户问题
            messages: 对话历史（可选）
            wiki_filter_score: 检索过滤分数，默认0.83
            temperature: 温度参数，默认0.5

        Returns:
            str: AI 回答内容
        """
        timestamp = str(int(time.time()))
        signature = self.auth.get_signature(timestamp)

        # 构建 WebSocket URL
        ws_url = f"{self.ws_url}?appId={self.app_id}&timestamp={timestamp}&signature={signature}"

        # 统一处理 file_ids 格式
        if isinstance(file_ids, list):
            file_ids_list = file_ids
        else:
            file_ids_list = [file_ids]

        # 构建请求体
        body = {
            "chatExtends": {
                "wikiPromptTpl": "请将以下内容作为已知信息：\n<wikicontent>\n请根据以上内容回答用户的问题。\n问题:<wikiquestion>\n回答:",
                "wikiFilterScore": wiki_filter_score,
                "temperature": temperature
            },
            "fileIds": file_ids_list,
            "messages": []
        }

        # 添加问题到消息列表
        body["messages"].append({
            "role": "user",
            "content": question
        })

        # 如果有历史消息，添加到前面
        if messages:
            for msg in messages:
                body["messages"].insert(0, msg)

        # WebSocket 调用
        answer = []

        def on_message(ws, message):
            data = json.loads(message)
            code = data.get('code')
            if code != 0:
                print(f'请求错误: {code}, {data}')
                ws.close()
                return

            content = data.get("content", "")
            status = data.get("status", 0)

            if content:
                answer.append(content)
                print(content, end='')

            if status == 2:  # 结束
                ws.close()

        def on_error(ws, error):
            print(f"WebSocket 错误: {error}")

        def on_close(ws, *args):
            pass

        def on_open(ws):
            thread.start_new_thread(_send_request, (ws, body))

        def _send_request(ws, data):
            ws.send(json.dumps(data))

        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(
            ws_url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )

        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        return "".join(answer)


# 全局实例
_knowledge_service = None


def get_knowledge_service():
    """获取知识库服务实例（单例）"""
    global _knowledge_service
    if _knowledge_service is None:
        _knowledge_service = KnowledgeService()
    return _knowledge_service


# 便捷函数
def upload_document(file_path, file_name=None, file_type="wiki"):
    """上传文档"""
    service = get_knowledge_service()
    return service.upload_document(file_path, file_name, file_type)


def delete_document(file_ids):
    """删除文档"""
    service = get_knowledge_service()
    return service.delete_document(file_ids)


def get_document_list(file_name=None, ext_name=None, current_page=1, page_size=10):
    """获取文档列表"""
    service = get_knowledge_service()
    return service.get_document_list(file_name, ext_name, current_page, page_size)


def search_document(file_ids, question, messages=None, wiki_filter_score=0.83, temperature=0.5):
    """检索文档"""
    service = get_knowledge_service()
    return service.search_document(file_ids, question, messages, wiki_filter_score, temperature)
