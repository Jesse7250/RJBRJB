"""Socrates Agent：苏格拉底式辅导

TODO:
- [待完成] 根据学生错误类型选择提问策略
- [待完成] 维护提问链状态，支持多轮追问
- [待完成] 接入代码执行结果，生成更精准的引导
- [待完成] 记录学生思考路径并可视化
"""
import json
import re
from typing import Any, Dict, Optional

from app.agents.base import BaseAgent


class SocratesAgent(BaseAgent):
    """引导学生自主发现答案"""

    name = "Socrates"
    system_prompt = """你是苏格拉底，古希腊哲学家和教育家。
你的辅导风格是引导学生自主发现答案，而不是直接给出解答。
通过精心设计的提问链，帮助学生建构知识。

输出 JSON：
{
  "stage": "clarification | assumption_probe | evidence_check | counter_example | convergence",
  "question": "引导性问题",
  "hint": "可选提示",
  "can_provide_answer": true,
  "answer": "如果学生要求直接答案，给出简洁答案"
}
只输出 JSON。"""

    def run(
        self,
        error_message: str,
        code: str,
        concept: str,
        profile: Dict[str, Any],
        depth: int = 0,
    ) -> Dict[str, Any]:
        """生成苏格拉底式提问"""
        stages = [
            "clarification",
            "assumption_probe",
            "evidence_check",
            "counter_example",
            "convergence",
        ]
        stage = stages[min(depth, len(stages) - 1)]

        prompt = f"""学生当前知识点：{concept}
学生代码：
```python
{code}
```
错误信息：{error_message}
学生画像：{json.dumps(profile, ensure_ascii=False)}

当前提问阶段：{stage}
请输出一个引导性提问 JSON。"""

        raw = self.think(prompt)
        result = self._extract_json(raw)

        if not result:
            result = self._fallback_question(stage, concept, error_message)

        result.setdefault("stage", stage)
        result.setdefault("can_provide_answer", depth >= 3)
        result["raw"] = raw
        return result

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取 JSON"""
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

    def _fallback_question(self, stage: str, concept: str, error_message: str) -> Dict[str, Any]:
        """兜底提问模板"""
        templates = {
            "clarification": {
                "question": f"这个错误提示你注意到了什么关键信息？",
                "hint": "仔细看报错中的类型和行号。",
            },
            "assumption_probe": {
                "question": f"你觉得{concept}的哪个特性可能导致这个错误？",
                "hint": f"回忆一下{concept}的基本规则。",
            },
            "evidence_check": {
                "question": "你能从代码中找到支持或反驳你判断的线索吗？",
                "hint": "逐行检查变量的值和类型。",
            },
            "counter_example": {
                "question": "如果换一个输入，你的代码还能正确运行吗？",
                "hint": "考虑边界情况。",
            },
            "convergence": {
                "question": "所以本质上，这个问题应该怎么解决？",
                "hint": "总结一下核心要点。",
                "answer": "请参考文档中的常见错误部分。",
            },
        }
        return dict(templates.get(stage, templates["clarification"]))
