import React, { useState } from 'react';
import {
  GitCompare,
  Plus,
  Minus,
  Edit2,
  AlertTriangle,
  Play,
  RotateCcw,
  CheckCircle,
  FileCode,
  Layers,
  ArrowRight,
  ShieldAlert,
} from 'lucide-react';
import { useRepoStore } from '../../store/useRepoStore';

export const RevisionCompareView: React.FC = () => {
  const {
    comparisonResult,
    isComparing,
    runComparison,
    selectNode,
    activeAnalysisId,
  } = useRepoStore();

  const [targetBranchInput, setTargetBranchInput] = useState('v2');
  const [activeTab, setActiveTab] = useState<'overview' | 'files' | 'symbols' | 'impact'>('overview');

  const handleRunCompare = async () => {
    await runComparison({
      base_ref: 'main',
      target_ref: targetBranchInput.trim() || 'v2',
      target_repository_url: 'https://github.com/repograph-demo/ecommerce-platform-v2',
    });
  };

  return (
    <div className="w-full h-full flex flex-col bg-space-950 text-slate-100 overflow-y-auto p-6">
      {/* Header and Controls */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-space-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <GitCompare className="w-5 h-5 text-indigo-400" />
            <h2 className="text-lg font-bold text-slate-100">Git Branch & Revision Comparison</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Compare two repository revisions to detect added, modified, deleted components, and map architectural impact.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 bg-space-900 border border-space-800 rounded-lg p-1.5 text-xs font-mono">
            <span className="text-slate-400 px-1.5">base: main</span>
            <span className="text-slate-600">⇄</span>
            <input
              type="text"
              value={targetBranchInput}
              onChange={(e) => setTargetBranchInput(e.target.value)}
              placeholder="target ref (e.g. v2)"
              className="bg-space-950 px-2 py-0.5 rounded border border-space-800 text-slate-200 focus:outline-none focus:border-indigo-500 w-28 text-center"
            />
          </div>

          <button
            onClick={handleRunCompare}
            disabled={isComparing}
            className="px-4 py-2 bg-gradient-to-r from-indigo-600 to-brand-600 hover:from-indigo-500 hover:to-brand-500 text-white rounded-lg text-xs font-medium transition flex items-center gap-2 shadow-lg shadow-indigo-500/10 disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5" />
            <span>{isComparing ? 'Comparing Revisions...' : 'Run Revision Comparison'}</span>
          </button>
        </div>
      </div>

      {!comparisonResult ? (
        <div className="flex-1 flex flex-col items-center justify-center p-12 text-center text-slate-500">
          <div className="w-16 h-16 rounded-2xl bg-space-900 border border-space-800 flex items-center justify-center mb-4 text-indigo-400 shadow-xl">
            <GitCompare className="w-8 h-8" />
          </div>
          <h3 className="text-base font-semibold text-slate-200 mb-2">No Comparison Run Yet</h3>
          <p className="text-xs text-slate-400 max-w-md leading-relaxed mb-4">
            Click <strong>"Run Revision Comparison"</strong> to compare the current repository baseline against the target revision (e.g. v2 feature branch).
          </p>
          <button
            onClick={handleRunCompare}
            disabled={isComparing}
            className="px-4 py-2 bg-space-900 hover:bg-space-850 border border-space-800 text-slate-200 rounded-lg text-xs font-mono transition"
          >
            Compare against built-in v2 sample revision
          </button>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Summary Stat Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-800/40">
              <div className="flex items-center justify-between text-emerald-400 mb-1">
                <span className="text-[10px] font-mono uppercase font-bold">Added Symbols</span>
                <Plus className="w-4 h-4" />
              </div>
              <div className="text-2xl font-bold font-mono text-emerald-300">
                +{comparisonResult.summary.added_count}
              </div>
              <span className="text-[10px] text-slate-400 font-mono">new components</span>
            </div>

            <div className="p-4 rounded-xl bg-amber-950/20 border border-amber-800/40">
              <div className="flex items-center justify-between text-amber-400 mb-1">
                <span className="text-[10px] font-mono uppercase font-bold">Modified Symbols</span>
                <Edit2 className="w-4 h-4" />
              </div>
              <div className="text-2xl font-bold font-mono text-amber-300">
                ~{comparisonResult.summary.modified_count}
              </div>
              <span className="text-[10px] text-slate-400 font-mono">changed definitions</span>
            </div>

            <div className="p-4 rounded-xl bg-rose-950/20 border border-rose-800/40">
              <div className="flex items-center justify-between text-rose-400 mb-1">
                <span className="text-[10px] font-mono uppercase font-bold">Removed Symbols</span>
                <Minus className="w-4 h-4" />
              </div>
              <div className="text-2xl font-bold font-mono text-rose-300">
                -{comparisonResult.summary.removed_count}
              </div>
              <span className="text-[10px] text-slate-400 font-mono">deleted code</span>
            </div>

            <div className="p-4 rounded-xl bg-cyan-950/20 border border-cyan-800/40">
              <div className="flex items-center justify-between text-cyan-400 mb-1">
                <span className="text-[10px] font-mono uppercase font-bold">Impacted Nodes</span>
                <ShieldAlert className="w-4 h-4" />
              </div>
              <div className="text-2xl font-bold font-mono text-cyan-300">
                {comparisonResult.summary.impacted_count}
              </div>
              <span className="text-[10px] text-slate-400 font-mono">downstream risk</span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex items-center gap-2 border-b border-space-800 pb-2">
            {[
              { id: 'overview', label: 'Diff Overlay Graph' },
              { id: 'files', label: `Changed Files (${comparisonResult.summary.changed_files_count})` },
              { id: 'symbols', label: `Architectural Changes (${comparisonResult.summary.added_count + comparisonResult.summary.modified_count})` },
              { id: 'impact', label: `Impacted Dependents (${comparisonResult.summary.impacted_count})` },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono transition ${
                  activeTab === tab.id
                    ? 'bg-space-850 text-indigo-400 font-bold border border-space-800'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-space-900'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab 1: Diff Overlay Graph Visualizer */}
          {activeTab === 'overview' && (
            <div className="p-4 rounded-xl bg-space-900/60 border border-space-800 space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-mono uppercase font-bold text-slate-300">
                  Semantic Graph Diff Overlay
                </span>
                <div className="flex items-center gap-3 text-[10px] font-mono">
                  <span className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
                    Added
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
                    Modified
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-rose-400" />
                    Removed
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
                    Impacted
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3 max-h-[460px] overflow-y-auto p-1">
                {comparisonResult.overlay_graph.nodes.map((node: any) => {
                  let badgeBg = 'bg-space-950 border-space-800 text-slate-400';
                  if (node.diff_status === 'added') {
                    badgeBg = 'bg-emerald-950/40 border-emerald-500/80 text-emerald-300 shadow-md shadow-emerald-500/10';
                  } else if (node.diff_status === 'modified') {
                    badgeBg = 'bg-amber-950/40 border-amber-500/80 text-amber-300 shadow-md shadow-amber-500/10';
                  } else if (node.diff_status === 'impacted') {
                    badgeBg = 'bg-cyan-950/40 border-cyan-500/80 text-cyan-300 shadow-md shadow-cyan-500/10';
                  }

                  return (
                    <div
                      key={node.id}
                      onClick={() => selectNode(node.id)}
                      className={`p-3 rounded-lg border cursor-pointer transition flex flex-col justify-between ${badgeBg}`}
                    >
                      <div>
                        <div className="flex items-center justify-between gap-2 mb-1">
                          <span className="font-mono text-xs font-bold truncate">{node.label}</span>
                          <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-space-850/80">
                            {node.diff_status}
                          </span>
                        </div>
                        <p className="text-[11px] font-mono text-slate-400 truncate">{node.file_path}</p>
                      </div>
                      <span className="text-[10px] font-mono text-slate-500 mt-2 capitalize">{node.layer}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Tab 2: Changed Files */}
          {activeTab === 'files' && (
            <div className="p-4 rounded-xl bg-space-900/60 border border-space-800 space-y-3 font-mono text-xs">
              {comparisonResult.files.added.map((f) => (
                <div key={f} className="flex items-center gap-2 text-emerald-400 p-2 rounded bg-space-950 border border-emerald-800/30">
                  <Plus className="w-3.5 h-3.5" />
                  <span>{f}</span>
                  <span className="text-[10px] ml-auto uppercase bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/40">added</span>
                </div>
              ))}
              {comparisonResult.files.modified.map((f) => (
                <div key={f} className="flex items-center gap-2 text-amber-400 p-2 rounded bg-space-950 border border-amber-800/30">
                  <Edit2 className="w-3.5 h-3.5" />
                  <span>{f}</span>
                  <span className="text-[10px] ml-auto uppercase bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-800/40">modified</span>
                </div>
              ))}
              {comparisonResult.files.deleted.map((f) => (
                <div key={f} className="flex items-center gap-2 text-rose-400 p-2 rounded bg-space-950 border border-rose-800/30">
                  <Minus className="w-3.5 h-3.5" />
                  <span>{f}</span>
                  <span className="text-[10px] ml-auto uppercase bg-rose-950/60 px-1.5 py-0.5 rounded border border-rose-800/40">deleted</span>
                </div>
              ))}
            </div>
          )}

          {/* Tab 3: Architectural Changes */}
          {activeTab === 'symbols' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Changed Routes & Schemas */}
              <div className="p-4 rounded-xl bg-space-900/60 border border-space-800 space-y-2">
                <span className="text-xs font-mono uppercase font-bold text-slate-300 block mb-2">
                  API Routes & Database Schema Changes
                </span>
                {comparisonResult.changes.changed_routes.map((r: any) => (
                  <div key={r.id} className="p-2 rounded bg-space-950 border border-space-800 text-xs font-mono flex items-center justify-between">
                    <span className="text-indigo-300 font-semibold">{r.label} ({r.type})</span>
                    <span className="text-[10px] uppercase text-emerald-400">{r.change_type}</span>
                  </div>
                ))}
                {comparisonResult.changes.changed_schemas.map((s: any) => (
                  <div key={s.id} className="p-2 rounded bg-space-950 border border-space-800 text-xs font-mono flex items-center justify-between">
                    <span className="text-rose-300 font-semibold">{s.label} (table)</span>
                    <span className="text-[10px] uppercase text-emerald-400">{s.change_type}</span>
                  </div>
                ))}
              </div>

              {/* Changed Tests */}
              <div className="p-4 rounded-xl bg-space-900/60 border border-space-800 space-y-2">
                <span className="text-xs font-mono uppercase font-bold text-slate-300 block mb-2">
                  Test Coverage Impact
                </span>
                {comparisonResult.changes.changed_tests.map((t: any) => (
                  <div key={t.id} className="p-2 rounded bg-space-950 border border-space-800 text-xs font-mono flex items-center justify-between">
                    <span className="text-amber-300 font-semibold">{t.label} (test)</span>
                    <span className="text-[10px] uppercase text-emerald-400">{t.change_type}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 4: Impacted Dependents */}
          {activeTab === 'impact' && (
            <div className="p-4 rounded-xl bg-space-900/60 border border-space-800 space-y-3">
              <span className="text-xs font-mono uppercase font-bold text-cyan-400 block mb-1">
                Downstream Components Potentially Impacted ({comparisonResult.changes.impacted_node_ids.length})
              </span>
              <p className="text-xs text-slate-400 mb-3">
                Identified through reverse-dependency analysis on the changed symbols:
              </p>
              <div className="flex flex-wrap gap-2">
                {comparisonResult.changes.impacted_node_ids.map((id: string) => (
                  <button
                    key={id}
                    onClick={() => selectNode(id)}
                    className="p-2 rounded bg-space-950 border border-cyan-800/40 text-cyan-300 font-mono text-xs hover:border-cyan-500 transition"
                  >
                    {id.split('::').pop()}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
