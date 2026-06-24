"""多智能体系统

对应需求/功能：
- 智学蜂巢 EduHive 的后端多智能体包，对外暴露所有 Agent 类。
- 当前实现采用 5 角色分层架构：
  - Orchestrator：总调度
  - Profiler：画像构建
  - Navigator：路径规划
  - Generator：资源生成（原 Builder）
  - Reviewer：审核 + 辅导 + 评估三位一体
- Reviewer 内部保留 4 个审核视角（Expert/Teacher/Student-Sim/Guardian）
  以及 Socrates 辅导和 Evaluator 评估能力。

主要导出：
- ProfilerAgent、NavigatorAgent、GeneratorAgent、ReviewerAgent、AgentOrchestrator
- BuilderAgent = GeneratorAgent（保留旧别名，兼容历史代码）

TODO:
- [已完成] 5 角色分层架构与包级导出已实现
- [已完成] BuilderAgent 别名兼容旧导入已实现
- [待完成] Reviewer 子模块可考虑进一步解耦，但当前已满足调用需求
"""
from app.agents.generator import GeneratorAgent
from app.agents.navigator import NavigatorAgent
from app.agents.orchestrator import AgentOrchestrator
from app.agents.profiler import ProfilerAgent
from app.agents.reviewer import ReviewerAgent

# 保留旧别名，兼容历史代码
BuilderAgent = GeneratorAgent

__all__ = [
    "ProfilerAgent",
    "NavigatorAgent",
    "GeneratorAgent",
    "BuilderAgent",      # 别名
    "ReviewerAgent",
    "AgentOrchestrator",
]
