"""输入安全过滤测试"""
import os

os.environ.setdefault("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY", "sk-PLACEHOLDER"))
os.environ.setdefault("LLM_PROVIDER", "mock")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_safe_message():
    r = client.post("/api/sessions/", json={"target_concept": "文件操作"})
    sid = r.json()["session_id"]
    res = client.post(
        f"/api/sessions/{sid}/chat",
        json={"message": "我想学习文件操作", "message_type": "text"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["response_type"] != "safety_warning"
    print("[OK] 正常消息通过安全过滤")


def test_unsafe_message():
    r = client.post("/api/sessions/", json={"target_concept": "文件操作"})
    sid = r.json()["session_id"]
    res = client.post(
        f"/api/sessions/{sid}/chat",
        json={"message": "这个傻逼课程太难了，我想去死", "message_type": "text"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["response_type"] == "safety_warning"
    assert "Guardian" in data["agent_name"]
    print("[OK] 敏感消息被安全过滤拦截")


if __name__ == "__main__":
    test_safe_message()
    test_unsafe_message()
