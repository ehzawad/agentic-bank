export interface ChatResponse {
  response: string;
  state: string;
  emotion: string;
  tool_calls: { tool: string; input: Record<string, unknown>; result: Record<string, unknown> }[];
  transferred_to_human: boolean;
}

export interface SessionResponse {
  session_id: string;
  greeting: string;
}

export async function createSession(): Promise<SessionResponse> {
  const res = await fetch('/api/sessions', { method: 'POST' });
  if (!res.ok) throw new Error('Failed to create session');
  return res.json();
}

export async function sendMessage(sessionId: string, message: string): Promise<ChatResponse> {
  const res = await fetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, message }),
  });
  if (!res.ok) throw new Error('Failed to send message');
  return res.json();
}
