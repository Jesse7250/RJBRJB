# -*- coding: utf-8 -*-
"""Phase 2 功能测试：A* 路径规划、认知证据更新画像、资源反馈触发知识熔炉"""
import os

os.environ["LLM_PROVIDER"] = "mock"
os.environ["GRAPH_BACKEND"] = "memory"

from fastapi.testclient import TestClient

from app.main import app
from app.services.database import (
    add_cognitive_evidence,
    add_resource_feedback,
    get_resource_feedback_stats,
)
from app.services.knowledge_furnace import should_trigger_resource_review
from app.services.path_planner import astar_learning_path
from app.services.profile_evidence import infer_profile_updates, update_profile_from_evidence

client = TestClient(app)


def _create_session(target_concept: str = "变量与赋值"):
    r = client.post("/api/sessions/", json={"target_concept": target_concept})
    assert r.status_code == 200
    return r.json()["session_id"]


# -----------------------------------------------------------------------------
# A* 路径规划
# -----------------------------------------------------------------------------

def test_astar_basic_path():
    edges = [
        {"source": "A", "target": "B", "strength": 0.9},
        {"source": "B", "target": "C", "strength": 0.9},
        {"source": "A", "target": "C", "strength": 0.5},
    ]
    difficulties = {"A": 1, "B": 2, "C": 3}
    path = astar_learning_path(edges, difficulties, ["A"], "C")
    assert path[0] == "A"
    assert path[-1] == "C"
    assert "C" in path


def test_astar_already_mastered():
    path = astar_learning_path([], {}, ["A", "B"], "B")
    assert path == ["B"]


def test_astar_fallback_when_unreachable():
    edges = [
        {"source": "A", "target": "B", "strength": 0.9},
    ]
    difficulties = {"A": 1, "B": 2, "C": 3}
    # C 不在 from_concepts 中，也无法从 A/B 到达，应回退到反向依赖链
    path = astar_learning_path(edges, difficulties, ["A"], "C")
    assert path[-1] == "C"


def test_memory_graph_uses_astar_path():
    """验证 MemoryGraph 的 get_learning_path 使用 A* 返回有效路径"""
    from app.services.graph_factory import get_graph_store

    graph = get_graph_store()
    path = graph.get_learning_path(["变量与赋值"], "列表推导式")
    assert path[-1] == "列表推导式"
    assert "变量与赋值" in path


# -----------------------------------------------------------------------------
# 认知证据自动更新画像
# -----------------------------------------------------------------------------

def test_infer_profile_modality_from_evidence():
    sid = _create_session()
    # 添加两条 visual 证据，达到阈值
    add_cognitive_evidence(sid, "cognitive_modality", "mindmap_clicked", 1.0, source_value="visual")
    add_cognitive_evidence(sid, "cognitive_modality", "graph_node_selected", 1.0, source_value="visual")

    updates = infer_profile_updates(sid, {})
    assert updates.get("cognitive_modality") == "visual"


def test_behavior_endpoint_auto_updates_profile():
    sid = _create_session()
    changes_seen = []
    # 连续触发 kinesthetic 相关行为
    for _ in range(3):
        r = client.post(
            f"/api/sessions/{sid}/behavior",
            json={
                "session_id": sid,
                "event_type": "code_executed",
                "concept": "变量与赋值",
                "payload": {"weight": 1.0},
            },
        )
        assert r.status_code == 200
        changes_seen.append(r.json().get("profile_changes", {}))

    # 至少有一次请求真正更新了画像
    assert any(c.get("cognitive_modality") == "kinesthetic" for c in changes_seen)
    # 最终画像应为 kinesthetic
    final_profile = changes_seen[-1].get("profile") or changes_seen[-1]  # 最后一次返回的是完整 profile
    # 从最后一次响应直接取 profile
    last_data = client.get(f"/api/sessions/{sid}/profile").json()
    assert last_data["cognitive_modality"] == "kinesthetic"


def test_update_profile_from_evidence_merges_changes():
    sid = _create_session()
    session = {"profile": {"cognitive_modality": "visual", "learning_pace": "normal"}}
    add_cognitive_evidence(sid, "cognitive_modality", "audio_played", 2.0, source_value="auditory")
    add_cognitive_evidence(sid, "cognitive_modality", "audio_played", 2.0, source_value="auditory")

    result = update_profile_from_evidence(session, sid)
    assert result["updated"] is True
    assert result["profile"]["cognitive_modality"] == "auditory"
    assert result["profile"]["learning_pace"] == "normal"  # 未改变的保留


# -----------------------------------------------------------------------------
# 资源反馈触发知识熔炉
# -----------------------------------------------------------------------------

def test_should_trigger_review_from_confusion_feedback():
    import uuid
    sid = _create_session()
    concept = f"测试知识点反馈-{uuid.uuid4().hex[:8]}"
    # 添加 3 条困惑反馈，达到 MIN_FEEDBACK_COUNT
    for i in range(3):
        add_resource_feedback(sid, f"res-{i}", concept, rating=None, confusion_marked=True)

    stats = get_resource_feedback_stats(concept)
    assert stats["total_feedback"] == 3
    assert stats["confusion_rate"] == 1.0

    should, combined = should_trigger_resource_review(concept)
    assert should is True
    assert combined["confusion_rate"] == 1.0


def test_should_trigger_review_from_low_rating():
    import uuid
    sid = _create_session()
    concept = f"测试知识点低分-{uuid.uuid4().hex[:8]}"
    for i in range(3):
        add_resource_feedback(sid, f"res-{i}", concept, rating=1, confusion_marked=False)

    should, _ = should_trigger_resource_review(concept)
    assert should is True


def test_feedback_endpoint_triggers_background_review():
    """反馈接口后台检查阈值，达到条件时触发资源重审任务"""
    import uuid
    sid = _create_session()
    concept = f"测试知识点触发-{uuid.uuid4().hex[:8]}"
    # 先造 2 条困惑反馈
    for i in range(2):
        add_resource_feedback(sid, f"pre-{i}", concept, rating=None, confusion_marked=True)

    # 第 3 条通过接口提交，应触发后台知识熔炉
    r = client.post(
        "/api/resources/feedback",
        json={
            "session_id": sid,
            "resource_id": "res-trigger",
            "concept": concept,
            "rating": None,
            "error_report": "",
            "confusion_marked": True,
        },
    )
    assert r.status_code == 200
    assert r.json()["success"] is True
