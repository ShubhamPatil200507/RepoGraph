import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import React from 'react';
import { App } from '../App';

// Mock Three.js / R3F Canvas and API calls
vi.mock('@react-three/fiber', () => ({
  Canvas: ({ children }: any) => <div data-testid="r3f-canvas">{children}</div>,
  useFrame: vi.fn(),
  useThree: () => ({ camera: { position: { set: vi.fn() }, lookAt: vi.fn() } }),
}));

vi.mock('@react-three/drei', () => ({
  OrbitControls: () => null,
  Html: ({ children }: any) => <div>{children}</div>,
  Stars: () => null,
  Line: () => null,
}));

describe('RepoGraph App Initial State', () => {
  it('renders RepoGraph wordmark and tagline on landing screen', () => {
    render(<App />);

    // Check brand wordmark
    expect(screen.getAllByText(/RepoGraph/i).length).toBeGreaterThan(0);

    // Check tagline
    expect(
      screen.getByText(/See how your code works\. Explore how everything connects\./i)
    ).toBeInTheDocument();

    // Check input field & analyze button
    expect(
      screen.getByPlaceholderText(/https:\/\/github\.com\/owner\/repository/i)
    ).toBeInTheDocument();
    expect(
      screen.getByRole('button', { name: /Analyze Repository/i })
    ).toBeInTheDocument();

    // Check sample repositories section
    expect(
      screen.getByText(/Try an Instant Sample Repository/i)
    ).toBeInTheDocument();
    expect(
      screen.getByText(/E-Commerce Platform Demo/i)
    ).toBeInTheDocument();
  });
});
