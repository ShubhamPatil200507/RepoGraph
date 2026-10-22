import React, { useState } from 'react';
import {
  Code2,
  ExternalLink,
  Sparkles,
  GitPullRequest,
  AlertTriangle,
  ArrowRight,
  ArrowLeft,
  X,
  Copy,
  Check,
  ShieldCheck,
  HelpCircle,
  Play,
  RotateCcw,
} from 'lucide-react';
import { useRepoStore } from '../../store/useRepoStore';
import { api } from '../../api/client';
import { ExplainResponse } from '../../types';
import { getLayerColor, TYPE_BADGES } from '../../utils/theme';

export const InspectorPanel: React.FC = () => {
  const {
    selectedNodeId,
    selectedNodeDetail,
    selectNode,
    activeAnalysisId,
    aiStatus,
    runTrace,
    traceResult,
    clearTrace,
    runImpact,
    impactResult,
    clearImpact,
  } = useRepoStore();

  const [activeTab, setActiveTab] = useState<'source' | 'deps' | 'gemma' | 'trace' | 'impact'>('source');
  const [copied, setCopied] = useState(false);

  // Gemma Explain State
  const [question, setQuestion] = useState('Explain the architectural role of this component, its relationships, and data flow.');
  const [explainLoading, setExplainLoading] = useState(false);
  const [explainResult, setExplainResult] = useState<ExplainResponse | null>(null);

  // Trace Target Input State
  const [targetNodeInput, setTargetNodeInput] = useState('');
  const [traceLoading, setTraceLoading] = useState(false);

  // Impact Loading State
  const [impactLoading, setImpactLoading] = useState(false);

  if (!selectedNodeDetail || !selectedNodeId) {
    return (
      <aside className="w-96 h-full border-l border-space-800 bg-space-900/60 backdrop-blur flex flex-col items-center justify-center p-6 text-center text-slate-500 z-10 select-none">
        <div className="w-12 h-12 rounded-xl bg-space-850 border border-space-800 flex items-center justify-center mb-3">
          <Code2 className="w-6 h-6 text-slate-500" />
        </div>
        <p className="text-sm font-medium text-slate-300 mb-1">Source Inspector</p>
        <p className="text-xs text-slate-400 max-w-[220px]">
          Click any node in the 3D or 2D view to inspect its source code, dependencies, and Gemma explanations.
        </p>
      </aside>
    );
  }

  const { node, source_code, github_url, incoming_edges, outgoing_edges } = selectedNodeDetail;
  const layerColor = getLayerColor(node.layer);
  const typeBadge = TYPE_BADGES[node.type] || { label: node.type, color: 'bg-slate-800 text-slate-300' };

  const handleCopyCode = () => {
    if (source_code) {
      navigator.clipboard.writeText(source_code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleExplain = async () => {
    if (!activeAnalysisId) return;
    setExplainLoading(true);
    setExplainResult(null);
    try {
      const res = await api.explainNode(activeAnalysisId, node.id, question);
      setExplainResult(res);
    } catch (err: any) {
      console.error('Explain error:', err);
    } finally {
      setExplainLoading(false);
    }
  };

  const handleRunTrace = async () => {
    setTraceLoading(true);
    await runTrace(node.id, targetNodeInput.trim() || undefined);
    setTraceLoading(false);
  };

  const handleRunImpact = async () => {
    setImpactLoading(true);
    await runImpact(node.id);
    setImpactLoading(false);
  };

  return (
    <aside className="w-[420px] h-full border-l border-space-800 bg-space-900/80 backdrop-blur flex flex-col z-10 shadow-2xl overflow-hidden select-none">
      {/* Inspector Header */}
      <div className="p-4 border-b border-space-800 bg-space-950/40">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded border ${typeBadge.color}`}>
              {typeBadge.label}
            </span>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${layerColor.bg} ${layerColor.text} ${layerColor.border}`}>
              {node.layer.replace('_', ' ')}
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-950/40 border border-emerald-800/40 text-emerald-400 flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" />
              {node.evidence_status}
            </span>
          </div>

          <button
            onClick={() => selectNode(null)}
            className="text-slate-400 hover:text-slate-100 p-1 rounded hover:bg-space-800"
            title="Close Inspector"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <h3 className="font-mono text-base font-bold text-slate-100 truncate mb-1" title={node.label}>
          {node.label}
        </h3>

        <div className="flex items-center justify-between text-xs font-mono text-slate-400">
          <span className="truncate max-w-[260px]" title={node.file_path}>
            {node.file_path}:{node.start_line || 1}
          </span>
          {github_url && (
            <a
              href={github_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 text-brand-400 hover:text-brand-300 transition text-[11px]"
            >
              <span>GitHub</span>
              <ExternalLink className="w-3 h-3" />
            </a>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-space-800 bg-space-950 text-xs font-medium">
        <button
          onClick={() => setActiveTab('source')}
          className={`flex-1 py-2 text-center transition border-b-2 ${
            activeTab === 'source'
              ? 'border-brand-500 text-brand-300 bg-brand-500/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Source
        </button>
        <button
          onClick={() => setActiveTab('deps')}
          className={`flex-1 py-2 text-center transition border-b-2 ${
            activeTab === 'deps'
              ? 'border-brand-500 text-brand-300 bg-brand-500/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Dependencies
        </button>
        <button
          onClick={() => setActiveTab('gemma')}
          className={`flex-1 py-2 text-center transition border-b-2 flex items-center justify-center gap-1 ${
            activeTab === 'gemma'
              ? 'border-brand-500 text-brand-300 bg-brand-500/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
          <span>Gemma 4</span>
        </button>
        <button
          onClick={() => setActiveTab('trace')}
          className={`flex-1 py-2 text-center transition border-b-2 ${
            activeTab === 'trace'
              ? 'border-brand-500 text-brand-300 bg-brand-500/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Trace
        </button>
        <button
          onClick={() => setActiveTab('impact')}
          className={`flex-1 py-2 text-center transition border-b-2 ${
            activeTab === 'impact'
              ? 'border-brand-500 text-brand-300 bg-brand-500/5'
              : 'border-transparent text-slate-400 hover:text-slate-200'
          }`}
        >
          Impact
        </button>
      </div>

      {/* Tab Panels */}
      <div className="flex-1 overflow-y-auto p-4 text-xs">
        {/* 1. Source Code Tab */}
        {activeTab === 'source' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-slate-400">
              <span className="font-mono text-[11px]">
                Lines {node.start_line || 1}–{node.end_line || (node.start_line || 1) + 20}
              </span>
              <button
                onClick={handleCopyCode}
                className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-slate-200 bg-space-850 px-2 py-0.5 rounded border border-space-800 transition"
              >
                {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                <span>{copied ? 'Copied' : 'Copy'}</span>
              </button>
            </div>

            {source_code ? (
              <div className="bg-space-950 rounded-lg p-3 font-mono text-[11px] leading-relaxed border border-space-800 overflow-x-auto text-slate-300 select-text">
                <pre>{source_code}</pre>
              </div>
            ) : (
              <div className="p-6 text-center text-slate-500 bg-space-950 rounded-lg border border-space-800">
                Source snippet not available for this node.
              </div>
            )}
          </div>
        )}

        {/* 2. Dependencies Tab */}
        {activeTab === 'deps' && (
          <div className="space-y-4">
            {/* Outgoing */}
            <div>
              <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                <ArrowRight className="w-3 h-3 text-cyan-400" />
                Outgoing Relationships ({outgoing_edges.length})
              </div>
              {outgoing_edges.length === 0 ? (
                <div className="p-3 text-center text-slate-500 bg-space-950 rounded-lg border border-space-800">
                  No outgoing dependencies detected.
                </div>
              ) : (
                <div className="space-y-1.5">
                  {outgoing_edges.map((edge) => (
                    <div
                      key={edge.id}
                      onClick={() => selectNode(edge.target)}
                      className="p-2 rounded-lg bg-space-950 border border-space-800 hover:border-brand-500/50 cursor-pointer transition flex items-center justify-between font-mono"
                    >
                      <div className="truncate">
                        <span className="text-[10px] text-cyan-400 px-1 py-0.2 rounded bg-cyan-950/40 mr-2">
                          {edge.type}
                        </span>
                        <span className="text-slate-200">{edge.target.split('::').pop()}</span>
                      </div>
                      <span className="text-[10px] text-slate-500">{edge.evidence_status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Incoming */}
            <div>
              <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                <ArrowLeft className="w-3 h-3 text-emerald-400" />
                Incoming References ({incoming_edges.length})
              </div>
              {incoming_edges.length === 0 ? (
                <div className="p-3 text-center text-slate-500 bg-space-950 rounded-lg border border-space-800">
                  No incoming references detected.
                </div>
              ) : (
                <div className="space-y-1.5">
                  {incoming_edges.map((edge) => (
                    <div
                      key={edge.id}
                      onClick={() => selectNode(edge.source)}
                      className="p-2 rounded-lg bg-space-950 border border-space-800 hover:border-brand-500/50 cursor-pointer transition flex items-center justify-between font-mono"
                    >
                      <div className="truncate">
                        <span className="text-[10px] text-emerald-400 px-1 py-0.2 rounded bg-emerald-950/40 mr-2">
                          {edge.type}
                        </span>
                        <span className="text-slate-200">{edge.source.split('::').pop()}</span>
                      </div>
                      <span className="text-[10px] text-slate-500">{edge.evidence_status}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 3. Gemma 4 Tab */}
        {activeTab === 'gemma' && (
          <div className="space-y-4">
            <div>
              <label className="text-[10px] uppercase font-mono text-slate-400 block mb-1.5">
                Architecture Question
              </label>
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                rows={2}
                className="w-full bg-space-950 text-xs text-slate-100 rounded-lg p-2.5 border border-space-800 focus:outline-none focus:border-brand-500 font-mono transition"
                placeholder="Ask Gemma about this component..."
              />

              <div className="flex flex-wrap gap-1 mt-1.5">
                {[
                  'Explain architectural role',
                  'What happens when called?',
                  'How does this connect to DB?',
                ].map((prompt) => (
                  <button
                    key={prompt}
                    onClick={() => setQuestion(prompt)}
                    className="text-[10px] font-mono px-2 py-0.5 rounded bg-space-850 hover:bg-space-800 text-slate-400 hover:text-slate-200 border border-space-800 transition"
                  >
                    {prompt}
                  </button>
                ))}
              </div>

              <button
                onClick={handleExplain}
                disabled={explainLoading}
                className="mt-3 w-full py-2 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white font-medium rounded-lg flex items-center justify-center gap-2 shadow-lg shadow-brand-500/10 transition disabled:opacity-50"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>{explainLoading ? 'Gemma is analyzing evidence...' : 'Explain with Gemma 4'}</span>
              </button>
            </div>

            {explainResult && (
              <div className="space-y-3 pt-2">
                {/* Findings */}
                {explainResult.verified_findings.length > 0 && (
                  <div className="p-3 bg-emerald-950/20 border border-emerald-800/40 rounded-lg">
                    <div className="text-[10px] uppercase font-mono tracking-wider text-emerald-400 font-bold mb-1.5 flex items-center gap-1.5">
                      <ShieldCheck className="w-3 h-3" />
                      Confirmed Findings
                    </div>
                    <ul className="list-disc pl-4 space-y-1 text-slate-300 leading-relaxed font-sans">
                      {explainResult.verified_findings.map((f, i) => (
                        <li key={i}>{f}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Hypotheses */}
                {explainResult.inferred_hypotheses.length > 0 && (
                  <div className="p-3 bg-cyan-950/20 border border-cyan-800/40 rounded-lg">
                    <div className="text-[10px] uppercase font-mono tracking-wider text-cyan-400 font-bold mb-1.5">
                      Inferred Hypotheses
                    </div>
                    <ul className="list-disc pl-4 space-y-1 text-slate-300 leading-relaxed font-sans">
                      {explainResult.inferred_hypotheses.map((h, i) => (
                        <li key={i}>{h}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Full narrative */}
                <div className="p-3 bg-space-950 border border-space-800 rounded-lg leading-relaxed text-slate-300 select-text whitespace-pre-wrap font-sans">
                  {explainResult.explanation}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 4. Feature Trace Tab */}
        {activeTab === 'trace' && (
          <div className="space-y-4">
            <div>
              <div className="text-[10px] uppercase font-mono text-slate-400 mb-1">Origin Node</div>
              <div className="p-2 bg-space-950 rounded border border-space-800 font-mono text-slate-200">
                {node.label} ({node.type})
              </div>
            </div>

            <div>
              <label className="text-[10px] uppercase font-mono text-slate-400 block mb-1">
                Target Node (Optional - Leave blank to trace downstream flow)
              </label>
              <input
                type="text"
                value={targetNodeInput}
                onChange={(e) => setTargetNodeInput(e.target.value)}
                placeholder="e.g. ModelD, checkout_cart, OrderService..."
                className="w-full bg-space-950 text-xs text-slate-100 rounded-lg p-2 border border-space-800 focus:outline-none focus:border-brand-500 font-mono"
              />
            </div>

            <div className="flex gap-2">
              <button
                onClick={handleRunTrace}
                disabled={traceLoading}
                className="flex-1 py-2 bg-brand-600 hover:bg-brand-500 text-white rounded-lg font-medium flex items-center justify-center gap-1.5 transition disabled:opacity-50"
              >
                <Play className="w-3.5 h-3.5" />
                <span>{traceLoading ? 'Tracing...' : 'Run Path Trace'}</span>
              </button>
              {traceResult && (
                <button
                  onClick={clearTrace}
                  className="px-3 py-2 bg-space-850 hover:bg-space-800 border border-space-800 rounded-lg text-slate-400 hover:text-slate-200"
                  title="Clear trace"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {traceResult && (
              <div className="space-y-2 pt-2">
                <div className="text-[10px] uppercase font-mono text-cyan-400 font-bold">
                  {traceResult.path_found ? `Path Discovered (${traceResult.path_nodes.length} nodes)` : 'No Path Found'}
                </div>

                <div className="space-y-1">
                  {traceResult.step_descriptions.map((step, idx) => (
                    <div key={idx} className="p-2 rounded bg-space-950 border border-space-800 font-mono text-[11px] text-slate-300">
                      {step}
                    </div>
                  ))}
                </div>

                {traceResult.explanation && (
                  <div className="p-3 bg-brand-950/20 border border-brand-800/40 rounded-lg text-slate-300 leading-relaxed font-sans whitespace-pre-wrap">
                    {traceResult.explanation}
                  </div>
                )}

                <div className="text-[10px] text-slate-500 italic mt-2">
                  {traceResult.disclaimer}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 5. Impact Tab */}
        {activeTab === 'impact' && (
          <div className="space-y-4">
            <div>
              <p className="text-slate-400 mb-3">
                Analyze direct and transitive components that statically depend on <strong className="text-slate-200">{node.label}</strong>.
              </p>
              <button
                onClick={handleRunImpact}
                disabled={impactLoading}
                className="w-full py-2 bg-amber-600 hover:bg-amber-500 text-white rounded-lg font-medium flex items-center justify-center gap-1.5 transition disabled:opacity-50 shadow-lg shadow-amber-500/10"
              >
                <AlertTriangle className="w-3.5 h-3.5" />
                <span>{impactLoading ? 'Traversing dependencies...' : 'Analyze Change Impact'}</span>
              </button>
            </div>

            {impactResult && (
              <div className="space-y-3 pt-2">
                <div className="grid grid-cols-2 gap-2 text-center">
                  <div className="p-2.5 rounded bg-space-950 border border-space-800">
                    <div className="text-base font-bold text-amber-400 font-mono">{impactResult.direct_dependents.length}</div>
                    <div className="text-[10px] text-slate-400 uppercase font-mono">Direct Dependents</div>
                  </div>
                  <div className="p-2.5 rounded bg-space-950 border border-space-800">
                    <div className="text-base font-bold text-rose-400 font-mono">{impactResult.transitive_dependents.length}</div>
                    <div className="text-[10px] text-slate-400 uppercase font-mono">Transitive</div>
                  </div>
                </div>

                {impactResult.affected_routes.length > 0 && (
                  <div className="p-2.5 rounded bg-emerald-950/20 border border-emerald-800/40">
                    <div className="text-[10px] uppercase font-mono text-emerald-400 font-bold mb-1">
                      Affected Routes ({impactResult.affected_routes.length})
                    </div>
                    <div className="text-[11px] font-mono text-slate-300">
                      {impactResult.affected_routes.map((r) => r.label).join(', ')}
                    </div>
                  </div>
                )}

                {impactResult.gemma_explanation && (
                  <div className="p-3 bg-space-950 border border-space-800 rounded-lg text-slate-300 leading-relaxed font-sans whitespace-pre-wrap">
                    {impactResult.gemma_explanation}
                  </div>
                )}

                <div className="text-[10px] text-slate-500 italic">
                  {impactResult.disclaimer}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </aside>
  );
};
