"""基于认知风格证据自动推断和更新学生画像

前端通过 /behavior 和 /events 接口上报学习行为，这些行为被记录为
cognitive_profile_evidence。本模块根据证据的权重和类型，自动推断学生的：
- 认知模态（text / visual / auditory / kinesthetic）
- 认知场依存/独立（dependent / independent）
- 学习节奏（slow / normal / fast）
- 目标导向（exam / application / exploration）

推断规则以加权投票为主：同一维度下，权重最高的取值胜出，但需要达到一定
阈值才更新画像，避免少量噪声导致画像抖动。
"""
import re
from typing import Any, Dict, List, Optional, Tuple

from app.services.database import get_cognitive_evidence


# 事件类型 -> (维度, 取值)
# 取值为 None 表示需要从 payload/description 中动态提取
EVENT_VALUE_MAP: Dict[str, Tuple[str, Optional[str]]] = {
    # 认知模态
    "mindmap_clicked": ("cognitive_modality", "visual"),
    "graph_node_selected": ("cognitive_modality", "visual"),
    "resource_switched": ("cognitive_modality", None),
    "audio_played": ("cognitive_modality", "auditory"),
    "code_executed": ("cognitive_modality", "kinesthetic"),
    "code_case_viewed": ("cognitive_modality", "kinesthetic"),
    "exercise_attempt": ("cognitive_modality", "kinesthetic"),
    "cognitive_style_preview": ("cognitive_modality", None),

    # 认知场依存/独立
    "hint_expanded": ("cognitive_field", "dependent"),
    "exercise_attempt_failed": ("cognitive_field", "dependent"),
    "self_exploration": ("cognitive_field", "independent"),

    # 学习节奏（由 page_stay 的 weight/时长决定）
    "page_stay": ("learning_pace", None),

    # 目标导向
    "profile_viewed": ("goal_orientation", "application"),
    "path_viewed": ("goal_orientation", "application"),
    "heatmap_cell_selected": ("goal_orientation", "application"),
}


# 各维度更新阈值：最少有效证据数或最小权重和
DIMENSION_THRESHOLDS: Dict[str, Dict[str, float]] = {
    "cognitive_modality": {"min_count": 2, "min_weight": 1.5},
    "cognitive_field": {"min_count": 2, "min_weight": 1.5},
    "learning_pace": {"min_count": 2, "min_weight": 30.0},
    "goal_orientation": {"min_count": 2, "min_weight": 1.5},
}


def _extract_mode_from_description(description: str) -> Optional[str]:
    """从描述中提取认知风格模式，如 'text' / 'visual' / 'auditory' / 'kinesthetic'"""
    if not description:
        return None
    text = description.lower()
    for mode in ("text", "visual", "auditory", "kinesthetic"):
        if mode in text:
            return mode
    # 中文兜底
    if "文字" in description:
        return "text"
    if "视觉" in description:
        return "visual"
    if "听觉" in description:
        return "auditory"
    if "动觉" in description or "动手" in description:
        return "kinesthetic"
    return None


def _normalize_modality(value: str) -> Optional[str]:
    text = value.strip().lower()
    aliases = {
        "text": "text",
        "document": "text",
        "lecture": "text",
        "visual": "visual",
        "mindmap": "visual",
        "video": "visual",
        "auditory": "auditory",
        "audio": "auditory",
        "kinesthetic": "kinesthetic",
        "exercise": "kinesthetic",
        "exercises": "kinesthetic",
        "code": "kinesthetic",
        "code_case": "kinesthetic",
        "sandbox": "kinesthetic",
    }
    return aliases.get(text)


def _pace_from_weight(weight: float) -> str:
    """根据页面停留时长推断学习节奏"""
    if weight > 60:
        return "slow"
    if weight < 15:
        return "fast"
    return "normal"


def _extract_value_from_evidence(evidence: dict) -> Optional[str]:
    """根据单条证据提取其暗示的画像取值"""
    event_type = evidence.get("evidence_type", "")
    dimension, fixed_value = EVENT_VALUE_MAP.get(event_type, (None, None))
    if dimension is None:
        return None

    # 固定映射
    if fixed_value:
        return fixed_value

    # 动态取值
    source_value = evidence.get("source_value")
    if source_value:
        if dimension == "cognitive_modality":
            return _normalize_modality(str(source_value)) or _extract_mode_from_description(str(source_value))
        return str(source_value)

    description = evidence.get("description", "")
    if event_type in {"cognitive_style_preview", "resource_switched"}:
        return _extract_mode_from_description(description)
    if event_type == "page_stay":
        weight = float(evidence.get("weight", 0.0))
        return _pace_from_weight(weight)

    return None


def infer_profile_updates(
    session_id: str,
    current_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """根据认知证据推断画像更新项

    Returns:
        只返回需要更新的字段，例如 {"cognitive_modality": "visual"}。
    """
    current_profile = current_profile or {}
    evidence_list = get_cognitive_evidence(session_id)
    if not evidence_list:
        return {}

    # 按维度聚合权重
    dimension_votes: Dict[str, Dict[str, float]] = {}
    dimension_counts: Dict[str, int] = {}
    for ev in evidence_list:
        dimension = ev.get("dimension")
        if dimension not in DIMENSION_THRESHOLDS:
            continue
        value = _extract_value_from_evidence(ev)
        if not value:
            continue
        weight = float(ev.get("weight", 1.0))
        dimension_votes.setdefault(dimension, {}).setdefault(value, 0.0)
        dimension_votes[dimension][value] += weight
        dimension_counts[dimension] = dimension_counts.get(dimension, 0) + 1

    updates: Dict[str, Any] = {}
    for dimension, votes in dimension_votes.items():
        threshold = DIMENSION_THRESHOLDS[dimension]
        total_weight = sum(votes.values())
        count = dimension_counts.get(dimension, 0)
        if count < threshold["min_count"] or total_weight < threshold["min_weight"]:
            continue
        # 选择权重最高的取值
        best_value = max(votes.items(), key=lambda x: x[1])[0]

        # 如果当前画像已有相同值，不更新
        if current_profile.get(dimension) == best_value:
            continue
        updates[dimension] = best_value

    return updates


def update_profile_from_evidence(
    session: Dict[str, Any],
    session_id: str,
) -> Dict[str, Any]:
    """根据证据自动更新会话画像，并返回更新结果

    Args:
        session: 会话字典，会被直接修改。
        session_id: 会话 ID。

    Returns:
        {"updated": bool, "changes": {...}, "profile": {...}}
    """
    profile = session.get("profile", {})
    updates = infer_profile_updates(session_id, profile)
    if updates:
        profile.update(updates)
        session["profile"] = profile
    return {
        "updated": bool(updates),
        "changes": updates,
        "profile": profile,
    }

