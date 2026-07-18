"""教师端 API"""
from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from app.services.auth import require_roles
from app.services.database import (
    create_course,
    create_course_material,
    delete_course,
    delete_course_material,
    get_course,
    get_course_material,
    get_course_material_file_path,
    list_course_materials,
    list_courses,
    update_course,
)

router = APIRouter()


class CourseCreateRequest(BaseModel):
    title: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    summary: str = Field(..., min_length=1)
    status: str = Field(default="draft")


class CourseUpdateRequest(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    summary: Optional[str] = None
    status: Optional[str] = None


def _normalize_teacher_course_status(status_value: Optional[str]) -> str:
    if not status_value:
        return "draft"
    if status_value == "published":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="教师课程需先提交审核，由管理端通过后发布。",
        )
    return status_value


def _check_course_access(course_id: str, payload: dict) -> dict:
    course = get_course(course_id)
    if not course:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    role = payload.get("role")
    username = payload.get("sub")
    if role != "admin" and course["teacher_username"] != username:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在或无权限")
    return course


def _require_public_course(course_id: str) -> dict:
    course = get_course(course_id)
    if not course or course["status"] != "published":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    return course


@router.get("/courses")
async def get_teacher_courses(payload: dict = Depends(require_roles("teacher", "admin"))):
    username = payload.get("sub")
    role = payload.get("role")
    teacher_username = None if role == "admin" else username
    return {"courses": list_courses(teacher_username)}


@router.get("/public/courses")
async def get_public_courses():
    courses = list_courses(status="published")
    for course in courses:
        course["materials_count"] = len(list_course_materials(course["course_id"]))
    return {"courses": courses}


@router.post("/courses")
async def add_course(payload: dict = Depends(require_roles("teacher", "admin")), body: CourseCreateRequest = None):
    if body is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少课程信息")
    username = payload.get("sub")
    role = payload.get("role")
    course = create_course(
        title=body.title.strip(),
        category=body.category.strip(),
        summary=body.summary.strip(),
        teacher_username=username,
        status=(body.status or "draft") if role == "admin" else _normalize_teacher_course_status(body.status),
    )
    return {"success": True, "course": course}


@router.patch("/courses/{course_id}")
async def edit_course(course_id: str, payload: dict = Depends(require_roles("teacher", "admin")), body: CourseUpdateRequest = None):
    if body is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="缺少更新信息")
    course = _check_course_access(course_id, payload)
    updates = body.model_dump(exclude_none=True)
    if payload.get("role") != "admin" and updates.get("status") == "published":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="教师课程需先提交审核，由管理端通过后发布。",
        )
    if payload.get("role") != "admin" and course["status"] == "published":
        content_changed = any(key in updates for key in ("title", "category", "summary"))
        if content_changed and "status" not in updates:
            updates["status"] = "pending_review"
    updated = update_course(course_id, updates)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    return {"success": True, "course": updated}


@router.delete("/courses/{course_id}")
async def remove_course(course_id: str, payload: dict = Depends(require_roles("teacher", "admin"))):
    course = _check_course_access(course_id, payload)
    materials = list_course_materials(course_id)
    for material in materials:
        delete_course_material(material["material_id"])
        file_path = get_course_material_file_path(material["stored_filename"])
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass
    deleted = delete_course(course_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    username = payload.get("sub")
    role = payload.get("role")
    teacher_username = None if role == "admin" else username
    return {"success": True, "course": course, "courses": list_courses(teacher_username)}


@router.get("/courses/{course_id}/materials")
async def list_teacher_course_materials(course_id: str, payload: dict = Depends(require_roles("teacher", "admin"))):
    _check_course_access(course_id, payload)
    return {"course": get_course(course_id), "materials": list_course_materials(course_id)}


@router.post("/courses/{course_id}/materials")
async def upload_course_material(
    course_id: str,
    payload: dict = Depends(require_roles("teacher", "admin")),
    file: UploadFile = File(...),
    note: str = Form(""),
):
    course = _check_course_access(course_id, payload)
    original_filename = Path(file.filename or "resource.bin").name
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="上传文件为空")
    if len(file_bytes) > 50 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="文件过大，单个文件请控制在 50MB 以内")

    material_id = uuid.uuid4().hex
    suffix = Path(original_filename).suffix
    stored_filename = f"{material_id}{suffix}"
    target_path = Path(get_course_material_file_path(stored_filename))
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(file_bytes)

    material = create_course_material(
        material_id=material_id,
        course_id=course_id,
        teacher_username=course["teacher_username"],
        original_filename=original_filename,
        stored_filename=stored_filename,
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(file_bytes),
        note=note.strip(),
    )
    response_course = course
    if payload.get("role") != "admin" and course["status"] == "published":
        response_course = update_course(course_id, {"status": "pending_review"}) or course
    return {"success": True, "course": response_course, "material": material, "materials": list_course_materials(course_id)}


@router.delete("/materials/{material_id}")
async def remove_course_material(material_id: str, payload: dict = Depends(require_roles("teacher", "admin"))):
    material = get_course_material(material_id)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料不存在")
    course = _check_course_access(material["course_id"], payload)
    deleted = delete_course_material(material_id)
    file_path = get_course_material_file_path(material["stored_filename"])
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass
    response_course = course
    if payload.get("role") != "admin" and course["status"] == "published":
        response_course = update_course(material["course_id"], {"status": "pending_review"}) or course
    return {"success": True, "course": response_course, "material": deleted, "materials": list_course_materials(material["course_id"])}


@router.get("/materials/{material_id}/download")
async def download_course_material(material_id: str, payload: dict = Depends(require_roles("teacher", "admin"))):
    material = get_course_material(material_id)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料不存在")
    _check_course_access(material["course_id"], payload)
    file_path = get_course_material_file_path(material["stored_filename"])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    return FileResponse(
        path=file_path,
        filename=material["original_filename"],
        media_type=material["mime_type"] or "application/octet-stream",
    )


@router.get("/public/courses/{course_id}/materials")
async def get_public_course_materials(course_id: str):
    course = _require_public_course(course_id)
    return {"course": course, "materials": list_course_materials(course_id)}


@router.get("/public/materials/{material_id}/download")
async def download_public_course_material(material_id: str):
    material = get_course_material(material_id)
    if not material:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="资料不存在")
    course = _require_public_course(material["course_id"])
    file_path = get_course_material_file_path(material["stored_filename"])
    if not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="文件不存在")
    return FileResponse(
        path=file_path,
        filename=material["original_filename"],
        media_type=material["mime_type"] or "application/octet-stream",
    )
