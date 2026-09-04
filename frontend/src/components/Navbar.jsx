import React, { useEffect } from 'react';
import { Activity, BarChart3, Boxes, CircleHelp, Gauge, GitFork, Map, Server, UserRound } from 'lucide-react';

const tabs = [
  ['map', 'Route Visualizer', Map],
  ['results', 'Optimization Runs', BarChart3],
  ['pareto', 'Pareto Explorer', GitFork],
  ['convergence', 'Convergence', Activity],
  ['reoptimize', 'Dynamic Re-Opt', Gauge]
];

const TAB_DESCRIPTIONS = {
  map: 'Route Visualizer: Configure fleet constraints, delivery nodes, and algorithm parameters to solve & animate vehicle dispatch routes.',
  results: 'Optimization Runs: Inspect detailed solution metrics, node delivery sequences, and export dispatch CSV data.',
  pareto: 'Pareto Explorer: Explore multi-objective trade-offs between delivery route time, distance, emissions, and cost.',
  convergence: 'Convergence: Track algorithm optimization convergence curves and iteration cost improvements.',
  reoptimize: 'Dynamic Re-Opt: Inject live traffic incidents or road closures and trigger dynamic real-time fleet re-routing.',
  benchmarks: 'Benchmark Summary: Compare hybrid QPSO performance against classical solvers (ACO, GA, OR-Tools, Dijkstra).'
};

export default function Navbar({ activeTab, setActiveTab, connected }) {
  // Apply theme class to body based on active tab for per-tab color schemes
  useEffect(() => {
    const themeClass = `theme-${activeTab}`;
    document.body.classList.remove(...Array.from(document.body.classList).filter(cls => cls.startsWith('theme-')));
    document.body.classList.add(themeClass);
  }, [activeTab]);

  const currentHelpText = TAB_DESCRIPTIONS[activeTab] || 'Explore enterprise route optimization tools and algorithms.';


  return (
    <header className="topbar">
      <div className="brand">
        <div className="brand-mark">
          <Boxes size={18} />
        </div>
        <div>
          <h1>QuantumRoute</h1>
          <span className="brand-sub">
            Enterprise Logistics
            <span className={`inline-dot ${connected ? 'online' : 'offline'}`} />
          </span>
        </div>
      </div>

      <nav className="top-links" aria-label="Workspace navigation">
        {tabs.map(([id, label]) => (
          <button
            key={id}
            onClick={() => setActiveTab(id)}
            className={activeTab === id ? 'active' : ''}
          >
            {label}
          </button>
        ))}
      </nav>

      <div className="top-actions">
        {/* Sleek Server Status Icon with Hover Tooltip Card */}
        <div className="nav-tooltip-wrapper">
          <button className={`icon-btn server-btn ${connected ? 'is-connected' : 'is-disconnected'}`} aria-label="Server Status">
            <Server size={18} />
            <span className={`server-status-dot ${connected ? 'online' : 'offline'}`} />
          </button>
          <div className="nav-tooltip-card server-card">
            <div className="server-card-head">
              <span className={`status-indicator-dot ${connected ? 'online' : 'offline'}`} />
              <strong>{connected ? 'API Online' : 'API Offline'}</strong>
            </div>
            <p>{connected ? 'FastAPI Backend running on Port 8000' : 'Unable to connect to FastAPI backend service'}</p>
          </div>
        </div>

        {/* Tab Help Tooltip Icon */}
        <div className="nav-tooltip-wrapper">
          <button className="icon-btn" aria-label="Tab Information">
            <CircleHelp size={18} />
          </button>
          <div className="nav-tooltip-card help-card">
            <strong>Active Tab Info</strong>
            <p>{currentHelpText}</p>
          </div>
        </div>

        {/* User Profile Tooltip Icon */}
        <div className="nav-tooltip-wrapper">
          <button className="icon-btn" aria-label="User Profile">
            <UserRound size={18} />
          </button>
          <div className="nav-tooltip-card user-card">
            <span>User</span>
          </div>
        </div>
      </div>
    </header>
  );
}
