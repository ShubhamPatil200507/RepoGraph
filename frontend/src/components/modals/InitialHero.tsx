import React, { useState } from 'react';
import {
  Box,
  ArrowRight,
  GitBranch,
  Sparkles,
  Layers,
  Database,
  ShieldCheck,
  AlertCircle,
} from 'lucide-react';
import { useRepoStore } from '../../store/useRepoStore';

const SAMPLE_REPOSITORIES = [
  {
    name: 'E-Commerce Platform Demo',
    url: 'https://github.com/repograph-demo/ecommerce-platform',
    desc: 'FastAPI routing, SQLAlchemy relational models, inventory services & React components',
    tags: ['Python', 'FastAPI', 'React', 'SQLAlchemy'],
  },
  {
    name: 'FastAPI Core Framework',
    url: 'https://github.com/tiangolo/fastapi',
    desc: 'High performance web framework for building APIs with Python',
    tags: ['Python', 'Starlette', 'Pydantic'],
  },
  {
    name: 'Flask Web Framework',
    url: 'https://github.com/pallets/flask',
    desc: 'Python micro-framework for web application architecture',
    tags: ['Python', 'Werkzeug', 'Jinja'],
  },
];

export const InitialHero: React.FC = () => {
  const { startAnalysis, isAnalyzing, analysisError } = useRepoStore();
  const [repoUrl, setRepoUrl] = useState('');
  const [branch, setBranch] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    startAnalysis(repoUrl.trim(), branch.trim() || undefined);
  };

  const handleSelectSample = (sampleUrl: string) => {
    setRepoUrl(sampleUrl);
    startAnalysis(sampleUrl);
  };

  return (
    <div className="w-full h-full flex flex-col items-center justify-center p-6 overflow-y-auto bg-space-950">
      <div className="max-w-2xl w-full text-center space-y-6 my-auto">
        {/* Brand Wordmark & Tagline */}
        <div className="flex flex-col items-center">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-brand-600 via-indigo-600 to-cyan-500 p-0.5 flex items-center justify-center shadow-2xl shadow-brand-500/20 mb-4">
            <div className="w-full h-full bg-space-950 rounded-[14px] flex items-center justify-center">
              <Box className="w-7 h-7 text-cyan-400" />
            </div>
          </div>

          <h1 className="text-3xl sm:text-4xl font-extrabold text-slate-100 tracking-tight">
            RepoGraph
          </h1>
          <p className="text-base sm:text-lg text-brand-300 font-medium mt-1">
            See how your code works. Explore how everything connects.
          </p>

          <p className="text-xs sm:text-sm text-slate-400 max-w-lg mt-3 leading-relaxed">
            Transform GitHub repositories into source-backed, three-dimensional maps of modules,
            entities, dependencies, and execution paths. Inspect real code relationships and use
            hosted Gemma 4 to explain complex architecture.
          </p>
        </div>

        {/* URL Input Form */}
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="flex flex-col sm:flex-row gap-2 bg-space-900/90 backdrop-blur p-2 rounded-xl border border-space-800 shadow-2xl">
            <div className="flex-1 flex items-center px-3 bg-space-950 rounded-lg border border-space-800/80">
              <input
                type="text"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repository"
                className="w-full bg-transparent py-2.5 text-xs sm:text-sm text-slate-100 placeholder-slate-500 font-mono focus:outline-none"
                disabled={isAnalyzing}
              />
            </div>

            <div className="w-full sm:w-32 flex items-center px-3 bg-space-950 rounded-lg border border-space-800/80">
              <GitBranch className="w-3.5 h-3.5 text-slate-500 mr-2 shrink-0" />
              <input
                type="text"
                value={branch}
                onChange={(e) => setBranch(e.target.value)}
                placeholder="branch"
                className="w-full bg-transparent py-2.5 text-xs text-slate-100 placeholder-slate-500 font-mono focus:outline-none"
                disabled={isAnalyzing}
              />
            </div>

            <button
              type="submit"
              disabled={isAnalyzing || !repoUrl.trim()}
              className="py-2.5 px-5 bg-gradient-to-r from-brand-600 to-indigo-600 hover:from-brand-500 hover:to-indigo-500 text-white text-xs sm:text-sm font-semibold rounded-lg flex items-center justify-center gap-2 shadow-lg shadow-brand-500/20 transition disabled:opacity-50 shrink-0"
            >
              <span>Analyze Repository</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

          {analysisError && (
            <div className="p-3 rounded-lg bg-rose-950/40 border border-rose-800/50 text-rose-300 text-xs flex items-center gap-2 text-left">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{analysisError}</span>
            </div>
          )}
        </form>

        {/* Feature Highlights */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-left">
          <div className="p-3.5 rounded-xl bg-space-900/60 border border-space-800">
            <div className="w-7 h-7 rounded-lg bg-cyan-950/60 border border-cyan-800/40 flex items-center justify-center mb-2">
              <Box className="w-4 h-4 text-cyan-400" />
            </div>
            <h4 className="text-xs font-semibold text-slate-200">3D Architecture Universe</h4>
            <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
              Explore navigable, deterministic 3D clusters grouped by architectural layer.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-space-900/60 border border-space-800">
            <div className="w-7 h-7 rounded-lg bg-indigo-950/60 border border-indigo-800/40 flex items-center justify-center mb-2">
              <Sparkles className="w-4 h-4 text-indigo-400" />
            </div>
            <h4 className="text-xs font-semibold text-slate-200">Gemma 4 Intelligence</h4>
            <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
              Grounded architectural explanations strictly backed by verified code snippets.
            </p>
          </div>

          <div className="p-3.5 rounded-xl bg-space-900/60 border border-space-800">
            <div className="w-7 h-7 rounded-lg bg-emerald-950/60 border border-emerald-800/40 flex items-center justify-center mb-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" />
            </div>
            <h4 className="text-xs font-semibold text-slate-200">Source-Backed Analysis</h4>
            <p className="text-[11px] text-slate-400 mt-1 leading-relaxed">
              Deterministic AST parsers discover relationships without relying on LLM guesses.
            </p>
          </div>
        </div>

        {/* Quick Sample Repositories */}
        <div className="text-left pt-2">
          <div className="text-xs font-mono uppercase tracking-wider text-slate-400 mb-2">
            Try an Instant Sample Repository
          </div>
          <div className="space-y-2">
            {SAMPLE_REPOSITORIES.map((sample) => (
              <div
                key={sample.name}
                onClick={() => handleSelectSample(sample.url)}
                className="p-3 rounded-lg bg-space-900/40 border border-space-800 hover:border-brand-500/50 hover:bg-space-900/80 cursor-pointer transition flex items-center justify-between"
              >
                <div>
                  <div className="text-xs font-semibold text-slate-200 flex items-center gap-2">
                    <span>{sample.name}</span>
                    <span className="font-mono text-[10px] text-slate-400 font-normal">({sample.url.replace('https://github.com/', '')})</span>
                  </div>
                  <p className="text-[11px] text-slate-400 mt-0.5">{sample.desc}</p>
                </div>
                <div className="hidden sm:flex items-center gap-1.5 shrink-0 ml-3">
                  {sample.tags.map((tag) => (
                    <span key={tag} className="text-[10px] font-mono px-2 py-0.5 rounded bg-space-950 border border-space-800 text-slate-400">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
