"""
语法教练 Agent - 调用 DeepSeek API 分析长难句
（通过统一 AIService 调用）
"""
from config import get_api_key
from services.ai_service import AIService


def _get_service() -> AIService:
    """获取配置好的 AI 服务实例"""
    return AIService(api_key=get_api_key())


def analyze_grammar(text: str) -> list[dict]:
    """
    从英语文章中挑选 1-2 个长难句进行语法分析
    返回 [{"sentence": "原句", "analysis": "详细语法分析"}, ...]
    解析失败时返回空列表
    """
    system_prompt = (
        "你是一名英语语法专家。请从以下英文文章中挑选 1-2 个最复杂的长难句，"
        "对每个句子进行详细的语法分析。"
        "分析内容包括：句子类型（复合句/并列句等）、从句划分、句子成分说明，并用中文解释。"
    )

    user_message = (
        f"请分析以下英语文章中的长难句。\n\n"
        f"请严格按照以下 JSON 数组格式返回，不要添加任何其他文字：\n"
        f'[{{"sentence": "原句", "analysis": "详细语法分析（用中文解释句子类型、从句划分、句子成分等）"}}]\n\n'
        f"{text}"
    )

    ai = _get_service()

    result = ai.chat_json_fallback(system_prompt, user_message, fallback=[])
    if isinstance(result, list):
        return result
    return []
