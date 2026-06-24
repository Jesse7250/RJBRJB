"""Agent Orchestrator：多智能体编排与路由（5 角色分层版）

职责：
1. 接收用户输入，识别意图
2. 维护会话状态
3. 按教育 SOP 在 5 个 Agent 之间路由消息
4. 提供超时熔断与异常降级
5. 对外保持原有接口稳定（handle_chat / generate_resource / ...）

5 个执行角色：
- Orchestrator（本类）
- Profiler
- Navigator
- Generator
- Reviewer（内部含 DebateCouncil / SocratesTutor / LearningEvaluator）
"""
import asyncio
import re
from typing import Any, AsyncIterator, Dict, List, Optional

from app.agents.base import AgentMessage, BaseAgent
from app.agents.generator import GeneratorAgent
from app.agents.navigator import NavigatorAgent
from app.agents.profiler import ProfilerAgent
from app.agents.reviewer import ReviewerAgent
from app.models.schemas import AgentResponse


class AgentOrchestrator:
    """Agent 编排器"""

    def __init__(self):
        self.profiler = ProfilerAgent()
        self.navigator = NavigatorAgent()
        self.generator = GeneratorAgent()
        self.reviewer = ReviewerAgent()

    @staticmethod
    def _to_dict(obj: Any) -> Any:
        if hasattr(obj, "model_dump"):
            return obj.model_dump()
        return obj

    # ------------------------------------------------------------------
    # 对外接口：聊天
    # ------------------------------------------------------------------
    def handle_chat(
        self,
        session: dict,
        message: str,
        message_type: str = "text",
    ) -> AgentResponse:
        """处理学生消息并返回 Agent 响应（同步版本）"""
        context = self._session_to_context(session)
        msg = AgentMessage(
            intent=self._classify_intent(message),
            stage="profiler",
            payload={"message": message, "message_type": message_type},
            context=context,
            from_agent="user",
        )
        result = self._route(msg)
        return self._to_agent_response(result)

    async def handle_chat_stream(
        self,
        session: dict,
        message: str,
        message_type: str = "text",
    ) -> AgentResponse:
        """处理学生消息并返回 Agent 响应（异步流式版本）

        当前内部仍调用同步 handle_chat，未来可拆分为多步骤 yield thinking 事件。
        """
        return await asyncio.to_thread(self.handle_chat, session, message, message_type)

    # ------------------------------------------------------------------
    # 对外接口：资源生成
    # ------------------------------------------------------------------
    def generate_resource(self, session: dict, concept: str, max_revisions: int = 1) -> Dict[str, Any]:
        """生成资源并执行辩论议会（同步版本，兼容旧接口）"""
        context = self._session_to_context(session)
        context["target_concept"] = concept

        msg = AgentMessage(
            intent="KNOWLEDGE_REQUEST",
            stage="generator",
            payload={"concept": concept, "max_revisions": max_revisions},
            context=context,
            from_agent="user",
        )
        final_msg = self._knowledge_flow(msg)

        package = self._to_dict(final_msg.payload.get("package", {}))
        debate_report = self._to_dict(final_msg.payload.get("debate_report", {}))
        validation = self._to_dict(final_msg.payload.get("validation", {}))

        # 同步更新会话状态
        session["last_package"] = package
        session["last_debate"] = debate_report
        session["target_concept"] = concept

        return {
            "concept": concept,
            "package": package,
            "debate_report": debate_report,
            "validation": validation,
        }

    async def generate_resource_stream(
        self,
        session: dict,
        concept: str,
        max_revisions: int = 1,
    ) -> AsyncIterator[Dict[str, Any]]:
        """生成资源并执行辩论议会（异步流式版本）"""
        context = self._session_to_context(session)
        context["target_concept"] = concept

        msg = AgentMessage(
            intent="KNOWLEDGE_REQUEST",
            stage="generator",
            payload={"concept": concept, "max_revisions": max_revisions},
            context=context,
            from_agent="user",
        )

        async def emit(stage: str, message: str, payload: Optional[Dict[str, Any]] = None):
            event: Dict[str, Any] = {"type": "progress", "stage": stage, "message": message}
            if payload:
                event.update(payload)
            yield event

        # 1. 路径规划
        async for e in emit("navigator", f"正在规划「{concept}」的学习路径..."):
            yield e
        nav_msg = await asyncio.to_thread(self.navigator.run, msg.with_stage("navigator"))
        path = nav_msg.payload.get("path", [concept])
        async for e in emit("navigator", f"学习路径：{' → '.join(path)}"):
            yield e

        # 2. 资源生成
        async for e in emit("builder", f"正在为「{concept}」生成个性化教学资源..."):
            yield e
        gen_msg = await asyncio.to_thread(self.generator.run, msg.with_stage("generator"))
        package = gen_msg.payload.get("package", {})
        async for e in emit(
            "builder",
            f"教学资源生成完成，包含 {len(package.get('document', ''))} 字讲解文档。",
        ):
            yield e

        # 3. 辩论审核
        async for e in emit("debate", "正在提交辩论议会审核..."):
            yield e
        review_msg = AgentMessage(
            intent="KNOWLEDGE_REQUEST",
            stage="reviewer",
            payload={"package": package, "action": "review"},
            context=context,
            from_agent="generator",
        )
        review_result = await asyncio.to_thread(self.reviewer.run, review_msg)
        debate_report = review_result.payload.get("debate_report", {})
        validation = review_result.payload.get("validation", {})
        review_mode = review_result.payload.get("review_mode", "full")
        async for e in emit(
            "debate",
            f"辩论议会结束（{review_mode} 模式），最终状态：{debate_report.get('status')}。",
            {"debate_report": debate_report},
        ):
            yield e

        # 4. 更新会话
        session["last_package"] = package
        session["last_debate"] = debate_report
        session["target_concept"] = concept

        result = {
            "concept": concept,
            "package": package,
            "debate_report": debate_report,
            "validation": validation,
            "review_mode": review_mode,
        }
        yield {"type": "complete", **result}
        async for e in emit("complete", "资源生成流程全部完成。", result):
            yield e

    # ------------------------------------------------------------------
    # 消息路由
    # ------------------------------------------------------------------
    def _route(self, msg: AgentMessage) -> AgentMessage:
        """按意图路由到对应流程"""
        intent = msg.intent
        if intent == "KNOWLEDGE_REQUEST":
            return self._knowledge_flow(msg)
        if intent == "CODE_HELP":
            return self._tutor_flow(msg)
        if intent == "PROGRESS_CHECK":
            return self._evaluate_flow(msg)
        if intent == "PATH_ADJUST":
            return self._path_adjust_flow(msg)
        # 默认聊天
        return self._safe_run(self.profiler, msg)

    def _knowledge_flow(self, msg: AgentMessage) -> AgentMessage:
        """学习新知识流程：Generator -> Reviewer -> Evaluator"""
        concept = msg.payload.get("concept") or self._extract_concept(msg.payload.get("message", "")) or msg.context.get("target_concept")
        if not concept:
            return msg.reply({
                "message": "你想学习哪个 Python 知识点呢？比如：变量与赋值、for循环、函数定义等。",
                "suggestions": ["变量与赋值", "for循环", "函数定义", "文件操作", "类与对象"],
            }, stage="profiler", from_agent="Profiler")

        msg = msg.with_payload(concept=concept).with_context(target_concept=concept)

        # 路径规划
        nav_msg = msg.with_stage("navigator")
        nav_result = self._safe_run(self.navigator, nav_msg)
        path = nav_result.payload.get("path", [concept])

        # 资源生成
        gen_msg = msg.with_stage("generator")
        gen_result = self._safe_run(self.generator, gen_msg)
        package = gen_result.payload.get("package")
        if not package:
            return msg.reply({"error": "资源生成失败"}, from_agent="Generator")

        # 审核
        review_msg = AgentMessage(
            intent=msg.intent,
            stage="reviewer",
            payload={"package": package, "action": "review"},
            context=msg.context,
            from_agent="Generator",
        )
        review_result = self._safe_run(self.reviewer, review_msg)

        # 返回给前端的响应
        return msg.reply(
            {
                "message": f"已为你生成「{concept}」的个性化学习资源，包含讲解文档、思维导图、练习题和代码案例。",
                "concept": concept,
                "path": path,
                "package": package,
                "debate_report": review_result.payload.get("debate_report", {}),
                "validation": review_result.payload.get("validation", {}),
                "review_mode": review_result.payload.get("review_mode", "full"),
            },
            stage="reviewer",
            from_agent="Reviewer",
        )

    def _tutor_flow(self, msg: AgentMessage) -> AgentMessage:
        """代码求助流程：Reviewer.tutor"""
        user_msg = msg.payload.get("message", "")
        concept = msg.context.get("target_concept", "当前知识点")

        # 从消息中简单提取代码块
        code_match = re.search(r"```python\s*(.*?)\s*```", user_msg, re.DOTALL)
        code = code_match.group(1) if code_match else "# 学生未提供代码"
        error_match = re.search(r"错误[：:]\s*(.+)", user_msg)
        error = error_match.group(1) if error_match else "请描述你遇到的错误"

        tutor_msg = AgentMessage(
            intent=msg.intent,
            stage="tutor",
            payload={"error_message": error, "code": code, "concept": concept},
            context=msg.context,
            from_agent="user",
        )
        result = self._safe_run(self.reviewer, tutor_msg)
        socratic = result.payload

        return msg.reply(
            {
                "message": socratic.get("question", "你遇到了什么问题？"),
                "hint": socratic.get("hint"),
                "can_provide_answer": socratic.get("can_provide_answer", False),
                "stage": socratic.get("stage"),
            },
            stage="tutor",
            from_agent="Socrates",
        )

    def _evaluate_flow(self, msg: AgentMessage) -> AgentMessage:
        """进度查询流程：Reviewer.evaluate"""
        concept = msg.context.get("target_concept", "当前知识点")

        eval_msg = AgentMessage(
            intent=msg.intent,
            stage="evaluator",
            payload={
                "concept": concept,
                "exercise_results": msg.payload.get("exercise_results", []),
                "code_runs": msg.payload.get("code_runs", []),
            },
            context=msg.context,
            from_agent="user",
        )
        result = self._safe_run(self.reviewer, eval_msg)
        evaluation = result.payload

        return msg.reply(
            {
                "message": evaluation.get("summary", "学习效果评估完成。"),
                "weak_points": evaluation.get("weak_points", []),
                "heatmap": evaluation.get("heatmap", {}),
                "next_recommendation": evaluation.get("next_recommendation", ""),
            },
            stage="evaluator",
            from_agent="Evaluator",
        )

    def _path_adjust_flow(self, msg: AgentMessage) -> AgentMessage:
        """路径调整流程：重新导航"""
        user_msg = msg.payload.get("message", "")
        concept = self._extract_concept(user_msg) or msg.context.get("target_concept")
        if not concept:
            return msg.reply({
                "message": "你想调整到哪个知识点呢？",
                "suggestions": ["变量与赋值", "for循环", "函数定义"],
            }, from_agent="Navigator")

        return self._knowledge_flow(msg.with_payload(concept=concept).with_context(target_concept=concept))

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------
    def _safe_run(self, agent: BaseAgent, msg: AgentMessage) -> AgentMessage:
        """带异常熔断的 Agent 调用"""
        try:
            return agent.run(msg)
        except Exception as e:
            # 降级：返回错误信息，不影响主流程
            return msg.reply(
                {"error": f"{agent.name} 执行失败: {str(e)}", "fallback": True},
                stage=msg.stage,
                from_agent=agent.name,
            )

    def _session_to_context(self, session: dict) -> Dict[str, Any]:
        """将 session 转为 AgentMessage context"""
        return {
            "session_id": session.get("session_id", ""),
            "user_id": session.get("user_id", ""),
            "profile": session.get("profile", {}),
            "dialogue_history": session.get("dialogue_history", []),
            "target_concept": session.get("target_concept"),
        }

    def _to_agent_response(self, msg: AgentMessage) -> AgentResponse:
        """将 AgentMessage 转为前端需要的 AgentResponse"""
        return AgentResponse(
            agent_name=msg.from_agent,
            response_type=msg.stage,
            content=msg.payload,
            profile_update=msg.context.get("profile"),
        )

    def _classify_intent(self, message: str) -> str:
        """识别学生意图（简化版，未来可交给 Profiler 或 LLM）"""
        msg = message.lower()
        if any(w in msg for w in ["学", "讲", "教", "什么是", "怎么", "如何做"]):
            return "KNOWLEDGE_REQUEST"
        if any(w in msg for w in ["错", "报错", "bug", "error", "运行不了"]):
            return "CODE_HELP"
        if any(w in msg for w in ["进度", "学得怎么样", "掌握", "测试"]):
            return "PROGRESS_CHECK"
        if any(w in msg for w in ["跳过", "下一个", "换", "不想学"]):
            return "PATH_ADJUST"
        return "CHAT"

    def _extract_concept(self, message: str) -> Optional[str]:
        """从消息中提取目标知识点（简化关键词匹配）"""
        keywords = ["变量与赋值", "for循环", "while循环", "函数定义", "类与对象",
                    "文件操作", "异常处理", "列表推导式", "字典操作", "字符串操作",
                    "条件语句", "模块导入", "递归", "装饰器", "生成器"]
        for kw in keywords:
            if kw in message:
                return kw
        return None
