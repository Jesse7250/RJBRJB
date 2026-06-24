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
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.agents.orchestrator import AgentOrchestrator
from app.models.schemas import StudentProfile
from app.services.database import (
    create_debate_record,
    create_generation_task,
    create_resource,
    create_session,
    get_session,
    log_event,
    update_generation_task,
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


def _stage_to_status(stage: str) -> str:
    """将 SSE stage 映射为任务状态"""
    mapping = {
        "cache": "completed",
        "builder": "generating",
        "validation": "generating",
        "revision": "debating",
        "debate": "debating",
        "complete": "completed",
    }
    return mapping.get(stage, "generating")


def _persist_resource_and_debate(task_id: str, session_id: str, result: dict):
    """将生成结果持久化到 resource 和 debate_record 表"""
    concept = result.get("concept", "")
    package = result.get("package", {})
    debate_report = result.get("debate_report", {})

    resource_id = str(uuid.uuid4())
    debate_id = str(uuid.uuid4())

    create_resource(
        resource_id=resource_id,
        task_id=task_id,
        session_id=session_id,
        concept=concept,
        document=package.get("document"),
        mindmap=package.get("mindmap"),
        exercises=package.get("exercises"),
        code_cases=package.get("code_cases"),
        audio_text=package.get("audio_text"),
        debate_report=debate_report,
        status="approved" if debate_report.get("status") in ("PASSED", "MODIFIED") else "rejected",
    )

    create_debate_record(
        debate_id=debate_id,
        task_id=task_id,
        resource_id=resource_id,
        concept=concept,
        status=debate_report.get("status", "PASSED"),
        rounds=debate_report.get("rounds"),
        final_votes=debate_report.get("final_votes"),
        summary=f"辩论结果：{debate_report.get('status', 'UNKNOWN')}",
    )

    return resource_id, debate_id


@router.post("/generate")
async def generate_resource(concept: str, request: Request):
    """生成某个知识点的学习资源并执行辩论议会（同步版本）"""
    session = _get_or_create_session(request)
    session_id = session["session_id"]
    task_id = str(uuid.uuid4())

    create_generation_task(task_id, session_id, concept, status="pending")

    orchestrator = AgentOrchestrator()
    result = orchestrator.generate_resource(session, concept)

    # 持久化生成结果
    resource_id, debate_id = _persist_resource_and_debate(task_id, session_id, result)
    update_generation_task(
        task_id,
        status="completed",
        progress=100,
        stage_message="资源生成与辩论审核完成",
        result={"resource_id": resource_id, "debate_id": debate_id},
    )

    session["target_concept"] = concept
    _save_session(request, session)
    log_event(session_id, "resource_generated", {
        "concept": concept,
        "debate_status": result.get("debate_report", {}).get("status"),
        "task_id": task_id,
        "resource_id": resource_id,
    })

    return result


@router.post("/generate-for-session/{session_id}")
async def generate_resource_for_session(session_id: str, concept: str, request: Request):
    """为指定会话生成资源（同步版本，兼容旧接口）"""
    session = _get_or_create_session(request, session_id)
    if not session:
        return {"error": "会话不存在"}

    task_id = str(uuid.uuid4())
    create_generation_task(task_id, session_id, concept, status="pending")

    orchestrator = AgentOrchestrator()
    result = orchestrator.generate_resource(session, concept)

    # 持久化生成结果
    resource_id, debate_id = _persist_resource_and_debate(task_id, session_id, result)
    update_generation_task(
        task_id,
        status="completed",
        progress=100,
        stage_message="资源生成与辩论审核完成",
        result={"resource_id": resource_id, "debate_id": debate_id},
    )

    session["target_concept"] = concept
    _save_session(request, session)
    log_event(session_id, "resource_generated", {
        "concept": concept,
        "debate_status": result.get("debate_report", {}).get("status"),
        "task_id": task_id,
        "resource_id": resource_id,
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
    task_id = str(uuid.uuid4())

    create_generation_task(task_id, session_id, concept, status="pending",
                           stage_message="等待开始生成...")

    async def event_generator():
        final_result = None
        try:
            async for event in orchestrator.generate_resource_stream(
                session, concept
            ):
                # 根据事件更新任务状态
                event_type = event.get("type")
                if event_type == "progress":
                    stage = event.get("stage", "generating")
                    progress = {"builder": 30, "validation": 50, "debate": 70,
                                "revision": 80, "complete": 100, "cache": 100}.get(stage, 30)
                    update_generation_task(
                        task_id,
                        status=_stage_to_status(stage),
                        progress=progress,
                        stage_message=event.get("message", ""),
                    )

                # SSE 格式：每个事件以 data: 开头，以两个换行结束
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                if event_type == "complete":
                    final_result = event
        except Exception as e:
            update_generation_task(
                task_id,
                status="failed",
                progress=0,
                stage_message="生成失败",
                error_message=str(e),
            )
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            # 持久化生成结果
            if final_result:
                try:
                    resource_id, debate_id = _persist_resource_and_debate(
                        task_id, session_id, final_result
                    )
                    update_generation_task(
                        task_id,
                        status="completed",
                        progress=100,
                        stage_message="资源生成与辩论审核完成",
                        result={"resource_id": resource_id, "debate_id": debate_id},
                    )
                except Exception as e:
                    update_generation_task(
                        task_id,
                        status="failed",
                        error_message=f"持久化失败: {e}",
                    )

            # 无论成功与否，都保存会话并记录日志
            session["target_concept"] = concept
            _save_session(request, session)
            log_event(session_id, "resource_generated", {
                "concept": concept,
                "debate_status": final_result.get("debate_report", {}).get("status") if final_result else "ERROR",
                "success": final_result is not None,
                "task_id": task_id,
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
