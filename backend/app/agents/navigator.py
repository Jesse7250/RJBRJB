"""Navigator Agent：学习路径规划

对应需求/功能：
- 基于知识图谱前置依赖与学生已掌握知识点，规划从当前状态到目标知识点的最优学习路径。
- 先由图存储计算拓扑路径，再由 LLM 基于画像做教学化调整与推荐理由生成。

主要类/函数：
- NavigatorAgent.run(message)：统一入口，提取 concept 和 profile，返回规划结果。
- NavigatorAgent._plan_path(...)：核心规划逻辑，包括图路径计算、LLM 教学化调整、
  去重、时长估算。
- _extract_json：解析 LLM 返回的 JSON 路径结果。

TODO:
- [已完成] 基于知识图谱前置依赖计算学习路径已实现
- [已完成] LLM 教学化路径调整与推荐理由生成已实现
- [已完成] 路径去重、目标补全、时长估算已实现
- [已完成] 图存储层已使用 A* 算法替代 BFS/shortestPath
- [待完成] 接入 BKT（贝叶斯知识追踪）动态更新掌握度
- [待完成] 根据学生画像调整路径难度与顺序（当前仅做了 Prompt 提示）
- [待完成] 支持多目标知识点路径规划
"""
import json
from typing import Any, Dict, List, Optional

from app.agents.base import AgentMessage, BaseAgent
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

    def run(self, message: AgentMessage) -> AgentMessage:
        """统一入口：规划学习路径"""
        target_concept = message.payload.get("concept") or message.context.get("target_concept")
        profile = message.context.get("profile", {})
        if not target_concept:
            return message.reply({"error": "未指定目标知识点"}, stage="navigator", from_agent=self.name)

        result = self._plan_path(target_concept, profile)
        return message.reply(result, stage="navigator", from_agent=self.name)

    def _plan_path(self, target_concept: str, profile: Dict[str, Any]) -> Dict[str, Any]:
        """规划学习路径（内部实现）"""
        graph = get_graph_store()
        mastered = profile.get("mastered_concepts", [])

        # 从知识图谱计算拓扑路径（当前底层为 shortestPath/BFS）
        graph_path = graph.get_learning_path(mastered, target_concept)

        # 让 LLM 基于图谱路径做教学化调整，并生成推荐理由
        prompt = f"""目标知识点：{target_concept}
学生已掌握：{mastered}
知识图谱推荐路径：{graph_path}
学生画像：{json.dumps(profile, ensure_ascii=False)}

请输出最终学习路径 JSON，并包含每条路径推荐理由：
{{
  "path": ["知识点1", "知识点2", "目标知识点"],
  "path_explanation": ["因为...", "由于...", "最终到达..."],
  "estimated_minutes": 60,
  "reason": "整体规划理由",
  "focus_concept": "当前重点知识点"
}}"""

        raw = self.think(prompt)
        llm_result = self._extract_json(raw)

        # 如果 LLM 返回了有效路径则采用，否则回退到图谱路径
        if llm_result and "path" in llm_result:
            path = llm_result["path"]
        else:
            path = graph_path

        # 确保目标在路径末尾
        if target_concept not in path:
            path = path + [target_concept]

        # 去重：保持顺序的同时移除重复知识点
        seen = set()
        unique_path = []
        for p in path:
            if p not in seen:
                seen.add(p)
                unique_path.append(p)

        # 根据每个知识点的预计学习时长累加得到总时长
        concept_details = [graph.get_concept(c) for c in unique_path]
        estimated = sum(c.get("estimated_time", 30) for c in concept_details if c)

        return {
            "path": unique_path,
            "path_explanation": llm_result.get("path_explanation", []) if llm_result else [],
            "estimated_minutes": estimated,
            "reason": llm_result.get("reason", "基于知识图谱前置依赖规划") if llm_result else "基于知识图谱前置依赖规划",
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
