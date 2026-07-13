"""TTS API endpoints."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.agents.llm import get_llm_provider
from app.services.spark_tts_ws import get_tts_client

router = APIRouter()


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=800, description="Text to synthesize")
    speed: int = Field(50, ge=0, le=100, description="Speech speed, 0-100")
    voice: str = Field("x4_xiaoyan", min_length=1, max_length=40, description="iFlytek voice name")


class TeachingScriptRequest(BaseModel):
    concept: str = Field("", max_length=80, description="Current concept")
    lecture: str = Field(..., min_length=1, max_length=12000, description="Markdown lecture text")


class TeachingScriptResponse(BaseModel):
    script: str
    provider: str = "deepseek-v4-pro"
    fallback: bool = False


def _fallback_teaching_script(lecture: str, concept: str = "") -> str:
    import re

    text = re.sub(r"```[\s\S]*?```", "这里有一段示例代码，学习时先看整体结构，再关注输入、处理和输出。", lecture)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"!\[[^\]]*]\([^)]*\)", "", text)
    text = re.sub(r"\[[^\]]+]\([^)]*\)", "", text)
    lines = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        heading = re.match(r"^#{1,6}\s*(.+)$", line)
        if heading:
            lines.append(f"接下来我们看{heading.group(1)}。")
            continue
        line = re.sub(r"^[-*+]\s+", "这里有一个要点：", line)
        line = re.sub(r"^\d+[.)、]\s+", "接下来一个重点是，", line)
        line = line.replace("**", "").replace("__", "")
        line = re.sub(r"[>#|]", " ", line)
        lines.append(line)
    body = re.sub(r"\s+", " ", " ".join(lines)).strip()
    if not body:
        body = "当前讲义内容较少，请先生成完整学习资源。"
    intro = f"这节课我们围绕{concept}来学习。" if concept else "这节课我们来学习当前知识点。"
    return f"{intro}我会像老师讲课一样，先带你抓住主线，再解释关键细节。{body}"[:760]


@router.post("/teaching-script", response_model=TeachingScriptResponse)
async def teaching_script(payload: TeachingScriptRequest):
    """Rewrite lecture Markdown into a natural teacher-style narration script."""

    fallback = _fallback_teaching_script(payload.lecture, payload.concept)
    try:
        llm = get_llm_provider()
        prompt = f"""请把下面的学习讲义改写成一段适合语音播报的中文老师讲课稿。

要求：
1. 基于讲义内容讲解，不要编造讲义没有的知识。
2. 不要逐字朗读 Markdown 标题、列表符号、代码块符号。
3. 代码不要整段念出来，只说明代码在做什么、学习时看哪里。
4. 语气像一位耐心的 Python 老师，适合学生边听边学。
5. 控制在 500 到 700 个汉字以内，直接输出讲课稿，不要输出 JSON。

当前知识点：{payload.concept or "当前知识点"}

讲义：
{payload.lecture[:6000]}
"""
        script = llm.chat(
            [
                {"role": "system", "content": "你是一名擅长把文字讲义改写成自然口播课的 Python 教师。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.55,
            max_tokens=1200,
        ).strip()
        if not script:
            return TeachingScriptResponse(script=fallback, fallback=True)
        return TeachingScriptResponse(script=script[:760])
    except Exception:
        return TeachingScriptResponse(script=fallback, fallback=True)


@router.post("/synthesize")
async def synthesize(payload: TTSRequest):
    """Convert text to MP3 audio."""

    client = get_tts_client()
    if not client.available:
        raise HTTPException(
            status_code=503,
            detail=(
                "TTS service is not configured. Set SPARK_TTS_APP_ID, "
                "SPARK_TTS_API_KEY, SPARK_TTS_API_SECRET and SPARK_TTS_API_URL in backend/.env."
            ),
        )

    result = client.synthesize(payload.text, vcn=payload.voice, speed=payload.speed)
    if result.audio is None:
        raise HTTPException(status_code=502, detail=result.error or "TTS synthesis failed")

    return Response(content=result.audio, media_type="audio/mpeg")


@router.get("/status")
async def tts_status():
    """Return whether server-side iFlytek TTS credentials are configured."""

    client = get_tts_client()
    return {
        "tts_available": client.available,
        "provider": client.provider,
        "endpoint": client.api_url,
        "voice": client.DEFAULT_VCN,
        "configured_fields": {
            "app_id": client.field_configured(client.app_id),
            "api_key": client.field_configured(client.api_key),
            "api_secret": client.field_configured(client.api_secret),
        },
    }
