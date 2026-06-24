"""Reviewer 包：审核 + 辅导 + 评估三位一体

对应需求/功能：
- Reviewer Agent 的内部子模块包，对外统一暴露 ReviewerAgent。
- 将资源审核（DebateCouncil）、苏格拉底辅导（SocratesTutor）、
  学习评估（LearningEvaluator）拆分为独立模块，降低 Orchestrator 复杂度。

主要导出：
- ReviewerAgent：统一入口，根据 stage/action 分发到 review / tutor / evaluate。
- DebateCouncil：4 视角（Expert/Teacher/Student-Sim/Guardian）资源审核议会。
- SocratesTutor：苏格拉底式提问辅导。
- LearningEvaluator：基于学习行为数据的效果评估。

TODO:
- [已完成] Reviewer 统一入口与三分路子模块已实现
- [已完成] 4 视角辩论议会与快速审核已实现
- [已完成] 苏格拉底辅导与学习评估已实现
- [待完成] DebateCouncil 的评分策略可配置化（当前阈值写死）
"""
from app.agents.reviewer.debate_council import DebateCouncil
from app.agents.reviewer.evaluator import LearningEvaluator
from app.agents.reviewer.reviewer_agent import ReviewerAgent
from app.agents.reviewer.socrates import SocratesTutor

__all__ = ["ReviewerAgent", "DebateCouncil", "SocratesTutor", "LearningEvaluator"]
