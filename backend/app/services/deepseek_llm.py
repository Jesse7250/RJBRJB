"""DeepSeek API 封装（OpenAI 兼容协议）

使用 httpx 直接调用，无需 openai 官方库，兼容 Python 3.13+。
支持：
1. 同步/异步非流式调用
2. 同步/异步流式调用（SSE）
3. 多轮对话上下文

文档参考：https://platform.deepseek.com/api-docs/
"""
import json
from typing import AsyncIterator, Iterator, List

import httpx

from app.core.config import get_settings


class DeepSeekMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class DeepSeekLLM:
    """DeepSeek 大模型封装"""

    # 默认使用 DeepSeek-V3， reasoning 任务可换 deepseek-reasoner
    DEFAULT_MODEL = "deepseek-chat"

    def __init__(self, model: str | None = None):
        settings = get_settings()
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = settings.DEEPSEEK_BASE_URL.rstrip("/")
        self.model = model or settings.DEEPSEEK_MODEL or self.DEFAULT_MODEL
        self.timeout = 60.0

        if not self.api_key:
            raise ValueError("DeepSeek API Key 未配置，请检查 .env 文件")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _build_payload(
        self,
        messages: List[DeepSeekMessage],
        temperature: float,
        max_tokens: int,
        stream: bool,
    ) -> dict:
        return {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

    def _parse_sse_line(self, line: str) -> str | None:
        """解析 SSE 流中的一行数据"""
        line = line.strip()
        if not line or not line.startswith("data: "):
            return None
        data = line[6:]  # 去掉 "data: " 前缀
        if data == "[DONE]":
            return None
        try:
            payload = json.loads(data)
            delta = payload.get("choices", [{}])[0].get("delta", {})
            return delta.get("content")
        except (json.JSONDecodeError, IndexError):
            return None

    def chat(
        self,
        messages: List[DeepSeekMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """同步非流式调用"""
        payload = self._build_payload(messages, temperature, max_tokens, stream=False)
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"].get("content", "")

    async def achat(
        self,
        messages: List[DeepSeekMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """异步非流式调用"""
        payload = self._build_payload(messages, temperature, max_tokens, stream=False)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"].get("content", "")

    def chat_stream(
        self,
        messages: List[DeepSeekMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Iterator[str]:
        """同步流式调用"""
        payload = self._build_payload(messages, temperature, max_tokens, stream=True)
        with httpx.Client(timeout=self.timeout) as client:
            with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            ) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    content = self._parse_sse_line(line)
                    if content:
                        yield content

    async def achat_stream(
        self,
        messages: List[DeepSeekMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """异步流式调用"""
        payload = self._build_payload(messages, temperature, max_tokens, stream=True)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                json=payload,
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    content = self._parse_sse_line(line)
                    if content:
                        yield content
