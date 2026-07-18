"""DeepSeek API 封装（OpenAI 兼容协议）

对应需求：
- 为智学蜂巢提供大模型调用能力，支撑教学资源生成、对话辅导等 Agent。
- 使用 httpx 直接调用 OpenAI 兼容协议，无需官方 SDK，兼容 Python 3.13+。

主要类/函数/接口：
- DeepSeekMessage：统一消息结构（role / content）。
- DeepSeekLLM：模型封装类。
  - chat / achat：同步/异步非流式调用。
  - chat_stream / achat_stream：同步/异步流式调用（SSE 解析）。
  - _build_payload / _parse_sse_line / _headers：内部请求构造与 SSE 解析。

支持能力：
1. 同步/异步非流式调用；
2. 同步/异步流式调用（SSE）；
3. 多轮对话上下文。

文档参考：https://platform.deepseek.com/api-docs/

TODO:
- [已完成] 同步/异步非流式与流式调用封装。
- [已完成] SSE 数据行解析与错误兼容。
- [待完成] 增加 token 用量统计与成本监控。
- [待完成] 增加模型调用重试、超时降级与熔断机制。
- [待完成] 支持 function calling / structured output，用于资源结构化生成。
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
    DEFAULT_MODEL = "deepseek-v4-pro"

    def __init__(self, model: str | None = None):
        settings = get_settings()
        self.api_key = settings.DEEPSEEK_API_KEY
        self.base_url = (settings.ANTHROPIC_BASE_URL or settings.DEEPSEEK_BASE_URL).rstrip("/")
        self.model = model or settings.DEEPSEEK_MODEL or self.DEFAULT_MODEL
        self.timeout = 120.0

        if not self.api_key:
            raise ValueError("DeepSeek API Key 未配置，请检查 .env 文件")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @property
    def _uses_anthropic_api(self) -> bool:
        return "/anthropic" in self.base_url.lower()

    def _anthropic_headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

    def _anthropic_messages_url(self) -> str:
        return self.base_url if self.base_url.endswith("/messages") else f"{self.base_url}/v1/messages"

    def _build_anthropic_payload(
        self,
        messages: List[DeepSeekMessage],
        temperature: float,
        max_tokens: int,
    ) -> dict:
        system_parts: list[str] = []
        converted: list[dict] = []
        for message in messages:
            content = message.content or ""
            if message.role == "system":
                system_parts.append(content)
                continue
            role = "assistant" if message.role == "assistant" else "user"
            if converted and converted[-1]["role"] == role:
                converted[-1]["content"] += f"\n\n{content}"
            else:
                converted.append({"role": role, "content": content})

        payload = {
            "model": self.model,
            "messages": converted or [{"role": "user", "content": ""}],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if system_parts:
            payload["system"] = "\n\n".join(system_parts)
        return payload

    @staticmethod
    def _parse_anthropic_text(data: dict) -> str:
        content = data.get("content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            text = "".join(
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            )
            if text:
                return text
            return "".join(
                block.get("thinking", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "thinking"
            )
        return data.get("text", "") or data.get("message", "")

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
        # 去掉 "data: " 前缀后解析 JSON，取第一个 choice 的 delta.content
        data = line[6:]
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
        if self._uses_anthropic_api:
            payload = self._build_anthropic_payload(messages, temperature, max_tokens)
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self._anthropic_messages_url(),
                    headers=self._anthropic_headers(),
                    json=payload,
                )
                response.raise_for_status()
                return self._parse_anthropic_text(response.json())

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
        if self._uses_anthropic_api:
            payload = self._build_anthropic_payload(messages, temperature, max_tokens)
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self._anthropic_messages_url(),
                    headers=self._anthropic_headers(),
                    json=payload,
                )
                response.raise_for_status()
                return self._parse_anthropic_text(response.json())

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
        if self._uses_anthropic_api:
            yield self.chat(messages, temperature, max_tokens)
            return

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
        if self._uses_anthropic_api:
            yield await self.achat(messages, temperature, max_tokens)
            return

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
