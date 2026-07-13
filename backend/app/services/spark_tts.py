"""iFlytek online TTS client.

This client uses the classic iFlytek REST TTS endpoint:
https://api.xfyun.cn/v1/service/v1/tts

The important detail is that the text payload must be base64 encoded and sent
as a form field named ``text``. Sending raw UTF-8 bytes makes the service return
an error JSON instead of audio.
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
from dataclasses import dataclass
from typing import Optional

import requests

from app.core.config import get_settings


@dataclass
class TTSResult:
    audio: Optional[bytes]
    error: str = ""
    provider: str = "iflytek-rest"


class SparkTTSClient:
    """iFlytek TTS REST client."""

    DEFAULT_VCN = "xiaoyan"
    ENDPOINT = "https://api.xfyun.cn/v1/service/v1/tts"

    def __init__(self):
        settings = get_settings()
        self.app_id = settings.SPARK_TTS_APP_ID
        self.api_key = settings.SPARK_TTS_API_KEY
        self.api_secret = settings.SPARK_TTS_API_SECRET

    @property
    def available(self) -> bool:
        return bool(self.app_id and self.api_key)

    def synthesize(self, text: str, vcn: str = DEFAULT_VCN, speed: int = 50) -> TTSResult:
        clean_text = text.strip()
        if not clean_text:
            return TTSResult(None, "empty text")
        if not self.available:
            return TTSResult(None, "SPARK_TTS_APP_ID or SPARK_TTS_API_KEY is missing")

        speed = max(0, min(100, int(speed)))
        param = {
            "auf": "audio/L16;rate=16000",
            "aue": "lame",
            "voice_name": vcn,
            "speed": str(speed),
            "volume": "60",
            "pitch": "50",
            "engine_type": "intp65",
            "text_type": "text",
        }
        x_param = base64.b64encode(
            json.dumps(param, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).decode("utf-8")
        cur_time = str(int(time.time()))
        x_checksum = hashlib.md5(
            (self.api_key + cur_time + x_param).encode("utf-8")
        ).hexdigest()
        encoded_text = base64.b64encode(clean_text.encode("utf-8")).decode("utf-8")

        try:
            response = requests.post(
                self.ENDPOINT,
                headers={
                    "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
                    "X-Appid": self.app_id,
                    "X-CurTime": cur_time,
                    "X-Param": x_param,
                    "X-CheckSum": x_checksum,
                },
                data={"text": encoded_text},
                timeout=30,
            )
        except requests.RequestException as exc:
            return TTSResult(None, f"request failed: {exc}")

        content_type = response.headers.get("Content-Type", "")
        if response.status_code != 200:
            return TTSResult(None, f"HTTP {response.status_code}: {response.text[:300]}")

        if "audio" in content_type and len(response.content) > 256:
            return TTSResult(response.content)

        try:
            payload = response.json()
            code = payload.get("code")
            message = payload.get("desc") or payload.get("message") or str(payload)
            return TTSResult(None, f"iFlytek error {code}: {message}")
        except ValueError:
            pass

        if len(response.content) > 256:
            return TTSResult(response.content)

        preview = response.text[:300] if response.text else "<empty response>"
        return TTSResult(None, f"unexpected response: {preview}")


_tts_client: Optional[SparkTTSClient] = None


def get_tts_client() -> SparkTTSClient:
    global _tts_client
    if _tts_client is None:
        _tts_client = SparkTTSClient()
    return _tts_client
