"""Pydantic 数据模型"""
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="消息角色: user/assistant/system")
    content: str = Field(..., description="消息内容")


class StudentProfile(BaseModel):
    """学生画像"""
    knowledge_level: float = Field(1.0, ge=1.0, le=5.0, description="知识水平 1-5")
    cognitive_field: str = Field("dependent", description="场依存/场独立: dependent/independent")
    cognitive_modality: str = Field("visual", description="视觉/听觉/动觉: visual/auditory/kinesthetic")
    learning_pace: str = Field("normal", description="学习节奏: slow/normal/fast")
    goal_orientation: str = Field("application", description="目标导向: exam/application/exploration")
    error_patterns: List[str] = Field(default_factory=list, description="常见错误模式")
    mastered_concepts: List[str] = Field(default_factory=list, description="已掌握知识点")


class SessionCreate(BaseModel):
    user_id: Optional[str] = None
    target_concept: Optional[str] = None


class SessionResponse(BaseModel):
    session_id: str
    profile: StudentProfile
    target_concept: Optional[str] = None
    suggested_path: List[str] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str
    message_type: str = "text"  # text / code / help / skip


class EventLogRequest(BaseModel):
    event_type: str  # exercise_submitted / code_executed / resource_generated / chat
    payload: Dict[str, Any] = Field(default_factory=dict)


class ResourceType(BaseModel):
    type: str  # document / mindmap / exercise / code_case / audio
    content: Any


class ResourcePackage(BaseModel):
    concept: str
    document: Optional[str] = None
    mindmap: Optional[str] = None
    exercises: Optional[List[Dict]] = None
    code_cases: Optional[List[Dict]] = None
    audio_text: Optional[str] = None


class DebateRound(BaseModel):
    round: int
    agent: str
    verdict: str  # PASS / WARN / REJECT
    message: str
    suggestion: Optional[str] = None


class DebateReport(BaseModel):
    status: str  # PASSED / MODIFIED / REJECTED
    rounds: List[DebateRound]
    final_votes: Dict[str, str]


class AgentResponse(BaseModel):
    agent_name: str
    response_type: str
    content: Any
    profile_update: Optional[Dict] = None
    debate_report: Optional[DebateReport] = None


class GraphNode(BaseModel):
    id: str
    name: str
    module: str
    difficulty: int


class GraphEdge(BaseModel):
    source: str
    target: str
    strength: float


class GraphData(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


# =============================================================================
# 新增：资源生成任务与资源模型
# =============================================================================

class GenerationTask(BaseModel):
    task_id: str
    session_id: str
    concept: str
    status: str = Field("pending", description="pending / planning / generating / debating / rendering / completed / failed")
    progress: int = Field(0, ge=0, le=100)
    stage_message: str = ""
    result: Dict[str, Any] = Field(default_factory=dict)
    error_message: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class Resource(BaseModel):
    resource_id: str
    task_id: Optional[str] = None
    session_id: str
    concept: str
    version: int = 1
    document: Optional[str] = None
    mindmap: Optional[str] = None
    exercises: Optional[List[Dict[str, Any]]] = None
    code_cases: Optional[List[Dict[str, Any]]] = None
    audio_text: Optional[str] = None
    debate_report: Optional[DebateReport] = None
    status: str = Field("approved", description="approved / rejected / cached / draft")
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ResourceVersion(BaseModel):
    version_id: Optional[int] = None
    resource_id: str
    concept: str
    version: int
    change_reason: str
    triggered_by: str
    content_snapshot: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = None


# =============================================================================
# 新增：代码提交与掌握度模型
# =============================================================================

class CodeSubmission(BaseModel):
    submission_id: str
    session_id: str
    exercise_id: Optional[str] = None
    concept: str
    code: str
    output: Optional[str] = None
    passed: bool = False
    error_type: str = Field("", description="syntax / runtime / logic / passed")
    execution_time: Optional[float] = None
    created_at: Optional[str] = None


class MasteryState(BaseModel):
    id: Optional[int] = None
    session_id: str
    concept: str
    p_known: float = Field(0.0, ge=0.0, le=1.0, description="BKT 掌握概率 0-1")
    evidence_count: int = 0
    last_updated: Optional[str] = None


class HeatmapData(BaseModel):
    concept: str
    p_known: float


# =============================================================================
# 新增：认知风格证据与资源反馈模型
# =============================================================================

class CognitiveEvidence(BaseModel):
    id: Optional[int] = None
    session_id: str
    dimension: str = Field(..., description="cognitive_field / cognitive_modality / learning_pace / etc")
    evidence_type: str = Field(..., description="click_mindmap / run_code / stay_audio / expand_hint / etc")
    weight: float = Field(..., ge=0.0, le=1.0)
    description: Optional[str] = None
    source_event_id: Optional[int] = None
    created_at: Optional[str] = None


class ResourceFeedback(BaseModel):
    feedback_id: Optional[int] = None
    session_id: str
    resource_id: str
    concept: str
    rating: Optional[int] = Field(None, ge=1, le=5)
    error_report: Optional[str] = None
    confusion_marked: bool = False
    created_at: Optional[str] = None


class ResourceFeedbackStats(BaseModel):
    concept: str
    total_feedback: int
    confusion_count: int
    confusion_rate: float
    average_rating: Optional[float]
    error_reports: List[str]
