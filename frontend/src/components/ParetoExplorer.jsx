import React, { useEffect, useMemo, useState } from 'react';
import {
  BarChart3,
  CheckCircle2,
  Download,
  Filter,
  LayoutDashboard,
  Map,
  Plus,
  RefreshCw,
  Truck,
  X,
} from 'lucide-react';
import {
  CartesianGrid,
  Cell,
  ReferenceLine,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

const ALGORITHMS = ['Hybrid QPSO', 'Plain QPSO', 'Classical'];
const BASELINE = { distance_km: 18.1, time_min: 78.2 };
const POINT_COLORS = ['#3020ad', '#168a7a', '#de7b27', '#b64070', '#3976bd', '#6f52a0'];
const MOCK_POINTS = [
  [54.6, 12.4, 253.2, 2.57, 1024, 99.8, 'Hybrid QPSO'],
  [57.1, 11.2, 241.6, 2.48, 968, 99.3, 'Hybrid QPSO'],
  [60.4, 10.4, 236.1, 2.39, 912, 98.9, 'Hybrid QPSO'],
  [63.8, 9.5, 228.4, 2.30, 856, 98.6, 'Plain QPSO'],
  [66.2, 8.7, 219.7, 2.18, 804, 98.1, 'Plain QPSO'],
  [69.7, 8.1, 210.3, 2.07, 752, 97.7, 'Plain QPSO'],
  [72.5, 7.5, 202.8, 1.96, 702, 97.2, 'Classical'],
  [75.1, 6.9, 195.4, 1.86, 648, 96.8, 'Classical'],
  [77.4, 6.4, 189.2, 1.78, 604, 96.2, 'Classical'],
  [80.1, 5.9, 182.7, 1.69, 566, 95.7, 'Classical'],
].map(([time_min, distance_km, congestion, emissions_co2_kg, quantum_iterations, confidence, algorithm], index) => ({
  id: `Q-OPT-8842-${String.fromCharCode(65 + index)}`,
  time_min,
  distance_km,
  congestion,
  emissions_co2_kg,
  quantum_iterations,
  confidence,
  algorithm,
}));
const FLEET = [78, 64, 83, 71, 91, 56, 74, 68, 87].map((utilization, index) => ({
  vehicle: `Vehicle ${index}`,
  utilization,
  driver: index === 4 ? 'Assigning' : 'On route',
  level: [82, 66, 91, 74, 58, 88, 63, 79, 46][index],
}));

export default function ParetoExplorer({ onApplyScenario }) {
  const [points, setPoints] = useState(MOCK_POINTS);
  const [activeWorkspaceView, setActiveWorkspaceView] = useState('analytics');
  const [selectedTradeOffPoint, setSelectedTradeOffPoint] = useState(MOCK_POINTS[0]);
  const [showFilterModal, setShowFilterModal] = useState(false);
  const [showBaselineOverlay, setShowBaselineOverlay] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [toast, setToast] = useState('');
  const [filters, setFilters] = useState({ maxTime: 85, maxDistance: 20, algorithms: ALGORITHMS });

  const filteredPoints = useMemo(() => points.filter((point) => (
    point.time_min <= filters.maxTime &&
    point.distance_km <= filters.maxDistance &&
    filters.algorithms.includes(point.algorithm)
  )), [filters, points]);

  useEffect(() => {
    if (!filteredPoints.some((point) => point.id === selectedTradeOffPoint?.id)) {
      setSelectedTradeOffPoint(filteredPoints[0] || null);
    }
  }, [filteredPoints, selectedTradeOffPoint]);

  const handleRefresh = () => {
    setIsRefreshing(true);
    window.setTimeout(() => {
      setPoints([...MOCK_POINTS].sort(() => Math.random() - 0.5));
      setIsRefreshing(false);
    }, 500);
  };

  const handleExportData = () => {
    const exportRows = filteredPoints.map((point) => ({
      id: point.id,
      travel_time_min: point.time_min,
      distance_km: point.distance_km,
      congestion_score: point.congestion,
      co2_kg: point.emissions_co2_kg,
      convergence_confidence: point.confidence,
    }));
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([JSON.stringify(exportRows, null, 2)], { type: 'application/json' }));
    link.download = 'pareto-frontier.json';
    link.click();
    URL.revokeObjectURL(link.href);
  };

  const handleApply = () => {
    if (!selectedTradeOffPoint) return;
    const algorithm = selectedTradeOffPoint.algorithm === 'Classical'
      ? 'Dijkstra Nearest-Neighbor'
      : selectedTradeOffPoint.algorithm === 'Plain QPSO'
        ? 'Quantum-Inspired PSO (QPSO)'
        : 'Hybrid QPSO + Exact-Cluster';
    onApplyScenario({ algorithm, priorityWeight: 0.85, distanceSensitivity: 1.2 });
    setToast(`Configuration ${selectedTradeOffPoint.id} applied to active dispatch!`);
    window.setTimeout(() => setToast(''), 3200);
  };

  const toggleAlgorithm = (algorithm) => setFilters((current) => ({
    ...current,
    algorithms: current.algorithms.includes(algorithm)
      ? current.algorithms.filter((item) => item !== algorithm)
      : [...current.algorithms, algorithm],
  }));

  return (
    <div className="pareto-layout interactive-pareto">
      <aside className="pareto-side">
        <div className="workspace"><b>Main Workspace</b><br /><small>Enterprise Tier</small></div>
        {[[LayoutDashboard, 'Overview', 'overview'], [Map, 'Live Tracking', 'live-tracking'], [Truck, 'Fleet Status', 'fleet-status'], [BarChart3, 'Analytics', 'analytics']].map(([Icon, label, view]) => (
          <button className={`nav-item ${activeWorkspaceView === view ? 'active' : ''}`} key={view} onClick={() => setActiveWorkspaceView(view)}><Icon size={16} /><span>{label}</span></button>
        ))}
        <button className="outline-btn workspace-new"><Plus size={15} /> New Scenario</button>
      </aside>

      <main className="pareto-main">
        <div className="page-head"><div><h2>Pareto Explorer</h2><p>Multi-objective route optimization</p></div><div className="button-row"><button className="outline-btn" onClick={() => setShowFilterModal((value) => !value)}><Filter size={14} /> Filter</button><button className="outline-btn" onClick={handleExportData}><Download size={14} /> Export</button><button className="primary-btn" onClick={handleRefresh} disabled={isRefreshing}>{isRefreshing && <RefreshCw className="spin" size={14} />} Refresh</button></div></div>
        {showFilterModal && <div className="pareto-filter"><div className="filter-head"><strong>Filter solution space</strong><button onClick={() => setShowFilterModal(false)} aria-label="Close filter"><X size={15} /></button></div><label>Max travel time <b>{filters.maxTime} min</b><input type="range" min="55" max="90" value={filters.maxTime} onChange={(event) => setFilters({ ...filters, maxTime: Number(event.target.value) })} /></label><label>Max distance <b>{filters.maxDistance} km</b><input type="range" min="7" max="20" step=".5" value={filters.maxDistance} onChange={(event) => setFilters({ ...filters, maxDistance: Number(event.target.value) })} /></label><div className="filter-options"><span>Algorithm source</span>{ALGORITHMS.map((algorithm) => <label key={algorithm}><input type="checkbox" checked={filters.algorithms.includes(algorithm)} onChange={() => toggleAlgorithm(algorithm)} />{algorithm}</label>)}</div></div>}

        {activeWorkspaceView === 'analytics' && <section className="card chart-card"><div className="results-section-head"><div><h3>Trade-off Solution Space</h3><p>{filteredPoints.length} non-dominated solutions shown</p></div>{showBaselineOverlay && <span className="baseline-chip">Baseline shown</span>}</div><div className="pareto-chart"><ResponsiveContainer><ScatterChart margin={{ top: 18, right: 18, bottom: 20, left: 8 }}><CartesianGrid stroke="#dfe2ee" /><XAxis type="number" dataKey="distance_km" name="Distance" unit=" km" stroke="#687083" /><YAxis type="number" dataKey="time_min" name="Travel time" unit=" min" stroke="#687083" /><Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ background: '#fff', border: '1px solid #cbd5e1' }} /><ReferenceLine x={BASELINE.distance_km} stroke="#6b7280" strokeDasharray="6 5" opacity={showBaselineOverlay ? 1 : 0} /><ReferenceLine y={BASELINE.time_min} stroke="#6b7280" strokeDasharray="6 5" opacity={showBaselineOverlay ? 1 : 0} /><Scatter data={filteredPoints} onClick={(event) => event?.payload && setSelectedTradeOffPoint(event.payload)}>{filteredPoints.map((point, index) => <Cell key={point.id} fill={selectedTradeOffPoint?.id === point.id ? '#f97316' : POINT_COLORS[index % POINT_COLORS.length]} stroke="#202537" strokeWidth={2} />)}</Scatter></ScatterChart></ResponsiveContainer></div></section>}
        {activeWorkspaceView === 'overview' && <div className="workspace-view-grid"><div className="workspace-kpi"><span>Active routes</span><strong>9</strong><small>All dispatch lanes live</small></div><div className="workspace-kpi"><span>Operational cost index</span><strong>69.4</strong><small>12.8% below baseline</small></div><div className="workspace-kpi"><span>Fleet health</span><strong>96%</strong><small>8 of 9 vehicles on route</small></div></div>}
        {activeWorkspaceView === 'live-tracking' && <div className="tracking-view"><div className="tracking-map"><div className="tracking-grid">{FLEET.map((row, index) => <i key={row.vehicle} style={{ left: `${18 + (index * 9) % 72}%`, top: `${20 + (index * 17) % 64}%`, background: POINT_COLORS[index % POINT_COLORS.length] }} />)}</div><span className="tracking-label">Bengaluru delivery zone</span></div><div className="tracking-list">{FLEET.slice(0, 5).map((row, index) => <div key={row.vehicle}><i style={{ background: POINT_COLORS[index % POINT_COLORS.length] }} /><span><b>{row.vehicle}</b><small>En route · {12 + index * 3} min ETA</small></span><strong>GPS live</strong></div>)}</div></div>}
        {activeWorkspaceView === 'fleet-status' && <div className="fleet-table-wrap"><table className="fleet-table"><thead><tr><th>Vehicle</th><th>Capacity utilization</th><th>Driver status</th><th>Battery / fuel</th></tr></thead><tbody>{FLEET.map((row) => <tr key={row.vehicle}><td><b>{row.vehicle}</b></td><td><div className="utilization"><span style={{ width: `${row.utilization}%` }} /><b>{row.utilization}%</b></div></td><td><span className={row.driver === 'On route' ? 'fleet-live' : 'fleet-warn'}>{row.driver}</span></td><td>{row.level}%</td></tr>)}</tbody></table></div>}
      </main>

      <aside className="pareto-detail"><h3 className="card-title">SELECTED TRADE-OFF POINT</h3>{selectedTradeOffPoint ? <><div className="insight">Configuration ID <b className="mono">{selectedTradeOffPoint.id}</b></div><div className="metrics"><div className="metric"><small>Travel Time</small><strong>{selectedTradeOffPoint.time_min.toFixed(1)} min</strong></div><div className="metric"><small>Distance</small><strong>{selectedTradeOffPoint.distance_km.toFixed(1)} km</strong></div><div className="metric"><small>Congestion</small><strong>{selectedTradeOffPoint.congestion.toFixed(2)}</strong></div><div className="metric"><small>CO2 Emission</small><strong>{selectedTradeOffPoint.emissions_co2_kg.toFixed(2)} kg</strong></div></div><div className="algorithm-metrics"><span>Algorithm source <b>{selectedTradeOffPoint.algorithm}</b></span><span>Quantum iterations <b>{selectedTradeOffPoint.quantum_iterations.toLocaleString()}</b></span><span>Convergence confidence <b>{selectedTradeOffPoint.confidence}%</b></span></div>{showBaselineOverlay && <div className="comparison-badge">+23.6 min saved vs. baseline (-30.2%)</div>}</> : <p className="muted">No points match the current filters.</p>}<div className="detail-actions"><button className="primary-btn" onClick={handleApply} disabled={!selectedTradeOffPoint}><CheckCircle2 size={14} /> Apply Configuration</button><button className={`outline-btn ${showBaselineOverlay ? 'active-action' : ''}`} onClick={() => setShowBaselineOverlay((value) => !value)}>↔ {showBaselineOverlay ? 'Hide Baseline' : 'Compare Baseline'}</button></div></aside>
      {toast && <div className="pareto-toast"><CheckCircle2 size={16} />{toast}</div>}
    </div>
  );
}
