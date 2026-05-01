export default function SentimentGauge({ data }) {
  if (!data) {
    return (
      <div className="glass card">
        <div className="card-header"><span className="card-title">💬 Sentiment Analysis</span></div>
        <div className="loading-overlay"><span className="spinner" /><p>Analyzing sentiment...</p></div>
      </div>
    );
  }

  const summary = data.state_summary || {};
  const count = summary.sentiment_count || 0;
  const exec = data.execution_summary || {};
  const tools = exec.tools_used || [];
  const hasSentiment = tools.some(t => t.toLowerCase().includes('sentiment')) || count > 0;

  return (
    <div className="glass card">
      <div className="card-header">
        <span className="card-title">💬 Sentiment Analysis</span>
        <span className={`card-badge ${hasSentiment ? 'badge-bullish' : 'badge-neutral'}`}>
          {hasSentiment ? 'Analyzed' : 'Pending'}
        </span>
      </div>
      <div className="gauge-container">
        <div className="gauge-score" style={{ color: hasSentiment ? 'var(--cyan)' : 'var(--text-muted)' }}>
          {count > 0 ? count : '—'}
        </div>
        <div className="gauge-label" style={{ color: 'var(--text-secondary)' }}>
          {count > 0 ? `${count} Result${count !== 1 ? 's' : ''}` : 'No sentiment data'}
        </div>
        <div className="gauge-bar">
          <div className={`gauge-fill bullish`} style={{ width: hasSentiment ? '70%' : '0%' }} />
        </div>
        <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Powered by VADER NLP + RSS Feeds
        </span>
      </div>
    </div>
  );
}
