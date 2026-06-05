"""
翻译官 Agent - 调用 DeepSeek API 进行英语文章逐段翻译
（通过统一 AIService 调用）

支持长文章自动分段翻译，避免 API 输出截断导致乱码
"""
import json
import re
from config import get_api_key
from services.ai_service import AIService

# 分段阈值：超过此字符数的文章将被分段翻译
CHUNK_THRESHOLD = 1500
# 每段最大字符数（按段落边界分割）
MAX_CHUNK_SIZE = 1200


def _get_service() -> AIService:
    """获取配置好的 AI 服务实例"""
    return AIService(api_key=get_api_key())


def _split_into_chunks(text: str) -> list[str]:
    """
    将长文章按段落边界分割成多个块
    每块不超过 MAX_CHUNK_SIZE 字符
    """
    # 按双换行分割段落
    paragraphs = re.split(r'\n\s*\n', text.strip())
    
    chunks = []
    current_chunk = []
    current_size = 0
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        para_size = len(para)
        
        # 如果单个段落就超过最大限制，按句子分割
        if para_size > MAX_CHUNK_SIZE:
            # 先保存当前块
            if current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
            
            # 按句子分割长段落
            sentences = re.split(r'(?<=[.!?])\s+', para)
            sub_chunk = []
            sub_size = 0
            for sent in sentences:
                if sub_size + len(sent) > MAX_CHUNK_SIZE and sub_chunk:
                    chunks.append(' '.join(sub_chunk))
                    sub_chunk = []
                    sub_size = 0
                sub_chunk.append(sent)
                sub_size += len(sent) + 1
            if sub_chunk:
                chunks.append(' '.join(sub_chunk))
            continue
        
        # 检查是否需要开始新块
        if current_size + para_size > MAX_CHUNK_SIZE and current_chunk:
            chunks.append('\n\n'.join(current_chunk))
            current_chunk = []
            current_size = 0
        
        current_chunk.append(para)
        current_size += para_size + 2  # +2 for \n\n
    
    # 保存最后一块
    if current_chunk:
        chunks.append('\n\n'.join(current_chunk))
    
    return chunks


def _translate_single_chunk(ai: AIService, text: str) -> dict:
    """
    翻译单个文本块，返回解析后的 JSON
    包含增强的容错处理
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

    try:
        content = ai.chat(system_prompt, user_message, max_tokens=8192)
    except Exception as e:
        raise RuntimeError(f"翻译 API 调用失败: {str(e)}") from e

    # JSON 解析失败时自动降级为原始文本，不重复调用 API
    return _parse_translation_json(content)


def _parse_translation_json(content: str) -> dict:
    """
    解析翻译结果 JSON，处理各种格式异常
    """
    # 移除 markdown 代码块标记
    content = content.strip()
    if content.startswith("```"):
        lines = content.split("\n")
        # 找到结束的 ```
        end_idx = len(lines) - 1
        while end_idx > 0 and not lines[end_idx].strip().startswith("```"):
            end_idx -= 1
        content = "\n".join(lines[1:end_idx])
    
    # 尝试直接解析
    try:
        result = json.loads(content)
        if isinstance(result, dict) and "paragraphs" in result:
            return result
    except json.JSONDecodeError:
        pass
    
    # 尝试修复常见 JSON 问题
    # 1. 移除可能的尾部逗号
    content = re.sub(r',\s*}', '}', content)
    content = re.sub(r',\s*]', ']', content)
    
    # 2. 尝试提取 JSON 对象
    json_match = re.search(r'\{[\s\S]*"paragraphs"[\s\S]*\}', content)
    if json_match:
        try:
            result = json.loads(json_match.group())
            if isinstance(result, dict) and "paragraphs" in result:
                return result
        except json.JSONDecodeError:
            pass
    
    # 3. 如果无法解析为 JSON，返回原始内容
    return {"raw_translation": content}


def _merge_chunk_results(results: list[dict]) -> dict:
    """
    合并多个分段翻译结果
    """
    all_paragraphs = []
    raw_translations = []
    
    for result in results:
        if "paragraphs" in result:
            all_paragraphs.extend(result["paragraphs"])
        elif "raw_translation" in result:
            raw_translations.append(result["raw_translation"])
    
    # 优先返回结构化结果
    if all_paragraphs:
        return {"paragraphs": all_paragraphs}
    
    # 降级返回原始翻译
    if raw_translations:
        return {"raw_translation": "\n\n---\n\n".join(raw_translations)}
    
    return {"paragraphs": []}


def translate_article(text: str) -> dict:
    """
    将英语文章逐段翻译成中文
    
    支持长文章自动分段翻译，避免 API 输出截断导致乱码
    返回 {"paragraphs": [{"original": "...", "translated": "..."}, ...]}
    解析失败时返回 {"raw_translation": "..."} 作为降级处理
    """
    if not text or not text.strip():
        return {"paragraphs": []}
    
    ai = _get_service()
    
    # 短文章直接翻译
    if len(text) <= CHUNK_THRESHOLD:
        try:
            return _translate_single_chunk(ai, text)
        except Exception as e:
            raise RuntimeError(f"翻译 API 调用失败: {str(e)}") from e
    
    # 长文章分段翻译
    chunks = _split_into_chunks(text)
    
    if len(chunks) <= 1:
        # 分段后仍然只有一块，直接翻译
        try:
            return _translate_single_chunk(ai, chunks[0])
        except Exception as e:
            raise RuntimeError(f"翻译 API 调用失败: {str(e)}") from e
    
    # 多块翻译
    results = []
    errors = []
    
    for i, chunk in enumerate(chunks):
        try:
            result = _translate_single_chunk(ai, chunk)
            results.append(result)
        except Exception as e:
            errors.append(f"第{i+1}段翻译失败: {str(e)}")
            # 继续翻译其他段落，不中断
    
    if not results:
        # 所有段落都失败
        raise RuntimeError(f"翻译失败: {'; '.join(errors)}")
    
    # 合并结果
    merged = _merge_chunk_results(results)
    
    # 如果有部分失败，添加警告信息
    if errors:
        merged["_warnings"] = errors
    
    return merged
