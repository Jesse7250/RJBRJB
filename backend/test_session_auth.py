"""会话与用户绑定测试"""
import os
import uuid

os.environ.setdefault("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY", "sk-PLACEHOLDER"))
os.environ.setdefault("LLM_PROVIDER", "mock")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_session_with_auth():
    username = f"session_user_{uuid.uuid4().hex[:8]}"
    # 注册
    r1 = client.post("/api/auth/register", json={"username": username, "password": "123456"})
    assert r1.status_code == 200
    token = r1.json()["access_token"]

    # 匿名创建会话
    r2 = client.post("/api/sessions/", json={"target_concept": "文件操作"})
    assert r2.status_code == 200
    anon_session = r2.json()["session_id"]

    # 登录后创建会话
    r3 = client.post(
        "/api/sessions/",
        json={"target_concept": "文件操作"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r3.status_code == 200
    user_session = r3.json()["session_id"]

    # 列表应只返回 user_session
    r4 = client.get("/api/sessions/", headers={"Authorization": f"Bearer {token}"})
    assert r4.status_code == 200
    data = r4.json()
    session_ids = [s["session_id"] for s in data["sessions"]]
    assert user_session in session_ids
    assert anon_session not in session_ids
    print("[OK] 会话与用户绑定测试通过")


if __name__ == "__main__":
    test_session_with_auth()
