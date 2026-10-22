import React from 'react';
import { useRepoStore } from './store/useRepoStore';
import { Header } from './components/layout/Header';
import { StatusBar } from './components/layout/StatusBar';
import { UniverseCanvas } from './components/canvas3d/UniverseCanvas';
import { FlowCanvas } from './components/canvas2d/FlowCanvas';
import { ApiFlowView } from './components/apiflow/ApiFlowView';
import { ERDiagramView } from './components/er/ERDiagramView';
import { RevisionCompareView } from './components/compare/RevisionCompareView';
import { FileTreePanel } from './components/filetree/FileTreePanel';
import { InspectorPanel } from './components/inspector/InspectorPanel';
import { InitialHero } from './components/modals/InitialHero';
import { IngestionProgressModal } from './components/modals/IngestionProgressModal';

export const App: React.FC = () => {
  const { graph, activeView } = useRepoStore();

  return (
    <div className="flex flex-col w-screen h-screen bg-space-950 text-slate-100 overflow-hidden font-sans">
      <Header />

      <main className="flex-1 flex relative overflow-hidden">
        {!graph ? (
          <InitialHero />
        ) : (
          <>
            <FileTreePanel />

            <div className="flex-1 relative h-full">
              {activeView === '3d' && <UniverseCanvas />}
              {activeView === '2d' && <FlowCanvas />}
              {activeView === 'api' && <ApiFlowView />}
              {activeView === 'er' && <ERDiagramView />}
              {activeView === 'compare' && <RevisionCompareView />}
            </div>

            <InspectorPanel />
          </>
        )}
      </main>

      {graph && <StatusBar />}

      <IngestionProgressModal />
    </div>
  );
};

export default App;
