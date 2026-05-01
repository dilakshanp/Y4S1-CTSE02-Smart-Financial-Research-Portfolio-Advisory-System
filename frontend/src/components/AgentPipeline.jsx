const ICONS = ['🎯', '📊', '⚠️', '💼'];

export default function AgentPipeline({ agents, states, status }) {
  return (
    <div className="pipeline">
      {agents.map((name, i) => {
        const state = states[i] || (status === 'completed' ? 'completed' : 'pending');
        return (
          <div key={i} style={{ display: 'flex', alignItems: 'center' }}>
            {i > 0 && (
              <span className={`pipeline-arrow ${state === 'active' || state === 'completed' ? 'active' : ''}`}>
                ▸
              </span>
            )}
            <div className={`pipeline-step ${state}`}>
              <span className="step-icon">{ICONS[i]}</span>
              <span className="step-label">{name}</span>
              <span className="step-status">
                {state === 'active' && <><span className="spinner" style={{ width: 12, height: 12 }} /> Working...</>}
                {state === 'completed' && '✓ Done'}
                {state === 'failed' && '✗ Failed'}
                {state === 'pending' && 'Waiting'}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
