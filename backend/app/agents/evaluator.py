"""Evaluator Agent：学习效果评估

TODO:
- [待完成] 实现完整 BKT（贝叶斯知识追踪）参数个性化
- [待完成] 接入学习行为日志（停留时长、点击、代码运行等）
- [待完成] 生成薄弱知识点热力图数据
- [待完成] 根据评估结果自动调整画像与路径
"""
import json
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent


class EvaluatorAgent(BaseAgent):
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

    def run(
        self,
        concept: str,
        exercise_results: List[Dict[str, Any]],
        code_runs: List[Dict[str, Any]],
        profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """评估学习效果"""
        prompt = f"""目标知识点：{concept}
练习结果：{json.dumps(exercise_results, ensure_ascii=False)}
代码运行记录：{json.dumps(code_runs, ensure_ascii=False)}
学生画像：{json.dumps(profile, ensure_ascii=False)}

请输出学习效果评估 JSON。"""

        raw = self.think(prompt)
        result = self._extract_json(raw)

        if not result:
            result = self._rule_based_evaluation(concept, exercise_results, code_runs)

        result["raw"] = raw
        return result

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取 JSON"""
        import re

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

    def _rule_based_evaluation(
        self,
        concept: str,
        exercise_results: List[Dict[str, Any]],
        code_runs: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """基于规则的评估兜底

        TODO: [待完成] 替换为完整 BKT 算法
        """
        total = len(exercise_results)
        correct = sum(1 for r in exercise_results if r.get("correct"))
        accuracy = correct / total if total > 0 else 0.0

        error_count = len([r for r in code_runs if r.get("has_error")])
        run_count = len(code_runs)

        # 简单 BKT 风格更新
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
