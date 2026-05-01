import { useEffect, useRef } from 'react';

export default function LogStream({ logs }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  if (logs.length === 0) {
    return <div className="log-stream"><p style={{ color: 'var(--text-muted)' }}>Waiting for agent activity...</p></div>;
  }

  const formatTime = (ts) => {
    if (!ts) return '';
    try {
      const d = new Date(ts);
      return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch { return ''; }
  };

  return (
    <div className="log-stream">
      {logs.map((log, i) => {
        const d = log.data || {};
        let msg = '';
        if (log.type === 'status') msg = d.message || d.status;
        else if (log.type === 'agent_log') {
          msg = `[${d.event_type || ''}]`;
          if (d.tool_name) msg += ` Tool: ${d.tool_name}`;
          if (d.input) msg += ` → ${d.input.slice(0, 100)}`;
          if (d.duration_ms) msg += ` (${d.duration_ms.toFixed(0)}ms)`;
        } else if (log.type === 'complete') msg = `✓ Pipeline completed in ${(d.total_duration_ms / 1000).toFixed(1)}s`;
        else if (log.type === 'error') msg = `✗ ${d.message}`;
        else msg = JSON.stringify(d).slice(0, 120);

        return (
          <div key={i} className="log-entry">
            <span className="log-time">{formatTime(log.timestamp)}</span>
            <span className="log-agent">{d.agent || log.type}</span>
            <span className="log-msg">{msg}</span>
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
}
