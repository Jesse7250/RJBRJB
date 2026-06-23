"""Debate Council：Society of Mind 辩论议会

4 个 Agent 从不同角度审核 Builder 生成的资源：
- Expert：技术准确性
- Teacher：教学方法论
- Student-Sim：可理解性
- Guardian：内容安全与幻觉

TODO:
- [待完成] 接入 Redis 缓存辩论结果，避免重复调用
- [待完成] 实现真正的多轮自由讨论（当前为固定轮次）
- [待完成] 根据修改建议自动调用 Builder 修订资源
- [待完成] 增加辩论耗时统计与超时控制
- [待完成] 支持对不同资源类型使用不同审核策略
"""
import re
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.models.schemas import DebateReport, DebateRound, ResourcePackage


class ExpertAgent(BaseAgent):
    name = "Expert"
    system_prompt = """你是 Python 技术专家，拥有 10 年以上 Python 开发经验。
你的任务是严格审核教学资源中的技术内容：语法是否正确、API 描述是否准确、代码示例是否能运行、是否符合最新 Python 版本标准。
发现问题必须明确指出。

回复格式：
PASS 或 WARN 或 REJECT
具体意见..."""

    def review(self, package: ResourcePackage, concept_info: dict) -> Dict[str, Any]:
        prompt = f"""知识点：{package.concept}
资源内容：
{package.document}

请从技术角度审核。"""
        raw = self.think(prompt)
        return self._parse_verdict(raw)

    def _parse_verdict(self, raw: str) -> Dict[str, Any]:
        return _parse_review(raw)


class TeacherAgent(BaseAgent):
    name = "Teacher"
    system_prompt = """你是教育学专家，专精编程教学法。
你的任务是从教学角度审核资源：概念引入是否符合认知发展规律、难度梯度是否合理、是否有足够的支架支持、是否考虑了常见的学习障碍。

评判标准：
- PASS：资源整体合理，即使有小建议也可通过。
- WARN：存在明显教学问题，需要修改。
- REJECT：存在严重教学错误，不能发布。

回复格式：
PASS 或 WARN 或 REJECT
具体意见..."""

    def review(self, package: ResourcePackage, concept_info: dict) -> Dict[str, Any]:
        prompt = f"""知识点：{package.concept}
学生画像：{concept_info.get('difficulty', 3)}/5 难度
资源内容：
{package.document}

请从教学法角度审核。"""
        raw = self.think(prompt)
        return self._parse_verdict(raw)

    def _parse_verdict(self, raw: str) -> Dict[str, Any]:
        return _parse_review(raw)


class StudentSimAgent(BaseAgent):
    name = "Student-Sim"
    system_prompt = """你是一位 Python 初学者，刚刚接触编程不久。
你的任务是以初学者的视角阅读教学资源，诚实地反馈哪些部分看不懂、哪些概念太抽象、哪些示例不够清晰。
你的反馈代表了真实学生可能遇到的困难。

注意：初学者通常能理解基础讲解，只有当资源明显超出你的理解能力，或者示例完全无法 follow 时，才给出 WARN 或 REJECT。小幅度的抽象是正常的。

回复格式：
PASS 或 WARN 或 REJECT
具体意见..."""

    def review(self, package: ResourcePackage, concept_info: dict) -> Dict[str, Any]:
        prompt = f"""知识点：{package.concept}
资源内容：
{package.document}

请从初学者可理解性角度审核。"""
        raw = self.think(prompt)
        return self._parse_verdict(raw)

    def _parse_verdict(self, raw: str) -> Dict[str, Any]:
        return _parse_review(raw)


class GuardianAgent(BaseAgent):
    name = "Guardian"
    system_prompt = """你是内容安全官。你的任务是严格审核教学资源的安全性和准确性：
是否包含敏感违规信息、是否存在大模型幻觉（编造不存在的 Python 语法/API）、是否与知识图谱中的事实一致。
你拥有一票否决权。

回复格式：
PASS 或 VETO
具体意见..."""

    def review(
        self,
        package: ResourcePackage,
        concept_info: dict,
        forbidden_concepts: List[str],
    ) -> Dict[str, Any]:
        prompt = f"""知识点：{package.concept}
前置知识：{concept_info.get('prerequisites', [])}
检测到的疑似超纲概念：{forbidden_concepts}
资源内容：
{package.document}

请从内容安全和防幻觉角度审核。注意："疑似超纲概念"仅供参考，你需要判断它们是否真的在当前资源中被深入讲解，还是只是顺带提及。如果只是顺带提及，不应否决。"""
        raw = self.think(prompt)
        result = self._parse_verdict(raw)

        # Guardian 拥有否决权，但不再因疑似超纲概念自动 VETO，
        # 而是让 LLM 根据实际内容判断。代码层仅对明确超纲做兜底。
        if forbidden_concepts and result["verdict"] not in ("REJECT", "VETO"):
            result["suggestion"] = (
                f"注意：内容中疑似提及后续知识 {forbidden_concepts}，"
                f"建议在讲解时明确说明这些概念将在后续课程中学习，避免学生困惑。"
                + (result.get("suggestion", ""))
            )

        return result

    def _parse_verdict(self, raw: str) -> Dict[str, Any]:
        return _parse_review(raw)


def _parse_review(raw: str) -> Dict[str, Any]:
    """解析 Agent 审核回复

    TODO: [待完成] 增强解析鲁棒性，支持更多 verdict 表达形式
    """
    raw = raw.strip()
    lines = raw.split("\n")
    first_line = lines[0].upper()

    verdict = "WARN"
    if "PASS" in first_line:
        verdict = "PASS"
    elif "VETO" in first_line or "REJECT" in first_line:
        verdict = "REJECT"
    elif "WARN" in first_line:
        verdict = "WARN"

    suggestion = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

    return {
        "verdict": verdict,
        "message": lines[0],
        "suggestion": suggestion,
        "raw": raw,
    }


class DebateCouncil:
    """辩论议会"""

    def __init__(self, max_rounds: int = 6, pass_threshold: float = 2.5):
        self.max_rounds = max_rounds
        # 4 个 Agent 投票，PASS=1, WARN=0.5；>=2.5 视为通过
        self.pass_threshold = pass_threshold
        self.expert = ExpertAgent()
        self.teacher = TeacherAgent()
        self.student_sim = StudentSimAgent()
        self.guardian = GuardianAgent()

    def debate(
        self, package: ResourcePackage, concept_info: dict, forbidden_concepts: List[str]
    ) -> DebateReport:
        """执行辩论并返回报告"""
        rounds: List[DebateRound] = []
        final_votes: Dict[str, str] = {}

        # 第 1 轮：Expert
        expert_result = self.expert.review(package, concept_info)
        rounds.append(
            DebateRound(
                round=1,
                agent="Expert",
                verdict=expert_result["verdict"],
                message=expert_result["message"],
                suggestion=expert_result.get("suggestion"),
            )
        )
        final_votes["Expert"] = expert_result["verdict"]

        # 第 2 轮：Teacher
        teacher_result = self.teacher.review(package, concept_info)
        rounds.append(
            DebateRound(
                round=2,
                agent="Teacher",
                verdict=teacher_result["verdict"],
                message=teacher_result["message"],
                suggestion=teacher_result.get("suggestion"),
            )
        )
        final_votes["Teacher"] = teacher_result["verdict"]

        # 第 3 轮：Student-Sim
        student_result = self.student_sim.review(package, concept_info)
        rounds.append(
            DebateRound(
                round=3,
                agent="Student-Sim",
                verdict=student_result["verdict"],
                message=student_result["message"],
                suggestion=student_result.get("suggestion"),
            )
        )
        final_votes["Student-Sim"] = student_result["verdict"]

        # 第 4 轮：Guardian（一票否决）
        guardian_result = self.guardian.review(package, concept_info, forbidden_concepts)
        rounds.append(
            DebateRound(
                round=4,
                agent="Guardian",
                verdict=guardian_result["verdict"],
                message=guardian_result["message"],
                suggestion=guardian_result.get("suggestion"),
            )
        )
        final_votes["Guardian"] = guardian_result["verdict"]

        # 第 5-6 轮：补充讨论（针对 WARN 项）
        warn_rounds = self._supplement_rounds(rounds, package, concept_info)
        rounds.extend(warn_rounds)

        # 投票表决：PASS=1, WARN=0.5, REJECT/VETO=0
        score = 0.0
        has_reject = False
        for v in final_votes.values():
            if v == "PASS":
                score += 1.0
            elif v == "WARN":
                score += 0.5
            elif v in ("REJECT", "VETO"):
                has_reject = True

        has_suggestions = any(r.suggestion for r in rounds)

        if has_reject:
            status = "REJECTED"
        elif score < self.pass_threshold:
            status = "REJECTED"
        elif has_suggestions or score < len(final_votes):
            status = "MODIFIED"
        else:
            status = "PASSED"

        return DebateReport(
            status=status,
            rounds=rounds,
            final_votes=final_votes,
        )

    def _supplement_rounds(
        self,
        rounds: List[DebateRound],
        package: ResourcePackage,
        concept_info: dict,
    ) -> List[DebateRound]:
        """补充讨论轮

        TODO: [待完成] 实现真正的多 Agent 自由讨论，而非单次确认
        """
        extra: List[DebateRound] = []
        warn_indices = [i for i, r in enumerate(rounds) if r.verdict == "WARN"]

        if not warn_indices:
            return extra

        # 简化处理：对第一个 WARN，让 Expert 再次确认
        round_num = 5
        prompt = f"""针对以下修改建议，请确认修改后是否通过：
{rounds[warn_indices[0]].suggestion}

资源内容：
{package.document}

回复 PASS 或 WARN。"""
        raw = self.expert.think(prompt)
        result = _parse_review(raw)
        extra.append(
            DebateRound(
                round=round_num,
                agent="Expert",
                verdict=result["verdict"],
                message=result["message"],
                suggestion=result.get("suggestion"),
            )
        )

        return extra
