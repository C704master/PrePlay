# coding: utf-8
"""
PrePlay 配置管理
从 .env 文件读取所有配置
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


# ============================================
# 讯飞星火红方魔鬼导师配置
# ============================================
XUNFEI_RED_WS_URL = os.getenv("XUNFEI_RED_WS_URL")
XUNFEI_RED_APP_ID = os.getenv("XUNFEI_RED_APP_ID")
XUNFEI_RED_API_SECRET = os.getenv("XUNFEI_RED_API_SECRET")
XUNFEI_RED_API_KEY = os.getenv("XUNFEI_RED_API_KEY")

RED_CONFIG = {
    "ws_url": XUNFEI_RED_WS_URL,
    "app_id": XUNFEI_RED_APP_ID,
    "api_secret": XUNFEI_RED_API_SECRET,
    "api_key": XUNFEI_RED_API_KEY
}

# ============================================
# 讯飞星火蓝方心理教练配置
# ============================================
XUNFEI_BLUE_WS_URL = os.getenv("XUNFEI_BLUE_WS_URL")
XUNFEI_BLUE_APP_ID = os.getenv("XUNFEI_BLUE_APP_ID")
XUNFEI_BLUE_API_SECRET = os.getenv("XUNFEI_BLUE_API_SECRET")
XUNFEI_BLUE_API_KEY = os.getenv("XUNFEI_BLUE_API_KEY")

BLUE_CONFIG = {
    "ws_url": XUNFEI_BLUE_WS_URL,
    "app_id": XUNFEI_BLUE_APP_ID,
    "api_secret": XUNFEI_BLUE_API_SECRET,
    "api_key": XUNFEI_BLUE_API_KEY
}

# ============================================
# Moonshot (Kimi) 报告生成配置
# ============================================
MOONSHOT_API_KEY = os.getenv("MOONSHOT_API_KEY")
MOONSHOT_API_URL = os.getenv("MOONSHOT_API_URL")
MOONSHOT_MODEL = os.getenv("MOONSHOT_MODEL")

MOONSHOT_CONFIG = {
    "api_key": MOONSHOT_API_KEY,
    "base_url": MOONSHOT_API_URL,
    "model": MOONSHOT_MODEL
}

# ============================================
# 数据库配置
# ============================================
DATABASE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "preplay.db"
)

# ============================================
# 讯飞星火知识库配置
# ============================================
CHATDOC_APP_ID = os.getenv("CHATDOC_APP_ID")
CHATDOC_API_SECRET = os.getenv("CHATDOC_API_SECRET")
CHATDOC_BASE_URL = os.getenv("CHATDOC_BASE_URL", "https://chatdoc.xfyun.cn")
CHATDOC_WS_URL = os.getenv("CHATDOC_WS_URL", "wss://chatdoc.xfyun.cn/openapi/chat")

CHATDOC_CONFIG = {
    "app_id": CHATDOC_APP_ID,
    "api_secret": CHATDOC_API_SECRET,
    "base_url": CHATDOC_BASE_URL,
    "ws_url": CHATDOC_WS_URL
}
