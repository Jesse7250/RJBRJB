"""神经符号认知架构 - 约束与校验层

三层防幻觉机制：
1. GraphRAG 知识锚定：从知识图谱获取约束，注入 Prompt
2. 生成后校验：AST 解析 + 未学概念检测
3. Guardian 安全过滤：由辩论议会执行
"""
import ast
import re
from typing import Dict, List

from app.services.graph_factory import get_graph_store


class NeuroSymbolicValidator:
    """神经符号融合校验器"""

    # Python 标准库常用模块，教学中默认允许使用
    DEFAULT_ALLOWED_MODULES = {
        "os", "sys", "json", "csv", "math", "random", "datetime",
        "time", "collections", "itertools", "functools", "re",
        "string", "pathlib", "io", "tempfile", "shutil",
    }

    # 基础通用概念，教学中经常顺带提及，不应视为超纲
    BASIC_CONCEPT_WHITELIST = {
        "变量", "赋值", "数据类型", "字符串", "数字", "整数", "浮点数",
        "布尔值", "列表", "元组", "字典", "集合", "条件语句", "if",
        "循环", "for", "while", "函数", "参数", "返回值", "模块",
        "导入", "异常", "错误", "输入输出", "print", "注释",
        "异常处理", "try", "except", "finally", "错误处理", "with",
        "上下文管理器", "编码", "路径",
    }

    def __init__(self):
        self.graph = get_graph_store()

    def get_concept_constraints(self, concept: str) -> Dict[str, any]:
        """获取知识图谱约束"""
        concept_info = self.graph.get_concept(concept) or {}
        return {
            "prerequisites": concept_info.get("prerequisites", []),
            "difficulty": concept_info.get("difficulty", 3),
            "estimated_time": concept_info.get("estimated_time", 30),
            "pitfalls": concept_info.get("pitfalls", []),
            "allowed_modules": concept_info.get("allowed_modules", []),
            "forbidden_concepts": self._compute_forbidden_concepts(concept),
        }

    def _compute_forbidden_concepts(self, concept: str) -> List[str]:
        """计算当前知识点未学过的概念"""
        all_concepts = self.graph.get_all_concepts()
        allowed = set(self.graph.get_prerequisites(concept))
        allowed.add(concept)
        return [c["name"] for c in all_concepts if c["name"] not in allowed]

    def build_constrained_prompt(
        self, concept: str, profile: Dict[str, any]
    ) -> str:
        """构建带知识图谱约束的 Prompt"""
        constraints = self.get_concept_constraints(concept)
        student_level = profile.get("knowledge_level", 2.0)
        difficulty = constraints["difficulty"]

        scaffolding = (
            "请在讲解时提供更多的代码示例和逐步解释，确保基础薄弱的学生也能理解。"
            if student_level < difficulty - 1
            else "可以适当增加挑战性的内容和拓展知识。"
        )

        pitfalls = constraints["pitfalls"]
        pitfalls_text = "\n".join(
            f"- {p.get('description', '')}" for p in pitfalls
        ) or "无"

        return f"""你是一位Python教学专家。请为"{concept}"生成教学资源。

【知识约束 - 必须遵守】
- 前置知识假设：学生已掌握 {', '.join(constraints['prerequisites']) if constraints['prerequisites'] else 'Python基础'}，请不要重复讲解这些内容
- 难度等级：{difficulty}/5
- 预计学习时长：{constraints['estimated_time']}分钟
- 禁止涉及的知识点：{', '.join(constraints['forbidden_concepts'][:10])}
- 常见易错点预警：
{pitfalls_text}

【学生画像 - 个性化调整】
- 学生当前水平：{student_level}/5
- 认知风格：{profile.get('cognitive_field', 'dependent')}型，{profile.get('cognitive_modality', 'visual')}偏好
{scaffolding}

【输出要求】
请生成以下内容：
1. 概念讲解（Markdown格式，含代码示例）
2. 配套练习题（3道，难度递增）
3. 常见错误警示

所有代码必须是可运行的Python代码。"""

    def _sanitize_code(self, code: str) -> str:
        r"""清理 LLM 生成的常见格式错误

        主要处理：
        1. 反斜杠后带有空格或换行导致的 line continuation 错误。
        2. Windows 路径裸反斜杠导致的 Unicode 转义错误（如 C:\Users、.\data\file）。
        3. 字符串中的转义序列误报（如 \U、\u、\N 等被当作 unicode escape）。

        说明：
        - 这里的清理仅用于 AST 校验，不会回写到展示给用户的资源内容。
        - 保护 \\、\'、\" 不被破坏，避免字符串引号失衡。
        """
        # 1. 移除显式行续符及其后的空白/换行（保留同一逻辑行的内容）
        code = re.sub(r"\\\s*\n\s*", "", code)

        # 2. 保护真实的双反斜杠与转义引号，避免后续替换破坏字符串结构
        placeholders = {
            "__EDU_BACKSLASH__": "\\\\",
            "__EDU_SQUOTE__": "\\'",
            "__EDU_DQUOTE__": '\\"',
        }
        for placeholder, literal in placeholders.items():
            code = code.replace(literal, placeholder)

        # 3. 将剩余的反斜杠+字母替换为正斜杠+字母，消除 unicodeescape 误报
        #    例如 C:\Users -> C:/Users；.\data -> ./data；\n -> /n（仅用于校验）
        code = re.sub(r"\\([A-Za-z])", r"/\1", code)

        # 4. 恢复受保护的转义序列
        for placeholder, literal in placeholders.items():
            code = code.replace(placeholder, literal)

        return code

    def validate_code_blocks(self, content: str, concept: str) -> List[str]:
        """校验 Markdown 中的 Python 代码块

        检查：
        1. 语法错误
        2. 导入未授权模块
        3. 调用未学概念（简化：通过概念名匹配）
        """
        violations = []
        constraints = self.get_concept_constraints(concept)
        allowed_modules = set(constraints.get("allowed_modules", []))
        forbidden_concepts = set(constraints.get("forbidden_concepts", []))

        # 合并允许模块：知识图谱配置 + 标准库默认白名单
        allowed_modules = allowed_modules | self.DEFAULT_ALLOWED_MODULES

        code_blocks = re.findall(r"```python\s*(.*?)\s*```", content, re.DOTALL)
        for code in code_blocks:
            code = code.strip()
            if not code:
                continue

            # AST 语法检查（先尝试清理后的代码）
            sanitized = self._sanitize_code(code)
            try:
                tree = ast.parse(sanitized)
            except SyntaxError as e:
                violations.append(f"代码语法错误: {e.msg}")
                continue

            # 导入检查
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name.split(".")[0]
                        if module_name not in allowed_modules:
                            violations.append(f"未授权导入模块: {module_name}")
                elif isinstance(node, ast.ImportFrom):
                    module_name = (node.module or "").split(".")[0]
                    if module_name and module_name not in allowed_modules:
                        violations.append(f"未授权导入模块: {module_name}")

        # 文本级别：检查是否提到未学概念（过滤基础通用概念）
        for concept_name in forbidden_concepts:
            if concept_name in self.BASIC_CONCEPT_WHITELIST:
                continue
            if concept_name in content:
                # 排除目标概念自身和前置知识
                if concept_name != concept and concept_name not in constraints["prerequisites"]:
                    violations.append(f"可能涉及未学概念: {concept_name}")

        return violations

    def validate_resource(
        self, content: str, concept: str
    ) -> Dict[str, any]:
        """完整校验入口"""
        forbidden = self.graph.check_forbidden_concepts(content, concept)
        ast_violations = self.validate_code_blocks(content, concept)

        return {
            "passed": len(forbidden) == 0 and len(ast_violations) == 0,
            "forbidden_concepts": forbidden,
            "ast_violations": ast_violations,
        }
