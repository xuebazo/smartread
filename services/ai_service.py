"""
统一 AI Service — 封装 DeepSeek API 调用
所有 Agent 通过此服务调用，不再直接 requests.post()
"""
import json
import requests
from dataclasses import dataclass, field
from typing import Any

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TIMEOUT = 60
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 4096


@dataclass
class AIService:
    """统一 AI 调用服务"""

    api_key: str
    model: str = DEFAULT_MODEL
    temperature: float = DEFAULT_TEMPERATURE
    max_tokens: int = DEFAULT_MAX_TOKENS
    timeout: int = DEFAULT_TIMEOUT
    base_url: str = DEEPSEEK_API_URL

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
    ) -> str:
        """
        发送 Chat Completions 请求，返回模型响应原文
        """
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens if max_tokens is not None else self.max_tokens,
        }

        response = requests.post(
            self.base_url,
            headers=self._headers,
            json=payload,
            timeout=timeout if timeout is not None else self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()

    def chat_json(
        self,
        system_prompt: str,
        user_message: str,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
    ) -> Any:
        """
        发送请求并尝试解析 JSON 响应
        自动处理 markdown 代码块包裹
        """
        content = self.chat(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=temperature,
            max_tokens=max_tokens,
            timeout=timeout,
        )
        return _parse_json_content(content)

    def chat_json_fallback(
        self,
        system_prompt: str,
        user_message: str,
        fallback: Any,
        *,
        temperature: float | None = None,
        max_tokens: int | None = None,
        timeout: int | None = None,
    ) -> Any:
        """
        发送请求并解析 JSON，失败时返回 fallback
        """
        try:
            content = self.chat(
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout,
            )
            return _parse_json_content(content)
        except (json.JSONDecodeError, requests.exceptions.RequestException, KeyError, IndexError):
            return fallback


def _parse_json_content(content: str) -> Any:
    """解析 LLM 返回的 JSON 内容，自动处理 markdown 代码块"""
    if content.startswith("```"):
        lines = content.split("\n")
        content = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else content
    return json.loads(content)
