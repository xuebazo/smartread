"""
翻译官 Agent - 调用 DeepSeek API 进行英语文章逐段翻译
（通过统一 AIService 调用）
"""
from config import get_api_key
from services.ai_service import AIService


def _get_service() -> AIService:
    """获取配置好的 AI 服务实例"""
    return AIService(api_key=get_api_key())


def translate_article(text: str) -> dict:
    """
    将英语文章逐段翻译成中文
    返回 {"paragraphs": [{"original": "...", "translated": "..."}, ...]}
    解析失败时返回 {"raw_translation": "..."} 作为降级处理
    """
    system_prompt = (
        "你是一名专业的英文翻译，请将以下英文文章逐段翻译成中文。"
        "保持原文段落结构，不增删内容，翻译流畅自然。"
    )

    user_message = (
        f"请将以下英文文章逐段翻译成中文。\n\n"
        f"请严格按照以下 JSON 格式返回，不要添加任何其他文字：\n"
        f'{{"paragraphs": [{{"original": "原文段落", "translated": "译文段落"}}, ...]}}\n\n'
        f"{text}"
    )

    ai = _get_service()

    try:
        result = ai.chat_json(system_prompt, user_message)
        return result
    except Exception:
        # JSON 解析失败，降级返回原始文本
        try:
            raw = ai.chat(system_prompt, user_message)
            return {"raw_translation": raw}
        except Exception as e:
            raise RuntimeError(f"翻译 API 调用失败: {str(e)}") from e
