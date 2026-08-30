import React from 'react';
import { Cpu, Map, TrendingDown, Layers, Zap, BarChart3 } from 'lucide-react';

export default function Navbar({ activeTab, setActiveTab, networkSummary }) {
  const tabs = [
    { id: 'map', label: 'Route Visualizer', icon: Map },
    { id: 'convergence', label: 'Convergence', icon: TrendingDown },
    { id: 'pareto', label: 'Pareto Explorer', icon: Layers },
    { id: 'reoptimize', label: 'Dynamic Re-Opt', icon: Zap },
    { id: 'benchmarks', label: 'Benchmark Report', icon: BarChart3 },
  ];

  return (
    <header className="glass-panel" style={{ margin: '16px 20px', padding: '14px 24px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{ background: 'linear-gradient(135deg, #ef4444, #f97316)', padding: '10px', borderRadius: '10px', display: 'flex', boxShadow: '0 0 15px rgba(239, 68, 68, 0.4)' }}>
          <Cpu size={24} color="#ffffff" />
        </div>
        <div>
          <h1 className="gradient-text" style={{ fontSize: '1.4rem', fontWeight: 800, margin: 0 }}>QuantumRoute</h1>
          <p style={{ fontSize: '0.78rem', color: '#a89a9c', margin: 0 }}>Hybrid Classical-Quantum VRP Optimization Platform</p>
        </div>
      </div>

      <nav style={{ display: 'flex', gap: '8px' }}>
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '9px 16px',
                borderRadius: '8px',
                border: 'none',
                cursor: 'pointer',
                fontSize: '0.88rem',
                fontWeight: 600,
                transition: 'all 0.2s ease',
                background: isActive ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.25), rgba(249, 115, 22, 0.25))' : 'transparent',
                color: isActive ? '#f97316' : '#a89a9c',
                boxShadow: isActive ? 'inset 0 0 0 1px rgba(249, 115, 22, 0.5)' : 'none'
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </nav>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', background: 'rgba(24, 13, 16, 0.8)', padding: '6px 14px', borderRadius: '20px', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
        <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#ef4444', boxShadow: '0 0 8px #ef4444' }} />
        <span style={{ fontSize: '0.8rem', color: '#fcf8f8' }}>
          Bengaluru Grid • Avg Speed: <strong>{networkSummary?.avg_speed_kmh?.toFixed(1) || '13.6'} km/h</strong>
        </span>
      </div>
    </header>
  );
}
