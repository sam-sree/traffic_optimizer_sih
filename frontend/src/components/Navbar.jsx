import React from 'react';
import { Activity, BarChart3, Boxes, CircleHelp, Gauge, GitFork, Map, UserRound } from 'lucide-react';

const tabs = [
  ['map', 'Route Visualizer', Map],
  ['results', 'Optimization Runs', BarChart3],
  ['pareto', 'Pareto Explorer', GitFork],
  ['convergence', 'Convergence', Activity],
  ['reoptimize', 'Dynamic Re-Opt', Gauge]
];

export default function Navbar({ activeTab, setActiveTab, connected }) {
  return (
    <>
      <header className="topbar">
        <div className="brand"><div className="brand-mark"><Boxes size={18} /></div><div><h1>QuantumRoute</h1><span>Enterprise Logistics</span></div></div>
        <nav className="top-links" aria-label="Workspace navigation">
          {tabs.map(([id, label]) => <button key={id} onClick={() => setActiveTab(id)} className={activeTab === id ? 'active' : ''}>{label}</button>)}
        </nav>
        <div className="top-actions">
          <span className={`connection-badge ${connected ? 'connected' : 'disconnected'}`} role="status">
            <span className="connection-dot" />{connected ? 'Backend Connected (Port 8000)' : 'Backend Disconnected'}
          </span>
          <CircleHelp size={18} /><UserRound size={18} />
        </div>
      </header>
    </>
  );
}
