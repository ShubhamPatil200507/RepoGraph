import React from 'react';
import {
  Database,
  Key,
  Link as LinkIcon,
  Table as TableIcon,
  AlertCircle,
  FileCode,
  ShieldCheck,
} from 'lucide-react';
import { useRepoStore } from '../../store/useRepoStore';
import { EREntity, ERRelationship } from '../../types';

export const ERDiagramView: React.FC = () => {
  const { erDiagram, selectNode } = useRepoStore();

  if (!erDiagram || !erDiagram.has_database_evidence || erDiagram.entities.length === 0) {
    return (
      <div className="w-full h-full flex flex-col items-center justify-center p-8 text-center bg-space-950">
        <div className="w-16 h-16 rounded-2xl bg-space-900 border border-space-800 flex items-center justify-center mb-4 text-slate-500 shadow-xl">
          <Database className="w-8 h-8 text-slate-400" />
        </div>
        <h3 className="text-base font-semibold text-slate-200 mb-2">
          No Database Evidence Detected
        </h3>
        <p className="text-sm text-slate-400 max-w-md leading-relaxed mb-4">
          {erDiagram?.detection_summary ||
            'RepoGraph inspected this repository for SQL DDL schemas, SQLAlchemy models, Prisma definitions, and Django models, but found no database entity declarations.'}
        </p>
        <div className="text-xs font-mono text-slate-500 bg-space-900 px-3 py-1.5 rounded border border-space-800">
          Supported: .sql, schema.prisma, SQLAlchemy Base/models, Django models.py
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full bg-space-950 overflow-y-auto p-6">
      {/* Header Info */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4 border-b border-space-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-rose-400" />
            <h2 className="text-lg font-bold text-slate-100">Database Entity-Relationship Map</h2>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            {erDiagram.detection_summary}
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-space-900 border border-space-800 text-slate-300">
            <span className="w-2 h-2 rounded-full bg-rose-400" />
            {erDiagram.entities.length} Entities
          </span>
          <span className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-space-900 border border-space-800 text-slate-300">
            <LinkIcon className="w-3.5 h-3.5 text-cyan-400" />
            {erDiagram.relationships.length} Relationships
          </span>
        </div>
      </div>

      {/* Grid of Database Entities */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {erDiagram.entities.map((entity) => (
          <EntityCard key={entity.id} entity={entity} relationships={erDiagram.relationships} onSelect={selectNode} />
        ))}
      </div>

      {/* Relationships Table / Summary */}
      {erDiagram.relationships.length > 0 && (
        <div className="mt-8 bg-space-900/60 border border-space-800 rounded-xl p-4">
          <h3 className="text-xs font-mono uppercase text-slate-400 mb-3 flex items-center gap-2">
            <LinkIcon className="w-3.5 h-3.5 text-brand-400" />
            Verified Foreign Key & Relation Links
          </h3>
          <div className="space-y-2">
            {erDiagram.relationships.map((rel) => (
              <div
                key={rel.id}
                className="flex items-center justify-between text-xs p-2.5 rounded-lg bg-space-950 border border-space-800"
              >
                <div className="flex items-center gap-2 font-mono">
                  <span className="text-slate-100 font-semibold">{rel.source_entity}</span>
                  <span className="text-slate-500 font-sans">➔</span>
                  <span className="text-slate-100 font-semibold">{rel.target_entity}</span>
                  <span className="text-[10px] text-cyan-400 px-1.5 py-0.5 rounded bg-cyan-950/40 border border-cyan-800/40">
                    {rel.cardinality}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-[11px] text-slate-400 font-mono">
                  {rel.source_file && (
                    <span>
                      {rel.source_file}:{rel.source_line || 1}
                    </span>
                  )}
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-950/40 border border-emerald-800/40 text-emerald-400">
                    {rel.evidence_status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

const EntityCard: React.FC<{
  entity: EREntity;
  relationships: ERRelationship[];
  onSelect: (id: string) => void;
}> = ({ entity, relationships, onSelect }) => {
  const outgoingRels = relationships.filter((r) => r.source_entity === entity.name);
  const incomingRels = relationships.filter((r) => r.target_entity === entity.name);

  return (
    <div className="rounded-xl bg-space-900 border border-space-800 overflow-hidden shadow-lg hover:border-slate-700 transition">
      {/* Table Header */}
      <div className="bg-space-850 p-3 border-b border-space-800 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <TableIcon className="w-4 h-4 text-rose-400" />
          <span className="font-mono text-sm font-bold text-slate-100">{entity.name}</span>
          {entity.table_name && entity.table_name !== entity.name && (
            <span className="text-[11px] font-mono text-slate-400">({entity.table_name})</span>
          )}
        </div>
        <span className="text-[10px] font-mono text-slate-500 truncate max-w-[140px]" title={entity.file_path}>
          {entity.file_path.split('/').pop()}
        </span>
      </div>

      {/* Columns List */}
      <div className="p-3 divide-y divide-space-800/60 max-h-[300px] overflow-y-auto">
        {entity.attributes.map((attr) => (
          <div key={attr.name} className="py-1.5 flex items-center justify-between text-xs">
            <div className="flex items-center gap-1.5 font-mono">
              {attr.is_primary_key && (
                <span title="Primary Key">
                  <Key className="w-3 h-3 text-amber-400" />
                </span>
              )}
              {attr.is_foreign_key && (
                <span title={`Foreign Key: ${attr.foreign_key_target || ''}`}>
                  <LinkIcon className="w-3 h-3 text-cyan-400" />
                </span>
              )}
              <span className={attr.is_primary_key ? 'text-amber-200 font-semibold' : 'text-slate-200'}>
                {attr.name}
              </span>
            </div>

            <div className="flex items-center gap-2 font-mono text-[11px]">
              <span className="text-slate-400">{attr.data_type}</span>
              {attr.is_nullable ? (
                <span className="text-[9px] text-slate-500">null</span>
              ) : (
                <span className="text-[9px] text-slate-400">req</span>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Relations Summary */}
      {(outgoingRels.length > 0 || incomingRels.length > 0) && (
        <div className="p-2.5 bg-space-950/60 border-t border-space-800 text-[11px] font-mono flex flex-wrap gap-2 text-slate-400">
          {outgoingRels.map((r) => (
            <span key={r.id} className="text-cyan-300">
              ➔ {r.target_entity}
            </span>
          ))}
          {incomingRels.map((r) => (
            <span key={r.id} className="text-emerald-300">
              ← {r.source_entity}
            </span>
          ))}
        </div>
      )}
    </div>
  );
};
