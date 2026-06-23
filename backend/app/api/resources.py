"""资源生成 API

支持两种模式：
1. 同步生成：POST /generate-for-session/{session_id}（兼容旧接口，测试用）
2. 流式生成：GET /stream-generate?session_id=xxx&concept=xxx（SSE，推荐生产环境）

TODO:
- [已完成] 资源生成改为异步任务 + SSE 流式返回进度
- [待完成] 接入 Redis 缓存已辩论通过的资源，避免重复调用 LLM
- [待完成] 生成真正的 TTS 音频文件并返回 URL
- [待完成] 增加生成超时熔断与重试机制
- [待完成] 支持批量生成多个知识点的学习资源
"""
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.agents.orchestrator import AgentOrchestrator
from app.models.schemas import StudentProfile
from app.services.database import (
    create_session,
    get_session,
    log_event,
    update_session,
)

router = APIRouter()


def _get_or_create_session(request: Request, session_id: str | None = None):
    """获取或创建会话（内存 + SQLite）"""
    sessions_db = request.app.state.sessions_db

    if session_id:
        # 先查内存缓存
        if session_id in sessions_db:
            return sessions_db[session_id]
        # 再查 SQLite
        row = get_session(session_id)
        if row:
            sessions_db[session_id] = row
            return row

    # 创建默认会话
    session = {
        "session_id": session_id or "default",
        "user_id": "default",
        "profile": StudentProfile().model_dump(),
        "dialogue_history": [],
        "target_concept": None,
    }
    if session_id:
        sessions_db[session_id] = session
        create_session(session_id, "default", session["profile"])
    else:
        sessions_db["default"] = session
    return session


def _save_session(request: Request, session: dict):
    """保存会活到内存和 SQLite"""
    request.app.state.sessions_db[session["session_id"]] = session
    update_session(
        session["session_id"],
        session["profile"],
        session.get("dialogue_history", []),
        session.get("target_concept"),
    )


@router.post("/generate")
async def generate_resource(concept: str, request: Request):
    """生成某个知识点的学习资源并执行辩论议会（同步版本）"""
    session = _get_or_create_session(request)
    orchestrator = AgentOrchestrator()
    result = orchestrator.generate_resource(session, concept)

    session["target_concept"] = concept
    _save_session(request, session)
    log_event(session["session_id"], "resource_generated", {
        "concept": concept,
        "debate_status": result.get("debate_report", {}).get("status"),
    })

    return result


@router.post("/generate-for-session/{session_id}")
async def generate_resource_for_session(session_id: str, concept: str, request: Request):
    """为指定会话生成资源（同步版本，兼容旧接口）"""
    session = _get_or_create_session(request, session_id)
    if not session:
        return {"error": "会话不存在"}

    orchestrator = AgentOrchestrator()
    result = orchestrator.generate_resource(session, concept)

    session["target_concept"] = concept
    _save_session(request, session)
    log_event(session_id, "resource_generated", {
        "concept": concept,
        "debate_status": result.get("debate_report", {}).get("status"),
    })

    return result


@router.get("/stream-generate")
async def stream_generate_resource(session_id: str, concept: str, request: Request):
    """流式生成资源（SSE）

    前端通过 EventSource 连接后，会收到以下事件：
    - event: progress -> data: {"stage": "builder", "message": "..."}
    - event: progress -> data: {"stage": "validation", "message": "..."}
    - event: progress -> data: {"stage": "debate", "message": "..."}
    - event: complete -> data: {"concept": ..., "package": ..., ...}
    - event: error -> data: {"message": "..."}
    """
    session = _get_or_create_session(request, session_id)
    orchestrator = AgentOrchestrator()

    async def event_generator():
        final_result = None
        try:
            async for event in orchestrator.generate_resource_stream(
                session, concept
            ):
                # SSE 格式：每个事件以 data: 开头，以两个换行结束
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
                if event.get("type") == "complete":
                    final_result = event
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            # 无论成功与否，都保存会话并记录日志
            session["target_concept"] = concept
            _save_session(request, session)
            log_event(session_id, "resource_generated", {
                "concept": concept,
                "debate_status": final_result.get("debate_report", {}).get("status") if final_result else "ERROR",
                "success": final_result is not None,
            })

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
