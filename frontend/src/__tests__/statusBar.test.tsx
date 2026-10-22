import { describe, it, expect, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { StatusBar } from '../components/layout/StatusBar';
import { useRepoStore } from '../store/useRepoStore';
import { NormalizedGraph } from '../types';

describe('StatusBar Component', () => {
  beforeEach(() => {
    useRepoStore.setState({ graph: null });
  });

  it('renders nothing when no graph is loaded', () => {
    const { container } = render(<StatusBar />);
    expect(container.firstChild).toBeNull();
  });

  it('renders files, symbols, connections, and coupling density metrics', () => {
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
      edges: [
        {
          id: 'e1',
          source: 'routes.py::checkout',
          target: 'order.py::Order',
          type: 'calls',
          evidence_status: 'verified',
        },
      ],
      summary: {
        total_files: 3,
        total_nodes: 12,
        total_edges: 28,
        coupling_density: 2.33,
        entry_points_count: 2,
        database_entities_count: 4,
        languages: { python: 3 },
        layers: { api: 1, business_logic: 6, database: 4, tests: 1 },
        warnings: [],
      },
    };

    useRepoStore.setState({ graph: mockGraph });

    render(<StatusBar />);

    expect(screen.getByText(/3 files/i)).toBeInTheDocument();
    expect(screen.getByText(/12 symbols/i)).toBeInTheDocument();
    expect(screen.getByText(/28 connections/i)).toBeInTheDocument();
    expect(screen.getByText('2.33')).toBeInTheDocument();
    expect(screen.getByText(/2 routes/i)).toBeInTheDocument();
    expect(screen.getByText(/4 db models/i)).toBeInTheDocument();
  });
});
