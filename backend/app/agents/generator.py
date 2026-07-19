"""Generator Agent：多模态学习资源生成

对应需求/功能：
- 根据学生画像与知识图谱约束，生成个性化 Python 教学资源包。
- 资源类型包括：概念讲解文档（Markdown）、思维导图（Mermaid）、编程练习题、
  可运行代码案例、语音讲解文本。
- 由 BuilderAgent 演进而来，职责更清晰：只负责生成教学资源，不参与审核。

主要类/函数：
- GeneratorAgent.run(message)：统一入口，从 AgentMessage 中提取 concept 和 profile，
  返回包含 ResourcePackage 的 AgentMessage。
- GeneratorAgent.generate(concept, profile)：核心生成逻辑，调用 LLM 并解析 JSON。
- GeneratorAgent.revise(...)：根据 Reviewer/DebateCouncil 的反馈修订资源包。
- _build_prompt / _build_revision_prompt：构造生成/修订 Prompt。
- _extract_json / _fallback_parse：LLM 输出解析与兜底拆分。
- _generate_mindmap：基于前置依赖和关联知识点生成简单 Mermaid 图。
- BuilderAgent = GeneratorAgent：为兼容旧导入保留别名。

TODO:
- [已完成] 5 类教学资源生成已实现
- [已完成] JSON 解析失败兜底与 Mermaid 思维导图回退已实现
- [已完成] 根据反馈修订资源 revise() 已实现
- [待完成] 接入真正的 TTS 服务生成音频文件 URL
- [待完成] 接入代码执行器自动验证生成的代码案例可运行性
- [待完成] 使用 JSON Schema / function calling 强制结构化输出，减少解析失败
"""
import json
import re
from typing import Any, Dict, List, Optional

from app.agents.base import AgentMessage, BaseAgent
from app.models.schemas import ResourcePackage
from app.services.code_executor import CodeExecutor
from app.services.graph_factory import get_graph_store


class GeneratorAgent(BaseAgent):
    """根据画像和知识约束生成 5 种资源类型"""

    name = "Generator"
    _DOC_START = "<!-- DOC_START -->"
    _DOC_END = "<!-- DOC_END -->"
    system_prompt = """你是一位资深的 Python 教学资源设计师。
你的任务是根据学生的画像和知识图谱约束，生成高质量的教学资源。

输出格式必须是 JSON：
{
  "document": "Markdown 格式的概念讲解文档",
  "mindmap": "Mermaid mindmap 径向思维导图语法，必须包含 前置依赖、后续概念、核心要点、易错点 四个分支",
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
5. 只输出 JSON，不要 markdown 代码块外的内容
6. mindmap 字段请使用 Mermaid 10 支持的 `mindmap` 语法，以 `mindmap\n  root((概念名))` 开头，至少展开 4 个分支，不能只有单个节点
7. 如果需要思考，请把思考过程放在 <think>...</think> 标签内，最终 JSON 放在标签外；document 字段中严禁出现思考过程、规划文字或 JSON 片段
8. document 字段必须包含真正的讲义 Markdown，内容充实、有知识点讲解、可运行代码示例和针对性练习"""

    def run(self, message: AgentMessage) -> AgentMessage:
        """统一入口：从 AgentMessage 中提取 concept 和 profile，生成资源"""
        # 优先从 payload 取 concept，其次从上下文中取目标知识点
        concept = message.payload.get("concept") or message.context.get("target_concept")
        profile = message.context.get("profile", {})
        if not concept:
            return message.reply({"error": "未指定知识点"}, stage="generator", from_agent=self.name)

        package = self.generate(concept, profile)
        return message.reply({"package": package.model_dump()}, stage="generator", from_agent=self.name)

    def generate(self, concept: str, profile: Dict[str, Any]) -> ResourcePackage:
        """生成资源包（保持与旧 BuilderAgent 兼容）"""
        graph = get_graph_store()
        concept_info = graph.get_concept(concept) or {}

        prompt = self._build_prompt(concept, concept_info, profile)
        raw = self.think(prompt, max_tokens=8192)

        # 尝试从 LLM 输出中解析 JSON；失败则使用兜底拆分
        parsed = self._extract_json(raw)
        if not parsed:
            parsed = self._fallback_parse(concept, raw)

        # 用解析结果构造 ResourcePackage，缺失字段提供合理默认值
        document = self._clean_document(parsed.get("document") or raw)
        if not self._is_substantial_document(document, concept):
            document = self._generate_document(concept, concept_info)

        mindmap = self._unescape_text(
            parsed.get("mindmap") or self._generate_mindmap(concept, concept_info)
        )

        exercises = self._normalize_exercises(
            [self._unescape_exercise(ex) for ex in (parsed.get("exercises") or [])], concept
        )
        if not exercises:
            exercises = self._default_exercises(concept, concept_info)

        code_cases = self._normalize_code_cases(
            [self._unescape_code_case(c) for c in (parsed.get("code_cases") or [])]
        )
        if not code_cases:
            code_cases = self._default_code_cases(concept)

        # 自动修正不可运行的代码案例（最多尝试 2 轮）
        code_cases = self._auto_fix_code_cases(
            code_cases, concept, concept_info, profile
        )

        package = ResourcePackage(
            concept=concept,
            document=document,
            mindmap=mindmap,
            exercises=exercises,
            code_cases=code_cases,
            audio_text=self._unescape_text(
                parsed.get(
                    "audio_text",
                    f"欢迎来到智慧伴学。本节我们学习「{concept}」。{concept_info.get('description', '')}",
                )
            ),
        )

        return package

    def revise(self, concept: str, profile: Dict[str, Any],
               current_package: Dict[str, Any], feedback: str) -> ResourcePackage:
        """根据反馈修订资源包"""
        prompt = self._build_revision_prompt(concept, profile, current_package, feedback)
        raw = self.think(prompt, max_tokens=8192)

        parsed = self._extract_json(raw)
        if not parsed:
            parsed = self._fallback_parse(concept, raw)

        return ResourcePackage(
            concept=concept,
            document=self._clean_document(
                parsed.get("document", current_package.get("document", raw))
            ),
            mindmap=parsed.get("mindmap", current_package.get("mindmap", "")),
            exercises=self._normalize_exercises(
                parsed.get("exercises", current_package.get("exercises", [])), concept
            ),
            code_cases=self._normalize_code_cases(
                parsed.get("code_cases", current_package.get("code_cases", []))
            ),
            audio_text=parsed.get("audio_text", current_package.get("audio_text", "")),
        )

    def _build_prompt(self, concept: str, concept_info: dict, profile: Dict[str, Any]) -> str:
        prerequisites = concept_info.get("prerequisites", []) or []
        next_concepts = concept_info.get("next_concepts", []) or []
        objectives = concept_info.get("learning_objectives", []) or []
        pitfalls = concept_info.get("pitfalls", []) or []
        common_pitfalls = concept_info.get("common_pitfalls", []) or []
        description = (concept_info.get("description") or "").strip()
        difficulty = concept_info.get("difficulty", 3)
        student_level = profile.get("knowledge_level", 2.0)

        scaffolding = (
            "请提供更多代码示例和逐步解释，确保基础薄弱的学生也能理解。"
            if student_level < difficulty - 1
            else "可以适当增加挑战性的内容和拓展知识。"
        )

        objectives_text = "\n".join(f"- {obj}" for obj in objectives[:6]) or "- 理解基本概念与用法"
        pitfalls_text = "\n".join(
            f"- {p.get('description', '')}" for p in pitfalls
        ) if pitfalls else "\n".join(f"- {p}" for p in common_pitfalls[:6]) or "- 无"

        return f"""请为知识点「{concept}」生成一份具体、可教学的 Python 教学资源。禁止套话，必须输出真正的知识点内容。

【知识点信息 - 必须融入讲义】
- 概念定义：{description or '请根据知识点自行给出准确定义'}
- 难度等级：{difficulty}/5
- 预计学习时长：{concept_info.get('estimated_time', 30)} 分钟
- 前置知识：{', '.join(prerequisites) if prerequisites else 'Python基础'}
- 后续关联：{', '.join(next_concepts) if next_concepts else '无'}
- 学习目标：
{objectives_text}
- 常见易错点：
{pitfalls_text}

【学生画像 - 个性化调整】
- 知识水平：{student_level}/5
- 认知风格：{profile.get('cognitive_field', 'dependent')} · {profile.get('cognitive_modality', 'visual')}
- 学习节奏：{profile.get('learning_pace', 'normal')}
- 目标导向：{profile.get('goal_orientation', 'application')}
{scaffolding}

【输出要求 - 必须具体】
1. 概念讲解（Markdown）：
   - 必须给出「{concept}」的准确定义，不能只说“它是重要基础”。如果上面的知识点信息较简略，请结合 Python 通用知识自行扩展。
   - 列出 3-5 个核心要点，每一点用一句话讲清楚“是什么/怎么用”，不要复制粘贴知识点信息。
   - 提供 2-3 个与该知识点**直接相关**的可运行 Python 代码示例，代码必须真正展示「{concept}」的用法，禁止用 `print("学习 {concept}")` 这类占位符糊弄。
   - 给出常见错误警示，每个错误配一个错误代码片段和正确写法。
   - 文档字数不少于 800 中文字符，确保内容充实、像真实教材一样有细节。
2. 思维导图：使用 Mermaid 10 `mindmap` 径向语法，以 `mindmap\n  root((概念名))` 开头，至少包含 前置依赖、后续概念、核心要点、易错点 四个分支，禁止只输出单个节点。
3. 3 道渐进式编程练习题，每题必须给出明确的 expected_output（通过运行 solution 代码能得到的确切输出）。
4. 1-2 个可运行代码实操案例，代码必须围绕「{concept}」编写。
5. 语音讲解文本（200 字以内）：用自然语言概括本讲义的定义、要点和练习重点。

**文档边界标记（必须遵守）**：
- document 字段的内容必须以 `<!-- DOC_START -->` 开头、以 `<!-- DOC_END -->` 结尾。
- 两个标记之间只能放真正的讲义 Markdown，严禁放思考过程、规划文字、JSON 片段。
- 讲义 Markdown 必须以 `# {concept}` 或 `## {concept}` 作为标题开头。

所有代码必须可在 Python 3.10+ 中运行，不要引入未授权的外部库。
代码中若涉及 Windows 路径或反斜杠，请使用原始字符串 r'...' 或正斜杠，避免转义错误。"""

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从 LLM 输出中提取 JSON：直接解析、markdown 代码块、raw_decode 兜底。"""
        # 去除 <think> 等推理标签，避免污染 JSON 解析
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
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
        # 从第一个 { 开始用 raw_decode 找第一个合法 JSON 对象，忽略后面多余的说明文字
        start = text.find("{")
        while start != -1:
            try:
                obj, _ = json.JSONDecoder().raw_decode(text, start)
                if isinstance(obj, dict):
                    return obj
            except (json.JSONDecodeError, ValueError):
                pass
            start = text.find("{", start + 1)
        return None

    def _clean_document(self, doc: str) -> str:
        """清洗 document 字段：去掉思考过程、规划文字、JSON 片段，保留真正讲义。"""
        if not doc:
            return doc
        # 1. 去掉 <think> 块
        doc = re.sub(r"<think>.*?</think>", "", doc, flags=re.DOTALL).strip()
        # 2. 如果模型遵循了 DOC_START / DOC_END 标记，直接提取标记之间的内容
        start = doc.find(self._DOC_START)
        if start != -1:
            start += len(self._DOC_START)
            end = doc.find(self._DOC_END, start)
            if end == -1:
                end = len(doc)
            doc = doc[start:end].strip()
        # 3. 兜底：确保文档从第一个 Markdown 标题开始
        m = re.search(r"^#{1,6}\s+.+", doc, re.MULTILINE)
        if m:
            doc = doc[m.start():]
        # 4. 去掉代码块外的 JSON 规划片段（通常出现在思考模型输出末尾）
        lines = doc.split("\n")
        in_code = False
        cut_idx = len(lines)
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("```"):
                in_code = not in_code
                continue
            if in_code:
                continue
            if stripped.startswith("{") or stripped.startswith("["):
                cut_idx = i
                break
        doc = "\n".join(lines[:cut_idx]).strip()
        # 5. 把 LLM 输出的字面量 \n \t 转回真正的换行/制表符
        doc = self._unescape_text(doc)
        return doc

    def _unescape_text(self, text: str) -> str:
        """把 LLM 输出里的字面量 \\n、\\t 转回真正的换行和制表符。

        注意：代码块内字符串字面量中的 \\n 会被保留，避免破坏 Python 字符串语义。
        """
        if not text:
            return text

        def _unescape_outside_code(segment: str) -> str:
            return segment.replace("\\n", "\n").replace("\\t", "\t")

        def _unescape_code(segment: str) -> str:
            """代码段：仅替换引号外的 \\n，保留字符串里的 \\n。"""
            result = []
            i = 0
            in_single = False
            in_double = False
            while i < len(segment):
                ch = segment[i]
                if ch == "\\" and i + 1 < len(segment):
                    nxt = segment[i + 1]
                    if nxt == "n" and not in_single and not in_double:
                        result.append("\n")
                        i += 2
                        continue
                    if nxt == "t" and not in_single and not in_double:
                        result.append("\t")
                        i += 2
                        continue
                if ch == '"' and not in_single:
                    in_double = not in_double
                elif ch == "'" and not in_double:
                    in_single = not in_single
                result.append(ch)
                i += 1
            return "".join(result)

        parts = re.split(r"(```[\s\S]*?```)", text)
        out = []
        for idx, part in enumerate(parts):
            if idx % 2 == 1 and part.startswith("```"):
                out.append(_unescape_code(part))
            else:
                out.append(_unescape_outside_code(part))
        return "".join(out)

    def _unescape_exercise(self, ex: Dict[str, Any]) -> Dict[str, Any]:
        """对练习题文本字段做 \\n 反转义，代码字段保留字符串内的 \\n。"""
        return {
            "question": self._unescape_text(ex.get("question", "")),
            "starter_code": self._unescape_text(ex.get("starter_code", "")),
            "expected_output": self._unescape_text(ex.get("expected_output", "")),
            "hints": [self._unescape_text(h) for h in (ex.get("hints") or [])],
            "solution": self._unescape_text(ex.get("solution", "")),
        }

    def _unescape_code_case(self, case: Dict[str, Any]) -> Dict[str, Any]:
        """对代码案例文本字段做 \\n 反转义。"""
        return {
            "title": self._unescape_text(case.get("title", "")),
            "code": self._unescape_text(case.get("code", "")),
            "explanation": self._unescape_text(case.get("explanation", "")),
        }

    def _fallback_parse(self, concept: str, raw: str) -> Dict[str, Any]:
        """JSON 解析失败时，按规则拆分内容"""
        # 兜底：提取所有 Python 代码块，前两个作为案例，其余作为练习题
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
                    "starter_code": f"# TODO: 完成「{concept}」练习 {i - 1}\n",
                    "expected_output": "",
                    "hints": [],
                    "solution": code.strip(),
                })

        return {
            "document": raw,
            "exercises": exercises,
            "code_cases": code_cases,
        }

    def _normalize_exercises(self, exercises: List[Dict[str, Any]], concept: str) -> List[Dict[str, Any]]:
        """补齐练习题字段，缺失 expected_output 时尝试执行 solution 推导。"""
        normalized = []
        executor = CodeExecutor(timeout=5.0)
        for ex in exercises:
            question = ex.get("question") or f"练习：{concept}"
            starter = ex.get("starter_code") or ""
            solution = ex.get("solution") or ""
            hints = ex.get("hints") or []
            expected = (ex.get("expected_output") or "").strip()
            if not expected:
                code_to_run = solution.strip() or starter.strip()
                if code_to_run:
                    try:
                        result = executor.execute(code_to_run)
                        if result.get("success") and result.get("stdout") is not None:
                            expected = result["stdout"].strip()
                    except Exception:
                        expected = ""
            normalized.append({
                "question": question,
                "starter_code": starter,
                "expected_output": expected,
                "hints": hints if isinstance(hints, list) else [hints] if hints else [],
                "solution": solution,
            })
        return normalized

    def _normalize_code_cases(self, code_cases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """校验代码案例是否可运行，并标记运行结果。"""
        normalized = []
        executor = CodeExecutor(timeout=5.0)
        for case in code_cases:
            title = case.get("title") or "代码案例"
            code = case.get("code") or ""
            explanation = case.get("explanation") or ""
            run_result = {"runnable": False, "stdout": "", "stderr": ""}
            if code.strip():
                try:
                    result = executor.execute(code)
                    run_result = {
                        "runnable": result.get("success", False),
                        "stdout": result.get("stdout", ""),
                        "stderr": result.get("stderr", ""),
                    }
                except Exception as e:
                    run_result["stderr"] = str(e)
            normalized.append({
                "title": title,
                "code": code,
                "explanation": explanation,
                "runnable": run_result["runnable"],
                "run_result": run_result,
            })
        return normalized

    def _auto_fix_code_cases(
        self,
        code_cases: List[Dict[str, Any]],
        concept: str,
        concept_info: dict,
        profile: Dict[str, Any],
        max_attempts: int = 2,
    ) -> List[Dict[str, Any]]:
        """对不可运行的代码案例自动调用 LLM 修正，最多尝试 max_attempts 轮。"""
        for _ in range(max_attempts):
            failed = [c for c in code_cases if not c.get("runnable", False)]
            if not failed:
                break

            fix_prompt = f"""你正在修正以下 Python 教学代码案例，使其可以在 Python 3.10+ 环境中正确运行。
知识点：{concept}
前置知识：{concept_info.get('prerequisites', [])}
常见易错点：{concept_info.get('pitfalls', [])}

以下案例执行失败，请只修正失败的案例，保持标题和讲解不变，输出 JSON 数组：
[
  {{"title": "案例标题", "code": "修正后的代码", "explanation": "案例说明"}}
]

失败案例：
{json.dumps([
    {
        "title": c.get("title"),
        "code": c.get("code"),
        "explanation": c.get("explanation"),
        "stderr": c.get("run_result", {}).get("stderr", ""),
    }
    for c in failed
], ensure_ascii=False, indent=2)}

只输出 JSON 数组，不要多余内容。"""

            try:
                raw = self.think(fix_prompt)
                fixed = self._extract_json(raw)
                if not fixed:
                    break
                # 支持直接数组或包裹在 {"code_cases": [...]} 中
                if isinstance(fixed, dict):
                    fixed = fixed.get("code_cases", [])
                if not isinstance(fixed, list):
                    break

                # 用修正后的结果替换失败案例
                fixed_by_title = {f.get("title"): f for f in fixed if f.get("title")}
                new_cases = []
                for case in code_cases:
                    if not case.get("runnable") and case.get("title") in fixed_by_title:
                        new_cases.append(fixed_by_title[case["title"]])
                    else:
                        new_cases.append(case)
                code_cases = self._normalize_code_cases(new_cases)
            except Exception:
                break
        return code_cases

    def _generate_mindmap(self, concept: str, concept_info: dict) -> str:
        """基于知识图谱约束生成真正的 Mermaid mindmap（径向思维导图）。"""
        prerequisites = concept_info.get("prerequisites", []) or []
        next_concepts = concept_info.get("next_concepts", []) or []
        objectives = concept_info.get("learning_objectives", []) or []
        pitfalls = concept_info.get("common_pitfalls", []) or [
            p.get("description", "") for p in concept_info.get("pitfalls", []) if p.get("description")
        ]

        def _escape(text: str) -> str:
            # Mermaid mindmap 节点里避免使用会破坏解析的引号/冒号
            return text.replace('"', "'").replace(":", "：")

        lines = ["mindmap"]
        lines.append(f"  root(({_escape(concept)}))")

        if prerequisites:
            lines.append("    前置依赖")
            for p in prerequisites[:6]:
                lines.append(f"      {_escape(p)}")
        else:
            lines.append("    前置依赖")
            lines.append("      无")

        if next_concepts:
            lines.append("    后续概念")
            for n in next_concepts[:6]:
                lines.append(f"      {_escape(n)}")
        else:
            lines.append("    后续概念")
            lines.append("      待探索")

        if objectives:
            lines.append("    核心要点")
            for obj in objectives[:6]:
                lines.append(f"      {_escape(obj)}")

        if pitfalls:
            lines.append("    易错点")
            for pit in pitfalls[:6]:
                lines.append(f"      {_escape(pit)}")

        return "\n".join(lines)

    def _is_substantial_document(self, document: str, concept: str) -> bool:
        """判断文档是否有实质内容，而非空泛模板。"""
        if not document or len(document.strip()) < 300:
            return False
        text = document.strip()
        # 只要有清晰的结构（多个标题 + 多个代码块），就认为有实质内容
        headings = re.findall(r"^#{1,3}\s+.+", text, re.MULTILINE)
        code_blocks = re.findall(r"```python\s*.*?\s*```", text, re.DOTALL)
        if len(headings) >= 3 and len(code_blocks) >= 2:
            return True
        # 包含典型空话模板才视为不实质
        generic_phrases = [
            "是 Python 学习中的重要基础",
            "是 Python 学习中的重要知识点",
            "如果你暂时没有生成到增强版讲义",
            "先用一句话描述这个知识点的用途",
        ]
        return not any(phrase in text for phrase in generic_phrases)

    def _default_exercises(self, concept: str, concept_info: dict) -> List[Dict[str, Any]]:
        """生成与知识点相关的默认练习题。"""
        objectives = concept_info.get("learning_objectives", []) or []
        pitfalls = concept_info.get("common_pitfalls", []) or [
            p.get("description", "") for p in concept_info.get("pitfalls", []) if p.get("description")
        ]
        objective_text = objectives[0] if objectives else f"理解 {concept} 的基本用法"
        pitfall_text = pitfalls[0] if pitfalls else "代码缩进或符号写错"
        return [
            {
                "question": f"请用自己的话解释「{concept}」在 Python 中主要解决什么问题。",
                "starter_code": "",
                "expected_output": "",
                "hints": [objective_text],
                "solution": f"# {concept} 的用途\nprint('{objective_text}')",
            },
            {
                "question": f"写一个最小 Python 示例，展示「{concept}」的基本用法，并输出结果。",
                "starter_code": f"# 展示 {concept} 的基本用法\n",
                "expected_output": f"示例：{concept}",
                "hints": ["使用 print 输出结果即可"],
                "solution": f"# {concept} 基本用法\nprint('示例：{concept}')",
            },
            {
                "question": f"找出一个与「{concept}」相关的常见错误并说明如何避免。",
                "starter_code": "",
                "expected_output": "",
                "hints": [pitfall_text],
                "solution": f"# 避免错误：{pitfall_text}\nprint('正确写法示例')",
            },
        ]

    def _default_code_cases(self, concept: str) -> List[Dict[str, Any]]:
        """生成与知识点相关的默认代码案例。"""
        return [
            {
                "title": f"{concept} 最小示例",
                "code": f"# {concept} 最小示例\nprint('Hello, {concept}!')",
                "explanation": f"运行并观察输出，建立对 {concept} 的直观认识。",
            },
            {
                "title": f"{concept} 常见用法",
                "code": f"# {concept} 常见用法\nvalue = 10\nprint(f'{concept} 示例值：{{value}}')",
                "explanation": "注意变量与输出的对应关系。",
            },
        ]

    def _generate_document(self, concept: str, concept_info: dict) -> str:
        """基于知识图谱约束生成有实质内容的讲义（LLM 不可用时兜底用）。"""
        description = (concept_info.get("description") or "").strip()
        prerequisites = concept_info.get("prerequisites", []) or []
        next_concepts = concept_info.get("next_concepts", []) or []
        objectives = concept_info.get("learning_objectives", []) or []
        common_pitfalls = concept_info.get("common_pitfalls", []) or []
        pitfalls = concept_info.get("pitfalls", []) or []

        lines = [f"# {concept}"]

        if description:
            lines.append(f"\n## 概念说明\n{description}")
        else:
            lines.append(f"\n## 概念说明\n{concept} 是 Python 学习中的一个基础知识点。掌握它能为后续进阶内容打下扎实基础。")

        if objectives:
            lines.append("\n## 学习目标")
            for obj in objectives[:6]:
                lines.append(f"- {obj}")

        if prerequisites:
            lines.append(f"\n## 前置知识\n学习本知识点前，建议先掌握：{', '.join(prerequisites[:6])}。")

        if next_concepts:
            lines.append(f"\n## 后续关联\n掌握后可继续学习：{', '.join(next_concepts[:6])}。")

        lines.append("\n## 核心要点")
        if objectives:
            for obj in objectives[:4]:
                lines.append(f"- {obj}")
        else:
            lines.append(f"- 理解 {concept} 的基本定义与使用场景。")
            lines.append(f"- 掌握 {concept} 的常用语法与关键操作。")
            lines.append(f"- 能够在简单程序中正确运用 {concept}。")

        lines.append("\n## 代码示例")
        lines.append(f"""```python
# 示例 1：{concept} 的最小可运行示例
print("学习 {concept} 的第一个示例")
```""")
        lines.append(f"""```python
# 示例 2：{concept} 的常见用法
value = 42
print(f"{concept} 的示例值：{{value}}")
```""")
        lines.append(f"""```python
# 示例 3：{concept} 的综合练习
def demo():
    return "{concept} 综合示例"

print(demo())
```""")

        if common_pitfalls or pitfalls:
            lines.append("\n## 常见错误")
            if common_pitfalls:
                for pit in common_pitfalls[:6]:
                    lines.append(f"- {pit}")
            else:
                for p in pitfalls[:6]:
                    desc = p.get("description", "")
                    example = p.get("example", "")
                    solution = p.get("solution", "")
                    lines.append(f"- {desc}")
                    if example:
                        lines.append(f"  - 错误示例：`{example}`")
                    if solution:
                        lines.append(f"  - 改正方法：{solution}")

        lines.append("\n## 学习建议")
        lines.append(f"- 先阅读概念说明，理解 {concept} 要解决什么问题。")
        lines.append("- 运行每个代码示例，观察输出并与预期对比。")
        lines.append("- 尝试修改示例中的关键值，验证自己是否真正掌握。")

        return "\n".join(lines)

    def build_fallback_package(self, concept: str) -> Dict[str, Any]:
        """构造基于知识图谱的兜底资源包，避免 LLM 超时时全是空话。"""
        graph = get_graph_store()
        concept_info = graph.get_concept(concept) or {}

        document = self._generate_document(concept, concept_info)
        mindmap = self._generate_mindmap(concept, concept_info)

        objectives = concept_info.get("learning_objectives", []) or []
        common_pitfalls = concept_info.get("common_pitfalls", []) or [
            p.get("description", "") for p in concept_info.get("pitfalls", []) if p.get("description")
        ]
        objective_text = objectives[0] if objectives else f"理解 {concept} 的基本用法"
        pitfall_text = common_pitfalls[0] if common_pitfalls else "代码缩进或符号写错"

        return {
            "concept": concept,
            "document": document,
            "mindmap": mindmap,
            "exercises": [
                {
                    "id": "fallback-1",
                    "type": "short_answer",
                    "question": f"请用自己的话解释「{concept}」在 Python 中主要解决什么问题。",
                    "answer": objective_text,
                    "expected_output": "",
                },
                {
                    "id": "fallback-2",
                    "type": "coding",
                    "question": f"写一个最小 Python 示例，展示「{concept}」的基本用法，并输出结果。",
                    "answer": f"# 示例：{concept}\nprint('示例：{concept}')",
                    "expected_output": f"示例：{concept}",
                },
                {
                    "id": "fallback-3",
                    "type": "coding",
                    "question": f"在以下代码中找出并修正一个与「{concept}」相关的常见错误。",
                    "answer": f"# 常见错误：{pitfall_text}\n# 请根据知识点写出正确代码",
                    "expected_output": "",
                },
            ],
            "code_cases": [
                {
                    "title": f"{concept} 最小示例",
                    "description": f"展示 {concept} 的最基础用法，帮助建立直观认识。",
                    "code": f"# {concept} 最小示例\nprint('Hello, {concept}!')",
                    "explanation": "先运行并观察输出，再尝试修改变量或参数。",
                },
                {
                    "title": f"{concept} 常见用法",
                    "description": f"展示 {concept} 在典型场景中的用法。",
                    "code": f"# {concept} 常见用法\nvalue = 10\nprint(f'{concept} 示例值：{{value}}')",
                    "explanation": "注意代码的执行顺序和输出格式。",
                },
            ],
            "audio_text": f"这一节我们学习{concept}。{concept_info.get('description', '')} 请结合讲义中的概念说明、代码示例和常见错误进行学习。",
            "fallback": True,
            "fallback_reason": "llm_timeout_or_degraded",
        }

    def _build_revision_prompt(
        self,
        concept: str,
        profile: Dict[str, Any],
        current_package: Dict[str, Any],
        feedback: str,
    ) -> str:
        return f"""请根据辩论议会的反馈，修订以下 Python 教学资源。

知识点：{concept}
学生画像：{json.dumps(profile, ensure_ascii=False)}

当前资源：
{json.dumps(current_package, ensure_ascii=False, indent=2)}

修订意见：
{feedback}

请输出修订后的完整资源，格式与生成时一致（JSON）。"""


# 为兼容旧导入保留别名
BuilderAgent = GeneratorAgent

