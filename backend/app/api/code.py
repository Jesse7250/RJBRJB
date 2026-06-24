"""代码执行与判题 API

TODO:
- [待完成] 接入 Docker 沙箱，支持第三方库
- [待完成] 接入 Pyodide 后端执行选项
- [已完成] 保存学生代码提交历史与错误模式到学习行为日志
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel

import uuid

from app.services.code_executor import CodeExecutor
from app.services.database import (
    create_code_submission,
    log_event,
)

router = APIRouter()


class ExecuteRequest(BaseModel):
    code: str


class JudgeRequest(BaseModel):
    code: str
    expected_output: str
    session_id: str | None = None
    concept: str | None = None


@router.post("/execute")
async def execute_code(payload: ExecuteRequest, request: Request):
    """执行 Python 代码并返回输出"""
    executor = CodeExecutor()
    result = executor.execute(payload.code)

    # 持久化代码提交记录
    error_type = ""
    if not result.get("success"):
        error_type = result.get("error_type", "runtime")
    create_code_submission(
        submission_id=str(uuid.uuid4()),
        session_id="anonymous",
        concept="",
        code=payload.code,
        output=result.get("stdout", "") + "\n" + result.get("stderr", ""),
        passed=result.get("success", False),
        error_type=error_type,
        execution_time=result.get("execution_time", 0.0),
    )

    # 记录代码执行事件
    log_event("anonymous", "code_executed", {
        "code": payload.code,
        "success": result.get("success"),
        "violations": result.get("violations"),
    })

    return result


@router.post("/judge")
async def judge_code(payload: JudgeRequest, request: Request):
    """判题：执行代码并对比期望输出"""
    executor = CodeExecutor()
    result = executor.judge(payload.code, payload.expected_output)

    session_id = payload.session_id or "anonymous"
    error_type = "passed" if result.get("passed") else result.get("error_type", "logic")

    # 持久化代码提交记录
    create_code_submission(
        submission_id=str(uuid.uuid4()),
        session_id=session_id,
        exercise_id="",
        concept=payload.concept or "",
        code=payload.code,
        output=result.get("actual_output", ""),
        passed=result.get("passed", False),
        error_type=error_type,
        execution_time=result.get("execution_time", 0.0),
    )

    # 记录练习提交事件
    log_event(session_id, "exercise_submitted", {
        "concept": payload.concept,
        "code": payload.code,
        "expected_output": payload.expected_output,
        "passed": result.get("passed"),
        "actual_output": result.get("actual_output"),
    })

    return result


@router.post("/judge-exercise")
async def judge_exercise(payload: JudgeRequest, request: Request):
    """判题并更新会话中的练习记录"""
    executor = CodeExecutor()
    result = executor.judge(payload.code, payload.expected_output)

    session_id = payload.session_id or "anonymous"
    error_type = "passed" if result.get("passed") else result.get("error_type", "logic")

    # 持久化代码提交记录
    create_code_submission(
        submission_id=str(uuid.uuid4()),
        session_id=session_id,
        exercise_id="",
        concept=payload.concept or "",
        code=payload.code,
        output=result.get("actual_output", ""),
        passed=result.get("passed", False),
        error_type=error_type,
        execution_time=result.get("execution_time", 0.0),
    )

    # 记录练习提交事件
    log_event(session_id, "exercise_submitted", {
        "concept": payload.concept,
        "code": payload.code,
        "expected_output": payload.expected_output,
        "passed": result.get("passed"),
        "actual_output": result.get("actual_output"),
    })

    return result
