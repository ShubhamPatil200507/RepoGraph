import { describe, it, expect } from 'vitest';
import { LAYER_COLORS, TYPE_BADGES, getLayerColor } from '../utils/theme';

describe('theme and styling utilities', () => {
  it('provides color definitions for all architectural layers', () => {
    const layers = ['ui', 'api', 'business_logic', 'data_access', 'database', 'configuration', 'tests', 'external'];
    for (const layer of layers) {
      expect(LAYER_COLORS[layer]).toBeDefined();
      expect(LAYER_COLORS[layer].hex).toMatch(/^#[0-9a-fA-F]{6}$/);
    }
  });

  it('provides badge configuration for all component types', () => {
    const types = ['file', 'class', 'function', 'route', 'model', 'component'];
    for (const t of types) {
      expect(TYPE_BADGES[t]).toBeDefined();
      expect(TYPE_BADGES[t].label).toBeTruthy();
    }
  });

  it('falls back gracefully for unknown layers', () => {
    const fallback = getLayerColor('unknown_layer');
    expect(fallback).toBeDefined();
    expect(fallback.hex).toBe('#64748b');
  });
});
