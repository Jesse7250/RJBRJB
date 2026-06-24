"""ReviewerAgent：审核 + 辅导 + 评估三位一体

对外是单一 Agent，内部包含：
- DebateCouncil：4 视角资源审核
- SocratesTutor：苏格拉底式辅导
- LearningEvaluator：学习效果评估

同时负责辩论缓存与降级策略。
"""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.agents.base import AgentMessage, BaseAgent
from app.agents.reviewer.debate_council import DebateCouncil
from app.agents.reviewer.evaluator import LearningEvaluator
from app.agents.reviewer.socrates import SocratesTutor
from app.models.schemas import DebateReport, ResourcePackage
from app.services.database import get_db


class ReviewerAgent(BaseAgent):
    """Reviewer：资源审核、辅导、评估"""

    name = "Reviewer"
    system_prompt = "你是教学资源质量管理员，负责审核资源、辅导学生和评估学习效果。"

    def __init__(self, llm=None):
        super().__init__(llm)
        self.debate_council = DebateCouncil()
        self.socrates = SocratesTutor()
        self.evaluator = LearningEvaluator()
        self._ensure_cache_table()

    # ------------------------------------------------------------------
    # 统一入口
    # ------------------------------------------------------------------
    def run(self, message: AgentMessage) -> AgentMessage:
        """根据 stage 分发到 review / tutor / evaluate"""
        stage = message.stage
        if stage == "reviewer":
            return self.review(message)
        if stage == "tutor":
            return self.tutor(message)
        if stage == "evaluator":
            return self.evaluate(message)
        # 默认按 payload 中的 action 分发
        action = message.payload.get("action", "review")
        if action == "review":
            return self.review(message)
        if action == "tutor":
            return self.tutor(message)
        if action == "evaluate":
            return self.evaluate(message)
        return message.reply({"error": f"未知的 Reviewer action: {action}"}, from_agent=self.name)

    # ------------------------------------------------------------------
    # 资源审核
    # ------------------------------------------------------------------
    def review(self, message: AgentMessage, mode: Optional[str] = None) -> AgentMessage:
        """审核生成的资源

        mode 决策：
        - fast：只走 Guardian 快速审核
        - full：完整 4-Agent 辩论
        """
        package_dict = message.payload.get("package")
        if not package_dict:
            return message.reply({"error": "缺少 package"}, stage="reviewer", from_agent=self.name)

        package = ResourcePackage(**package_dict)
        concept = package.concept
        profile = message.context.get("profile", {})

        # 1. 检查缓存
        cached = self._get_cached_debate(concept, profile)
        if cached:
            return message.reply(
                {"debate_report": cached, "from_cache": True},
                stage="reviewer",
                from_agent=self.name,
            )

        # 2. 神经符号校验（前置依赖、AST）
        from app.services.graph_factory import get_graph_store
        from app.services.neuro_symbolic import NeuroSymbolicValidator

        graph = get_graph_store()
        concept_info = graph.get_concept(concept) or {}
        forbidden = graph.check_forbidden_concepts(package.document, concept)
        ast_violations = NeuroSymbolicValidator().validate_code_blocks(package.document, concept)
        all_forbidden = list(set(forbidden + ast_violations))

        # 3. 选择审核模式
        if mode is None:
            mode = self._select_review_mode(package, concept, all_forbidden)

        if mode == "fast":
            report = self.debate_council.fast_review(package, concept_info, all_forbidden)
        else:
            report = self.debate_council.debate(package, concept_info, all_forbidden)
            # 如果被拒绝，尝试修订一次
            if report.status == "REJECTED":
                report = self._revise_and_re_debate(package, concept_info, all_forbidden, profile)

        # 4. 缓存通过的审核结果
        if report.status in ("PASSED", "MODIFIED"):
            self._set_cached_debate(concept, profile, report)

        return message.reply(
            {
                "debate_report": report.model_dump(),
                "validation": {
                    "forbidden_concepts": all_forbidden,
                    "ast_violations": ast_violations,
                },
                "review_mode": mode,
            },
            stage="reviewer",
            from_agent=self.name,
        )

    def _select_review_mode(self, package: ResourcePackage, concept: str,
                            forbidden_concepts: List[str]) -> str:
        """选择审核模式：代码题、新知识点、高风险 → full；普通讲解 → fast"""
        # 代码案例多则走完整辩论
        code_case_count = len(package.code_cases or [])
        # 有 AST 或超纲问题则走完整辩论
        if forbidden_concepts or code_case_count > 0:
            return "full"
        # 默认快速审核
        return "fast"

    def _revise_and_re_debate(self, package: ResourcePackage, concept_info: dict,
                              forbidden_concepts: List[str],
                              profile: Dict[str, Any]) -> DebateReport:
        """辩论被拒绝后，根据建议修订并重新审核一次"""
        from app.agents.generator import GeneratorAgent

        feedback_lines = []
        for r in self.debate_council.debate(package, concept_info, forbidden_concepts).rounds:
            if r.verdict in ("WARN", "REJECT", "VETO") and r.suggestion:
                feedback_lines.append(f"- {r.agent}：{r.suggestion}")
        feedback = "\n".join(feedback_lines) or "请整体提升教学资源质量。"

        generator = GeneratorAgent()
        revised_package = generator.revise(package.concept, profile, package.model_dump(), feedback)
        return self.debate_council.debate(revised_package, concept_info, forbidden_concepts)

    # ------------------------------------------------------------------
    # 苏格拉底辅导
    # ------------------------------------------------------------------
    def tutor(self, message: AgentMessage) -> AgentMessage:
        """苏格拉底式辅导"""
        return self.socrates.run(message)

    # ------------------------------------------------------------------
    # 学习评估
    # ------------------------------------------------------------------
    def evaluate(self, message: AgentMessage) -> AgentMessage:
        """学习效果评估"""
        return self.evaluator.run(message)

    # ------------------------------------------------------------------
    # 辩论缓存（SQLite 内）
    # ------------------------------------------------------------------
    def _ensure_cache_table(self):
        db = get_db()
        try:
            if "debate_cache" not in db.table_names():
                db["debate_cache"].create({
                    "cache_key": str,
                    "concept": str,
                    "profile_hash": str,
                    "report": str,      # JSON
                    "created_at": str,
                }, pk="cache_key", if_not_exists=True)
                db["debate_cache"].create_index(["concept"], if_not_exists=True)
        finally:
            db.conn.close()

    def _make_debate_cache_key(self, concept: str, profile: Dict[str, Any]) -> str:
        profile_key = json.dumps({
            "knowledge_level": profile.get("knowledge_level", 1.0),
            "cognitive_field": profile.get("cognitive_field", "dependent"),
            "cognitive_modality": profile.get("cognitive_modality", "visual"),
            "learning_pace": profile.get("learning_pace", "normal"),
            "goal_orientation": profile.get("goal_orientation", "application"),
        }, sort_keys=True, ensure_ascii=False)
        profile_hash = hashlib.md5(profile_key.encode()).hexdigest()[:12]
        return f"{concept}:{profile_hash}"

    def _get_cached_debate(self, concept: str, profile: Dict[str, Any],
                           max_age_hours: int = 168) -> Optional[DebateReport]:
        db = get_db()
        try:
            key = self._make_debate_cache_key(concept, profile)
            try:
                row = db["debate_cache"].get(key)
            except Exception:
                return None
            if not row:
                return None
            created = datetime.fromisoformat(row["created_at"])
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if datetime.now(timezone.utc) - created > timedelta(hours=max_age_hours):
                db["debate_cache"].delete(key)
                return None
            return DebateReport(**json.loads(row["report"]))
        finally:
            db.conn.close()

    def _set_cached_debate(self, concept: str, profile: Dict[str, Any], report: DebateReport):
        db = get_db()
        try:
            db["debate_cache"].upsert({
                "cache_key": self._make_debate_cache_key(concept, profile),
                "concept": concept,
                "profile_hash": self._make_debate_cache_key(concept, profile).split(":", 1)[1],
                "report": report.model_dump_json(),
                "created_at": datetime.utcnow().isoformat(),
            }, ["cache_key"])
        finally:
            db.conn.close()
