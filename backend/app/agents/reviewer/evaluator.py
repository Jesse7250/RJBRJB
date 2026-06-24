"""学习效果评估模块（Reviewer 内部子能力）

对应需求/功能：
- 基于学生的学习行为数据（练习结果、代码运行记录、画像）评估学习效果。
- 输出掌握度变化、薄弱点、学习总结与下一步建议，并更新 BKT 掌握度状态。

主要类/函数：
- LearningEvaluator.run(message)：统一入口，提取学习数据并返回评估结果。
- LearningEvaluator.evaluate(...)：核心评估逻辑，调用 LLM 并做规则兜底。
- _extract_json：解析 LLM 返回的 JSON 评估结果。
- _rule_based_evaluation：基于练习正确率的规则兜底评估。
- _compute_bkt_p_known：简化的 BKT 掌握度更新（线性更新）。

TODO:
- [已完成] 基于练习与代码运行数据的评估已实现
- [已完成] LLM 输出解析与规则兜底已实现
- [已完成] 简化 BKT 掌握度更新与 heatmap 返回已实现
- [待完成] 替换为标准 BKT 公式（当前为简单线性更新）
- [待完成] 增加更多行为特征（停留时长、尝试次数、求助次数）
- [待完成] 使用 LLM function calling 强制输出 JSON
"""
import json
import re
from typing import Any, Dict, List, Optional

from app.agents.base import AgentMessage, BaseAgent
from app.services.database import get_mastery_heatmap, update_mastery_state


class LearningEvaluator(BaseAgent):
    """基于学习行为数据评估学习效果"""

    name = "Evaluator"
    system_prompt = """你是一位学习数据分析师。
你的任务是基于学生的学习行为数据，计算知识掌握度，识别薄弱点，生成学习效果报告。

输出 JSON：
{
  "mastery_delta": {"知识点": 0.15},
  "weak_points": ["薄弱知识点1"],
  "summary": "学习效果总结",
  "next_recommendation": "下一步学习建议"
}
只输出 JSON。"""

    def run(self, message: AgentMessage) -> AgentMessage:
        """统一入口"""
        session_id = message.context.get("session_id", "")
        concept = message.payload.get("concept") or message.context.get("target_concept", "")
        exercise_results = message.payload.get("exercise_results", [])
        code_runs = message.payload.get("code_runs", [])
        profile = message.context.get("profile", {})

        result = self.evaluate(concept, exercise_results, code_runs, profile, session_id)
        return message.reply(result, stage="evaluator", from_agent=self.name)

    def evaluate(self, concept: str, exercise_results: List[Dict[str, Any]],
                 code_runs: List[Dict[str, Any]], profile: Dict[str, Any],
                 session_id: str = "") -> Dict[str, Any]:
        prompt = f"""目标知识点：{concept}
练习结果：{json.dumps(exercise_results, ensure_ascii=False)}
代码运行记录：{json.dumps(code_runs, ensure_ascii=False)}
学生画像：{json.dumps(profile, ensure_ascii=False)}

请输出学习效果评估 JSON。"""

        raw = ""
        try:
            raw = self.think(prompt)
            result = self._extract_json(raw)
        except Exception:
            result = None

        # LLM 失败时使用规则兜底
        if not result:
            result = self._rule_based_evaluation(concept, exercise_results, code_runs)

        # 更新 BKT 掌握度：根据本次 delta 更新 p_known 并写入数据库
        if session_id:
            delta = result.get("mastery_delta", {}).get(concept, 0.0)
            p_known = self._compute_bkt_p_known(session_id, concept, delta)
            update_mastery_state(session_id, concept, p_known)
            result["heatmap"] = get_mastery_heatmap(session_id)

        result["raw"] = raw
        return result

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return None

    def _rule_based_evaluation(self, concept: str, exercise_results: List[Dict[str, Any]],
                               code_runs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """基于规则的评估兜底：根据练习正确率给出掌握度变化"""
        total = len(exercise_results)
        correct = sum(1 for r in exercise_results if r.get("correct") or r.get("passed"))
        accuracy = correct / total if total > 0 else 0.0

        error_count = len([r for r in code_runs if r.get("has_error") or not r.get("passed")])
        run_count = len(code_runs)

        # 根据正确率给出掌握度增量
        delta = 0.0
        if accuracy >= 0.8:
            delta = 0.2
        elif accuracy >= 0.5:
            delta = 0.1
        else:
            delta = 0.02

        weak_points = []
        if accuracy < 0.6:
            weak_points.append(concept)

        return {
            "mastery_delta": {concept: delta},
            "weak_points": weak_points,
            "summary": f"练习正确率 {accuracy:.0%}，代码运行 {run_count} 次（错误 {error_count} 次）。",
            "next_recommendation": "建议继续巩固基础概念" if weak_points else "可以进入下一个知识点",
        }

    def _compute_bkt_p_known(self, session_id: str, concept: str, delta: float) -> float:
        """简化 BKT：在原有 p_known 基础上根据 delta 线性更新"""
        from app.services.database import get_mastery_state
        states = get_mastery_state(session_id, concept)
        current = states[0]["p_known"] if states else 0.0
        # 简单线性更新：delta 越大、当前掌握度越低时提升越多
        new_p = min(1.0, max(0.0, current + delta * (1 - current)))
        return new_p
