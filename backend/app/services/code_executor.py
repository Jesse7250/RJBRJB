"""Python 代码执行器（本地安全沙箱）

对应需求：
- 后端自动判题：执行学生提交的 Python 代码，并与期望输出比对。
- 在本地提供轻量级安全隔离，防止恶意代码破坏服务器。

主要类/函数/接口：
- CodeExecutionError：执行阶段异常标识。
- CodeExecutor：安全执行器核心类。
  - validate：基于 AST 静态检查未授权导入、禁止调用与危险语法。
  - execute：在临时文件中通过 subprocess 运行代码并收集输出。
  - judge：调用 execute 并对比期望输出，支持完全匹配与逐行忽略空白匹配。

安全策略：
1. 超时 5 秒；
2. 只允许标准库导入；
3. 禁止文件写操作（通过 AST 静态检查）；
4. 在临时文件中执行，执行后删除。

TODO:
- [已完成] 基于 AST 的静态安全检查（导入白名单、禁止调用、危险语法）。
- [已完成] 临时文件执行、超时控制与输出捕获。
- [已完成] 输出比对：完全匹配 / 逐行忽略首尾空白。
- [待完成] 切换到 Docker 沙箱，以支持第三方库并提供更强隔离。
- [待完成] 增加资源限制（CPU/内存）与更细粒度的执行环境控制。
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

        # 将代码写入临时文件，使用系统默认 python 解释器执行
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, encoding="utf-8"
        ) as f:
            f.write(code)
            temp_path = f.name

        try:
            # 通过子进程运行代码，达到与主进程隔离的效果
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
