"""SQLite 持久化与学习行为日志

提供：
1. 会话与画像持久化
2. 学习行为事件记录（chat、resource_generated、exercise_submitted、code_executed）
3. 简单的学习行为统计接口

TODO:
- [待完成] 未来可迁移到 PostgreSQL
- [待完成] 增加用户表和认证
- [待完成] 增加索引优化查询
"""
import json
import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlite_utils import Database

from app.core.config import get_settings


def _db_path() -> str:
    settings = get_settings()
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite:///"):
        db_path = db_url[10:]
    else:
        db_path = db_url
    db_path = os.path.abspath(db_path)
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    return db_path


def get_db() -> Database:
    """获取新的 SQLite 数据库实例（每个线程独立连接，避免跨线程问题）"""
    conn = sqlite3.connect(_db_path(), check_same_thread=False)
    db = Database(conn)
    init_db(db)
    return db


def init_db(db: Database):
    """初始化数据库表"""
    if "sessions" not in db.table_names():
        db["sessions"].create({
            "session_id": str,
            "user_id": str,
            "profile": str,  # JSON
            "dialogue_history": str,  # JSON
            "target_concept": str,
            "created_at": str,
            "updated_at": str,
        }, pk="session_id")

    if "learning_events" not in db.table_names():
        db["learning_events"].create({
            "id": int,
            "session_id": str,
            "event_type": str,
            "payload": str,  # JSON
            "created_at": str,
        }, pk="id", if_not_exists=True)
        db["learning_events"].create_index(["session_id"], if_not_exists=True)
        db["learning_events"].create_index(["event_type"], if_not_exists=True)

    if "users" not in db.table_names():
        db["users"].create({
            "username": str,
            "hashed_password": str,
            "created_at": str,
        }, pk="username")


def _now() -> str:
    return datetime.utcnow().isoformat()


def create_user(username: str, hashed_password: str):
    db = get_db()
    try:
        db["users"].insert({
            "username": username,
            "hashed_password": hashed_password,
            "created_at": _now(),
        })
    finally:
        db.conn.close()


def get_user(username: str) -> Optional[dict]:
    db = get_db()
    try:
        row = db["users"].get(username)
        if not row:
            return None
        return {
            "username": row["username"],
            "hashed_password": row["hashed_password"],
            "created_at": row["created_at"],
        }
    except Exception:
        return None
    finally:
        db.conn.close()


def create_session(session_id: str, user_id: str, profile: dict, target_concept: Optional[str] = None):
    db = get_db()
    try:
        db["sessions"].insert({
            "session_id": session_id,
            "user_id": user_id,
            "profile": json.dumps(profile, ensure_ascii=False),
            "dialogue_history": json.dumps([], ensure_ascii=False),
            "target_concept": target_concept,
            "created_at": _now(),
            "updated_at": _now(),
        }, replace=True)
    finally:
        db.conn.close()


def get_session(session_id: str) -> Optional[dict]:
    db = get_db()
    try:
        row = db["sessions"].get(session_id)
        if not row:
            return None
        return {
            "session_id": row["session_id"],
            "user_id": row["user_id"],
            "profile": json.loads(row["profile"]),
            "dialogue_history": json.loads(row["dialogue_history"]),
            "target_concept": row["target_concept"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }
    finally:
        db.conn.close()


def update_session(session_id: str, profile: dict, dialogue_history: list, target_concept: Optional[str] = None):
    db = get_db()
    try:
        updates = {
            "profile": json.dumps(profile, ensure_ascii=False),
            "dialogue_history": json.dumps(dialogue_history, ensure_ascii=False),
            "updated_at": _now(),
        }
        if target_concept is not None:
            updates["target_concept"] = target_concept
        db["sessions"].update(session_id, updates)
    finally:
        db.conn.close()


def log_event(session_id: str, event_type: str, payload: Dict[str, Any]):
    """记录学习行为事件"""
    db = get_db()
    try:
        db["learning_events"].insert({
            "session_id": session_id,
            "event_type": event_type,
            "payload": json.dumps(payload, ensure_ascii=False),
            "created_at": _now(),
        })
    finally:
        db.conn.close()


def get_session_events(session_id: str, event_type: Optional[str] = None) -> List[dict]:
    db = get_db()
    try:
        table = db["learning_events"]
        where = {"session_id": session_id}
        if event_type:
            where["event_type"] = event_type
        rows = table.rows_where(" AND ".join(f"{k} = ?" for k in where), list(where.values()))
        return [
            {
                "id": r["id"],
                "session_id": r["session_id"],
                "event_type": r["event_type"],
                "payload": json.loads(r["payload"]),
                "created_at": r["created_at"],
            }
            for r in rows
        ]
    finally:
        db.conn.close()


def get_session_stats(session_id: str) -> dict:
    """获取会话学习统计"""
    db = get_db()
    try:
        events = list(db["learning_events"].rows_where("session_id = ?", [session_id]))

        stats = {
            "total_events": len(events),
            "chat_count": 0,
            "resource_generated_count": 0,
            "exercise_submitted_count": 0,
            "code_executed_count": 0,
            "exercise_passed_count": 0,
            "exercise_failed_count": 0,
        }

        for e in events:
            et = e["event_type"]
            if et == "chat":
                stats["chat_count"] += 1
            elif et == "resource_generated":
                stats["resource_generated_count"] += 1
            elif et == "exercise_submitted":
                stats["exercise_submitted_count"] += 1
                payload = json.loads(e["payload"])
                if payload.get("passed"):
                    stats["exercise_passed_count"] += 1
                else:
                    stats["exercise_failed_count"] += 1
            elif et == "code_executed":
                stats["code_executed_count"] += 1

        return stats
    finally:
        db.conn.close()
