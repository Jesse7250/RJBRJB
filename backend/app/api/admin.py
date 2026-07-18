"""管理后台 API"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.services.auth import require_roles
from app.services.database import get_db, list_course_materials, list_courses, list_users, update_course
from app.services.knowledge_furnace import trigger_resource_review

router = APIRouter()


class AdminCourseUpdateRequest(BaseModel):
    title: str | None = None
    category: str | None = None
    summary: str | None = None
    status: str | None = None


@router.get("/stats")
async def get_admin_stats(payload: dict = Depends(require_roles("admin"))):
    db = get_db()
    try:
        stats = {
            "sessions": len(list(db["sessions"].rows)),
            "users": len(list(db["users"].rows)),
            "learning_events": len(list(db["learning_events"].rows)),
            "resources": len(list(db["resource"].rows)) if "resource" in db.table_names() else 0,
            "generation_tasks": len(list(db["generation_task"].rows)) if "generation_task" in db.table_names() else 0,
            "debate_records": len(list(db["debate_record"].rows)) if "debate_record" in db.table_names() else 0,
            "code_submissions": len(list(db["code_submission"].rows)) if "code_submission" in db.table_names() else 0,
            "resource_versions": len(list(db["resource_version"].rows)) if "resource_version" in db.table_names() else 0,
            "resource_feedback": len(list(db["resource_feedback"].rows)) if "resource_feedback" in db.table_names() else 0,
            "courses": len(list(db["courses"].rows)) if "courses" in db.table_names() else 0,
        }
        submissions = list(db["code_submission"].rows_where("passed IS NOT NULL")) if "code_submission" in db.table_names() else []
        total = len(submissions)
        passed = sum(1 for r in submissions if r["passed"])
        stats["code_pass_rate"] = round(passed / total, 4) if total else 0.0
        stats["total_submissions"] = total
        return {"status": "ok", "stats": stats}
    finally:
        db.conn.close()


@router.get("/users")
async def get_admin_users(payload: dict = Depends(require_roles("admin"))):
    return {"users": list_users()}


@router.get("/courses")
async def get_admin_courses(payload: dict = Depends(require_roles("admin"))):
    courses = list_courses()
    for course in courses:
        materials = list_course_materials(course["course_id"])
        course["materials"] = materials
        course["materials_count"] = len(materials)
    return {"courses": courses}


@router.patch("/courses/{course_id}")
async def patch_admin_course(course_id: str, body: AdminCourseUpdateRequest, payload: dict = Depends(require_roles("admin"))):
    updated = update_course(course_id, body.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    materials = list_course_materials(course_id)
    updated["materials"] = materials
    updated["materials_count"] = len(materials)
    return {"success": True, "course": updated}


@router.post("/resource-review")
async def trigger_manual_resource_review(
    concept: str = Query(..., description="需要重审的知识点"),
    reason: str = Query("manual", description="触发原因，如 manual / error_rate / feedback"),
    payload: dict = Depends(require_roles("admin")),
):
    result = trigger_resource_review(concept, triggered_by=reason, force=True)
    if not result:
        return {"success": False, "concept": concept, "reason": reason, "message": "重审未执行"}
    return {
        "success": True,
        "concept": concept,
        "reason": reason,
        "task_id": result["task_id"],
        "resource_id": result["resource_id"],
        "version": result["version"],
    }

