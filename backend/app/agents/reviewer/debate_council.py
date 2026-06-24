"""Debate Council：Reviewer 内部的 4 视角审核模块

这不是对外暴露的 Agent，而是 ReviewerAgent 内部调用的 4 个审核 Prompt：
- ExpertReviewer：技术准确性
- TeacherReviewer：教学方法论
- StudentReviewer：可理解性
- GuardianReviewer：内容安全与幻觉

通过内部模块化，降低外部 Orchestrator 的复杂度。
"""
import re
from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.models.schemas import DebateReport, DebateRound, ResourcePackage


class ExpertReviewer(BaseAgent):
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
        return _parse_review(raw)


class TeacherReviewer(BaseAgent):
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
        return _parse_review(raw)


class StudentReviewer(BaseAgent):
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
        return _parse_review(raw)


class GuardianReviewer(BaseAgent):
    name = "Guardian"
    system_prompt = """你是内容安全官。你的任务是严格审核教学资源的安全性和准确性：
是否包含敏感违规信息、是否存在大模型幻觉（编造不存在的 Python 语法/API）、是否与知识图谱中的事实一致。
你拥有一票否决权。

回复格式：
PASS 或 VETO
具体意见..."""

    def review(self, package: ResourcePackage, concept_info: dict,
               forbidden_concepts: List[str]) -> Dict[str, Any]:
        prompt = f"""知识点：{package.concept}
前置知识：{concept_info.get('prerequisites', [])}
检测到的疑似超纲概念：{forbidden_concepts}
资源内容：
{package.document}

请从内容安全和防幻觉角度审核。注意："疑似超纲概念"仅供参考，你需要判断它们是否真的在当前资源中被深入讲解，还是只是顺带提及。如果只是顺带提及，不应否决。"""
        raw = self.think(prompt)
        result = _parse_review(raw)

        # Guardian 拥有否决权，但不再因疑似超纲概念自动 VETO
        if forbidden_concepts and result["verdict"] not in ("REJECT", "VETO"):
            result["suggestion"] = (
                f"注意：内容中疑似提及后续知识 {forbidden_concepts}，"
                f"建议在讲解时明确说明这些概念将在后续课程中学习，避免学生困惑。"
                + (result.get("suggestion", ""))
            )
        return result


def _parse_review(raw: str) -> Dict[str, Any]:
    """解析 Agent 审核回复"""
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
    """辩论议会：Reviewer 内部调用"""

    def __init__(self, max_rounds: int = 6, pass_threshold: float = 2.5):
        self.max_rounds = max_rounds
        # PASS=1, WARN=0.5, REJECT/VETO=0；4 个 Agent >= 2.5 视为通过
        self.pass_threshold = pass_threshold
        self.expert = ExpertReviewer()
        self.teacher = TeacherReviewer()
        self.student_sim = StudentReviewer()
        self.guardian = GuardianReviewer()

    def debate(self, package: ResourcePackage, concept_info: dict,
               forbidden_concepts: List[str]) -> DebateReport:
        """执行完整 4-Agent 辩论"""
        rounds: List[DebateRound] = []
        final_votes: Dict[str, str] = {}

        reviewers = [
            ("Expert", self.expert),
            ("Teacher", self.teacher),
            ("Student-Sim", self.student_sim),
            ("Guardian", self.guardian),
        ]

        for i, (name, reviewer) in enumerate(reviewers, start=1):
            if name == "Guardian":
                result = reviewer.review(package, concept_info, forbidden_concepts)
            else:
                result = reviewer.review(package, concept_info)

            rounds.append(DebateRound(
                round=i,
                agent=name,
                verdict=result["verdict"],
                message=result["message"],
                suggestion=result.get("suggestion"),
            ))
            final_votes[name] = result["verdict"]

        score = sum(1 if v == "PASS" else 0.5 if v == "WARN" else 0 for v in final_votes.values())
        if score >= self.pass_threshold and final_votes.get("Guardian") != "REJECT":
            status = "PASSED"
        else:
            status = "REJECTED"

        # 如果有 WARN 但没有 REJECT，视为 MODIFIED
        if status == "PASSED" and any(v == "WARN" for v in final_votes.values()):
            status = "MODIFIED"

        summary = f"辩论投票：{final_votes}，综合得分 {score}/{len(reviewers)}，结果 {status}。"

        return DebateReport(status=status, rounds=rounds, final_votes=final_votes)

    def fast_review(self, package: ResourcePackage, concept_info: dict,
                    forbidden_concepts: List[str]) -> DebateReport:
        """快速审核：只走 Guardian 一个视角"""
        result = self.guardian.review(package, concept_info, forbidden_concepts)
        round_obj = DebateRound(
            round=1,
            agent="Guardian",
            verdict=result["verdict"],
            message=result["message"],
            suggestion=result.get("suggestion"),
        )
        status = "PASSED" if result["verdict"] == "PASS" else "REJECTED"
        return DebateReport(
            status=status,
            rounds=[round_obj],
            final_votes={"Guardian": result["verdict"]},
        )
