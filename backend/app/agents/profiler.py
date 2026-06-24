"""Profiler Agent：对话式学生画像构建

TODO:
- [待完成] 引入更科学的认知风格量表对话流程
- [待完成] 基于学习行为数据动态更新画像（不仅是对话）
- [待完成] 增加隐性知识诊断嵌入策略
- [待完成] 使用 LLM function calling 强制输出 JSON
"""
import json
import re
from typing import Any, Dict, List, Optional

from app.agents.base import AgentMessage, BaseAgent
from app.models.schemas import StudentProfile


class ProfilerAgent(BaseAgent):
    """通过自然语言对话推断和更新学生画像"""

    name = "Profiler"
    system_prompt = """你是一位教育心理学专家，擅长通过对话洞察学生的学习特征。
你的任务是在自然对话中自动推断学生的知识基础、认知风格和学习偏好。
不要让学生感觉到在被测试。

请根据对话内容，输出一个 JSON 格式的学生画像更新：
{
  "knowledge_level": 1.0-5.0,
  "cognitive_field": "dependent" | "independent",
  "cognitive_modality": "visual" | "auditory" | "kinesthetic",
  "learning_pace": "slow" | "normal" | "fast",
  "goal_orientation": "exam" | "application" | "exploration",
  "error_patterns": ["语法错误", "逻辑错误"],
  "mastered_concepts": ["已掌握知识点1", "已掌握知识点2"],
  "inferred_from": "简短说明推断依据"
}

只输出 JSON，不要输出其他解释。"""

    def run(self, message: AgentMessage) -> AgentMessage:
        """统一入口：根据用户消息更新画像并识别意图"""
        user_message = message.payload.get("message", "")
        current_profile = message.context.get("profile", {})
        dialogue_history = message.context.get("dialogue_history", [])

        result = self._infer_profile(user_message, current_profile, dialogue_history)

        new_context = {**message.context, "profile": result["profile"]}
        return AgentMessage(
            intent=result["intent"],
            stage="profiler",
            payload={
                "response_message": result["response_message"],
                "profile": result["profile"],
            },
            context=new_context,
            from_agent=self.name,
            metadata={**message.metadata, "raw": result.get("raw", "")},
        )

    def _infer_profile(
        self,
        message: str,
        current_profile: Optional[Dict[str, Any]] = None,
        dialogue_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """根据用户消息更新画像（内部实现）"""
        current_profile = current_profile or {}
        dialogue_history = dialogue_history or []

        prompt = self._build_prompt(message, current_profile, dialogue_history)
        raw = self.think(prompt)

        # 尝试解析 JSON
        profile_update = self._extract_json(raw)
        if not profile_update:
            profile_update = self._rule_based_inference(message, current_profile)

        # 合并画像
        merged = self._merge_profile(current_profile, profile_update)
        profile = StudentProfile(**merged)

        # 识别意图
        intent = self._classify_intent(message)

        # 生成回复
        response_message = self._generate_response(message, intent, profile)

        return {
            "profile": profile.model_dump(),
            "response_message": response_message,
            "intent": intent,
            "raw": raw,
        }

    def _build_prompt(
        self,
        message: str,
        current_profile: Dict[str, Any],
        dialogue_history: List[Dict[str, str]],
    ) -> str:
        history_text = "\n".join(
            [f"{t['role']}: {t['content']}" for t in dialogue_history[-6:]]
        )
        return f"""当前画像：{json.dumps(current_profile, ensure_ascii=False)}

对话历史：
{history_text}

学生最新消息：{message}

请输出更新后的学生画像 JSON。"""

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

    def _rule_based_inference(
        self, message: str, current_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """规则-based 画像推断（兜底）

        TODO: [待完成] 扩展更多认知风格推断信号
        """
        update: Dict[str, Any] = {}

        # 认知风格推断
        if any(w in message for w in ["图", "看", "视觉", "展示"]):
            update["cognitive_modality"] = "visual"
        elif any(w in message for w in ["听", "语音", "讲", "说"]):
            update["cognitive_modality"] = "auditory"
        elif any(w in message for w in ["写", "跑", "试", "练"]):
            update["cognitive_modality"] = "kinesthetic"

        if any(w in message for w in ["对吗", "是不是", "确认", "步骤"]):
            update["cognitive_field"] = "dependent"
        elif any(w in message for w in ["我试试", "我觉得", "想自己", "探索"]):
            update["cognitive_field"] = "independent"

        # 目标导向
        if any(w in message for w in ["考试", "分数", "通过", "及格", "高分"]):
            update["goal_orientation"] = "exam"
        elif any(w in message for w in ["项目", "应用", "做东西", "实践"]):
            update["goal_orientation"] = "application"
        elif any(w in message for w in ["原理", "为什么", "深入", "本质"]):
            update["goal_orientation"] = "exploration"

        # 学习节奏
        if any(w in message for w in ["慢一点", "详细", "耐心", "没懂"]):
            update["learning_pace"] = "slow"
        elif any(w in message for w in ["快一点", "跳过", "已经会了", "简洁"]):
            update["learning_pace"] = "fast"

        # 知识水平（基于自评）
        if any(w in message for w in ["零基础", "完全不懂", "初学"]):
            update["knowledge_level"] = 1.0
        elif any(w in message for w in ["学过一点", "基础"]):
            update["knowledge_level"] = 2.0
        elif any(w in message for w in ["有项目经验", "做过"]):
            update["knowledge_level"] = 4.0

        return update

    def _merge_profile(
        self, current: Dict[str, Any], update: Dict[str, Any]
    ) -> Dict[str, Any]:
        """合并画像，保留已有值，用新值覆盖"""
        merged = dict(current)
        for key, value in update.items():
            if value is not None:
                merged[key] = value
        return merged

    def _classify_intent(self, message: str) -> str:
        """识别学生意图

        TODO: [待完成] 使用 LLM 做更准确的意图分类
        """
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

    def _generate_response(
        self, message: str, intent: str, profile: StudentProfile
    ) -> str:
        """生成自然语言回复"""
        if intent == "KNOWLEDGE_REQUEST":
            return "好的，我已经了解了你的学习背景，接下来为你规划学习路径并生成个性化资源。"
        if intent == "CODE_HELP":
            return "别急，我们一起看看这个错误。先告诉我，你觉得问题可能出在哪里？"
        if intent == "PROGRESS_CHECK":
            return f"你目前已经掌握了 {len(profile.mastered_concepts)} 个知识点，继续保持！"
        return "收到，我会根据你的特点调整后续学习内容。"
