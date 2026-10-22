import React, { useEffect } from 'react';
import {
  Route,
  ArrowRight,
  ShieldCheck,
  Cpu,
  Database,
  Globe,
  Lock,
  Layers,
  FileCode,
  Info,
} from 'lucide-react';
import { useRepoStore } from '../../store/useRepoStore';

export const ApiFlowView: React.FC = () => {
  const {
    apiRoutes,
    activeRouteId,
    apiFlowData,
    loadApiRoutes,
    loadApiFlow,
    selectNode,
  } = useRepoStore();

  useEffect(() => {
    loadApiRoutes();
  }, [loadApiRoutes]);

  const METHOD_COLORS: Record<string, string> = {
    GET: 'bg-emerald-950/60 text-emerald-400 border-emerald-800/60',
    POST: 'bg-blue-950/60 text-blue-400 border-blue-800/60',
    PUT: 'bg-amber-950/60 text-amber-400 border-amber-800/60',
    DELETE: 'bg-rose-950/60 text-rose-400 border-rose-800/60',
    PATCH: 'bg-purple-950/60 text-purple-400 border-purple-800/60',
  };

  return (
    <div className="w-full h-full flex bg-space-950 text-slate-100 overflow-hidden">
      {/* Route List Sidebar */}
      <aside className="w-80 h-full border-r border-space-800 bg-space-900/60 flex flex-col shrink-0">
        <div className="p-4 border-b border-space-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Route className="w-4 h-4 text-brand-400" />
            <h3 className="text-xs font-mono uppercase font-bold text-slate-200">
              API Route Inventory
            </h3>
          </div>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-space-850 border border-space-800 text-slate-400">
            {apiRoutes.length} Endpoints
          </span>
        </div>

        <div className="flex-1 overflow-y-auto divide-y divide-space-800/50 p-2 space-y-1">
          {apiRoutes.length === 0 ? (
            <div className="p-6 text-center text-xs text-slate-500">
              Scanning codebase for API route declarations (@router, app.get, express)...
            </div>
          ) : (
            apiRoutes.map((rt) => {
              const isActive = rt.id === activeRouteId;
              const badgeClass = METHOD_COLORS[rt.http_method.toUpperCase()] || 'bg-slate-800 text-slate-300 border-slate-700';

              return (
                <button
                  key={rt.id}
                  onClick={() => loadApiFlow(rt.id)}
                  className={`w-full text-left p-3 rounded-lg border transition flex flex-col gap-1.5 ${
                    isActive
                      ? 'bg-brand-950/40 border-brand-500/80 shadow-lg shadow-brand-500/10'
                      : 'bg-space-900/40 border-space-800/60 hover:bg-space-850 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${badgeClass}`}>
                      {rt.http_method}
                    </span>
                    <span className="text-[10px] font-mono text-slate-500 truncate max-w-[140px]">
                      {rt.file_path.split('/').pop()}
                    </span>
                  </div>

                  <span className="text-xs font-mono text-slate-200 truncate font-semibold">
                    {rt.route_path}
                  </span>

                  <span className="text-[11px] text-slate-400 truncate">
                    Handler: <code className="text-slate-300 font-mono">{rt.label}</code>
                  </span>
                </button>
              );
            })
          )}
        </div>
      </aside>

      {/* Main Flow Stage Canvas */}
      <div className="flex-1 h-full overflow-y-auto p-6 flex flex-col">
        {apiFlowData && apiFlowData.route ? (
          <>
            {/* Route Summary Banner */}
            <div className="mb-6 p-4 rounded-xl bg-space-900/80 border border-space-800 shadow-xl flex flex-wrap items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span
                    className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${
                      METHOD_COLORS[apiFlowData.route.http_method.toUpperCase()] || 'bg-slate-800 text-slate-300'
                    }`}
                  >
                    {apiFlowData.route.http_method}
                  </span>
                  <span className="text-base font-mono font-bold text-slate-100">
                    {apiFlowData.route.route_path}
                  </span>
                </div>
                <p className="text-xs text-slate-400 font-mono">
                  Handler: <span className="text-slate-200 font-semibold">{apiFlowData.route.label}</span> in {apiFlowData.route.file_path}:{apiFlowData.route.start_line || 1}
                </p>
              </div>

              <div className="flex items-center gap-3">
                <button
                  onClick={() => selectNode(apiFlowData.route.id)}
                  className="px-3 py-1.5 bg-brand-600 hover:bg-brand-500 text-white rounded-lg text-xs font-medium transition flex items-center gap-1.5"
                >
                  <FileCode className="w-3.5 h-3.5" />
                  <span>Inspect Handler Code</span>
                </button>
              </div>
            </div>

            {/* Pipeline Flow Stages */}
            <div className="flex-1 space-y-6">
              {/* Stage 1: Entry Route */}
              <StageSection
                title="1. Route Entry & Parameter Validation"
                icon={<Route className="w-4 h-4 text-emerald-400" />}
                items={apiFlowData.stages.route}
                colorBorder="border-emerald-800/40"
                onSelectNode={selectNode}
              />

              {/* Stage 2: Middleware & Auth */}
              {apiFlowData.stages.middleware_auth.length > 0 && (
                <StageSection
                  title="2. Authentication & Authorization Guards"
                  icon={<Lock className="w-4 h-4 text-cyan-400" />}
                  items={apiFlowData.stages.middleware_auth}
                  colorBorder="border-cyan-800/40"
                  onSelectNode={selectNode}
                />
              )}

              {/* Stage 3: Service Logic */}
              {apiFlowData.stages.service_logic.length > 0 && (
                <StageSection
                  title="3. Controller & Business Services"
                  icon={<Cpu className="w-4 h-4 text-indigo-400" />}
                  items={apiFlowData.stages.service_logic}
                  colorBorder="border-indigo-800/40"
                  onSelectNode={selectNode}
                />
              )}

              {/* Stage 4: Data Access */}
              {apiFlowData.stages.data_access.length > 0 && (
                <StageSection
                  title="4. Data Access & Repositories"
                  icon={<Layers className="w-4 h-4 text-amber-400" />}
                  items={apiFlowData.stages.data_access}
                  colorBorder="border-amber-800/40"
                  onSelectNode={selectNode}
                />
              )}

              {/* Stage 5: Database Entities */}
              {apiFlowData.stages.database_entities.length > 0 && (
                <StageSection
                  title="5. Connected Database Models & Tables"
                  icon={<Database className="w-4 h-4 text-rose-400" />}
                  items={apiFlowData.stages.database_entities}
                  colorBorder="border-rose-800/40"
                  onSelectNode={selectNode}
                />
              )}

              {/* Stage 6: External Integrations */}
              {apiFlowData.stages.external_integrations.length > 0 && (
                <StageSection
                  title="6. External Services & APIs"
                  icon={<Globe className="w-4 h-4 text-purple-400" />}
                  items={apiFlowData.stages.external_integrations}
                  colorBorder="border-purple-800/40"
                  onSelectNode={selectNode}
                />
              )}
            </div>

            {/* Disclaimer Footer */}
            <div className="mt-8 p-3 rounded-lg bg-space-900 border border-space-800 text-[11px] text-slate-400 flex items-start gap-2">
              <Info className="w-4 h-4 text-cyan-400 shrink-0 mt-0.5" />
              <span>{apiFlowData.disclaimer}</span>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-500">
            <Route className="w-12 h-12 text-slate-600 mb-3" />
            <p className="text-sm font-medium text-slate-300 mb-1">Select an API Route</p>
            <p className="text-xs text-slate-400 max-w-sm">
              Choose an endpoint from the left sidebar to trace its framework-aware data flow from HTTP entry to database operations.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

const StageSection: React.FC<{
  title: string;
  icon: React.ReactNode;
  items: any[];
  colorBorder: string;
  onSelectNode: (id: string) => void;
}> = ({ title, icon, items, colorBorder, onSelectNode }) => {
  return (
    <div className={`p-4 rounded-xl bg-space-900/60 border ${colorBorder}`}>
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <h4 className="text-xs font-mono uppercase font-bold text-slate-200">{title}</h4>
        <span className="text-[10px] font-mono text-slate-500">({items.length})</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {items.map((item) => (
          <div
            key={item.id}
            onClick={() => onSelectNode(item.id)}
            className="p-3 rounded-lg bg-space-950 border border-space-800 hover:border-slate-600 cursor-pointer transition flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="font-mono text-xs font-bold text-slate-100 truncate">{item.label}</span>
                <span className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded bg-space-850 text-slate-400 border border-space-800">
                  {item.type}
                </span>
              </div>
              <p className="text-[11px] font-mono text-slate-400 truncate">
                {item.file_path}:{item.start_line || 1}
              </p>
              {item.summary && (
                <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                  {item.summary}
                </p>
              )}
            </div>

            <div className="mt-2.5 pt-2 border-t border-space-850 flex items-center justify-between text-[10px]">
              <span className="text-slate-500 font-mono capitalize">{item.layer.replace('_', ' ')}</span>
              <span className="text-emerald-400 font-mono flex items-center gap-1">
                <ShieldCheck className="w-3 h-3" />
                {item.evidence_status || 'verified'}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
