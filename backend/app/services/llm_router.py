"""LLM Router — 统一调用 DeepSeek / OpenAI / Claude

封装目标：
- 统一 chat_completion 接口
- 强制 JSON 模式（response_format={"type": "json_object"}）
- 3 次重试 + 指数退避
- 失败时返回结构化错误，不抛异常到上层
"""

import json
import logging
import time
from typing import Any, Dict, List, Optional
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


class LLMRouter:
    """LLM 统一路由

    使用示例：
        llm = LLMRouter()
        result = llm.chat([
            {"role": "system", "content": "你是一个分析师"},
            {"role": "user", "content": "分析这只股票"},
        ])
    """

    def __init__(self) -> None:
        self._provider = "deepseek"
        self._api_key = settings.deepseek_api_key
        self._model = settings.deepseek_model
        self._base_url = "https://api.deepseek.com/v1"

        # 备选 provider
        if not self._api_key and settings.openai_api_key:
            self._provider = "openai"
            self._api_key = settings.openai_api_key
            self._model = "gpt-4o"
            self._base_url = "https://api.openai.com/v1"
        elif not self._api_key and settings.anthropic_api_key:
            self._provider = "anthropic"
            self._api_key = settings.anthropic_api_key
            self._model = "claude-3-sonnet-20240229"
            self._base_url = "https://api.anthropic.com/v1"

        if not self._api_key:
            raise ValueError("未配置任何 LLM API Key（DEEPSEEK_API_KEY / OPENAI_API_KEY / ANTHROPIC_API_KEY）")

        self._client = httpx.Client(timeout=60.0)
        logger.info("LLMRouter initialized: provider=%s model=%s", self._provider, self._model)

    def _request(self, messages: List[Dict[str, str]], temperature: float = 0.7, response_format: Optional[Dict[str, str]] = None) -> str:
        """单次 HTTP 请求"""
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        payload: Dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            payload["response_format"] = response_format

        url = f"{self._base_url}/chat/completions"
        resp = self._client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
        return content.strip()

    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.7, force_json: bool = True, max_retries: int = 3) -> Dict[str, Any]:
        """带重试的 chat 接口，返回 JSON 对象

        Args:
            messages: OpenAI 格式的消息列表
            temperature: 随机性（0-2）
            force_json: 是否强制 JSON 模式
            max_retries: 最大重试次数

        Returns:
            解析后的 JSON 字典，或包含 error 字段的错误字典
        """
        response_format = {"type": "json_object"} if force_json else None

        for attempt in range(max_retries):
            try:
                logger.info("[LLM] call %s attempt %d/%d", self._model, attempt + 1, max_retries)
                content = self._request(messages, temperature, response_format)
                result = json.loads(content)
                logger.info("[LLM] success")
                return result
            except httpx.HTTPStatusError as e:
                wait = 2 ** attempt
                logger.warning("[LLM] HTTP %d: %s, retrying in %ds", e.response.status_code, e, wait)
                if attempt < max_retries - 1:
                    time.sleep(wait)
                else:
                    return {"error": f"HTTP {e.response.status_code}", "detail": str(e)}
            except json.JSONDecodeError as e:
                logger.error("[LLM] JSON decode failed: %s", e)
                return {"error": "JSON decode failed", "raw_content": content, "detail": str(e)}
            except Exception as e:
                logger.error("[LLM] unexpected error: %s", e)
                return {"error": "unexpected", "detail": str(e)}

        return {"error": "max_retries_exceeded"}
