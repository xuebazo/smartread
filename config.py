r"""
SmartRead 配置模块 - API Key 管理
从 D:\smartread\.env 文件加载 DeepSeek API 密钥
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
_ENV_PATH = Path(__file__).parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)
else:
    load_dotenv()  # 降级尝试默认路径


def get_api_key() -> str:
    """
    获取 DeepSeek API Key
    优先从环境变量读取，未配置时抛出明确错误提示
    """
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise RuntimeError(
            "未找到 DEEPSEEK_API_KEY，请在 D:\\smartread\\.env 文件中配置后重试。\n"
            "示例内容：DEEPSEEK_API_KEY=sk-your-key-here"
        )
    return api_key
