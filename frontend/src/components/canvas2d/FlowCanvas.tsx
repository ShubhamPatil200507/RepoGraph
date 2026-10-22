import React, { useMemo, useCallback } from 'react';
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  Handle,
  Position,
  NodeProps,
  Edge,
  Node,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { useRepoStore } from '../../store/useRepoStore';
import { GraphNode } from '../../types';
import { getLayerColor, TYPE_BADGES } from '../../utils/theme';

// Custom 2D Node Component
const CustomNode: React.FC<NodeProps> = ({ data, selected }) => {
  const node = data.node as GraphNode;
  const layerColor = getLayerColor(node.layer);
  const typeBadge = TYPE_BADGES[node.type] || { label: node.type, color: 'bg-slate-800 text-slate-300' };

  return (
    <div
      className={`min-w-[190px] max-w-[240px] rounded-lg bg-space-900 border p-2.5 shadow-md transition-all ${
        selected
          ? 'border-brand-400 ring-2 ring-brand-500/30 shadow-brand-500/10'
          : `${layerColor.border} hover:border-slate-500`
      }`}
    >
      <Handle type="target" position={Position.Top} className="!bg-slate-500 !w-2 !h-2" />

      <div className="flex items-center justify-between gap-1 mb-1">
        <span className={`text-[9px] font-mono uppercase px-1.5 py-0.5 rounded border ${typeBadge.color}`}>
          {typeBadge.label}
        </span>
        <span className={`text-[9px] font-mono ${layerColor.text}`}>
          {node.layer.replace('_', ' ')}
        </span>
      </div>

      <div className="font-mono text-xs font-semibold text-slate-100 truncate mb-0.5" title={node.label}>
        {node.label}
      </div>

      <div className="text-[10px] text-slate-400 truncate font-mono" title={node.file_path}>
        {node.file_path}:{node.start_line || 1}
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-slate-500 !w-2 !h-2" />
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

export const FlowCanvas: React.FC = () => {
  const {
    graph,
    selectedNodeId,
    selectNode,
    searchQuery,
    selectedLayers,
    selectedTypes,
    selectedFileFilter,
    traceResult,
    impactResult,
  } = useRepoStore();

  const traceNodeIds = useMemo(() => {
    if (!traceResult?.path_nodes) return new Set<string>();
    return new Set(traceResult.path_nodes.map((n) => n.id));
  }, [traceResult]);

  const directImpactIds = useMemo(() => {
    if (!impactResult?.direct_dependents) return new Set<string>();
    return new Set(impactResult.direct_dependents.map((n) => n.id));
  }, [impactResult]);

  const transitiveImpactIds = useMemo(() => {
    if (!impactResult?.transitive_dependents) return new Set<string>();
    return new Set(impactResult.transitive_dependents.map((n) => n.id));
  }, [impactResult]);

  // Compute 2D nodes
  const initialNodes: Node[] = useMemo(() => {
    if (!graph) return [];
    return graph.nodes
      .filter((n) => {
        if (searchQuery) {
          const q = searchQuery.toLowerCase();
          if (!n.label.toLowerCase().includes(q) && !n.file_path.toLowerCase().includes(q)) {
            return false;
          }
        }
        if (selectedLayers.length > 0 && !selectedLayers.includes(n.layer)) {
          return false;
        }
        if (selectedTypes.length > 0 && !selectedTypes.includes(n.type)) {
          return false;
        }
        if (selectedFileFilter && n.file_path !== selectedFileFilter) {
          return false;
        }
        return true;
      })
      .map((node) => ({
        id: node.id,
        type: 'custom',
        position: {
          x: node.position_2d?.x ?? 0,
          y: node.position_2d?.y ?? 0,
        },
        data: { node },
        selected:
          node.id === selectedNodeId ||
          traceNodeIds.has(node.id) ||
          directImpactIds.has(node.id) ||
          transitiveImpactIds.has(node.id),
      }));
  }, [
    graph,
    selectedNodeId,
    searchQuery,
    selectedLayers,
    selectedTypes,
    selectedFileFilter,
    traceNodeIds,
    directImpactIds,
    transitiveImpactIds,
  ]);

  // Compute 2D edges
  const initialEdges: Edge[] = useMemo(() => {
    if (!graph) return [];
    const validNodeIds = new Set(initialNodes.map((n) => n.id));

    return graph.edges
      .filter((e) => validNodeIds.has(e.source) && validNodeIds.has(e.target))
      .map((edge) => {
        const isHighlighted = edge.source === selectedNodeId || edge.target === selectedNodeId;
        return {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          label: edge.type.replace('_', ' '),
          labelStyle: { fill: '#94a3b8', fontSize: 10, fontFamily: 'monospace' },
          style: {
            stroke: isHighlighted ? '#38bdf8' : '#334155',
            strokeWidth: isHighlighted ? 2 : 1,
          },
          animated: isHighlighted,
        };
      });
  }, [graph, initialNodes, selectedNodeId]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Sync state when props change
  React.useEffect(() => {
    setNodes(initialNodes);
  }, [initialNodes, setNodes]);

  React.useEffect(() => {
    setEdges(initialEdges);
  }, [initialEdges, setEdges]);

  const onNodeClick = useCallback(
    (_: any, node: Node) => {
      selectNode(node.id);
    },
    [selectNode]
  );

  const onPaneClick = useCallback(() => {
    selectNode(null);
  }, [selectNode]);

  if (!graph) return null;

  return (
    <div className="w-full h-full bg-space-950">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        fitView
        colorMode="dark"
        minZoom={0.15}
        maxZoom={2.0}
      >
        <Background color="#1e293b" gap={20} size={1} />
        <Controls className="!bg-space-900 !border-space-800 !text-slate-300" />
        <MiniMap
          nodeColor={(n) => {
            const nodeData = n.data?.node as GraphNode;
            return nodeData ? getLayerColor(nodeData.layer).hex : '#64748b';
          }}
          className="!bg-space-900/90 !border-space-800"
          maskColor="rgba(8, 11, 17, 0.7)"
        />
      </ReactFlow>
    </div>
  );
};
