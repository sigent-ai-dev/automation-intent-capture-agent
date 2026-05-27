import { CONFIG } from '../config/constants';
import type { CreateSessionResponse, SessionDetailResponse, SessionResultResponse } from '../types/session';

const baseUrl = () => CONFIG.API_URL;

export const sessionService = {
  async create(projectName: string): Promise<CreateSessionResponse> {
    const res = await fetch(`${baseUrl()}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ project_name: projectName || 'unnamed' }),
    });
    if (!res.ok) throw new Error(`Failed to create session: ${res.status}`);
    return res.json();
  },

  async get(sessionId: string): Promise<SessionDetailResponse> {
    const res = await fetch(`${baseUrl()}/sessions/${sessionId}`);
    if (!res.ok) throw new Error(`Failed to get session: ${res.status}`);
    return res.json();
  },

  async getResult(sessionId: string): Promise<SessionResultResponse> {
    const res = await fetch(`${baseUrl()}/sessions/${sessionId}/result`);
    if (!res.ok) throw new Error(`Failed to get result: ${res.status}`);
    return res.json();
  },

  async list(): Promise<{ sessions: Array<{ session_id: string; status: string; project_name: string }> }> {
    const res = await fetch(`${baseUrl()}/sessions`);
    if (!res.ok) throw new Error(`Failed to list sessions: ${res.status}`);
    return res.json();
  },

  async cancel(sessionId: string): Promise<void> {
    const res = await fetch(`${baseUrl()}/sessions/${sessionId}`, { method: 'DELETE' });
    if (!res.ok && res.status !== 204) throw new Error(`Failed to cancel session: ${res.status}`);
  },
};
