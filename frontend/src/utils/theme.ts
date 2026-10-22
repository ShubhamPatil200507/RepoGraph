export const LAYER_COLORS: Record<string, { bg: string; text: string; hex: string; border: string }> = {
  ui: {
    bg: 'bg-cyan-500/10',
    text: 'text-cyan-400',
    hex: '#06b6d4',
    border: 'border-cyan-500/30',
  },
  api: {
    bg: 'bg-emerald-500/10',
    text: 'text-emerald-400',
    hex: '#10b981',
    border: 'border-emerald-500/30',
  },
  business_logic: {
    bg: 'bg-indigo-500/10',
    text: 'text-indigo-400',
    hex: '#6366f1',
    border: 'border-indigo-500/30',
  },
  data_access: {
    bg: 'bg-amber-500/10',
    text: 'text-amber-400',
    hex: '#f59e0b',
    border: 'border-amber-500/30',
  },
  database: {
    bg: 'bg-rose-500/10',
    text: 'text-rose-400',
    hex: '#f43f5e',
    border: 'border-rose-500/30',
  },
  configuration: {
    bg: 'bg-slate-500/10',
    text: 'text-slate-300',
    hex: '#94a3b8',
    border: 'border-slate-500/30',
  },
  tests: {
    bg: 'bg-purple-500/10',
    text: 'text-purple-400',
    hex: '#a855f7',
    border: 'border-purple-500/30',
  },
  external: {
    bg: 'bg-zinc-500/10',
    text: 'text-zinc-400',
    hex: '#71717a',
    border: 'border-zinc-500/30',
  },
};

export const TYPE_BADGES: Record<string, { label: string; color: string }> = {
  file: { label: 'File', color: 'bg-slate-800 text-slate-300 border-slate-700' },
  module: { label: 'Module', color: 'bg-slate-800 text-slate-300 border-slate-700' },
  class: { label: 'Class', color: 'bg-indigo-950 text-indigo-300 border-indigo-800' },
  method: { label: 'Method', color: 'bg-blue-950 text-blue-300 border-blue-800' },
  function: { label: 'Function', color: 'bg-sky-950 text-sky-300 border-sky-800' },
  route: { label: 'API Route', color: 'bg-emerald-950 text-emerald-300 border-emerald-800' },
  model: { label: 'DB Model', color: 'bg-rose-950 text-rose-300 border-rose-800' },
  component: { label: 'Component', color: 'bg-cyan-950 text-cyan-300 border-cyan-800' },
  config: { label: 'Config', color: 'bg-zinc-800 text-zinc-300 border-zinc-700' },
  test: { label: 'Test', color: 'bg-purple-950 text-purple-300 border-purple-800' },
};

export function getLayerColor(layer: string) {
  return LAYER_COLORS[layer] || {
    bg: 'bg-slate-500/10',
    text: 'text-slate-300',
    hex: '#64748b',
    border: 'border-slate-500/30',
  };
}
