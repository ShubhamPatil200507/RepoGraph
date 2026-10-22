import React from 'react';
import { Check, Loader2, AlertCircle } from 'lucide-react';
import { useRepoStore } from '../../store/useRepoStore';

export const IngestionProgressModal: React.FC = () => {
  const { isAnalyzing, analysisStatus, analysisError } = useRepoStore();

  if (!isAnalyzing && !analysisError) return null;

  const stages = analysisStatus?.stages || [
    { stage_id: 1, name: 'Validating repository URL', completed: false, current: true },
    { stage_id: 2, name: 'Fetching repository metadata', completed: false, current: false },
    { stage_id: 3, name: 'Downloading source files', completed: false, current: false },
    { stage_id: 4, name: 'Parsing supported files', completed: false, current: false },
    { stage_id: 5, name: 'Building dependency graph', completed: false, current: false },
    { stage_id: 6, name: 'Preparing visualization', completed: false, current: false },
    { stage_id: 7, name: 'Ready to explore', completed: false, current: false },
  ];

  return (
    <div className="fixed inset-0 z-50 bg-space-950/80 backdrop-blur-md flex items-center justify-center p-4 select-none">
      <div className="max-w-md w-full bg-space-900 border border-space-800 rounded-2xl p-6 shadow-2xl space-y-5 animate-in fade-in duration-200">
        <div>
          <h3 className="text-base font-bold text-slate-100">
            {analysisError ? 'Analysis Interrupted' : 'Ingesting Repository'}
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            {analysisError
              ? 'An error occurred during static code extraction.'
              : analysisStatus?.progress_message || 'Initializing static analysis pipeline...'}
          </p>
        </div>

        {/* Stages list */}
        <div className="space-y-2.5">
          {stages.map((stage) => {
            const isCompleted = stage.completed;
            const isCurrent = stage.current && !analysisError;

            return (
              <div
                key={stage.stage_id}
                className={`flex items-center gap-3 p-2.5 rounded-lg border text-xs font-mono transition ${
                  isCompleted
                    ? 'bg-space-950 border-space-800 text-slate-300'
                    : isCurrent
                    ? 'bg-brand-950/40 border-brand-500/40 text-brand-300 font-semibold'
                    : 'bg-space-950/40 border-space-850/40 text-slate-500'
                }`}
              >
                <div className="w-5 h-5 rounded-full flex items-center justify-center shrink-0">
                  {isCompleted ? (
                    <div className="w-4 h-4 rounded-full bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center">
                      <Check className="w-3 h-3 text-emerald-400" />
                    </div>
                  ) : isCurrent ? (
                    <Loader2 className="w-4 h-4 text-brand-400 animate-spin" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-space-800 flex items-center justify-center text-[10px] text-slate-500">
                      {stage.stage_id}
                    </div>
                  )}
                </div>

                <span>{stage.name}</span>
              </div>
            );
          })}
        </div>

        {analysisError && (
          <div className="p-3 bg-rose-950/40 border border-rose-800/50 rounded-lg text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
            <span>{analysisError}</span>
          </div>
        )}
      </div>
    </div>
  );
};
