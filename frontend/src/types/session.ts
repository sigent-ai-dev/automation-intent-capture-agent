export type SessionStatus =
  | 'idle'
  | 'creating'
  | 'connecting'
  | 'negotiating'
  | 'active'
  | 'completing'
  | 'complete'
  | 'cancelled'
  | 'failed';

export interface SessionProgress {
  sectionsCovered: string[];
  proposalRounds: number;
  alignmentReached: boolean;
}

export interface SessionResult {
  intentMd: string;
  state: Record<string, unknown>;
  auditMd: string;
}

export interface Session {
  id: string;
  projectName: string;
  status: SessionStatus;
  joinUrl: string;
  createdAt: string;
  progress: SessionProgress;
  result: SessionResult | null;
  error: string | null;
}

export interface CreateSessionResponse {
  session_id: string;
  join_url: string;
  status: string;
  created_at: string;
}

export interface SessionDetailResponse {
  session_id: string;
  status: string;
  progress: { sections_covered: string[]; proposal_rounds: number; alignment_reached: boolean };
  participants: string[];
}

export interface SessionResultResponse {
  intent_md: string;
  state: Record<string, unknown>;
  audit_md: string;
}
