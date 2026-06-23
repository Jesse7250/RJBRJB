"""测试代码执行与判题接口"""
import os
import sys

os.environ["GRAPH_BACKEND"] = "memory"
os.environ["LLM_PROVIDER"] = "mock"

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_execute():
    print("\n--- 执行代码 ---")
    r = client.post("/api/code/execute", json={"code": "print('Hello, Python!')"})
    print(r.json())
    assert r.status_code == 200
    assert r.json()["success"] is True
    assert "Hello, Python!" in r.json()["stdout"]


def test_judge_pass():
    print("\n--- 判题：通过 ---")
    code = "print(2 + 3)"
    r = client.post("/api/code/judge", json={
        "code": code,
        "expected_output": "5",
    })
    data = r.json()
    print(data)
    assert r.status_code == 200
    assert data["passed"] is True


def test_judge_fail():
    print("\n--- 判题：不通过 ---")
    code = "print(2 + 2)"
    r = client.post("/api/code/judge", json={
        "code": code,
        "expected_output": "5",
    })
    data = r.json()
    print(data)
    assert r.status_code == 200
    assert data["passed"] is False


def test_forbidden_import():
    print("\n--- 禁止导入 ---")
    r = client.post("/api/code/execute", json={"code": "import requests\nprint('ok')"})
    print(r.json())
    assert r.status_code == 200
    assert r.json()["success"] is False


if __name__ == "__main__":
    test_execute()
    test_judge_pass()
    test_judge_fail()
    test_forbidden_import()
    print("\n[OK] 代码执行与判题测试通过")
