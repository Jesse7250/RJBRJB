"""一键运行所有后端测试"""
import subprocess
import sys

TESTS = [
    "test_auth.py",
    "test_session_auth.py",
    "test_cache.py",
    "test_chat_stream.py",
    "test_code_executor.py",
    "test_evaluator.py",
    "test_full_chain.py",
    "test_safety_filter.py",
    "test_sse.py",
    "test_ablation.py",
    "test_backslash_sanitize.py",
]


def main():
    failures = []
    for test in TESTS:
        print(f"\n{'='*60}")
        print(f"Running {test}")
        print('=' * 60)
        result = subprocess.run(
            [sys.executable, test],
            cwd=".",
        )
        if result.returncode != 0:
            failures.append(test)

    print("\n" + "=" * 60)
    if failures:
        print(f"[FAIL] 以下测试未通过：{', '.join(failures)}")
        sys.exit(1)
    else:
        print(f"[OK] 全部 {len(TESTS)} 个测试通过")


if __name__ == "__main__":
    main()
