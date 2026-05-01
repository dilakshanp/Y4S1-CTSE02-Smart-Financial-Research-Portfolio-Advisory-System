import { useState, useEffect, useCallback } from 'react';
import './index.css';
import { submitResearch, streamResearch, getSampleQueries, healthCheck } from './api';
import QueryInput from './components/QueryInput';
import AgentPipeline from './components/AgentPipeline';
import MarketDataCard from './components/MarketDataCard';
import SentimentGauge from './components/SentimentGauge';
import RiskMatrix from './components/RiskMatrix';
import ReportViewer from './components/ReportViewer';
import LogStream from './components/LogStream';
import SessionHistory from './components/SessionHistory';

const AGENTS = ['Coordinator', 'Market Analyst', 'Risk Specialist', 'Portfolio Advisor'];

export default function App() {
  const [health, setHealth] = useState(null);
  const [samples, setSamples] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pipelineStatus, setPipelineStatus] = useState('idle'); // idle | running | completed | failed
  const [agentStates, setAgentStates] = useState({});
  const [logs, setLogs] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    healthCheck().then(setHealth);
    getSampleQueries().then(d => setSamples(d.queries || []));
  }, []);

  const detectActiveAgent = useCallback((agentName) => {
    const lower = (agentName || '').toLowerCase();
    if (lower.includes('coordinator') || lower === 'system') return 0;
    if (lower.includes('market') || lower.includes('analyst')) return 1;
    if (lower.includes('risk')) return 2;
    if (lower.includes('portfolio') || lower.includes('advisor')) return 3;
    return -1;
  }, []);

  const handleSubmit = useCallback(async (query) => {
    setLoading(true);
    setPipelineStatus('running');
    setAgentStates({});
    setLogs([]);
    setResult(null);
    setError(null);

    try {
      const { query_id } = await submitResearch(query);

      streamResearch(query_id, (event) => {
        if (event.type === 'agent_log') {
          setLogs(prev => [...prev, event]);
          const idx = detectActiveAgent(event.data?.agent);
          if (idx >= 0) {
            setAgentStates(prev => {
              const next = { ...prev };
              // Mark all previous as completed
              for (let i = 0; i < idx; i++) next[i] = 'completed';
              next[idx] = 'active';
              return next;
            });
          }
        } else if (event.type === 'status') {
          setLogs(prev => [...prev, event]);
        } else if (event.type === 'complete') {
          setResult(event.data);
          setPipelineStatus('completed');
          setAgentStates({ 0: 'completed', 1: 'completed', 2: 'completed', 3: 'completed' });
          setLoading(false);
        } else if (event.type === 'error') {
          setError(event.data?.message || 'Pipeline failed');
          setPipelineStatus('failed');
          setLoading(false);
        } else if (event.type === 'done') {
          setLoading(false);
        }
      });
    } catch (err) {
      setError(err.message);
      setPipelineStatus('failed');
      setLoading(false);
    }
  }, [detectActiveAgent]);

  const isHealthy = health?.status === 'healthy';

  return (
    <>
      {/* Header */}
      <header className="header">
        <div className="container header-inner">
          <div className="logo">
            <span className="logo-icon">📊</span>
            <div>
              <h1>Financial Research MAS</h1>
              <span className="logo-sub">Multi-Agent System • CrewAI + Ollama</span>
            </div>
          </div>
          <div className={`health-badge ${isHealthy ? '' : 'offline'}`}>
            <span className="health-dot"></span>
            {isHealthy ? 'System Online' : 'Connecting...'}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container" style={{ flex: 1, paddingBottom: 40 }}>
        <QueryInput
          onSubmit={handleSubmit}
          loading={loading}
          samples={samples}
        />

        {pipelineStatus !== 'idle' && (
          <AgentPipeline agents={AGENTS} states={agentStates} status={pipelineStatus} />
        )}

        {error && (
          <div className="glass card" style={{ borderColor: 'var(--red)', marginBottom: 20 }}>
            <div className="card-header">
              <span className="card-title">❌ Error</span>
            </div>
            <p style={{ color: 'var(--red)', fontSize: '0.9rem' }}>{error}</p>
          </div>
        )}

        {(loading || result) && (
          <>
            <div className="results-grid">
              <MarketDataCard data={result} />
              <SentimentGauge data={result} />
              <RiskMatrix data={result} />
            </div>

            <ReportViewer data={result} loading={loading} />

            <div className="glass card" style={{ marginTop: 20 }}>
              <div className="card-header">
                <span className="card-title">🔍 Agent Activity Log</span>
                <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{logs.length} events</span>
              </div>
              <LogStream logs={logs} />
            </div>
          </>
        )}

        {pipelineStatus === 'idle' && (
          <SessionHistory />
        )}
      </main>

      <footer className="footer">
        <div className="container">
          SE4010 – CTSE Assignment 2 • Smart Financial Research MAS • SLIIT © 2026
        </div>
      </footer>
    </>
  );
}
