import React, { useState } from 'react';
import { runReoptimize } from '../api';
import { Zap } from 'lucide-react';

export default function ReoptimizationPanel() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleTriggerDisruption = async () => {
    setLoading(true);
    try {
      const res = await runReoptimize({ severity: 5.5 });
      setData(res);
    } catch (err) {
      console.error("Re-optimization failed", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ margin: '0 20px', height: 'calc(100vh - 120px)', display: 'grid', gridTemplateColumns: '380px 1fr', gap: '20px' }}>
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
        <h2 style={{ fontSize: '1.1rem', color: '#fcf8f8', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Zap size={18} color="#f97316" /> Dynamic Traffic Incident Simulation
        </h2>
        <p style={{ fontSize: '0.85rem', color: '#a89a9c' }}>
          Simulates dynamic traffic disruptions (5.5x travel time delay) mid-route to evaluate local QAOA cluster re-solving vs full-network re-computation.
        </p>

        <button
          onClick={handleTriggerDisruption}
          disabled={loading}
          className="glow-btn"
          style={{ background: 'linear-gradient(135deg, #ef4444, #f97316)', marginTop: '12px' }}
        >
          {loading ? 'Simulating Traffic Disruption...' : 'Inject Mid-Route Traffic Incident'}
        </button>
      </div>

      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '1.1rem', color: '#f97316', marginBottom: '16px' }}>"What Changed" Re-Optimization Metrics</h3>
        {data ? (
          <div style={{ display: 'grid', gridTemplateRows: 'auto 1fr', gap: '20px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
              <div style={{ background: '#180d10', padding: '16px', borderRadius: '10px', border: '1px solid #3f1922' }}>
                <span style={{ fontSize: '0.8rem', color: '#a89a9c' }}>Full Re-Solve Time</span>
                <p style={{ fontSize: '1.4rem', fontWeight: 700, color: '#ef4444' }}>{data.full_resolve_time_ms.toFixed(1)} ms</p>
              </div>
              <div style={{ background: '#180d10', padding: '16px', borderRadius: '10px', border: '1px solid #3f1922' }}>
                <span style={{ fontSize: '0.8rem', color: '#a89a9c' }}>Local QAOA Re-Solve</span>
                <p style={{ fontSize: '1.4rem', fontWeight: 700, color: '#f97316' }}>{data.local_reopt_time_ms.toFixed(1)} ms</p>
              </div>
              <div style={{ background: '#180d10', padding: '16px', borderRadius: '10px', border: '1px solid #3f1922' }}>
                <span style={{ fontSize: '0.8rem', color: '#a89a9c' }}>Scalability Speedup</span>
                <p style={{ fontSize: '1.4rem', fontWeight: 700, color: '#f59e0b' }}>{data.speedup_factor.toFixed(2)}x Faster</p>
              </div>
            </div>

            <div style={{ background: '#180d10', padding: '20px', borderRadius: '10px', border: '1px solid #3f1922' }}>
              <h4 style={{ color: '#fcf8f8', fontSize: '0.95rem', marginBottom: '12px' }}>Cluster Re-Solve Isolation Summary</h4>
              <p style={{ color: '#fcf8f8', fontSize: '0.88rem', marginBottom: '8px' }}>
                • Affected Clusters Re-Solved Locally: <strong style={{ color: '#f97316' }}>{data.affected_clusters_count} of {data.total_clusters_count}</strong>
              </p>
              <p style={{ color: '#fcf8f8', fontSize: '0.88rem' }}>
                • Re-Optimized Total Travel Time: <strong>{data.reoptimized_time_min.toFixed(1)} minutes</strong>
              </p>
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '80%', color: '#a89a9c' }}>
            Click "Inject Mid-Route Traffic Incident" to trigger real-time re-optimization.
          </div>
        )}
      </div>
    </div>
  );
}
