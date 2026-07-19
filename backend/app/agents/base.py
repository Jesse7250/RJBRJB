"""Agent 基类与统一消息协议

对应需求/功能：
- 为智慧伴学多智能体系统定义统一的 Agent 抽象与消息格式。
- 所有 Agent（Profiler / Navigator / Generator / Reviewer / Orchestrator）
  通过 AgentMessage 进行通信，便于 Orchestrator 统一路由、状态传递与后续
  接入 LangGraph 等图编排框架。

主要类/接口：
- AgentMessage：Pydantic 模型，定义 Agent 间统一消息协议，包含 intent、stage、
  payload、context、metadata 及链式更新方法（with_payload / with_context /
  with_stage / reply）。
- BaseAgent：所有 Agent 的抽象基类，提供 system_prompt、LLM 实例、think()
  调用入口和 _format_context() 工具方法；子类必须实现 run(message)。

TODO:
- [已完成] AgentMessage 统一消息协议已实现
- [已完成] BaseAgent 基类与 think() 调用已实现
- [待完成] 统一超时、熔断、日志和降级处理（当前仅在 Orchestrator._safe_run 中做简单降级）
- [待完成] 接入 LangGraph / 类似图编排框架时，可能需要把 AgentMessage 扩展为节点状态
"""
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.agents.llm import BaseLLM, get_llm_provider


class AgentMessage(BaseModel):
    """Agent 间统一消息协议"""

    intent: str = Field("chat", description="用户意图: chat / knowledge_request / code_help / progress_check / path_adjust")
    stage: str = Field("profiler", description="当前处理阶段: profiler / navigator / generator / reviewer / tutor / evaluator")
    payload: Dict[str, Any] = Field(default_factory=dict, description="当前阶段输入数据")
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="会话上下文: profile / dialogue_history / target_concept / session_id 等",
    )
    from_agent: str = Field("user", description="消息来源 Agent")
    to_agent: str = Field("", description="目标 Agent（空表示由 Orchestrator 决定）")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="元数据: depth / error_count / from_cache 等")

    def with_payload(self, **kwargs) -> "AgentMessage":
        """返回一个 payload 被更新的副本（保持原消息不可变，便于链式传递）"""
        new_payload = {**self.payload, **kwargs}
        return self.model_copy(update={"payload": new_payload})

    def with_context(self, **kwargs) -> "AgentMessage":
        """返回一个 context 被更新的副本（保持原消息不可变）"""
        new_context = {**self.context, **kwargs}
        return self.model_copy(update={"context": new_context})

    def with_stage(self, stage: str) -> "AgentMessage":
        """返回一个 stage 被更新的副本，用于 Orchestrator 路由到不同 Agent"""
        return self.model_copy(update={"stage": stage})

    def reply(self, payload: Dict[str, Any], stage: Optional[str] = None, from_agent: Optional[str] = None) -> "AgentMessage":
        """构造当前消息的回复消息，保留上下文与意图"""
        update = {"payload": payload, "from_agent": from_agent or self.from_agent}
        if stage:
            update["stage"] = stage
        return self.model_copy(update=update)


class BaseAgent:
    """所有 Agent 的基类

    子类必须实现 run(message: AgentMessage) -> AgentMessage。
    子类可以选择实现 think() 用于直接调用 LLM。
    """

    name: str = "BaseAgent"
    system_prompt: str = "你是一个智能助手。"

    def __init__(self, llm: Optional[BaseLLM] = None):
        self.llm = llm or get_llm_provider()

    def think(self, user_prompt: str, context: Optional[Dict[str, Any]] = None, max_tokens: int = 4096) -> str:
        """调用 LLM 获取回复：system_prompt + 可选上下文 + 用户输入"""
        messages = [{"role": "system", "content": self.system_prompt}]
        if context:
            # 将字典上下文拼接为 LLM 可读的键值对文本
            messages.append({
                "role": "system",
                "content": f"上下文信息：{self._format_context(context)}",
            })
        messages.append({"role": "user", "content": user_prompt})
        return self.llm.chat(messages, max_tokens=max_tokens)

    def _format_context(self, context: Dict[str, Any]) -> str:
        """将上下文格式化为字符串"""
        parts = []
        for key, value in context.items():
            parts.append(f"{key}: {value}")
        return "\n".join(parts)

    def run(self, message: AgentMessage) -> AgentMessage:
        """统一入口，子类必须实现"""
        raise NotImplementedError(f"{self.__class__.__name__} 未实现 run 方法")

