"""Agent Orchestrator：多智能体编排与路由

根据学生意图，决定调用哪个 Agent，并管理完整学习流程：
Profiler -> Navigator -> Builder -> DebateCouncil -> Renderer -> Socrates -> Evaluator -> Profiler

TODO:
- [待完成] 用 LLM 做意图分类与知识点 NER，替代关键词匹配
- [待完成] 实现 Speaker Selection 教育 SOP 路由函数
- [待完成] 增加 Agent 超时熔断与异常恢复
- [待完成] 接入学习行为日志记录
- [待完成] 根据 Evaluator 结果自动闭环更新画像与学习路径
- [待完成] 支持多轮苏格拉底辅导的状态追踪
"""
import asyncio
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from app.agents.builder import BuilderAgent
from app.agents.debate_council import DebateCouncil
from app.agents.evaluator import EvaluatorAgent
from app.agents.navigator import NavigatorAgent
from app.agents.profiler import ProfilerAgent
from app.agents.socrates import SocratesAgent
from app.models.schemas import AgentResponse
from app.core.config import get_settings
from app.services.graph_factory import get_graph_store
from app.services.neuro_symbolic import NeuroSymbolicValidator
from app.services.resource_cache import (
    get_cached_resource,
    set_cached_resource,
)


class AgentOrchestrator:
    """Agent 编排器"""

    def __init__(self):
        self.profiler = ProfilerAgent()
        self.navigator = NavigatorAgent()
        self.builder = BuilderAgent()
        self.debate_council = DebateCouncil()
        self.socrates = SocratesAgent()
        self.evaluator = EvaluatorAgent()
        self.validator = NeuroSymbolicValidator()

    def _get_cached_resource(
        self, concept: str, profile: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        ttl = get_settings().RESOURCE_CACHE_TTL_HOURS
        return get_cached_resource(concept, profile, max_age_hours=ttl)

    def _set_cached_resource(
        self, concept: str, profile: Dict[str, Any], result: Dict[str, Any]
    ):
        set_cached_resource(concept, profile, result)

    def handle_chat(
        self,
        session: dict,
        message: str,
        message_type: str = "text",
    ) -> AgentResponse:
        """处理学生消息并返回 Agent 响应（同步版本）"""
        profile = session.get("profile", {})
        dialogue_history = session.get("dialogue_history", [])

        # Step 1: Profiler 更新画像 + 识别意图
        profiler_result = self.profiler.run(
            message=message,
            current_profile=profile,
            dialogue_history=dialogue_history,
        )
        profile = profiler_result["profile"]
        session["profile"] = profile
        intent = profiler_result["intent"]

        # Step 2: 根据意图路由
        if intent == "KNOWLEDGE_REQUEST":
            return self._handle_knowledge_request(session, message, profile)

        if intent == "CODE_HELP":
            return self._handle_code_help(session, message, profile)

        if intent == "PROGRESS_CHECK":
            return self._handle_progress_check(session, profile)

        if intent == "PATH_ADJUST":
            return self._handle_path_adjust(session, message, profile)

        # 默认聊天回复
        return AgentResponse(
            agent_name="Profiler",
            response_type="chat",
            content={
                "message": profiler_result["response_message"],
                "intent": intent,
            },
            profile_update=profile,
        )

    async def handle_chat_stream(
        self,
        session: dict,
        message: str,
        message_type: str = "text",
    ) -> AgentResponse:
        """处理学生消息并返回 Agent 响应（异步流式版本）

        当前为简化实现：内部仍调用同步 handle_chat，但用 to_thread 避免阻塞事件循环，
        未来可拆分为多步骤 yield thinking 事件。
        """
        return await asyncio.to_thread(self.handle_chat, session, message, message_type)

    def _build_debate_feedback(self, debate_report: Dict[str, Any]) -> str:
        """从辩论议会报告中提取修订建议"""
        lines = []
        for r in debate_report.get("rounds", []):
            if r.get("verdict") in ("WARN", "REJECT", "VETO") and r.get("suggestion"):
                lines.append(f"- {r['agent']}：{r['suggestion']}")
        return "\n".join(lines) or "请整体提升教学资源质量，确保概念准确、代码可运行。"

    def _validate_and_debate(
        self, package, concept: str, concept_info: Dict[str, Any]
    ) -> tuple[List[str], List[str], Any]:
        """执行校验与辩论议会"""
        graph = get_graph_store()
        forbidden = graph.check_forbidden_concepts(package.document, concept)
        ast_violations = self.validator.validate_code_blocks(package.document, concept)
        all_forbidden = list(set(forbidden + ast_violations))
        debate_report = self.debate_council.debate(package, concept_info, all_forbidden)
        return all_forbidden, ast_violations, debate_report

    def generate_resource(
        self, session: dict, concept: str, max_revisions: int = 1
    ) -> Dict[str, Any]:
        """生成资源并执行辩论议会（同步版本，兼容旧接口）

        若辩论议会 REJECTED，会根据建议自动修订（默认最多 1 轮）。
        已生成并审核通过的资源会被缓存，避免重复调用 LLM。
        """
        profile = session.get("profile", {})
        cached = self._get_cached_resource(concept, profile)
        if cached:
            session["last_package"] = cached["package"]
            session["last_debate"] = cached["debate_report"]
            return cached

        graph = get_graph_store()
        concept_info = graph.get_concept(concept) or {}

        # Builder 生成资源
        package = self.builder.run(concept, profile)
        all_forbidden, ast_violations, debate_report = self._validate_and_debate(
            package, concept, concept_info
        )

        # 修订循环
        for _ in range(max_revisions):
            if debate_report.status != "REJECTED":
                break
            feedback = self._build_debate_feedback(debate_report.model_dump())
            package = self.builder.revise(
                concept, profile, package.model_dump(), feedback
            )
            all_forbidden, ast_violations, debate_report = self._validate_and_debate(
                package, concept, concept_info
            )

        # 更新会话
        session["last_package"] = package.model_dump()
        session["last_debate"] = debate_report.model_dump()

        result = {
            "concept": concept,
            "package": package.model_dump(),
            "debate_report": debate_report.model_dump(),
            "validation": {
                "forbidden_concepts": all_forbidden,
                "ast_violations": ast_violations,
            },
        }
        self._set_cached_resource(concept, profile, result)
        return result

    async def generate_resource_stream(
        self,
        session: dict,
        concept: str,
        max_revisions: int = 1,
    ) -> AsyncIterator[Dict[str, Any]]:
        """生成资源并执行辩论议会（异步流式版本）

        输出事件：
        - {"type": "progress", "stage": "builder", "message": "..."}
        - {"type": "progress", "stage": "validation", "message": "..."}
        - {"type": "progress", "stage": "debate", "message": "..."}
        - {"type": "complete", "concept": ..., "package": ..., "debate_report": ..., "validation": ...}

        若辩论议会 REJECTED，会根据建议自动修订（默认最多 1 轮）。
        已生成并审核通过的资源会被缓存，命中时直接返回。
        """

        async def emit(stage: str, message: str, payload: Optional[Dict[str, Any]] = None):
            event: Dict[str, Any] = {"type": "progress", "stage": stage, "message": message}
            if payload:
                event.update(payload)
            yield event

        profile = session.get("profile", {})

        cached = self._get_cached_resource(concept, profile)
        if cached:
            async for e in emit("cache", "命中资源缓存，直接使用已审核通过的资源。"):
                yield e
            session["last_package"] = cached["package"]
            session["last_debate"] = cached["debate_report"]
            yield {"type": "complete", **cached}
            async for e in emit("complete", "资源生成流程全部完成（缓存命中）。", cached):
                yield e
            return

        async for e in emit("builder", f"正在为「{concept}」生成个性化教学资源..."):
            yield e
        # Builder 中的 LLM 调用是同步阻塞的，用 to_thread 避免阻塞事件循环
        package = await asyncio.to_thread(self.builder.run, concept, profile)
        async for e in emit(
            "builder",
            f"教学资源生成完成，包含 {len(package.document)} 字讲解文档、{len(package.exercises)} 道练习题。",
        ):
            yield e

        graph = get_graph_store()
        concept_info = await asyncio.to_thread(graph.get_concept, concept)
        concept_info = concept_info or {}

        # 校验 + 辩论
        forbidden = await asyncio.to_thread(graph.check_forbidden_concepts, package.document, concept)
        ast_violations = await asyncio.to_thread(
            self.validator.validate_code_blocks, package.document, concept
        )
        all_forbidden = list(set(forbidden + ast_violations))
        if all_forbidden:
            async for e in emit(
                "validation",
                f"检测到 {len(all_forbidden)} 个潜在问题：{', '.join(all_forbidden[:5])}",
            ):
                yield e
        else:
            async for e in emit("validation", "神经符号校验通过，未发现超纲或语法问题。"):
                yield e

        debate_report = await asyncio.to_thread(
            self.debate_council.debate, package, concept_info, all_forbidden
        )

        # 修订循环
        for revision in range(max_revisions):
            if debate_report.status != "REJECTED":
                break
            async for e in emit(
                "revision",
                f"辩论议会建议修订，正在进行第 {revision + 1} 轮优化...",
            ):
                yield e
            feedback = self._build_debate_feedback(debate_report.model_dump())
            package = await asyncio.to_thread(
                self.builder.revise, concept, profile, package.model_dump(), feedback
            )
            forbidden = await asyncio.to_thread(graph.check_forbidden_concepts, package.document, concept)
            ast_violations = await asyncio.to_thread(
                self.validator.validate_code_blocks, package.document, concept
            )
            all_forbidden = list(set(forbidden + ast_violations))
            if all_forbidden:
                async for e in emit(
                    "validation",
                    f"修订后检测到 {len(all_forbidden)} 个潜在问题：{', '.join(all_forbidden[:5])}",
                ):
                    yield e
            else:
                async for e in emit("validation", "修订后神经符号校验通过。"):
                    yield e
            debate_report = await asyncio.to_thread(
                self.debate_council.debate, package, concept_info, all_forbidden
            )

        async for e in emit(
            "debate",
            f"辩论议会结束，最终状态：{debate_report.status}，共 {len(debate_report.rounds)} 轮。",
            {"debate_report": debate_report.model_dump()},
        ):
            yield e

        # 更新会话
        session["last_package"] = package.model_dump()
        session["last_debate"] = debate_report.model_dump()

        result = {
            "concept": concept,
            "package": package.model_dump(),
            "debate_report": debate_report.model_dump(),
            "validation": {
                "forbidden_concepts": all_forbidden,
                "ast_violations": ast_violations,
            },
        }
        self._set_cached_resource(concept, profile, result)

        yield {"type": "complete", **result}
        async for e in emit("complete", "资源生成流程全部完成。", result):
            yield e

    def _handle_code_help(self, session: dict, message: str, profile: dict) -> AgentResponse:
        """处理代码求助"""
        concept = session.get("target_concept", "当前知识点")
        # 从消息中简单提取代码块
        import re
        code_match = re.search(r"```python\s*(.*?)\s*```", message, re.DOTALL)
        code = code_match.group(1) if code_match else "# 学生未提供代码"
        error_match = re.search(r"错误[：:]\s*(.+)", message)
        error = error_match.group(1) if error_match else "请描述你遇到的错误"

        socratic = self.socrates.run(error, code, concept, profile)

        return AgentResponse(
            agent_name="Socrates",
            response_type="tutoring",
            content={
                "message": socratic["question"],
                "hint": socratic.get("hint"),
                "can_provide_answer": socratic.get("can_provide_answer", False),
                "stage": socratic.get("stage"),
            },
            profile_update=profile,
        )

    def _handle_knowledge_request(
        self, session: dict, message: str, profile: dict
    ) -> AgentResponse:
        """处理学习请求"""
        # 提取目标知识点（简化：先用关键词，后续可用 LLM NER）
        target_concept = self._extract_concept(message) or session.get("target_concept")
        if not target_concept:
            return AgentResponse(
                agent_name="Profiler",
                response_type="chat",
                content={
                    "message": "你想学习哪个 Python 知识点呢？比如：变量与赋值、for循环、函数定义等。",
                    "suggestions": ["变量与赋值", "for循环", "函数定义", "文件操作", "类与对象"],
                },
                profile_update=profile,
            )

        session["target_concept"] = target_concept

        # Navigator 规划路径
        nav_result = self.navigator.run(target_concept, profile)

        # 返回路径建议，前端可选择是否生成资源
        return AgentResponse(
            agent_name="Navigator",
            response_type="path_plan",
            content={
                "message": f"我识别到你想学习「{target_concept}」。为你规划了学习路径：{' → '.join(nav_result['path'])}，预计耗时 {nav_result['estimated_minutes']} 分钟。",
                "target_concept": target_concept,
                "suggested_path": nav_result["path"],
                "estimated_minutes": nav_result["estimated_minutes"],
                "next_action": "generate_resource",
            },
            profile_update=profile,
        )

    def _handle_path_adjust(
        self, session: dict, message: str, profile: dict
    ) -> AgentResponse:
        """处理路径调整请求（如跳过、换题）"""
        return AgentResponse(
            agent_name="Navigator",
            response_type="path_plan",
            content={
                "message": "已收到你的调整请求，我会重新规划学习路径。",
                "next_action": "recalculate_path",
            },
            profile_update=profile,
        )

    def _handle_progress_check(self, session: dict, profile: dict) -> AgentResponse:
        """处理进度查询"""
        mastered = profile.get("mastered_concepts", [])
        return AgentResponse(
            agent_name="Evaluator",
            response_type="evaluation",
            content={
                "message": f"你已经掌握了 {len(mastered)} 个知识点：{', '.join(mastered[:5])}{'...' if len(mastered) > 5 else ''}。",
                "mastered_count": len(mastered),
                "mastered_concepts": mastered,
            },
            profile_update=profile,
        )

    def _extract_concept(self, message: str) -> Optional[str]:
        """从消息中提取知识点（简化关键词匹配）

        TODO: [待完成] 替换为 LLM NER 或语义匹配
        """
        concept_keywords = {
            "变量": "变量与赋值",
            "赋值": "变量与赋值",
            "数据类型": "基本数据类型",
            "类型": "基本数据类型",
            "运算符": "运算符",
            "输入": "输入与输出",
            "输出": "输入与输出",
            "print": "输入与输出",
            "input": "输入与输出",
            "条件": "条件语句",
            "if": "条件语句",
            "for": "for循环",
            "循环": "for循环",
            "while": "while循环",
            "嵌套": "嵌套循环",
            "列表": "列表",
            "字典": "字典",
            "元组": "元组",
            "集合": "集合",
            "字符串": "字符串操作",
            "函数": "函数定义与调用",
            "参数": "函数参数",
            "作用域": "变量作用域",
            "递归": "递归函数",
            "文件": "文件操作",
            "异常": "异常处理",
            "错误": "常见异常类型",
            "类": "类与对象",
            "对象": "类与对象",
            "继承": "继承与多态",
            "math": "math模块",
            "random": "random模块",
            "datetime": "datetime模块",
            "os": "os模块",
            "csv": "CSV文件处理",
            "json": "JSON文件处理",
            "推导式": "列表推导式",
            "生成器": "生成器",
            "装饰器": "装饰器",
        }
        for keyword, concept in concept_keywords.items():
            if keyword in message:
                return concept
        return None
