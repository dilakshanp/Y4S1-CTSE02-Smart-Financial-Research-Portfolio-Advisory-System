import { useState, useEffect } from 'react';
import { getSessions } from '../api';

export default function SessionHistory() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSessions()
      .then(d => setSessions(d.sessions || []))
      .catch(() => setSessions([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return null;

  if (sessions.length === 0) {
    return (
      <div className="empty-state" style={{ marginTop: 60 }}>
        <div className="icon">🔬</div>
        <h3 style={{ marginBottom: 8, fontSize: '1.1rem' }}>Ready to Analyze</h3>
        <p>Enter a stock research query above to get started.<br />The AI agents will analyze market data, sentiment, and risk.</p>
      </div>
    );
  }

  const badgeClass = (status) => {
    if (status === 'completed') return 'badge-bullish';
    if (status === 'failed') return 'badge-bearish';
    return 'badge-neutral';
  };

  return (
    <div style={{ marginTop: 32 }}>
      <h2 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-secondary)', marginBottom: 16 }}>
        📋 Recent Sessions
      </h2>
      <div className="session-list">
        {sessions.slice(0, 10).map((s, i) => (
          <div key={i} className="session-item">
            <span className="session-query">{s.user_query}</span>
            <span className={`session-status card-badge ${badgeClass(s.status)}`}>{s.status}</span>
            <span className="session-time">{s.created_at || ''}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
