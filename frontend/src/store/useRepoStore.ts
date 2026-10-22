import { useState, useEffect, useCallback } from 'react';
import { api } from '../api/client';
import {
  ActiveView,
  AIStatusResponse,
  AnalysisStatusResponse,
  ApiFlowData,
  ApiRouteInfo,
  ComparisonResult,
  ERDiagramData,
  FileItem,
  GraphNode,
  ImpactResponse,
  NodeDetailResponse,
  NormalizedGraph,
  TraceResponse,
} from '../types';

export interface RepoState {
  activeAnalysisId: string | null;
  analysisStatus: AnalysisStatusResponse | null;
  graph: NormalizedGraph | null;
  fileTree: FileItem | null;
  erDiagram: ERDiagramData | null;
  selectedNodeId: string | null;
  selectedNodeDetail: NodeDetailResponse | null;
  activeView: ActiveView;
  isAnalyzing: boolean;
  analysisError: string | null;
  aiStatus: AIStatusResponse | null;
  searchQuery: string;
  selectedLayers: string[];
  selectedTypes: string[];
  selectedFileFilter: string | null;
  traceResult: TraceResponse | null;
  impactResult: ImpactResponse | null;
  apiRoutes: ApiRouteInfo[];
  activeRouteId: string | null;
  apiFlowData: ApiFlowData | null;
  comparisonResult: ComparisonResult | null;
  isComparing: boolean;
}

let globalState: RepoState = {
  activeAnalysisId: null,
  analysisStatus: null,
  graph: null,
  fileTree: null,
  erDiagram: null,
  selectedNodeId: null,
  selectedNodeDetail: null,
  activeView: '3d',
  isAnalyzing: false,
  analysisError: null,
  aiStatus: null,
  searchQuery: '',
  selectedLayers: [],
  selectedTypes: [],
  selectedFileFilter: null,
  traceResult: null,
  impactResult: null,
  apiRoutes: [],
  activeRouteId: null,
  apiFlowData: null,
  comparisonResult: null,
  isComparing: false,
};

const listeners = new Set<() => void>();

function emitChange() {
  for (const listener of listeners) {
    listener();
  }
}

function updateState(partial: Partial<RepoState>) {
  globalState = { ...globalState, ...partial };
  emitChange();
}

export function useRepoStore() {
  const [state, setState] = useState<RepoState>(globalState);

  useEffect(() => {
    const handleChange = () => setState(globalState);
    listeners.add(handleChange);
    return () => {
      listeners.delete(handleChange);
    };
  }, []);

  // Poll AI status on mount
  useEffect(() => {
    if (!state.aiStatus) {
      api.getAIStatus()
        .then((ai) => updateState({ aiStatus: ai }))
        .catch(() => updateState({
          aiStatus: {
            available: false,
            configured_model: 'gemma-4-26b-a4b-it',
            preferred_model: 'gemma-4-26b-a4b-it',
            message: 'AI Service unreachable or not configured.'
          }
        }));
    }
  }, [state.aiStatus]);

  const startAnalysis = useCallback(async (repoUrl: string, branch?: string) => {
    updateState({
      isAnalyzing: true,
      analysisError: null,
      selectedNodeId: null,
      selectedNodeDetail: null,
      traceResult: null,
      impactResult: null,
    });

    try {
      const res = await api.analyzeRepository(repoUrl, branch);
      const analysisId = res.analysis_id;
      updateState({ activeAnalysisId: analysisId });

      // Poll analysis progress
      const pollInterval = setInterval(async () => {
        try {
          const status = await api.getAnalysisStatus(analysisId);
          updateState({ analysisStatus: status });

          if (status.status === 'completed') {
            clearInterval(pollInterval);
            const [graph, files, er] = await Promise.all([
              api.getGraph(analysisId),
              api.getFiles(analysisId),
              api.getERDiagram(analysisId),
            ]);

            updateState({
              graph,
              fileTree: files,
              erDiagram: er,
              isAnalyzing: false,
            });
          } else if (status.status === 'failed') {
            clearInterval(pollInterval);
            updateState({
              isAnalyzing: false,
              analysisError: status.errors.join('; ') || 'Analysis failed.',
            });
          }
        } catch (err: any) {
          clearInterval(pollInterval);
          updateState({
            isAnalyzing: false,
            analysisError: err.message || 'Error checking analysis status.',
          });
        }
      }, 700);

    } catch (err: any) {
      updateState({
        isAnalyzing: false,
        analysisError: err.message || 'Failed to start repository analysis.',
      });
    }
  }, []);

  const selectNode = useCallback(async (nodeId: string | null) => {
    if (!nodeId) {
      updateState({ selectedNodeId: null, selectedNodeDetail: null });
      return;
    }

    updateState({ selectedNodeId: nodeId });

    if (globalState.activeAnalysisId) {
      try {
        const detail = await api.getNodeDetails(globalState.activeAnalysisId, nodeId);
        updateState({ selectedNodeDetail: detail });
      } catch {
        // Fallback detail if node fetch fails
        if (globalState.graph) {
          const node = globalState.graph.nodes.find((n) => n.id === nodeId);
          if (node) {
            updateState({
              selectedNodeDetail: {
                node,
                incoming_edges: globalState.graph.edges.filter((e) => e.target === nodeId),
                outgoing_edges: globalState.graph.edges.filter((e) => e.source === nodeId),
                neighbor_nodes: [],
              },
            });
          }
        }
      }
    }
  }, []);

  const setView = useCallback((view: ActiveView) => {
    updateState({ activeView: view });
    if (view === 'api' && globalState.activeAnalysisId && globalState.apiRoutes.length === 0) {
      api.getApiRoutes(globalState.activeAnalysisId).then((routes) => {
        updateState({ apiRoutes: routes });
        if (routes.length > 0) {
          updateState({ activeRouteId: routes[0].id });
          api.getApiFlow(globalState.activeAnalysisId!, routes[0].id).then((flow) => {
            updateState({ apiFlowData: flow });
          });
        }
      });
    }
  }, []);

  const loadApiRoutes = useCallback(async () => {
    if (!globalState.activeAnalysisId) return;
    try {
      const routes = await api.getApiRoutes(globalState.activeAnalysisId);
      updateState({ apiRoutes: routes });
      if (routes.length > 0 && !globalState.activeRouteId) {
        updateState({ activeRouteId: routes[0].id });
        const flow = await api.getApiFlow(globalState.activeAnalysisId, routes[0].id);
        updateState({ apiFlowData: flow });
      }
    } catch (err: any) {
      console.error('Failed to load API routes:', err);
    }
  }, []);

  const loadApiFlow = useCallback(async (routeId: string) => {
    if (!globalState.activeAnalysisId) return;
    updateState({ activeRouteId: routeId });
    try {
      const flow = await api.getApiFlow(globalState.activeAnalysisId, routeId);
      updateState({ apiFlowData: flow });
    } catch (err: any) {
      console.error('Failed to load API flow:', err);
    }
  }, []);

  const runComparison = useCallback(async (params?: { target_analysis_id?: string; target_repository_url?: string; target_branch?: string; base_ref?: string; target_ref?: string }) => {
    if (!globalState.activeAnalysisId) return;
    updateState({ isComparing: true });
    try {
      const res = await api.compareRevisions(globalState.activeAnalysisId, params);
      updateState({ comparisonResult: res, isComparing: false });
    } catch (err: any) {
      console.error('Comparison failed:', err);
      updateState({ isComparing: false });
    }
  }, []);

  const setSearchQuery = useCallback((query: string) => {
    updateState({ searchQuery: query });
  }, []);

  const toggleLayerFilter = useCallback((layer: string) => {
    const current = new Set(globalState.selectedLayers);
    if (current.has(layer)) {
      current.delete(layer);
    } else {
      current.add(layer);
    }
    updateState({ selectedLayers: Array.from(current) });
  }, []);

  const toggleTypeFilter = useCallback((type: string) => {
    const current = new Set(globalState.selectedTypes);
    if (current.has(type)) {
      current.delete(type);
    } else {
      current.add(type);
    }
    updateState({ selectedTypes: Array.from(current) });
  }, []);

  const setFileFilter = useCallback((path: string | null) => {
    updateState({ selectedFileFilter: path });
  }, []);

  const runTrace = useCallback(async (startNodeId: string, targetNodeId?: string) => {
    if (!globalState.activeAnalysisId) return;
    try {
      const res = await api.tracePath(globalState.activeAnalysisId, startNodeId, targetNodeId);
      updateState({ traceResult: res });
    } catch (err: any) {
      updateState({
        traceResult: {
          path_found: false,
          path_nodes: [],
          path_edges: [],
          step_descriptions: [err.message || 'Trace failed.'],
          disclaimer: 'Trace request failed.',
        },
      });
    }
  }, []);

  const clearTrace = useCallback(() => {
    updateState({ traceResult: null });
  }, []);

  const runImpact = useCallback(async (nodeId: string) => {
    if (!globalState.activeAnalysisId) return;
    try {
      const res = await api.analyzeImpact(globalState.activeAnalysisId, nodeId);
      updateState({ impactResult: res });
    } catch (err: any) {
      console.error('Impact analysis error:', err);
    }
  }, []);

  const clearImpact = useCallback(() => {
    updateState({ impactResult: null });
  }, []);

  const resetAll = useCallback(() => {
    updateState({
      activeAnalysisId: null,
      analysisStatus: null,
      graph: null,
      fileTree: null,
      erDiagram: null,
      selectedNodeId: null,
      selectedNodeDetail: null,
      isAnalyzing: false,
      analysisError: null,
      searchQuery: '',
      selectedLayers: [],
      selectedTypes: [],
      selectedFileFilter: null,
      traceResult: null,
      impactResult: null,
      apiRoutes: [],
      activeRouteId: null,
      apiFlowData: null,
      comparisonResult: null,
      isComparing: false,
    });
  }, []);

  return {
    ...state,
    startAnalysis,
    selectNode,
    setView,
    setSearchQuery,
    toggleLayerFilter,
    toggleTypeFilter,
    setFileFilter,
    runTrace,
    clearTrace,
    runImpact,
    clearImpact,
    loadApiRoutes,
    loadApiFlow,
    runComparison,
    resetAll,
  };
}
