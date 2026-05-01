import { useState } from 'react';

export default function QueryInput({ onSubmit, loading, samples }) {
  const [query, setQuery] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !loading) onSubmit(query.trim());
  };

  return (
    <section className="query-section">
      <form onSubmit={handleSubmit} className="query-box">
        <input
          id="research-query-input"
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter your research query (e.g., Analyze AAPL, MSFT, GOOGL for a moderate-risk portfolio)"
          disabled={loading}
        />
        <button id="submit-research-btn" type="submit" className="btn-primary" disabled={loading || !query.trim()}>
          {loading ? <><span className="spinner" /> Analyzing...</> : '🔬 Analyze'}
        </button>
      </form>
      {samples.length > 0 && (
        <div className="sample-queries">
          {samples.map((s, i) => (
            <button key={i} className="sample-chip" onClick={() => { setQuery(s); }} disabled={loading}>
              {s.length > 45 ? s.slice(0, 45) + '…' : s}
            </button>
          ))}
        </div>
      )}
    </section>
  );
}
