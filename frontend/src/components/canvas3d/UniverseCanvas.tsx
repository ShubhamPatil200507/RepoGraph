import React, { useRef, useMemo, useState, useEffect } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { OrbitControls, Html, Stars, Line } from '@react-three/drei';
import * as THREE from 'three';
import {
  Maximize2,
  RotateCcw,
  Eye,
  EyeOff,
  Crosshair,
  Layers,
  HelpCircle,
} from 'lucide-react';
import { useRepoStore } from '../../store/useRepoStore';
import { GraphNode, GraphEdge } from '../../types';
import { getLayerColor, LAYER_COLORS } from '../../utils/theme';

// Node 3D Component
const NodeMesh: React.FC<{
  node: GraphNode;
  isSelected: boolean;
  isNeighbor: boolean;
  isDimmed: boolean;
  isTraceNode: boolean;
  isDirectImpact?: boolean;
  isTransitiveImpact?: boolean;
  showLabels: boolean;
  onClick: () => void;
}> = ({
  node,
  isSelected,
  isNeighbor,
  isDimmed,
  isTraceNode,
  isDirectImpact = false,
  isTransitiveImpact = false,
  showLabels,
  onClick,
}) => {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  const pos: [number, number, number] = useMemo(() => {
    if (node.position_3d) {
      return [node.position_3d.x, node.position_3d.y, node.position_3d.z];
    }
    return [0, 0, 0];
  }, [node.position_3d]);

  const color = useMemo(() => {
    if (isDirectImpact) return '#f59e0b'; // Amber for direct dependent
    if (isTransitiveImpact) return '#f43f5e'; // Rose for transitive dependent
    if (isTraceNode) return '#06b6d4';
    return getLayerColor(node.layer).hex;
  }, [node.layer, isTraceNode, isDirectImpact, isTransitiveImpact]);

  useFrame((state) => {
    if (!meshRef.current) return;
    if (isSelected) {
      const scale = 1.35 + Math.sin(state.clock.elapsedTime * 4) * 0.15;
      meshRef.current.scale.set(scale, scale, scale);
    } else if (hovered) {
      meshRef.current.scale.set(1.2, 1.2, 1.2);
    } else {
      meshRef.current.scale.set(1.0, 1.0, 1.0);
    }
  });

  const nodeRadius = useMemo(() => {
    if (node.type === 'file') return 1.8;
    if (node.type === 'class' || node.type === 'model' || node.type === 'component') return 1.5;
    if (node.type === 'route') return 1.3;
    return 1.1;
  }, [node.type]);

  const opacity = isDimmed ? 0.18 : 1.0;

  return (
    <group position={pos}>
      <mesh
        ref={meshRef}
        onClick={(e) => {
          e.stopPropagation();
          onClick();
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          setHovered(true);
        }}
        onPointerOut={() => setHovered(false)}
      >
        <sphereGeometry args={[nodeRadius, 24, 24]} />
        <meshStandardMaterial
          color={color}
          emissive={isSelected ? color : hovered ? color : '#000000'}
          emissiveIntensity={isSelected ? 0.6 : hovered ? 0.3 : 0}
          transparent
          opacity={opacity}
          roughness={0.3}
          metalness={0.2}
        />
      </mesh>

      {/* Selected Node Ring */}
      {isSelected && (
        <mesh rotation={[Math.PI / 2, 0, 0]}>
          <ringGeometry args={[nodeRadius + 0.6, nodeRadius + 0.9, 32]} />
          <meshBasicMaterial color="#38bdf8" side={THREE.DoubleSide} transparent opacity={0.8} />
        </mesh>
      )}

      {/* Label or Tooltip */}
      {(showLabels || hovered || isSelected || isTraceNode) && !isDimmed && (
        <Html
          position={[0, nodeRadius + 1.2, 0]}
          center
          distanceFactor={55}
          style={{ pointerEvents: 'none', transition: 'all 0.15s ease' }}
        >
          <div
            className={`px-2 py-0.5 rounded text-[11px] font-mono whitespace-nowrap shadow-lg backdrop-blur border transition-all ${
              isSelected
                ? 'bg-brand-950/95 text-brand-300 border-brand-500 font-bold scale-110'
                : hovered
                ? 'bg-space-900/95 text-slate-100 border-slate-600 scale-105'
                : 'bg-space-950/80 text-slate-300 border-space-800 text-[10px]'
            }`}
          >
            <span>{node.label}</span>
            {hovered && (
              <span className="text-[9px] text-slate-400 block font-sans">
                {node.type} • {node.layer}
              </span>
            )}
          </div>
        </Html>
      )}
    </group>
  );
};

// Edge 3D Component
const EdgeLine: React.FC<{
  edge: GraphEdge;
  sourceNode?: GraphNode;
  targetNode?: GraphNode;
  isHighlighted: boolean;
  isDimmed: boolean;
  isTraceEdge: boolean;
}> = ({ sourceNode, targetNode, isHighlighted, isDimmed, isTraceEdge }) => {
  if (!sourceNode?.position_3d || !targetNode?.position_3d) return null;

  const points: [number, number, number][] = [
    [sourceNode.position_3d.x, sourceNode.position_3d.y, sourceNode.position_3d.z],
    [targetNode.position_3d.x, targetNode.position_3d.y, targetNode.position_3d.z],
  ];

  const color = isTraceEdge ? '#38bdf8' : isHighlighted ? '#818cf8' : '#334155';
  const opacity = isTraceEdge ? 0.95 : isHighlighted ? 0.8 : isDimmed ? 0.08 : 0.35;

  return (
    <Line
      points={points}
      color={color}
      lineWidth={isHighlighted || isTraceEdge ? 2 : 1}
      transparent
      opacity={opacity}
    />
  );
};

// Architectural Layer Planes
const LayerPlanes: React.FC = () => {
  const planes = [
    { name: 'UI / Presentation', z: 36.0, color: '#06b6d4' },
    { name: 'API / Routing', z: 20.0, color: '#10b981' },
    { name: 'Business Logic', z: 0.0, color: '#6366f1' },
    { name: 'Data Access', z: -20.0, color: '#f59e0b' },
    { name: 'Database', z: -36.0, color: '#f43f5e' },
  ];

  return (
    <group>
      {planes.map((p) => (
        <group key={p.name} position={[0, 0, p.z]}>
          <gridHelper
            args={[90, 18, p.color, '#1e293b']}
            rotation={[Math.PI / 2, 0, 0]}
          />
          <Html position={[-42, -42, 0]} distanceFactor={60}>
            <div className="text-[10px] font-mono tracking-wider uppercase px-2 py-0.5 rounded bg-space-950/80 border border-space-800 text-slate-400 select-none">
              {p.name}
            </div>
          </Html>
        </group>
      ))}
    </group>
  );
};

// Camera Controller for Smooth Focus
const CameraFocus: React.FC<{ targetNode?: GraphNode | null }> = ({ targetNode }) => {
  const { camera } = useThree();
  const controlsRef = useRef<any>(null);

  useEffect(() => {
    if (targetNode?.position_3d) {
      const { x, y, z } = targetNode.position_3d;
      camera.position.set(x + 15, y + 15, z + 25);
      camera.lookAt(x, y, z);
    }
  }, [targetNode, camera]);

  return null;
};

export const UniverseCanvas: React.FC = () => {
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

  const isLargeGraph = (graph?.nodes?.length || 0) > 150;
  const [showLabels, setShowLabels] = useState(!isLargeGraph);
  const [showPlanes, setShowPlanes] = useState(true);
  const [cameraResetKey, setCameraResetKey] = useState(0);

  const controlsRef = useRef<any>(null);

  // Filtered nodes
  const filteredNodes = useMemo(() => {
    if (!graph) return [];
    return graph.nodes.filter((node) => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const matchesLabel = node.label.toLowerCase().includes(q);
        const matchesPath = node.file_path.toLowerCase().includes(q);
        if (!matchesLabel && !matchesPath) return false;
      }
      if (selectedLayers.length > 0 && !selectedLayers.includes(node.layer)) {
        return false;
      }
      if (selectedTypes.length > 0 && !selectedTypes.includes(node.type)) {
        return false;
      }
      if (selectedFileFilter && node.file_path !== selectedFileFilter) {
        return false;
      }
      return true;
    });
  }, [graph, searchQuery, selectedLayers, selectedTypes, selectedFileFilter]);

  const nodesById = useMemo(() => {
    if (!graph) return new Map<string, GraphNode>();
    return new Map(graph.nodes.map((n) => [n.id, n]));
  }, [graph]);

  // Neighbors of selected node
  const neighborIds = useMemo(() => {
    if (!selectedNodeId || !graph) return new Set<string>();
    const neighbors = new Set<string>();
    for (const edge of graph.edges) {
      if (edge.source === selectedNodeId) neighbors.add(edge.target);
      if (edge.target === selectedNodeId) neighbors.add(edge.source);
    }
    return neighbors;
  }, [selectedNodeId, graph]);

  // Trace nodes & edges
  const traceNodeIds = useMemo(() => {
    if (!traceResult?.path_nodes) return new Set<string>();
    return new Set(traceResult.path_nodes.map((n) => n.id));
  }, [traceResult]);

  const traceEdgeIds = useMemo(() => {
    if (!traceResult?.path_edges) return new Set<string>();
    return new Set(traceResult.path_edges.map((e) => e.id));
  }, [traceResult]);

  // Impact nodes
  const directImpactIds = useMemo(() => {
    if (!impactResult?.direct_dependents) return new Set<string>();
    return new Set(impactResult.direct_dependents.map((n) => n.id));
  }, [impactResult]);

  const transitiveImpactIds = useMemo(() => {
    if (!impactResult?.transitive_dependents) return new Set<string>();
    return new Set(impactResult.transitive_dependents.map((n) => n.id));
  }, [impactResult]);

  const hasImpactActive = directImpactIds.size > 0 || transitiveImpactIds.size > 0;

  const selectedNode = selectedNodeId ? nodesById.get(selectedNodeId) : null;

  const handleResetCamera = () => {
    if (controlsRef.current) {
      controlsRef.current.reset();
    }
    setCameraResetKey((prev) => prev + 1);
  };

  if (!graph) return null;

  return (
    <div className="relative w-full h-full bg-space-950 overflow-hidden">
      <Canvas
        key={cameraResetKey}
        camera={{ position: [0, 45, 95], fov: 45 }}
        gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
      >
        <color attach="background" args={['#080b11']} />
        <ambientLight intensity={0.7} />
        <pointLight position={[50, 50, 50]} intensity={1.2} />
        <pointLight position={[-50, -50, -50]} intensity={0.5} />

        <Stars radius={120} depth={50} count={3000} factor={4} saturation={0} fade speed={1} />

        {showPlanes && <LayerPlanes />}

        {/* Nodes */}
        {filteredNodes.map((node) => {
          const isSelected = node.id === selectedNodeId;
          const isNeighbor = neighborIds.has(node.id);
          const isTraceNode = traceNodeIds.has(node.id);
          const isDirectImpact = directImpactIds.has(node.id);
          const isTransitiveImpact = transitiveImpactIds.has(node.id);

          const isDimmed = Boolean(
            (selectedNodeId && !isSelected && !isNeighbor && !isDirectImpact && !isTransitiveImpact) ||
            (traceNodeIds.size > 0 && !isTraceNode) ||
            (hasImpactActive && !isDirectImpact && !isTransitiveImpact && node.id !== impactResult?.target_node?.id)
          );

          return (
            <NodeMesh
              key={node.id}
              node={node}
              isSelected={isSelected}
              isNeighbor={isNeighbor}
              isDimmed={isDimmed}
              isTraceNode={isTraceNode}
              isDirectImpact={isDirectImpact}
              isTransitiveImpact={isTransitiveImpact}
              showLabels={showLabels}
              onClick={() => selectNode(node.id)}
            />
          );
        })}

        {/* Edges */}
        {graph.edges.map((edge) => {
          const sourceNode = nodesById.get(edge.source);
          const targetNode = nodesById.get(edge.target);
          if (!sourceNode || !targetNode) return null;

          const isHighlighted =
            edge.source === selectedNodeId || edge.target === selectedNodeId;
          const isTraceEdge = traceEdgeIds.has(edge.id);
          const isDimmed = Boolean(
            (selectedNodeId && !isHighlighted) ||
            (traceEdgeIds.size > 0 && !isTraceEdge)
          );

          return (
            <EdgeLine
              key={edge.id}
              edge={edge}
              sourceNode={sourceNode}
              targetNode={targetNode}
              isHighlighted={isHighlighted}
              isDimmed={isDimmed}
              isTraceEdge={isTraceEdge}
            />
          );
        })}

        <OrbitControls
          ref={controlsRef}
          enableDamping
          dampingFactor={0.06}
          minDistance={15}
          maxDistance={250}
        />

        <CameraFocus targetNode={selectedNode} />
      </Canvas>

      {/* Floating Canvas Controls */}
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-1.5 bg-space-900/90 backdrop-blur p-1 rounded-lg border border-space-800 shadow-xl">
        <button
          onClick={handleResetCamera}
          className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-space-800 rounded transition"
          title="Reset Camera View"
        >
          <RotateCcw className="w-4 h-4" />
        </button>

        <button
          onClick={() => setShowLabels((prev) => !prev)}
          className={`p-1.5 rounded transition ${
            showLabels ? 'text-brand-400 bg-brand-500/10' : 'text-slate-400 hover:text-slate-100 hover:bg-space-800'
          }`}
          title={showLabels ? 'Hide Labels' : 'Show All Labels'}
        >
          {showLabels ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
        </button>

        <button
          onClick={() => setShowPlanes((prev) => !prev)}
          className={`p-1.5 rounded transition ${
            showPlanes ? 'text-brand-400 bg-brand-500/10' : 'text-slate-400 hover:text-slate-100 hover:bg-space-800'
          }`}
          title={showPlanes ? 'Hide Layer Grids' : 'Show Layer Grids'}
        >
          <Layers className="w-4 h-4" />
        </button>

        {isLargeGraph && (
          <div
            className="p-1 text-[9px] font-mono text-cyan-400 text-center max-w-[60px] leading-tight bg-space-950/80 rounded border border-cyan-800/40"
            title="LOD active: Rendering optimized for high-density graph"
          >
            LOD ON
          </div>
        )}
      </div>

      {/* Universe Layer Legend */}
      <div className="absolute bottom-4 left-4 z-10 bg-space-900/90 backdrop-blur p-2.5 rounded-lg border border-space-800 shadow-xl hidden md:block">
        <div className="text-[10px] font-mono uppercase text-slate-400 mb-1.5">Architectural Layers</div>
        <div className="flex flex-col gap-1 text-[11px]">
          {Object.entries(LAYER_COLORS).map(([layer, val]) => (
            <div key={layer} className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: val.hex }} />
              <span className="text-slate-300 capitalize">{layer.replace('_', ' ')}</span>
            </div>
          ))}

          <div className="pt-1.5 mt-1 border-t border-space-800 flex flex-col gap-1 text-[10px] font-mono">
            <div className="flex items-center gap-2 text-cyan-400">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span>Trace Path</span>
            </div>
            <div className="flex items-center gap-2 text-amber-400">
              <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
              <span>Direct Dependent</span>
            </div>
            <div className="flex items-center gap-2 text-rose-400">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-400" />
              <span>Transitive Impact</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
