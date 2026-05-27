/**
 * @vitest-environment jsdom
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { sessionService } from './sessionService';

const mockFetch = vi.fn();
(globalThis as any).fetch = mockFetch; // eslint-disable-line @typescript-eslint/no-explicit-any

beforeEach(() => {
  mockFetch.mockReset();
});

describe('sessionService', () => {
  describe('create', () => {
    it('posts to /sessions and returns response', async () => {
      const mockResponse = { session_id: 'abc', join_url: '/join/abc', status: 'pending', created_at: '2026-01-01' };
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockResponse) });

      const result = await sessionService.create('my-project');

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/sessions'),
        expect.objectContaining({ method: 'POST' }),
      );
      expect(result.session_id).toBe('abc');
    });

    it('throws on non-ok response', async () => {
      mockFetch.mockResolvedValue({ ok: false, status: 500 });
      await expect(sessionService.create('test')).rejects.toThrow('Failed to create session: 500');
    });
  });

  describe('cancel', () => {
    it('sends DELETE request', async () => {
      mockFetch.mockResolvedValue({ ok: true, status: 204 });
      await sessionService.cancel('abc');
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/sessions/abc'),
        expect.objectContaining({ method: 'DELETE' }),
      );
    });
  });

  describe('getResult', () => {
    it('fetches session result', async () => {
      const mockResult = { intent_md: '# Intent', state: {}, audit_md: '# Audit' };
      mockFetch.mockResolvedValue({ ok: true, json: () => Promise.resolve(mockResult) });

      const result = await sessionService.getResult('abc');
      expect(result.intent_md).toBe('# Intent');
    });

    it('throws on 404', async () => {
      mockFetch.mockResolvedValue({ ok: false, status: 404 });
      await expect(sessionService.getResult('abc')).rejects.toThrow('Failed to get result: 404');
    });
  });
});
