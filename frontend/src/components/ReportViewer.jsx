export default function ReportViewer({ data, loading }) {
  if (loading && !data) {
    return (
      <div className="glass card" style={{ marginTop: 20 }}>
        <div className="card-header"><span className="card-title">📄 Advisory Report</span></div>
        <div className="loading-overlay">
          <span className="spinner" />
          <p>Generating advisory report...</p>
        </div>
      </div>
    );
  }

  if (!data?.result) return null;

  const report = data.result;

  // Simple markdown-to-html (handles headers, bold, tables, lists)
  const renderMarkdown = (md) => {
    let html = md
      .replace(/^### (.+)$/gm, '<h3>$1</h3>')
      .replace(/^## (.+)$/gm, '<h2>$1</h2>')
      .replace(/^# (.+)$/gm, '<h1>$1</h1>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/^- (.+)$/gm, '<li>$1</li>')
      .replace(/^(\d+)\. (.+)$/gm, '<li>$2</li>')
      .replace(/\n{2,}/g, '</p><p>')
      .replace(/\n/g, '<br/>');

    // Wrap in paragraphs
    html = '<p>' + html + '</p>';
    // Fix list items
    html = html.replace(/(<li>.*?<\/li>)/gs, '<ul>$1</ul>');
    html = html.replace(/<\/ul><ul>/g, '');

    return html;
  };

  return (
    <div className="glass card" style={{ marginTop: 20 }}>
      <div className="card-header">
        <span className="card-title">📄 Advisory Report</span>
        <span className="card-badge badge-bullish">
          {data.status === 'completed' ? '✓ Generated' : data.status}
        </span>
      </div>
      <div
        className="report-viewer"
        dangerouslySetInnerHTML={{ __html: renderMarkdown(report) }}
      />
      {data.total_duration_ms && (
        <div style={{ padding: '12px 24px', borderTop: '1px solid var(--border)', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Generated in {(data.total_duration_ms / 1000).toFixed(1)}s •
          Agents: {(data.execution_summary?.agents_involved || []).join(', ') || 'N/A'}
        </div>
      )}
    </div>
  );
}
