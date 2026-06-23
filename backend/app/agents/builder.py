"""Builder Agent：多模态学习资源生成

TODO:
- [待完成] 使用更鲁棒的输出格式（如 JSON Schema / function calling）约束 LLM
- [待完成] 生成练习题时自动附带测试用例与判题逻辑
- [待完成] 生成真实的 Mermaid 思维导图（当前为简单依赖图）
- [待完成] 接入讯飞 TTS 生成音频文件
- [待完成] 根据认知风格调整资源内容深度与示例数量
- [待完成] 实现资源生成结果缓存
"""
import json
import re
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.models.schemas import ResourcePackage
from app.services.graph_factory import get_graph_store


class BuilderAgent(BaseAgent):
    """根据画像和知识约束生成 5 种资源类型"""

    name = "Builder"
    system_prompt = """你是一位资深的 Python 教学资源设计师。
你的任务是根据学生的画像和知识图谱约束，生成高质量的教学资源。

输出格式必须是 JSON：
{
  "document": "Markdown 格式的概念讲解文档",
  "mindmap": "Mermaid 思维导图语法",
  "exercises": [
    {"question": "题目描述", "starter_code": "初始代码", "expected_output": "期望输出", "hints": ["提示1"], "solution": "参考答案"}
  ],
  "code_cases": [
    {"title": "案例标题", "code": "可运行代码", "explanation": "案例说明"}
  ],
  "audio_text": "用于语音讲解的文本"
}

注意：
1. 所有代码必须可在 Python 3.10+ 运行
2. 不要引入未授权的外部库
3. 练习题要有难度梯度
4. 代码中的反斜杠请使用原始字符串 r'...' 或正斜杠路径，避免转义导致语法错误
5. 只输出 JSON，不要 markdown 代码块外的内容"""

    def run(
        self,
        concept: str,
        profile: Dict[str, Any],
    ) -> ResourcePackage:
        """生成资源包"""
        graph = get_graph_store()
        concept_info = graph.get_concept(concept) or {}

        prompt = self._build_prompt(concept, concept_info, profile)
        raw = self.think(prompt)

        # 解析 JSON
        parsed = self._extract_json(raw)
        if not parsed:
            parsed = self._fallback_parse(concept, raw)

        package = ResourcePackage(
            concept=concept,
            document=parsed.get("document", raw),
            mindmap=parsed.get("mindmap", self._generate_mindmap(concept, concept_info)),
            exercises=parsed.get("exercises", []),
            code_cases=parsed.get("code_cases", []),
            audio_text=parsed.get(
                "audio_text",
                f"欢迎来到智学蜂巢。本节我们学习「{concept}」。{concept_info.get('description', '')}",
            ),
        )

        return package

    def _build_prompt(self, concept: str, concept_info: dict, profile: Dict[str, Any]) -> str:
        prerequisites = concept_info.get("prerequisites", [])
        pitfalls = concept_info.get("pitfalls", [])
        difficulty = concept_info.get("difficulty", 3)
        student_level = profile.get("knowledge_level", 2.0)

        scaffolding = (
            "请提供更多代码示例和逐步解释，确保基础薄弱的学生也能理解。"
            if student_level < difficulty - 1
            else "可以适当增加挑战性的内容和拓展知识。"
        )

        return f"""请为知识点「{concept}」生成一份 Python 教学资源。

【知识约束 - 必须遵守】
- 前置知识：学生已掌握 {', '.join(prerequisites) if prerequisites else 'Python基础'}
- 难度等级：{difficulty}/5
- 预计学习时长：{concept_info.get('estimated_time', 30)} 分钟
- 常见易错点：{', '.join([p.get('description', '') for p in pitfalls]) if pitfalls else '无'}

【学生画像 - 个性化调整】
- 知识水平：{student_level}/5
- 认知风格：{profile.get('cognitive_field', 'dependent')} · {profile.get('cognitive_modality', 'visual')}
- 学习节奏：{profile.get('learning_pace', 'normal')}
- 目标导向：{profile.get('goal_orientation', 'application')}
{scaffolding}

【输出要求】
1. 概念讲解（Markdown 格式，含 2-3 个代码示例）
2. 思维导图（Mermaid 语法）
3. 3 道渐进式编程练习题
4. 1-2 个可运行代码实操案例
5. 常见错误警示
6. 语音讲解文本（200 字以内）

所有代码必须可在 Python 3.10+ 中运行，不要引入未授权的外部库。
代码中若涉及 Windows 路径或反斜杠，请使用原始字符串 r'...' 或正斜杠，避免转义错误。"""

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从 LLM 输出中提取 JSON

        TODO: [待完成] 增加更多容错和结构化输出格式校验
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None

    def _fallback_parse(self, concept: str, raw: str) -> Dict[str, Any]:
        """JSON 解析失败时，按规则拆分内容

        TODO: [待完成] 改进兜底解析，支持更多资源类型
        """
        # 提取所有代码块
        code_blocks = re.findall(r"```python\s*(.*?)\s*```", raw, re.DOTALL)

        exercises = []
        code_cases = []
        for i, code in enumerate(code_blocks):
            if i < 2:
                code_cases.append({
                    "title": f"代码案例 {i + 1}",
                    "code": code.strip(),
                    "explanation": "",
                })
            else:
                exercises.append({
                    "question": f"练习 {i - 1}",
                    "starter_code": code.strip(),
                    "expected_output": "",
                    "hints": [],
                    "solution": code.strip(),
                })

        return {
            "document": raw,
            "exercises": exercises,
            "code_cases": code_cases,
        }

    def revise(
        self,
        concept: str,
        profile: Dict[str, Any],
        current_package: Dict[str, Any],
        feedback: str,
    ) -> ResourcePackage:
        """根据辩论议会反馈修订资源包"""
        prompt = self._build_revision_prompt(concept, profile, current_package, feedback)
        raw = self.think(prompt)

        parsed = self._extract_json(raw)
        if not parsed:
            parsed = self._fallback_parse(concept, raw)

        return ResourcePackage(
            concept=concept,
            document=parsed.get("document", current_package.get("document", raw)),
            mindmap=parsed.get("mindmap", current_package.get("mindmap", "")),
            exercises=parsed.get("exercises", current_package.get("exercises", [])),
            code_cases=parsed.get("code_cases", current_package.get("code_cases", [])),
            audio_text=parsed.get("audio_text", current_package.get("audio_text", "")),
        )

    def _build_revision_prompt(
        self,
        concept: str,
        profile: Dict[str, Any],
        current_package: Dict[str, Any],
        feedback: str,
    ) -> str:
        """构建修订 Prompt"""
        return f"""请为知识点「{concept}」修订以下 Python 教学资源。

【学生画像】
{json.dumps(profile, ensure_ascii=False)}

【当前资源】
{json.dumps(current_package, ensure_ascii=False)}

【辩论议会反馈 - 必须据此修改】
{feedback}

【输出要求】
输出 JSON，结构与之前一致：
{{
  "document": "Markdown 格式的概念讲解文档",
  "mindmap": "Mermaid 思维导图语法",
  "exercises": [...],
  "code_cases": [...],
  "audio_text": "语音讲解文本"
}}

注意：
1. 保留当前资源中合理的部分，仅针对反馈进行修订。
2. 所有代码必须可在 Python 3.10+ 运行，不要引入未授权外部库。
3. 代码中若涉及 Windows 路径或反斜杠，请使用原始字符串 r'...' 或正斜杠。
4. 只输出 JSON，不要 markdown 代码块外的内容。"""

    def _generate_mindmap(self, concept: str, concept_info: dict) -> str:
        """生成 Mermaid 思维导图

        TODO: [待完成] 让 LLM 生成知识点内部结构的思维导图，而非仅依赖关系
        """
        prerequisites = concept_info.get("prerequisites", [])
        next_concepts = concept_info.get("next_concepts", [])

        lines = ["graph TD"]
        lines.append(f"    A[{concept}] --> B[前置知识]")
        for i, pre in enumerate(prerequisites[:5]):
            lines.append(f"    B --> B{i}[{pre}]")

        lines.append(f"    A --> C[后续知识]")
        for i, nxt in enumerate(next_concepts[:5]):
            lines.append(f"    C --> C{i}[{nxt}]")

        return "\n".join(lines)
