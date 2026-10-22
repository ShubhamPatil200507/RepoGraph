export type EvidenceStatus = 'verified' | 'inferred' | 'unknown';

export type NodeType =
  | 'file'
  | 'module'
  | 'class'
  | 'method'
  | 'function'
  | 'route'
  | 'model'
  | 'component'
  | 'config'
  | 'test';

export type EdgeType =
  | 'imports'
  | 'calls'
  | 'contains'
  | 'inherits'
  | 'implements'
  | 'routes_to'
  | 'reads_from'
  | 'writes_to'
  | 'references'
  | 'tests'
  | 'depends_on';

export type ArchitecturalLayer =
  | 'ui'
  | 'api'
  | 'business_logic'
  | 'data_access'
  | 'database'
  | 'configuration'
  | 'tests'
  | 'external';

export interface Position3D {
  x: float;
  y: float;
  z: float;
}

export interface Position2D {
  x: float;
  y: float;
}

export type float = number;

export interface GraphNode {
  id: string;
  label: string;
  type: NodeType | string;
  file_path: string;
  start_line?: number;
  end_line?: number;
  language: string;
  summary?: string;
  metadata: Record<string, any>;
  confidence: number;
  evidence_status: EvidenceStatus;
  layer: ArchitecturalLayer | string;
  cluster?: string;
  position_3d?: Position3D;
  position_2d?: Position2D;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType | string;
  evidence: string;
  source_file?: string;
  source_line?: number;
  confidence: number;
  evidence_status: EvidenceStatus;
}

export interface GraphSummary {
  total_files: number;
  total_nodes: number;
  total_edges: number;
  entry_points_count?: number;
  database_entities_count?: number;
  coupling_density?: number;
  languages: Record<string, number>;
  layers: Record<string, number>;
  warnings: string[];
}

export interface NormalizedGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
  summary: GraphSummary;
}

export interface FileItem {
  path: string;
  name: string;
  is_directory: boolean;
  size_bytes: number;
  language?: string;
  layer?: string;
  node_count: number;
  children?: FileItem[];
}

export interface ERAttribute {
  name: string;
  data_type: string;
  is_primary_key: boolean;
  is_foreign_key: boolean;
  foreign_key_target?: string;
  is_nullable: boolean;
}

export interface EREntity {
  id: string;
  name: string;
  table_name?: string;
  file_path: string;
  start_line?: number;
  end_line?: number;
  attributes: ERAttribute[];
}

export interface ERRelationship {
  id: string;
  source_entity: string;
  target_entity: string;
  cardinality: string;
  evidence_status: EvidenceStatus;
  source_file?: string;
  source_line?: number;
}

export interface ERDiagramData {
  has_database_evidence: boolean;
  detection_summary: string;
  entities: EREntity[];
  relationships: ERRelationship[];
}

export interface AnalysisStageInfo {
  stage_id: number;
  name: string;
  completed: boolean;
  current: boolean;
}

export interface AnalysisStatusResponse {
  analysis_id: string;
  status: 'in_progress' | 'completed' | 'failed';
  current_stage: string;
  progress_message: string;
  stages: AnalysisStageInfo[];
  summary?: GraphSummary;
  errors: string[];
  created_at: number;
  repository: Record<string, any>;
}

export interface NodeDetailResponse {
  node: GraphNode;
  source_code?: string;
  line_start?: number;
  line_end?: number;
  github_url?: string;
  incoming_edges: GraphEdge[];
  outgoing_edges: GraphEdge[];
  neighbor_nodes: GraphNode[];
}

export interface GroundingEvidenceItem {
  file_path: string;
  line_range: string;
  symbol_name: string;
  relationship?: string;
  snippet: string;
}

export interface ExplainResponse {
  explanation: string;
  confidence: number;
  verified_findings: string[];
  inferred_hypotheses: string[];
  unresolved_questions: string[];
  grounding_evidence: GroundingEvidenceItem[];
  ai_available: boolean;
  model_used?: string;
}

export interface TraceResponse {
  path_found: boolean;
  path_nodes: GraphNode[];
  path_edges: GraphEdge[];
  step_descriptions: string[];
  explanation?: string;
  disclaimer: string;
}

export interface ImpactResponse {
  target_node: GraphNode;
  direct_dependents: GraphNode[];
  transitive_dependents: GraphNode[];
  affected_routes: GraphNode[];
  affected_database: GraphNode[];
  affected_tests: GraphNode[];
  affected_layers: Record<string, number>;
  total_impact_count: number;
  risk_level?: 'low' | 'medium' | 'high' | 'critical' | string;
  gemma_explanation?: string;
  disclaimer: string;
}

export interface AIStatusResponse {
  available: boolean;
  configured_model: string;
  preferred_model: string;
  message: string;
}

export type ActiveView = '3d' | '2d' | 'api' | 'er' | 'compare';

export interface ApiRouteInfo {
  id: string;
  label: string;
  http_method: string;
  route_path: string;
  file_path: string;
  start_line?: number;
  end_line?: number;
  summary?: string;
  confidence: number;
}

export interface ApiFlowData {
  route: {
    id: string;
    label: string;
    http_method: string;
    route_path: string;
    file_path: string;
    start_line?: number;
    summary?: string;
  };
  stages: {
    route: any[];
    middleware_auth: any[];
    service_logic: any[];
    data_access: any[];
    database_entities: any[];
    external_integrations: any[];
  };
  flow_nodes: GraphNode[];
  flow_edges: GraphEdge[];
  total_connected_components: number;
  disclaimer: string;
}

export interface ComparisonResult {
  comparison_meta: {
    base_ref: string;
    target_ref: string;
    total_base_nodes: number;
    total_target_nodes: number;
  };
  summary: {
    added_count: number;
    modified_count: number;
    removed_count: number;
    impacted_count: number;
    changed_files_count: number;
  };
  files: {
    added: string[];
    modified: string[];
    deleted: string[];
  };
  changes: {
    added_symbols: any[];
    modified_symbols: any[];
    removed_symbols: any[];
    changed_routes: any[];
    changed_schemas: any[];
    changed_tests: any[];
    impacted_node_ids: string[];
  };
  overlay_graph: {
    nodes: any[];
    edges: GraphEdge[];
  };
}
