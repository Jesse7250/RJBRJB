"""快速验证后端 API"""
import os

os.environ["GRAPH_BACKEND"] = "memory"
os.environ["LLM_PROVIDER"] = "mock"

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    print("/health:", r.status_code, r.json())
    assert r.status_code == 200


def test_graph():
    r = client.get("/api/graph/")
    data = r.json()
    print("/api/graph/:", r.status_code, len(data.get("nodes", [])), "nodes")
    assert r.status_code == 200
    assert len(data["nodes"]) > 0


def test_session():
    r = client.post("/api/sessions/", json={"target_concept": "文件操作"})
    data = r.json()
    print("/api/sessions/:", r.status_code, data["session_id"])
    assert r.status_code == 200
    return data["session_id"]


def test_chat(session_id: str):
    r = client.post(
        f"/api/sessions/{session_id}/chat",
        json={"message": "我想学习文件操作", "message_type": "text"},
    )
    data = r.json()
    print("/chat agent:", data.get("agent_name"))
    print("/chat type:", data.get("response_type"))
    print("/chat next_action:", data.get("content", {}).get("next_action"))
    assert r.status_code == 200


def test_generate_resource(session_id: str):
    r = client.post(f"/api/resources/generate-for-session/{session_id}?concept=文件操作")
    data = r.json()
    print("/resources/generate status:", r.status_code)
    print("concept:", data.get("concept"))
    print("debate_status:", data.get("debate_report", {}).get("status"))
    print("debate rounds:", len(data.get("debate_report", {}).get("rounds", [])))
    print("validation:", data.get("validation"))
    print("package keys:", list(data.get("package", {}).keys()))
    assert r.status_code == 200
    assert data.get("concept") == "文件操作"
    assert "package" in data
    assert "debate_report" in data


if __name__ == "__main__":
    test_health()
    test_graph()
    sid = test_session()
    test_chat(sid)
    test_generate_resource(sid)
    print("\n[OK] 所有接口验证通过")
