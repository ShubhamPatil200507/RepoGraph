import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import React from 'react';
import { Header } from '../components/layout/Header';
import { useRepoStore } from '../store/useRepoStore';
import { NormalizedGraph } from '../types';

describe('Header Component', () => {
  beforeEach(() => {
    // Reset store state
    useRepoStore.setState({
      graph: null,
      activeAnalysisId: null,
      analysisStatus: null,
      activeView: '3d',
    });
  });

  it('renders RepoGraph brand wordmark and MVP badge', () => {
    render(<Header />);
    expect(screen.getByText('RepoGraph')).toBeInTheDocument();
    expect(screen.getByText('MVP')).toBeInTheDocument();
  });

  it('renders navigation tabs and dual export buttons when graph is loaded', () => {
    const mockGraph: NormalizedGraph = {
      nodes: [
        {
          id: 'routes.py::checkout',
          label: 'checkout',
          type: 'route',
          file_path: 'routes.py',
          layer: 'api',
          confidence: 0.95,
          evidence_status: 'verified',
        },
      ],
      edges: [],
      summary: {
        total_files: 1,
        total_nodes: 1,
        total_edges: 0,
        languages: { python: 1 },
        layers: { api: 1 },
        warnings: [],
      },
    };

    useRepoStore.setState({
      graph: mockGraph,
      activeAnalysisId: 'test-analysis-123',
      analysisStatus: {
        analysis_id: 'test-analysis-123',
        status: 'completed',
        current_stage: 'Completed',
        progress_message: 'Analysis ready',
        stages: [],
        errors: [],
        created_at: Date.now(),
        repository: {
          owner: 'repograph-demo',
          repo: 'ecommerce-platform',
          branch: 'main',
        },
      },
    });

    render(<Header />);

    // View tabs
    expect(screen.getByText('3D Universe')).toBeInTheDocument();
    expect(screen.getByText('2D Graph')).toBeInTheDocument();
    expect(screen.getByText('API Flow')).toBeInTheDocument();
    expect(screen.getByText('ER Diagram')).toBeInTheDocument();
    expect(screen.getByText('Revision Diff')).toBeInTheDocument();

    // Dual export buttons
    expect(screen.getByText('Export Graph JSON')).toBeInTheDocument();
    expect(screen.getByText('Export Graphify')).toBeInTheDocument();
  });

  it('triggers native graph JSON download when Export Graph JSON is clicked', () => {
    const mockGraph: NormalizedGraph = {
      nodes: [],
      edges: [],
      summary: {
        total_files: 0,
        total_nodes: 0,
        total_edges: 0,
        languages: {},
        layers: {},
        warnings: [],
      },
    };

    useRepoStore.setState({
      graph: mockGraph,
      activeAnalysisId: 'test-analysis-123',
    });

    // Mock URL.createObjectURL and document.createElement
    const createObjectURLMock = vi.fn().mockReturnValue('blob:mock-url');
    const revokeObjectURLMock = vi.fn();
    global.URL.createObjectURL = createObjectURLMock;
    global.URL.revokeObjectURL = revokeObjectURLMock;

    render(<Header />);

    const exportBtn = screen.getByText('Export Graph JSON');
    fireEvent.click(exportBtn);

    expect(createObjectURLMock).toHaveBeenCalled();
    expect(revokeObjectURLMock).toHaveBeenCalled();
  });
});
