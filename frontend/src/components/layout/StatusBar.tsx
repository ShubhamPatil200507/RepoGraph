import React from 'react';
import { FileCode2, Share2, Layers, AlertTriangle, ShieldCheck } from 'lucide-react';
import { useRepoStore } from '../../store/useRepoStore';

export const StatusBar: React.FC = () => {
  const { graph } = useRepoStore();

  if (!graph) return null;

  const { summary } = graph;

  return (
    <footer className="h-7 border-t border-space-800 bg-space-950 px-4 flex items-center justify-between text-[11px] font-mono text-slate-400 select-none z-20">
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-1.5">
          <FileCode2 className="w-3.5 h-3.5 text-slate-500" />
          <span>{summary.total_files} files</span>
        </span>

        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
          <span>{summary.total_nodes} symbols</span>
        </span>

        <span className="flex items-center gap-1.5">
          <Share2 className="w-3.5 h-3.5 text-slate-500" />
          <span>{summary.total_edges} connections</span>
        </span>

        {/* Languages */}
        <div className="hidden md:flex items-center gap-2 pl-2 border-l border-space-800 text-[10px]">
          {Object.entries(summary.languages).map(([lang, count]) => (
            <span key={lang} className="text-slate-500">
              {lang}: <strong className="text-slate-300 font-normal">{count}</strong>
            </span>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-3">
        {summary.warnings.length > 0 && (
          <span className="flex items-center gap-1 text-amber-400 text-[10px]" title={summary.warnings.join('; ')}>
            <AlertTriangle className="w-3 h-3" />
            <span>{summary.warnings.length} parse warnings</span>
          </span>
        )}

        <span className="text-[10px] text-slate-500">
          Deterministic AST • Seeded Layout
        </span>
      </div>
    </footer>
  );
};
