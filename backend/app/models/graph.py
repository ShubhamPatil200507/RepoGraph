from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EvidenceStatus(str, Enum):
    VERIFIED = "verified"
    INFERRED = "inferred"
    UNKNOWN = "unknown"


class NodeType(str, Enum):
    FILE = "file"
    MODULE = "module"
    CLASS = "class"
    METHOD = "method"
    FUNCTION = "function"
    ROUTE = "route"
    MODEL = "model"
    COMPONENT = "component"
    CONFIG = "config"
    TEST = "test"


class EdgeType(str, Enum):
    IMPORTS = "imports"
    CALLS = "calls"
    CONTAINS = "contains"
    INHERITS = "inherits"
    IMPLEMENTS = "implements"
    ROUTES_TO = "routes_to"
    READS_FROM = "reads_from"
    WRITES_TO = "writes_to"
    REFERENCES = "references"
    TESTS = "tests"
    DEPENDS_ON = "depends_on"


class ArchitecturalLayer(str, Enum):
    UI = "ui"
    API = "api"
    BUSINESS_LOGIC = "business_logic"
    DATA_ACCESS = "data_access"
    DATABASE = "database"
    CONFIGURATION = "configuration"
    TESTS = "tests"
    EXTERNAL = "external"


class Position3D(BaseModel):
    x: float
    y: float
    z: float


class Position2D(BaseModel):
    x: float
    y: float


class GraphNode(BaseModel):
    id: str
    label: str
    type: str  # NodeType or str
    file_path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    language: str = "unknown"
    summary: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 1.0
    evidence_status: str = EvidenceStatus.VERIFIED.value
    layer: str = ArchitecturalLayer.BUSINESS_LOGIC.value
    cluster: Optional[str] = None
    position_3d: Optional[Position3D] = None
    position_2d: Optional[Position2D] = None


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str = EdgeType.DEPENDS_ON.value
    evidence: str = ""
    source_file: Optional[str] = None
    source_line: Optional[int] = None
    confidence: float = 1.0
    evidence_status: str = EvidenceStatus.VERIFIED.value


class FileItem(BaseModel):
    path: str
    name: str
    is_directory: bool = False
    size_bytes: int = 0
    language: Optional[str] = None
    layer: Optional[str] = None
    node_count: int = 0
    children: Optional[List[FileItem]] = None


class ERAttribute(BaseModel):
    name: str
    data_type: str = "text"
    is_primary_key: bool = False
    is_foreign_key: bool = False
    foreign_key_target: Optional[str] = None
    is_nullable: bool = True


class EREntity(BaseModel):
    id: str
    name: str
    table_name: Optional[str] = None
    file_path: str
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    attributes: List[ERAttribute] = Field(default_factory=list)


class ERRelationship(BaseModel):
    id: str
    source_entity: str
    target_entity: str
    cardinality: str = "one-to-many"
    evidence_status: str = EvidenceStatus.VERIFIED.value
    source_file: Optional[str] = None
    source_line: Optional[int] = None


class ERDiagramData(BaseModel):
    has_database_evidence: bool = False
    detection_summary: str = ""
    entities: List[EREntity] = Field(default_factory=list)
    relationships: List[ERRelationship] = Field(default_factory=list)


class GraphSummary(BaseModel):
    total_files: int = 0
    total_nodes: int = 0
    total_edges: int = 0
    languages: Dict[str, int] = Field(default_factory=dict)
    layers: Dict[str, int] = Field(default_factory=dict)
    warnings: List[str] = Field(default_factory=list)


class NormalizedGraph(BaseModel):
    nodes: List[GraphNode] = Field(default_factory=list)
    edges: List[GraphEdge] = Field(default_factory=list)
    summary: GraphSummary = Field(default_factory=GraphSummary)
