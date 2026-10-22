from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.models.graph import GraphNode, GraphEdge, FileItem, ERDiagramData, GraphSummary


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    app_name: str = "RepoGraph"
    tagline: str = "See how your code works. Explore how everything connects."


class AIStatusResponse(BaseModel):
    available: bool
    configured_model: str
    preferred_model: str
    message: str


class AnalyzeRepoRequest(BaseModel):
    repository_url: str = Field(..., description="Public GitHub repository URL (e.g. https://github.com/owner/repo)")
    branch: Optional[str] = Field(None, description="Optional branch or commit reference")


class AnalyzeRepoResponse(BaseModel):
    analysis_id: str
    status: str  # in_progress, completed, failed
    stage: str
    message: str
    repository: Dict[str, Any]


class AnalysisStageInfo(BaseModel):
    stage_id: int
    name: str
    completed: bool
    current: bool


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: str  # in_progress, completed, failed
    current_stage: str
    progress_message: str
    stages: List[AnalysisStageInfo]
    summary: Optional[GraphSummary] = None
    errors: List[str] = Field(default_factory=list)
    created_at: float
    repository: Dict[str, Any]


class NodeDetailResponse(BaseModel):
    node: GraphNode
    source_code: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    github_url: Optional[str] = None
    incoming_edges: List[GraphEdge] = Field(default_factory=list)
    outgoing_edges: List[GraphEdge] = Field(default_factory=list)
    neighbor_nodes: List[GraphNode] = Field(default_factory=list)


class ExplainRequest(BaseModel):
    node_id: str
    secondary_node_id: Optional[str] = None
    question: str = "Explain the role of this component, its relationships, and architectural context."


class GroundingEvidenceItem(BaseModel):
    file_path: str
    line_range: str
    symbol_name: str
    relationship: Optional[str] = None
    snippet: str


class ExplainResponse(BaseModel):
    explanation: str
    confidence: float
    verified_findings: List[str] = Field(default_factory=list)
    inferred_hypotheses: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    grounding_evidence: List[GroundingEvidenceItem] = Field(default_factory=list)
    ai_available: bool
    model_used: Optional[str] = None


class TraceRequest(BaseModel):
    start_node_id: str
    target_node_id: Optional[str] = None
    max_depth: int = 6


class TraceResponse(BaseModel):
    path_found: bool
    path_nodes: List[GraphNode] = Field(default_factory=list)
    path_edges: List[GraphEdge] = Field(default_factory=list)
    step_descriptions: List[str] = Field(default_factory=list)
    explanation: Optional[str] = None
    disclaimer: str = (
        "Static graph paths represent statically identified imports, calls, or containment links. "
        "They do not guarantee dynamic runtime execution sequence or conditional execution paths."
    )


class ImpactRequest(BaseModel):
    node_id: str
    max_depth: int = 4


class ImpactResponse(BaseModel):
    target_node: GraphNode
    direct_dependents: List[GraphNode] = Field(default_factory=list)
    transitive_dependents: List[GraphNode] = Field(default_factory=list)
    affected_routes: List[GraphNode] = Field(default_factory=list)
    affected_database: List[GraphNode] = Field(default_factory=list)
    affected_tests: List[GraphNode] = Field(default_factory=list)
    affected_layers: Dict[str, int] = Field(default_factory=dict)
    total_impact_count: int = 0
    gemma_explanation: Optional[str] = None
    disclaimer: str = (
        "Change impact is computed via static reverse-dependency graph traversal. "
        "Runtime reflection, dynamic routing, or external consumers are not guaranteed to be captured."
    )
