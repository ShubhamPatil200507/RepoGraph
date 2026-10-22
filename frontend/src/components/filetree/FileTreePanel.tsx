import React, { useState } from 'react';
import {
  Folder,
  FolderOpen,
  FileText,
  Search,
  Filter,
  X,
  ChevronRight,
  ChevronDown,
  Layers,
  Code,
} from 'lucide-react';
import { useRepoStore } from '../../store/useRepoStore';
import { FileItem } from '../../types';
import { LAYER_COLORS, TYPE_BADGES } from '../../utils/theme';

export const FileTreePanel: React.FC = () => {
  const {
    fileTree,
    searchQuery,
    setSearchQuery,
    selectedLayers,
    toggleLayerFilter,
    selectedTypes,
    toggleTypeFilter,
    selectedFileFilter,
    setFileFilter,
  } = useRepoStore();

  const [activeTab, setActiveTab] = useState<'tree' | 'filters'>('tree');

  return (
    <aside className="w-72 h-full border-r border-space-800 bg-space-900/60 backdrop-blur flex flex-col z-10 select-none">
      {/* Search Input */}
      <div className="p-3 border-b border-space-800">
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search symbols or files..."
            className="w-full bg-space-950 text-xs text-slate-100 placeholder-slate-500 rounded-lg pl-8 pr-7 py-1.5 border border-space-800 focus:outline-none focus:border-brand-500 font-mono transition"
          />
          {searchQuery && (
            <button
              onClick={() => setSearchQuery('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-200"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {/* Tab switch between Tree and Filters */}
        <div className="flex gap-2 mt-2">
          <button
            onClick={() => setActiveTab('tree')}
            className={`flex-1 py-1 rounded text-xs font-medium text-center transition ${
              activeTab === 'tree'
                ? 'bg-space-800 text-slate-100 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            File Tree
          </button>
          <button
            onClick={() => setActiveTab('filters')}
            className={`flex-1 py-1 rounded text-xs font-medium text-center transition flex items-center justify-center gap-1.5 ${
              activeTab === 'filters'
                ? 'bg-space-800 text-slate-100 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Filter className="w-3 h-3" />
            <span>Filters</span>
            {(selectedLayers.length > 0 || selectedTypes.length > 0) && (
              <span className="w-1.5 h-1.5 rounded-full bg-brand-400" />
            )}
          </button>
        </div>
      </div>

      {/* Active File Filter Banner */}
      {selectedFileFilter && (
        <div className="px-3 py-1.5 bg-brand-950/40 border-b border-brand-800/40 flex items-center justify-between text-xs font-mono">
          <span className="text-brand-300 truncate text-[11px]" title={selectedFileFilter}>
            {selectedFileFilter}
          </span>
          <button
            onClick={() => setFileFilter(null)}
            className="text-brand-400 hover:text-brand-200 p-0.5"
            title="Clear file filter"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-2">
        {activeTab === 'tree' ? (
          <div>
            {fileTree?.children && fileTree.children.length > 0 ? (
              fileTree.children.map((child) => (
                <FileTreeNode
                  key={child.path}
                  item={child}
                  selectedPath={selectedFileFilter}
                  onSelectPath={setFileFilter}
                />
              ))
            ) : (
              <div className="p-4 text-center text-xs text-slate-500">
                No files parsed.
              </div>
            )}
          </div>
        ) : (
          <div className="p-2 space-y-4">
            {/* Layer Filters */}
            <div>
              <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                <Layers className="w-3 h-3 text-brand-400" />
                Architectural Layers
              </div>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(LAYER_COLORS).map(([layer, val]) => {
                  const isActive = selectedLayers.includes(layer);
                  return (
                    <button
                      key={layer}
                      onClick={() => toggleLayerFilter(layer)}
                      className={`text-xs px-2 py-1 rounded-md border font-mono transition flex items-center gap-1.5 ${
                        isActive
                          ? `${val.bg} ${val.text} ${val.border} font-semibold ring-1 ring-inset ring-current`
                          : 'bg-space-950 border-space-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <span className="w-2 h-2 rounded-full" style={{ backgroundColor: val.hex }} />
                      <span className="capitalize">{layer.replace('_', ' ')}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Type Filters */}
            <div>
              <div className="text-[10px] uppercase font-mono tracking-wider text-slate-400 mb-2 flex items-center gap-1.5">
                <Code className="w-3 h-3 text-cyan-400" />
                Component Types
              </div>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(TYPE_BADGES).map(([type, val]) => {
                  const isActive = selectedTypes.includes(type);
                  return (
                    <button
                      key={type}
                      onClick={() => toggleTypeFilter(type)}
                      className={`text-xs px-2 py-1 rounded-md border font-mono transition ${
                        isActive
                          ? `${val.color} ring-1 ring-inset ring-current font-semibold`
                          : 'bg-space-950 border-space-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      {val.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </aside>
  );
};

const FileTreeNode: React.FC<{
  item: FileItem;
  selectedPath: string | null;
  onSelectPath: (p: string | null) => void;
}> = ({ item, selectedPath, onSelectPath }) => {
  const [isOpen, setIsOpen] = useState(false);
  const isSelected = selectedPath === item.path;

  if (item.is_directory) {
    return (
      <div className="text-xs">
        <button
          onClick={() => setIsOpen((prev) => !prev)}
          className="w-full text-left py-1 px-1.5 rounded hover:bg-space-850 flex items-center gap-1.5 text-slate-300 font-mono transition"
        >
          {isOpen ? (
            <ChevronDown className="w-3 h-3 text-slate-500 shrink-0" />
          ) : (
            <ChevronRight className="w-3 h-3 text-slate-500 shrink-0" />
          )}
          {isOpen ? (
            <FolderOpen className="w-3.5 h-3.5 text-brand-400 shrink-0" />
          ) : (
            <Folder className="w-3.5 h-3.5 text-brand-400 shrink-0" />
          )}
          <span className="truncate">{item.name}</span>
        </button>

        {isOpen && item.children && (
          <div className="pl-4 border-l border-space-800/80 ml-2">
            {item.children.map((child) => (
              <FileTreeNode
                key={child.path}
                item={child}
                selectedPath={selectedPath}
                onSelectPath={onSelectPath}
              />
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <button
      onClick={() => onSelectPath(isSelected ? null : item.path)}
      className={`w-full text-left py-1 px-1.5 rounded flex items-center justify-between text-xs font-mono transition ${
        isSelected
          ? 'bg-brand-950/80 border border-brand-500/40 text-brand-300 font-semibold'
          : 'text-slate-400 hover:text-slate-200 hover:bg-space-850'
      }`}
      title={item.path}
    >
      <div className="flex items-center gap-1.5 truncate">
        <FileText className="w-3.5 h-3.5 text-slate-500 shrink-0" />
        <span className="truncate">{item.name}</span>
      </div>
      {item.node_count > 0 && (
        <span className="text-[10px] text-slate-500 bg-space-950 px-1.5 py-0.2 rounded border border-space-800">
          {item.node_count}
        </span>
      )}
    </button>
  );
};
