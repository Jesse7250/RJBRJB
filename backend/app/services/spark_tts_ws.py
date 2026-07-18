"""iFlytek WebSocket TTS client.

Expected endpoint:
    wss://tts-api.xfyun.cn/v2/tts
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import ssl
from dataclasses import dataclass
from email.utils import formatdate
from typing import Optional
from urllib.parse import urlencode, urlsplit

import websocket

from app.core.config import get_settings


@dataclass
class TTSResult:
    audio: Optional[bytes]
    error: str = ""
    provider: str = "iflytek-ws"


class SparkTTSWebSocketClient:
    """iFlytek WebSocket TTS client."""

    DEFAULT_VCN = "x4_xiaoyan"
    DEFAULT_ENDPOINT = "wss://tts-api.xfyun.cn/v2/tts"

    def __init__(self):
        settings = get_settings()
        self.app_id = settings.SPARK_TTS_APP_ID.strip()
        self.api_key = settings.SPARK_TTS_API_KEY.strip()
        self.api_secret = settings.SPARK_TTS_API_SECRET.strip()
        self.api_url = (settings.SPARK_TTS_API_URL or self.DEFAULT_ENDPOINT).strip()

    @property
    def provider(self) -> str:
        return "iflytek-ws"

    @property
    def available(self) -> bool:
        return all(
            self.field_configured(value)
            for value in (self.app_id, self.api_key, self.api_secret, self.api_url)
        )

    @staticmethod
    def field_configured(value: str) -> bool:
        normalized = (value or "").strip().lower()
        return bool(normalized) and not (
            normalized.startswith("your_")
            or normalized.endswith("_here")
            or normalized in {"replace_me", "changeme", "todo"}
        )

    def _authorized_url(self) -> str:
        parsed = urlsplit(self.api_url)
        host = parsed.netloc
        path = parsed.path or "/v2/tts"
        date = formatdate(usegmt=True)
        signature_origin = f"host: {host}\ndate: {date}\nGET {path} HTTP/1.1"
        signature_sha = hmac.new(
            self.api_secret.encode("utf-8"),
            signature_origin.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        signature = base64.b64encode(signature_sha).decode("utf-8")
        authorization_origin = (
            f'api_key="{self.api_key}", algorithm="hmac-sha256", '
            f'headers="host date request-line", signature="{signature}"'
        )
        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")
        query = urlencode({"authorization": authorization, "date": date, "host": host})
        return f"{parsed.scheme}://{host}{path}?{query}"

    def _request_payload(self, text: str, vcn: str, speed: int) -> dict:
        speed = max(0, min(100, int(speed)))
        return {
            "common": {
                "app_id": self.app_id,
            },
            "business": {
                "aue": "lame",
                "auf": "audio/L16;rate=16000",
                "vcn": vcn,
                "speed": speed,
                "volume": 60,
                "pitch": 50,
                "tte": "UTF8",
            },
            "data": {
                "status": 2,
                "text": base64.b64encode(text.encode("utf-8")).decode("utf-8"),
            },
        }

    def synthesize(self, text: str, vcn: str = DEFAULT_VCN, speed: int = 50) -> TTSResult:
        clean_text = text.strip()
        if not clean_text:
            return TTSResult(None, "empty text")
        if not self.available:
            return TTSResult(
                None,
                "SPARK_TTS_APP_ID, SPARK_TTS_API_KEY, SPARK_TTS_API_SECRET or SPARK_TTS_API_URL is missing",
            )

        audio_chunks: list[bytes] = []
        ws = None
        try:
            ws = websocket.create_connection(
                self._authorized_url(),
                timeout=30,
                sslopt={"cert_reqs": ssl.CERT_NONE},
            )
            ws.send(json.dumps(self._request_payload(clean_text, vcn, speed), ensure_ascii=False))

            while True:
                raw_message = ws.recv()
                if not raw_message:
                    return TTSResult(None, "empty websocket message")
                message = json.loads(raw_message)
                code = message.get("code", 0)
                if code != 0:
                    detail = message.get("message") or message.get("desc") or str(message)
                    return TTSResult(None, f"iFlytek error {code}: {detail}")

                data = message.get("data") or {}
                audio = data.get("audio")
                if audio:
                    audio_chunks.append(base64.b64decode(audio))

                if data.get("status") == 2:
                    break
        except Exception as exc:
            return TTSResult(None, f"websocket request failed: {exc}")
        finally:
            if ws is not None:
                try:
                    ws.close()
                except Exception:
                    pass

        audio_bytes = b"".join(audio_chunks)
        if len(audio_bytes) <= 256:
            return TTSResult(None, "iFlytek returned no valid audio")
        return TTSResult(audio_bytes)


_tts_client: Optional[SparkTTSWebSocketClient] = None


def get_tts_client() -> SparkTTSWebSocketClient:
    global _tts_client
    if _tts_client is None:
        _tts_client = SparkTTSWebSocketClient()
    return _tts_client

