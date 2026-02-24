# coding: utf-8
"""
KIMI 报告生成服务
"""
import requests
from typing import List
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import MOONSHOT_CONFIG


class ReportGenerator:
    """使用 Moonshot (KIMI) 生成训练报告"""

    def __init__(self, config=None):
        self.config = config or MOONSHOT_CONFIG
        self.api_key = self.config["api_key"]
        self.base_url = self.config["base_url"]
        self.model = self.config["model"]

    def generate(self, conversation: List[dict]) -> str:
        """
        生成 Markdown 格式的训练报告

        Args:
            conversation: 对话历史列表

        Returns:
            markdown 格式的报告
        """
        prompt = self._build_prompt(conversation)

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": """你是 PrePlay 专业的训练报告生成助手。你的职责是分析用户与红方魔鬼导师、蓝方心理教练的完整对话，生成一份结构清晰、有指导意义的训练报告。请严格按照以下结构生成 Markdown 格式的报告：

# PrePlay 训练报告

生成时间：[当前时间]

## 📈 训练摘要

[统计数据的 Markdown 列表]

## ⚠️ 发现的问题

[分析对话中发现的主要问题，按类别分组]

## 💡 改进建议

[针对问题给出具体的改进建议]

## 🌟 鼓励与肯定

[正面的鼓励语言，2-3 句话]"""
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.6,
                    "max_tokens": 4000
                },
                timeout=60
            )

            response.raise_for_status()

            markdown = response.json()["choices"][0]["message"]["content"]
            return markdown

        except requests.exceptions.RequestException as e:
            print(f"报告生成失败: {str(e)}")
            raise Exception(f"无法生成报告: {str(e)}")

    def _build_prompt(self, conversation: List[dict]) -> str:
        """构建报告生成的提示词"""
        total = len(conversation)
        user_count = len([m for m in conversation if m["role"] == "user"])
        assistant_count = len([m for m in conversation if m["role"] == "assistant"])

        stats = f"""
- 总消息数：{total}
- 用户提问：{user_count} 次
- 智能体回复：{assistant_count} 次
"""

        formatted_conv = []
        for msg in conversation:
            role_map = {"user": "你", "assistant": "AI回复"}
            role = role_map.get(msg.get("role", "user"), "AI")
            source = msg.get("source", "")
            if source:
                role = f"{role}({source})"

            timestamp = msg.get("timestamp", "")
            formatted_conv.append(f"[{timestamp}] {role}: {msg.get('content', '')}")

        conv_text = "\n\n".join(formatted_conv)

        return f"""
以下是对话内容：

{conv_text}

{stats}

请严格按照要求的结构生成报告。
"""


# 全局实例
_report_generator = None


def get_report_generator():
    """获取报告生成器实例（单例）"""
    global _report_generator
    if _report_generator is None:
        _report_generator = ReportGenerator()
    return _report_generator


def generate_report(conversation: List[dict]) -> str:
    """
    生成训练报告

    Args:
        conversation: 对话历史列表

    Returns:
        markdown 格式的报告
    """
    generator = get_report_generator()
    return generator.generate(conversation)
