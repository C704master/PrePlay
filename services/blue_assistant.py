# coding: utf-8
"""
蓝方心理教练服务
"""
import _thread as thread
import base64
import hashlib
import hmac
import json
import ssl
from datetime import datetime
from time import mktime
from urllib.parse import urlparse, urlencode
from wsgiref.handlers import format_date_time
import websocket
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import BLUE_CONFIG


class WsParam:
    """WebSocket 鉴权参数生成"""
    def __init__(self, APPID, APIKey, APISecret, Assistant_url):
        self.APPID = APPID
        self.APIKey = APIKey
        self.APISecret = APISecret
        self.host = urlparse(Assistant_url).netloc
        self.path = urlparse(Assistant_url).path
        self.Assistant_url = Assistant_url

    def create_url(self):
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        signature_sha = hmac.new(self.APISecret.encode('utf-8'), signature_origin.encode('utf-8'),
                                 digestmod=hashlib.sha256).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding='utf-8')

        authorization_origin = f'api_key="{self.APIKey}", algorithm="hmac-sha256", headers="host date request-line", signature="{signature_sha_base64}"'

        authorization = base64.b64encode(authorization_origin.encode('utf-8')).decode(encoding='utf-8')

        v = {
            "authorization": authorization,
            "date": date,
            "host": self.host
        }
        url = self.Assistant_url + '?' + urlencode(v)
        return url


class BlueAssistant:
    """蓝方心理教练客户端"""

    def __init__(self, config=None):
        self.config = config or BLUE_CONFIG
        self.ws_url = self.config["ws_url"]
        self.app_id = self.config["app_id"]
        self.api_secret = self.config["api_secret"]
        self.api_key = self.config["api_key"]
        self.sid = ""
        self.answer = ""
        self.ws = None

    def _gen_params(self, question, chat_history=None):
        """生成助手API请求参数"""
        messages = []
        if chat_history:
            messages.extend(chat_history)

        messages.append({"role": "user", "content": question})

        data = {
            "header": {
                "app_id": self.app_id,
                "uid": "user123"
            },
            "parameter": {
                "chat": {
                    "domain": "generalv3.5",
                    "temperature": 0.7,
                    "max_tokens": 2048,
                    "top_k": 5
                }
            },
            "payload": {
                "message": {
                    "text": messages
                }
            }
        }
        return data

    def _on_message(self, ws, message):
        """收到websocket消息的处理"""
        data = json.loads(message)

        code = data['header']['code']
        if code != 0:
            print(f'蓝方请求错误: {code}, {data}')
            ws.close()
            return

        if 'sid' in data['header']:
            self.sid = data['header']['sid']

        choices = data["payload"]["choices"]
        status = choices["status"]
        content = choices["text"][0]["content"]

        print(content, end="")
        self.answer += content

        if status == 2:
            ws.close()

    def _on_error(self, ws, error):
        """收到websocket错误的处理"""
        print(f"蓝方错误: {error}")

    def _on_close(self, ws, one, two):
        """收到websocket关闭的处理"""
        pass

    def _on_open(self, ws):
        """收到websocket连接建立的处理"""
        thread.start_new_thread(self._run, (ws,))

    def _run(self, ws):
        """发送消息"""
        data = json.dumps(self._gen_params(ws.question, ws.chat_history))
        ws.send(data)

    def chat(self, question, chat_history=None):
        """
        与蓝方对话一次

        Args:
            question: 用户问题
            chat_history: 对话历史（可选）

        Returns:
            (answer, sid): 回答内容和会话ID
        """
        wsParam = WsParam(
            self.app_id,
            self.api_key,
            self.api_secret,
            self.ws_url
        )
        wsUrl = wsParam.create_url()

        self.answer = ""

        websocket.enableTrace(False)
        ws = websocket.WebSocketApp(
            wsUrl,
            on_message=self._on_message,
            on_error=self._on_error,
            on_close=self._on_close,
            on_open=self._on_open
        )

        ws.question = question
        ws.chat_history = chat_history

        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})

        return self.answer, self.sid


# 全局实例
_blue_assistant = None


def get_blue_assistant():
    """获取蓝方实例（单例）"""
    global _blue_assistant
    if _blue_assistant is None:
        _blue_assistant = BlueAssistant()
    return _blue_assistant


def chat_with_blue(question, chat_history=None):
    """
    与蓝方心理教练对话一次

    Args:
        question: 用户问题
        chat_history: 对话历史（可选）

    Returns:
        (answer, sid): 回答内容和会话ID
    """
    assistant = get_blue_assistant()
    return assistant.chat(question, chat_history)
