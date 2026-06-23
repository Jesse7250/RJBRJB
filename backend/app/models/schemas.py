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
