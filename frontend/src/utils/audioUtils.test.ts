import { describe, it, expect } from 'vitest';
import { float32ToInt16, computeLevel } from './audioUtils';

describe('float32ToInt16', () => {
  it('converts silence to zeros', () => {
    const input = new Float32Array([0, 0, 0, 0]);
    const result = float32ToInt16(input);
    expect(result.every((v) => v === 0)).toBe(true);
  });

  it('converts max positive to 32767', () => {
    const input = new Float32Array([1.0]);
    const result = float32ToInt16(input);
    expect(result[0]).toBe(32767);
  });

  it('converts max negative to -32768', () => {
    const input = new Float32Array([-1.0]);
    const result = float32ToInt16(input);
    expect(result[0]).toBe(-32768);
  });

  it('clamps values beyond [-1, 1]', () => {
    const input = new Float32Array([2.0, -2.0]);
    const result = float32ToInt16(input);
    expect(result[0]).toBe(32767);
    expect(result[1]).toBe(-32768);
  });
});

describe('computeLevel', () => {
  it('returns 0 for silence', () => {
    const input = new Float32Array([0, 0, 0, 0]);
    expect(computeLevel(input)).toBe(0);
  });

  it('returns ~1 for full-scale signal', () => {
    const input = new Float32Array([1.0, 1.0, 1.0, 1.0]);
    expect(computeLevel(input)).toBeCloseTo(1.0);
  });

  it('returns RMS for mixed signal', () => {
    const input = new Float32Array([0.5, -0.5, 0.5, -0.5]);
    expect(computeLevel(input)).toBeCloseTo(0.5);
  });
});
