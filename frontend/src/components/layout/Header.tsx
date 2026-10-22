import React, { useState } from 'react';
import {
  Box,
  Layers,
  Database,
  GitBranch,
  GitCompare,
  Route,
  RotateCcw,
  Download,
  Share2,
} from 'lucide-react';
import { useRepoStore } from '../../store/useRepoStore';
import { api } from '../../api/client';

export const Header: React.FC = () => {
  const {
    activeView,
    setView,
    analysisStatus,
    aiStatus,
    resetAll,
    graph,
    activeAnalysisId,
  } = useRepoStore();

  const [downloadingGraphify, setDownloadingGraphify] = useState(false);
  const repo = analysisStatus?.repository;

  const handleExportGraphify = async () => {
    if (!activeAnalysisId) return;
    setDownloadingGraphify(true);
    try {
      const graphData = await api.getGraphifyExport(activeAnalysisId);
      const blob = new Blob([JSON.stringify(graphData, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `graphify-export-${repo?.repo || 'codebase'}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export Graphify JSON:', err);
    } finally {
      setDownloadingGraphify(false);
    }
  };

  return (
    <header className="h-14 border-b border-space-800 bg-space-900/90 backdrop-blur px-4 flex items-center justify-between z-20 select-none">
      {/* Brand & Wordmark */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-600 via-indigo-600 to-cyan-500 p-0.5 flex items-center justify-center shadow-lg shadow-brand-500/10">
            <div className="w-full h-full bg-space-950 rounded-[7px] flex items-center justify-center">
              <Box className="w-4 h-4 text-cyan-400" />
            </div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-slate-100 text-base tracking-tight">RepoGraph</span>
              <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-brand-500/10 border border-brand-500/20 text-brand-300">
                MVP
              </span>
            </div>
          </div>
        </div>

        {repo && (
          <div className="hidden md:flex items-center gap-2 pl-4 border-l border-space-800 text-xs">
            <span className="text-slate-400">repo:</span>
            <span className="font-mono font-medium text-slate-200">
              {repo.owner}/{repo.repo}
            </span>
            {repo.branch && (
              <span className="flex items-center gap-1 text-slate-400 font-mono text-[11px] bg-space-850 px-2 py-0.5 rounded border border-space-800">
                <GitBranch className="w-3 h-3 text-brand-400" />
                {repo.branch}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Center: View Switcher */}
      {graph && (
        <div className="flex items-center bg-space-950 p-1 rounded-lg border border-space-800">
          <button
            onClick={() => setView('3d')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all ${
              activeView === '3d'
                ? 'bg-brand-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-space-850'
            }`}
            title="3D Architecture Universe"
          >
            <Box className="w-3.5 h-3.5" />
            <span>3D Universe</span>
          </button>

          <button
            onClick={() => setView('2d')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all ${
              activeView === '2d'
                ? 'bg-brand-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-space-850'
            }`}
            title="2D Flow Graph"
          >
            <Layers className="w-3.5 h-3.5" />
            <span>2D Graph</span>
          </button>

          <button
            onClick={() => setView('api')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all ${
              activeView === 'api'
                ? 'bg-brand-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-space-850'
            }`}
            title="API Data-Flow Explorer"
          >
            <Route className="w-3.5 h-3.5" />
            <span>API Flow</span>
          </button>

          <button
            onClick={() => setView('er')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all ${
              activeView === 'er'
                ? 'bg-brand-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-space-850'
            }`}
            title="Entity-Relationship Diagram"
          >
            <Database className="w-3.5 h-3.5" />
            <span>ER Diagram</span>
          </button>

          <button
            onClick={() => setView('compare')}
            className={`flex items-center gap-1.5 px-3 py-1 rounded-md text-xs font-medium transition-all ${
              activeView === 'compare'
                ? 'bg-brand-600 text-white shadow-sm'
                : 'text-slate-400 hover:text-slate-200 hover:bg-space-850'
            }`}
            title="Git Revision Comparison"
          >
            <GitCompare className="w-3.5 h-3.5" />
            <span>Revision Diff</span>
          </button>
        </div>
      )}

      {/* Right: AI Model Status, Graphify Export & Actions */}
      <div className="flex items-center gap-2.5">
        {/* Graphify Export & Sponsor Badge */}
        {graph && (
          <button
            onClick={handleExportGraphify}
            disabled={downloadingGraphify}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-mono bg-indigo-950/40 hover:bg-indigo-900/60 border border-indigo-500/30 text-indigo-300 transition"
            title="Export as Graphify Knowledge Graph (graphify-out/graph.json)"
          >
            <Download className="w-3 h-3 text-indigo-400" />
            <span className="hidden lg:inline">{downloadingGraphify ? 'Exporting...' : 'Export Graphify'}</span>
          </button>
        )}

        {/* Gemma Status Pill */}
        <div
          className={`flex items-center gap-2 px-2.5 py-1 rounded-full text-xs border ${
            aiStatus?.available
              ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-300'
              : 'bg-space-850 border-space-800 text-slate-400'
          }`}
          title={aiStatus?.message || 'Hosted Gemma Status'}
        >
          <span
            className={`w-2 h-2 rounded-full ${
              aiStatus?.available ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400'
            }`}
          />
          <span className="font-mono text-[11px]">
            {aiStatus?.configured_model || 'gemma-4-26b-a4b-it'}
          </span>
          <span className="text-[10px] text-slate-400">
            {aiStatus?.available ? 'Ready' : 'No Key'}
          </span>
        </div>

        {graph && (
          <button
            onClick={resetAll}
            className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 bg-space-850 hover:bg-space-800 border border-space-800 px-3 py-1.5 rounded-md transition"
            title="Analyze another repository"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">New Repo</span>
          </button>
        )}
      </div>
    </header>
  );
};
