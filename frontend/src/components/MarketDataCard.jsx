export default function MarketDataCard({ data }) {
  if (!data) {
    return (
      <div className="glass card">
        <div className="card-header"><span className="card-title">📈 Market Data</span></div>
        <div className="loading-overlay"><span className="spinner" /><p>Fetching market data...</p></div>
      </div>
    );
  }

  const summary = data.state_summary || {};
  const count = summary.market_data_count || 0;

  return (
    <div className="glass card">
      <div className="card-header">
        <span className="card-title">📈 Market Data</span>
        <span className="card-badge badge-neutral">{count} ticker{count !== 1 ? 's' : ''}</span>
      </div>
      {count > 0 ? (
        <div className="metrics-grid">
          <div className="metric-item">
            <span className="metric-label">Tickers Analyzed</span>
            <span className="metric-value">{count}</span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Data Source</span>
            <span className="metric-value">Yahoo Finance</span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Status</span>
            <span className="metric-value" style={{ color: 'var(--green)' }}>✓ Fetched</span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Duration</span>
            <span className="metric-value">{(data.total_duration_ms / 1000).toFixed(1)}s</span>
          </div>
        </div>
      ) : (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No market data in results</p>
      )}
    </div>
  );
}
