import {
  AIStatusResponse,
  AnalysisStatusResponse,
  ERDiagramData,
  ExplainResponse,
  FileItem,
  ImpactResponse,
  NodeDetailResponse,
  NormalizedGraph,
  TraceResponse,
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}: ${res.statusText}`;
    try {
      const data = await res.json();
      if (data.detail) {
        errorDetail = typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // Use fallback
    }
    throw new Error(errorDetail);
  }

  return res.json();
}

export const api = {
  getAIStatus: () => request<AIStatusResponse>('/ai/status'),

  analyzeRepository: (repositoryUrl: string, branch?: string) =>
    request<{
      analysis_id: string;
      status: string;
      stage: string;
      message: string;
      repository: Record<string, any>;
    }>('/repositories/analyze', {
      method: 'POST',
      body: JSON.stringify({ repository_url: repositoryUrl, branch: branch || null }),
    }),

  getAnalysisStatus: (analysisId: string) =>
    request<AnalysisStatusResponse>(`/analyses/${analysisId}`),

  getGraph: (analysisId: string) =>
    request<NormalizedGraph>(`/analyses/${analysisId}/graph`),

  getGraphifyExport: (analysisId: string) =>
    request<Record<string, any>>(`/analyses/${analysisId}/graphify`),

  getFiles: (analysisId: string) =>
    request<FileItem>(`/analyses/${analysisId}/files`),

  getERDiagram: (analysisId: string) =>
    request<ERDiagramData>(`/analyses/${analysisId}/er-diagram`),

  getNodeDetails: (analysisId: string, nodeId: string) =>
    request<NodeDetailResponse>(`/analyses/${analysisId}/nodes/${encodeURIComponent(nodeId)}`),

  explainNode: (analysisId: string, nodeId: string, question: string, secondaryNodeId?: string) =>
    request<ExplainResponse>(`/analyses/${analysisId}/explain`, {
      method: 'POST',
      body: JSON.stringify({
        node_id: nodeId,
        question,
        secondary_node_id: secondaryNodeId || null,
      }),
    }),

  tracePath: (analysisId: string, startNodeId: string, targetNodeId?: string, maxDepth: number = 6) =>
    request<TraceResponse>(`/analyses/${analysisId}/trace`, {
      method: 'POST',
      body: JSON.stringify({
        start_node_id: startNodeId,
        target_node_id: targetNodeId || null,
        max_depth: maxDepth,
      }),
    }),

  analyzeImpact: (analysisId: string, nodeId: string, maxDepth: number = 4) =>
    request<ImpactResponse>(`/analyses/${analysisId}/impact`, {
      method: 'POST',
      body: JSON.stringify({
        node_id: nodeId,
        max_depth: maxDepth,
      }),
    }),

  deleteAnalysis: (analysisId: string) =>
    request<{ message: string }>(`/analyses/${analysisId}`, {
      method: 'DELETE',
    }),
};
