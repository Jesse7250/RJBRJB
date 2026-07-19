"""讯飞星火大模型 API 封装

对应需求：
- 为智慧伴学提供备选大模型调用能力，在国内网络环境下作为 DeepSeek 的 fallback。
- 支持流式对话生成与非阻塞同步调用。

主要类/函数/接口：
- SparkMessage：统一消息结构（role / content）。
- SparkLLM：讯飞星火模型封装类。
  - _build_auth_url：基于 HMAC-SHA256 构造带鉴权签名的 WebSocket URL。
  - _build_payload：构造符合讯飞协议的请求体。
  - chat：同步非流式调用（内部复用流式生成并拼接结果）。
  - chat_stream：同步流式调用，通过 websocket 在线程中接收并实时 yield chunk。
  - achat / achat_stream：异步包装，方便在 FastAPI 异步路由中调用。

支持能力：
1. 流式对话生成；
2. 非阻塞同步调用；
3. 多轮对话上下文。

文档参考：https://www.xfyun.cn/doc/spark/Web.html

TODO:
- [已完成] WebSocket 鉴权、payload 构造与同步流式调用。
- [已完成] 异步接口包装（基于 run_in_executor）。
- [待完成] 增加 token 用量统计、错误码映射与重试机制。
- [待完成] 优化 chat_stream 的类型标注（当前标注为 str，实际返回生成器）。
- [待完成] 支持星火 v4.0 多模态与 function calling 能力。
"""
import base64
import hashlib
import hmac
import json
import threading
import time
from typing import AsyncIterator, Callable, Dict, List, Optional
from urllib.parse import urlparse

import websocket

from app.core.config import get_settings


class SparkMessage:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content

    def to_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class SparkLLM:
    """讯飞星火大模型封装"""

    def __init__(self):
        settings = get_settings()
        self.app_id = settings.SPARK_APP_ID
        self.api_key = settings.SPARK_API_KEY
        self.api_secret = settings.SPARK_API_SECRET
        self.api_url = settings.SPARK_API_URL
        self.domain = settings.SPARK_DOMAIN

        if not all([self.app_id, self.api_key, self.api_secret]):
            raise ValueError("讯飞星火 API 配置不完整，请检查 .env 文件")

    def _build_auth_url(self) -> str:
        """构建带鉴权签名的 WebSocket URL"""
        parsed = urlparse(self.api_url)
        host = parsed.netloc
        path = parsed.path

        # RFC1123 格式时间
        date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime())

        # 拼接签名原文
        signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"

        # HMAC-SHA256 签名
        signature_sha = hmac.new(
            self.api_secret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature = base64.b64encode(signature_sha).decode("utf-8")

        # 构造 authorization
        authorization_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature}"'
        )
        authorization = base64.b64encode(
            authorization_origin.encode("utf-8")
        ).decode("utf-8")

        # 拼接 URL
        auth_url = (
            f"{self.api_url}?authorization={authorization}"
            f"&date={date}&host={host}"
        )
        return auth_url

    def _build_payload(
        self,
        messages: List[SparkMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> dict:
        return {
            "header": {
                "app_id": self.app_id,
                "uid": "eduhive",
            },
            "parameter": {
                "chat": {
                    "domain": self.domain,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                }
            },
            "payload": {
                "message": {
                    "text": [msg.to_dict() for msg in messages]
                }
            },
        }

    def chat(
        self,
        messages: List[SparkMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """同步非流式调用"""
        result = []
        for chunk in self.chat_stream(messages, temperature, max_tokens):
            result.append(chunk)
        return "".join(result)

    def chat_stream(
        self,
        messages: List[SparkMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """同步流式调用，返回生成器"""
        auth_url = self._build_auth_url()
        payload = self._build_payload(messages, temperature, max_tokens)

        response_chunks = []
        finished = threading.Event()
        error_msg = [None]

        def on_message(ws, message):
            try:
                data = json.loads(message)
                header = data.get("header", {})
                payload_data = data.get("payload", {})

                if header.get("code") != 0:
                    error_msg[0] = f"API错误: {header.get('message')}"
                    finished.set()
                    return

                choices = payload_data.get("choices", {})
                text = choices.get("text", [])
                if text:
                    content = text[0].get("content", "")
                    response_chunks.append(content)

                status = choices.get("status", 0)
                if status == 2:  # 最后一条
                    finished.set()
            except Exception as e:
                error_msg[0] = str(e)
                finished.set()

        def on_error(ws, error):
            error_msg[0] = str(error)
            finished.set()

        def on_close(ws, close_status_code, close_msg):
            finished.set()

        def on_open(ws):
            ws.send(json.dumps(payload))

        ws = websocket.WebSocketApp(
            auth_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )

        wst = threading.Thread(target=ws.run_forever)
        wst.daemon = True
        wst.start()

        # 在 websocket 后台线程接收消息的同时，实时 yield 已收到的 chunk
        last_yielded = 0
        while not finished.is_set() or last_yielded < len(response_chunks):
            while last_yielded < len(response_chunks):
                yield response_chunks[last_yielded]
                last_yielded += 1
            time.sleep(0.05)

        wst.join(timeout=5)

        if error_msg[0]:
            raise RuntimeError(f"讯飞 API 调用失败: {error_msg[0]}")

    async def achat(
        self,
        messages: List[SparkMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        """异步非流式调用"""
        return self.chat(messages, temperature, max_tokens)

    async def achat_stream(
        self,
        messages: List[SparkMessage],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """异步流式调用"""
        import asyncio

        loop = asyncio.get_event_loop()
        sync_gen = self.chat_stream(messages, temperature, max_tokens)

        while True:
            try:
                chunk = await loop.run_in_executor(None, next, sync_gen)
                yield chunk
            except StopIteration:
                break



