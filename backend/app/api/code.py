"""代码执行与判题 API

TODO:
- [待完成] 接入 Docker 沙箱，支持第三方库
- [待完成] 接入 Pyodide 后端执行选项
- [已完成] 保存学生代码提交历史与错误模式到学习行为日志
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.services.code_executor import CodeExecutor
from app.services.database import log_event

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

    # 记录练习提交事件
    log_event(payload.session_id or "anonymous", "exercise_submitted", {
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

    # 记录练习提交事件
    log_event(payload.session_id or "anonymous", "exercise_submitted", {
        "concept": payload.concept,
        "code": payload.code,
        "expected_output": payload.expected_output,
        "passed": result.get("passed"),
        "actual_output": result.get("actual_output"),
    })

    return result
