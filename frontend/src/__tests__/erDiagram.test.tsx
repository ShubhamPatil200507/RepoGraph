import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { ERDiagramView } from '../components/er/ERDiagramView';
import * as storeModule from '../store/useRepoStore';

describe('ERDiagramView', () => {
  it('renders honest empty state when no database evidence exists', () => {
    vi.spyOn(storeModule, 'useRepoStore').mockReturnValue({
      erDiagram: {
        has_database_evidence: false,
        detection_summary: 'No database entities detected.',
        entities: [],
        relationships: [],
      },
      selectNode: vi.fn(),
    } as any);

    render(<ERDiagramView />);
    expect(screen.getByText(/No Database Evidence Detected/i)).toBeInTheDocument();
    expect(screen.getByText(/No database entities detected\./i)).toBeInTheDocument();
  });

  it('renders entities and attributes when database models are detected', () => {
    vi.spyOn(storeModule, 'useRepoStore').mockReturnValue({
      erDiagram: {
        has_database_evidence: true,
        detection_summary: 'Detected 1 database entity.',
        entities: [
          {
            id: 'entity::User',
            name: 'User',
            table_name: 'users',
            file_path: 'backend/models/user.py',
            start_line: 5,
            end_line: 20,
            attributes: [
              {
                name: 'id',
                data_type: 'Integer',
                is_primary_key: true,
                is_foreign_key: false,
                is_nullable: false,
              },
              {
                name: 'username',
                data_type: 'String',
                is_primary_key: false,
                is_foreign_key: false,
                is_nullable: false,
              },
            ],
          },
        ],
        relationships: [],
      },
      selectNode: vi.fn(),
    } as any);

    render(<ERDiagramView />);
    expect(screen.getByText(/Database Entity-Relationship Map/i)).toBeInTheDocument();
    expect(screen.getByText('User')).toBeInTheDocument();
    expect(screen.getByText('id')).toBeInTheDocument();
    expect(screen.getByText('username')).toBeInTheDocument();
  });
});
