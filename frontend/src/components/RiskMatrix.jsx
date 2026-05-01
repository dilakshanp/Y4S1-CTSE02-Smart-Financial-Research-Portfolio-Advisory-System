export default function RiskMatrix({ data }) {
  if (!data) {
    return (
      <div className="glass card">
        <div className="card-header"><span className="card-title">⚠️ Risk Assessment</span></div>
        <div className="loading-overlay"><span className="spinner" /><p>Calculating risk metrics...</p></div>
      </div>
    );
  }

  const summary = data.state_summary || {};
  const count = summary.risk_metrics_count || 0;
  const exec = data.execution_summary || {};

  return (
    <div className="glass card">
      <div className="card-header">
        <span className="card-title">⚠️ Risk Assessment</span>
        <span className={`card-badge ${count > 0 ? 'badge-medium' : 'badge-neutral'}`}>
          {count > 0 ? `${count} Assessed` : 'Pending'}
        </span>
      </div>
      {count > 0 ? (
        <div className="metrics-grid">
          <div className="metric-item">
            <span className="metric-label">Tickers Assessed</span>
            <span className="metric-value">{count}</span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Metrics Computed</span>
            <span className="metric-value">Vol, β, SR, VaR, DD</span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Tools Used</span>
            <span className="metric-value">{exec.total_tool_calls || 0}</span>
          </div>
          <div className="metric-item">
            <span className="metric-label">Errors</span>
            <span className="metric-value" style={{ color: exec.total_errors ? 'var(--red)' : 'var(--green)' }}>
              {exec.total_errors || 0}
            </span>
          </div>
        </div>
      ) : (
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>No risk data in results</p>
      )}
    </div>
  );
}
