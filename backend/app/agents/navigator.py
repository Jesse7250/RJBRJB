"""Navigator Agent：学习路径规划

TODO:
- [待完成] 实现 A* 算法替代当前 BFS/shortestPath
- [待完成] 接入 BKT（贝叶斯知识追踪）动态更新掌握度
- [待完成] 根据学生画像调整路径难度与顺序
- [待完成] 支持多目标知识点路径规划
"""
import json
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.services.graph_factory import get_graph_store


class NavigatorAgent(BaseAgent):
    """基于知识图谱和画像规划最优学习路径"""

    name = "Navigator"
    system_prompt = """你是一位资深 Python 课程教师，精通教学序列设计。
你的任务是基于学生的画像和知识掌握状态，规划最优学习路径。

请输出 JSON：
{
  "path": ["知识点1", "知识点2", "目标知识点"],
  "estimated_minutes": 60,
  "reason": "路径规划理由",
  "focus_concept": "当前重点知识点"
}
只输出 JSON。"""

    def run(
        self,
        target_concept: str,
        profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """规划学习路径

        Returns:
            {
                "path": List[str],
                "estimated_minutes": int,
                "reason": str,
                "focus_concept": str,
            }
        """
        graph = get_graph_store()
        mastered = profile.get("mastered_concepts", [])

        # 从知识图谱计算路径
        graph_path = graph.get_learning_path(mastered, target_concept)

        # 让 LLM 基于图谱路径做教学化调整
        prompt = f"""目标知识点：{target_concept}
学生已掌握：{mastered}
知识图谱推荐路径：{graph_path}
学生画像：{json.dumps(profile, ensure_ascii=False)}

请输出最终学习路径 JSON。"""

        raw = self.think(prompt)
        llm_result = self._extract_json(raw)

        if llm_result and "path" in llm_result:
            path = llm_result["path"]
        else:
            path = graph_path

        # 确保目标在路径末尾
        if target_concept not in path:
            path = path + [target_concept]

        # 去重
        seen = set()
        unique_path = []
        for p in path:
            if p not in seen:
                seen.add(p)
                unique_path.append(p)

        # 计算预计时长
        concept_details = [graph.get_concept(c) for c in unique_path]
        estimated = sum(c.get("estimated_time", 30) for c in concept_details if c)

        return {
            "path": unique_path,
            "estimated_minutes": estimated,
            "reason": llm_result.get("reason", "基于知识图谱前置依赖规划"),
            "focus_concept": unique_path[-1] if unique_path else target_concept,
            "graph_path": graph_path,
            "raw": raw,
        }

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """从文本中提取 JSON"""
        import re

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
