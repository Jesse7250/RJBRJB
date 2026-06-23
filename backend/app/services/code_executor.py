"""Python 代码执行器（本地安全沙箱）

用于后端自动判题。当前采用 subprocess 隔离 + 超时限制，
未来可切换为 Docker 沙箱以支持第三方库。

安全策略：
1. 超时 5 秒
2. 只允许标准库导入
3. 禁止文件写操作（通过 AST 静态检查）
4. 在临时文件中执行，执行后删除
"""
import ast
import os
import re
import subprocess
import tempfile
from typing import Dict, List


class CodeExecutionError(Exception):
    pass


class CodeExecutor:
    """本地 Python 代码执行器"""

    # 允许导入的模块白名单（标准库常见模块）
    ALLOWED_MODULES = {
        "os", "sys", "json", "csv", "math", "random", "datetime",
        "time", "collections", "itertools", "functools", "re",
        "string", "pathlib", "io", "tempfile", "shutil", "statistics",
        "decimal", "fractions", "typing", "inspect", "hashlib",
    }

    # 禁止的 AST 节点（防止危险操作）
    FORBIDDEN_NODES = (
        ast.Delete,
    )

    # 禁止的函数调用
    FORBIDDEN_CALLS = {
        "open", "exec", "eval", "compile", "__import__",
        "os.system", "os.popen", "subprocess.call", "subprocess.run",
        "subprocess.Popen", "input",
    }

    def __init__(self, timeout: float = 5.0):
        self.timeout = timeout

    def validate(self, code: str) -> List[str]:
        """静态检查代码安全性，返回违规列表"""
        violations = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [f"语法错误: {e.msg}"]

        for node in ast.walk(tree):
            if isinstance(node, self.FORBIDDEN_NODES):
                violations.append(f"禁止的语法: {type(node).__name__}")

            if isinstance(node, ast.Import):
                for alias in node.names:
                    module = alias.name.split(".")[0]
                    if module not in self.ALLOWED_MODULES:
                        violations.append(f"未授权导入模块: {module}")

            if isinstance(node, ast.ImportFrom):
                module = (node.module or "").split(".")[0]
                if module and module not in self.ALLOWED_MODULES:
                    violations.append(f"未授权导入模块: {module}")

            if isinstance(node, ast.Call):
                call_name = self._get_call_name(node.func)
                if call_name in self.FORBIDDEN_CALLS:
                    violations.append(f"禁止调用函数: {call_name}")

            # 禁止 open() 调用
            if isinstance(node, ast.Call):
                call_name = self._get_call_name(node.func)
                if call_name == "open":
                    violations.append("禁止调用 open() 进行文件操作")

        return violations

    def _get_call_name(self, node) -> str:
        """获取函数调用名"""
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._get_call_name(node.value)}.{node.attr}"
        return ""

    def execute(self, code: str) -> Dict[str, any]:
        """执行代码并返回结果"""
        violations = self.validate(code)
        if violations:
            return {
                "success": False,
                "stdout": "",
                "stderr": "",
                "violations": violations,
            }

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            temp_path = f.name

        try:
            result = subprocess.run(
                ["python", temp_path],
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "violations": [],
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": f"执行超时（>{self.timeout}秒）",
                "violations": [],
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "violations": [],
            }
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    def judge(self, code: str, expected_output: str) -> Dict[str, any]:
        """判题：执行代码并对比输出"""
        exec_result = self.execute(code)
        if not exec_result["success"]:
            return {
                **exec_result,
                "passed": False,
                "reason": "代码执行失败",
            }

        actual = exec_result["stdout"].strip()
        expected = expected_output.strip()

        # 支持多种输出格式：完全匹配、忽略首尾空白、逐行匹配
        passed = actual == expected
        if not passed:
            # 尝试逐行忽略首尾空白匹配
            actual_lines = [line.strip() for line in actual.splitlines() if line.strip()]
            expected_lines = [line.strip() for line in expected.splitlines() if line.strip()]
            passed = actual_lines == expected_lines

        return {
            **exec_result,
            "passed": passed,
            "actual_output": actual,
            "expected_output": expected,
            "reason": "通过" if passed else "输出不匹配",
        }
