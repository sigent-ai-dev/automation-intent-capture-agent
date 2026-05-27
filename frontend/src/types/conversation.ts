export interface Message {
  id: string;
  role: 'user' | 'agent';
  text: string;
  timestamp: Date;
  isFinal: boolean;
}
