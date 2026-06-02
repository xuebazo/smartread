"""
词汇导师 Agent - 调用 DeepSeek API 提取四六级核心词汇
（通过统一 AIService 调用）
"""
from config import get_api_key
from services.ai_service import AIService


def _get_service() -> AIService:
    """获取配置好的 AI 服务实例"""
    return AIService(api_key=get_api_key())


def extract_vocabulary(text: str) -> list[dict]:
    """
    从英语文章中提取四六级核心词汇
    返回 [{"word": "", "phonetic": "", "meaning": "", "sentence": ""}, ...]
    解析失败时返回空列表
    """
    system_prompt = (
        "你是一名英语词汇教学专家。请扫描以下英语文章，"
        "提取其中符合大学英语四、六级考试难度的核心词汇和短语。"
        "为每个词汇生成以下四个字段："
        "word(词汇本身), phonetic(音标), meaning(在文中的中文释义), sentence(包含该词汇的原文例句)。"
    )

    user_message = (
        f"请从以下英语文章中提取四六级核心词汇。\n\n"
        f"请严格按照以下 JSON 数组格式返回，不要添加任何其他文字：\n"
        f'[{{"word": "example", "phonetic": "/ɪɡˈzæmpəl/", "meaning": "例子", "sentence": "This is an example."}}]\n\n'
        f"{text}"
    )

    ai = _get_service()

    result = ai.chat_json_fallback(system_prompt, user_message, fallback=[])
    if isinstance(result, list):
        return result
    return []
