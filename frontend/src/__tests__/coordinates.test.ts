/**
 * Phase 13 — Coordinate Safety & Utility Tests
 * 
 * Tests the pure coordinate validation functions and displacement calculations
 * used by all frontend components. These are the mathematical safety gates
 * that prevent NaN/Infinity from reaching the UI layer.
 */
import { describe, it, expect } from 'vitest';
import {
  isValidLatitude,
  isValidLongitude,
  isFiniteCoord,
  displacementKm,
  formatCoord,
} from '../utils/coordinates';

// ─── Latitude Validation ───────────────────────────────────────────────────

describe('isValidLatitude', () => {
  it('accepts valid Antarctic latitudes', () => {
    expect(isValidLatitude(-65.0)).toBe(true);
    expect(isValidLatitude(-72.5)).toBe(true);
    expect(isValidLatitude(-90)).toBe(true);
    expect(isValidLatitude(0)).toBe(true);
    expect(isValidLatitude(90)).toBe(true);
  });

  it('rejects latitude below -90', () => {
    expect(isValidLatitude(-90.001)).toBe(false);
    expect(isValidLatitude(-100)).toBe(false);
  });

  it('rejects latitude above 90', () => {
    expect(isValidLatitude(90.001)).toBe(false);
    expect(isValidLatitude(180)).toBe(false);
  });

  it('rejects NaN latitude', () => {
    expect(isValidLatitude(NaN)).toBe(false);
  });

  it('rejects Infinity latitude', () => {
    expect(isValidLatitude(Infinity)).toBe(false);
    expect(isValidLatitude(-Infinity)).toBe(false);
  });
});

// ─── Longitude Validation ──────────────────────────────────────────────────

describe('isValidLongitude', () => {
  it('accepts valid longitudes', () => {
    expect(isValidLongitude(45.0)).toBe(true);
    expect(isValidLongitude(-60.2)).toBe(true);
    expect(isValidLongitude(-180)).toBe(true);
    expect(isValidLongitude(180)).toBe(true);
    expect(isValidLongitude(0)).toBe(true);
  });

  it('rejects longitude below -180', () => {
    expect(isValidLongitude(-180.001)).toBe(false);
    expect(isValidLongitude(-200)).toBe(false);
  });

  it('rejects longitude above 180', () => {
    expect(isValidLongitude(180.001)).toBe(false);
    expect(isValidLongitude(200)).toBe(false);
  });

  it('rejects NaN longitude', () => {
    expect(isValidLongitude(NaN)).toBe(false);
  });

  it('rejects Infinity longitude', () => {
    expect(isValidLongitude(Infinity)).toBe(false);
    expect(isValidLongitude(-Infinity)).toBe(false);
  });
});

// ─── Finite Coordinate Check ───────────────────────────────────────────────

describe('isFiniteCoord', () => {
  it('accepts finite numbers', () => {
    expect(isFiniteCoord(0)).toBe(true);
    expect(isFiniteCoord(-65.123)).toBe(true);
    expect(isFiniteCoord(12345.678)).toBe(true);
  });

  it('rejects NaN', () => {
    expect(isFiniteCoord(NaN)).toBe(false);
  });

  it('rejects Infinity', () => {
    expect(isFiniteCoord(Infinity)).toBe(false);
    expect(isFiniteCoord(-Infinity)).toBe(false);
  });
});

// ─── Displacement Calculation ──────────────────────────────────────────────

describe('displacementKm', () => {
  it('computes zero displacement', () => {
    expect(displacementKm(0, 0)).toBe(0);
  });

  it('computes correct displacement for known values', () => {
    // 3000m dx, 4000m dy → 5000m → 5.0 km
    expect(displacementKm(3000, 4000)).toBeCloseTo(5.0, 6);
  });

  it('handles negative displacements', () => {
    expect(displacementKm(-3000, -4000)).toBeCloseTo(5.0, 6);
  });

  it('handles single-axis displacement', () => {
    expect(displacementKm(10000, 0)).toBeCloseTo(10.0, 6);
    expect(displacementKm(0, 10000)).toBeCloseTo(10.0, 6);
  });
});

// ─── Coordinate Formatting ────────────────────────────────────────────────

describe('formatCoord', () => {
  it('formats to 4 decimal places by default', () => {
    expect(formatCoord(-65.12345678)).toBe('-65.1235');
  });

  it('respects custom decimal places', () => {
    expect(formatCoord(45.1, 2)).toBe('45.10');
  });

  it('formats zero', () => {
    expect(formatCoord(0)).toBe('0.0000');
  });
});
