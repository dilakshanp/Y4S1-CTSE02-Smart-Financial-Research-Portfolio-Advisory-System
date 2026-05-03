//Running localhost 5001 for development; update API_BASE for production deployment

const API_BASE = 'http://localhost:5001/api';

export async function submitResearch(query) {
  const res = await fetch(`${API_BASE}/research`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query }),
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getResearch(queryId) {
  const res = await fetch(`${API_BASE}/research/${queryId}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export function streamResearch(queryId, onEvent) {
  const evtSource = new EventSource(`${API_BASE}/research/${queryId}/stream`);
  evtSource.onmessage = (e) => {
    try {
      const event = JSON.parse(e.data);
      onEvent(event);
      if (event.type === 'done' || event.type === 'error') {
        evtSource.close();
      }
    } catch (err) {
      console.error('SSE parse error', err);
    }
  };
  evtSource.onerror = () => {
    evtSource.close();
    onEvent({ type: 'error', data: { message: 'Connection lost' } });
  };
  return evtSource;
}

export async function getSessions() {
  const res = await fetch(`${API_BASE}/sessions`);
  if (!res.ok) return { sessions: [] };
  return res.json();
}

export async function getSampleQueries() {
  const res = await fetch(`${API_BASE}/sample-queries`);
  if (!res.ok) return { queries: [] };
  return res.json();
}

export async function healthCheck() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    return res.ok ? await res.json() : { status: 'unhealthy' };
  } catch {
    return { status: 'unreachable' };
  }
}

