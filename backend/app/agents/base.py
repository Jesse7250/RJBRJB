"""Agent 基类

TODO:
- [待完成] 增加 Agent 调用耗时统计
- [待完成] 增加 Agent 记忆（Memory）管理
- [待完成] 支持流式 think 输出
"""
from typing import Any, Dict, List, Optional

from app.agents.llm import BaseLLM, get_llm_provider


class BaseAgent:
    """所有 Agent 的基类

    子类可以选择实现 run() 或自定义方法（如 review）。
    """

    name: str = "BaseAgent"
    system_prompt: str = "你是一个智能助手。"

    def __init__(self, llm: Optional[BaseLLM] = None):
        self.llm = llm or get_llm_provider()

    def think(self, user_prompt: str, context: Optional[Dict[str, Any]] = None) -> str:
        """调用 LLM 获取回复"""
        messages = [{"role": "system", "content": self.system_prompt}]
        if context:
            messages.append({
                "role": "system",
                "content": f"上下文信息：{self._format_context(context)}",
            })
        messages.append({"role": "user", "content": user_prompt})
        return self.llm.chat(messages)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """将上下文格式化为字符串"""
        parts = []
        for key, value in context.items():
            parts.append(f"{key}: {value}")
        return "\n".join(parts)

    def run(self, *args, **kwargs) -> Dict[str, Any]:
        """默认 run 实现，子类可重写"""
        raise NotImplementedError(f"{self.__class__.__name__} 未实现 run 方法")
