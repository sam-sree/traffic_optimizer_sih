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
import { CircleMarker, MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet';
import L from 'leaflet';

const ALGORITHMS = ['Hybrid QPSO', 'Plain QPSO', 'Classical'];
const BASELINE = { distance_km: 18.1, time_min: 78.2 };
const POINT_COLORS = ['#4f46e5', '#06b6d4', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6'];

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
  vehicle: `Vehicle ${index + 1}`,
  utilization,
  driver: index === 4 ? 'Assigning' : 'On route',
  level: [82, 66, 91, 74, 58, 88, 63, 79, 46][index],
}));

const TRACKING_VEHICLES = FLEET.map((vehicle, index) => ({
  ...vehicle,
  id: index,
  lat: 12.956 + (index * 0.0041) % 0.038,
  lon: 77.620 + (index * 0.0037) % 0.040,
  eta: 12 + index * 3,
}));

function TrackingMapFocus({ vehicle }) {
  const map = useMap();
  useEffect(() => {
    if (vehicle) map.flyTo([vehicle.lat, vehicle.lon], 15, { duration: 0.45 });
  }, [map, vehicle]);
  return null;
}

function vehicleIcon(vehicle, selected) {
  return L.divIcon({
    className: `vehicle-marker ${selected ? 'selected' : ''}`,
    html: `<span class="vehicle-pulse"></span><b>V${vehicle.id + 1}</b>`,
    iconSize: [42, 30],
    iconAnchor: [21, 15],
  });
}

export default function ParetoExplorer({ onApplyScenario }) {
  const [points, setPoints] = useState(MOCK_POINTS);
  const [activeWorkspaceView, setActiveWorkspaceView] = useState('analytics');
  const [selectedTradeOffPoint, setSelectedTradeOffPoint] = useState(MOCK_POINTS[0]);
  const [showFilterModal, setShowFilterModal] = useState(false);
  const [showBaselineOverlay, setShowBaselineOverlay] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [toast, setToast] = useState('');
  const [filters, setFilters] = useState({ maxTime: 85, maxDistance: 20, algorithms: ALGORITHMS });
  const [selectedVehicle, setSelectedVehicle] = useState(TRACKING_VEHICLES[0]);

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
    <div className="pareto-layout flex flex-col gap-6">
      <div className="page-head">
        <div>
          <h2>Pareto Explorer</h2>
          <p>Multi-objective trade-off analysis & solution space exploration.</p>
        </div>
        <div className="button-row flex gap-3">
          <button className="outline-btn" onClick={() => setShowFilterModal((value) => !value)}>
            <Filter size={14} /> Filter
          </button>
          <button className="outline-btn" onClick={handleExportData}>
            <Download size={14} /> Export
          </button>
          <button className="primary-btn" onClick={handleRefresh} disabled={isRefreshing}>
            {isRefreshing && <RefreshCw className="spin" size={14} />} Refresh
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Sidebar Navigation */}
        <aside className="card pareto-side lg:col-span-3 p-6 flex flex-col gap-4">
          <div className="workspace p-4 rounded-xl bg-indigo-50/80 border border-indigo-100 text-indigo-950">
            <b className="block text-sm font-bold">Main Workspace</b>
            <small className="text-indigo-600 font-semibold uppercase tracking-wider text-[10px]">Enterprise Tier</small>
          </div>

          <div className="flex flex-col gap-2">
            {[
              [LayoutDashboard, 'Overview', 'overview'],
              [Map, 'Live Tracking', 'live-tracking'],
              [Truck, 'Fleet Status', 'fleet-status'],
              [BarChart3, 'Analytics', 'analytics']
            ].map(([Icon, label, view]) => (
              <button
                className={`nav-item flex items-center gap-3 p-3 rounded-xl text-xs font-semibold text-left transition-all ${
                  activeWorkspaceView === view
                    ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
                key={view}
                onClick={() => setActiveWorkspaceView(view)}
              >
                <Icon size={16} />
                <span>{label}</span>
              </button>
            ))}
          </div>

          <button className="outline-btn mt-4 flex items-center justify-center gap-2">
            <Plus size={15} /> New Scenario
          </button>
        </aside>

        {/* Center Content View */}
        <main className="pareto-main lg:col-span-6 flex flex-col gap-6 relative">
          {showFilterModal && (
            <div className="pareto-filter absolute top-0 right-0 z-30 w-80 p-5 bg-white/95 backdrop-blur-xl rounded-2xl border border-slate-200 shadow-2xl flex flex-col gap-4">
              <div className="filter-head flex justify-between items-center pb-2 border-b border-slate-200">
                <strong className="text-slate-900 font-bold text-sm">Filter Solution Space</strong>
                <button onClick={() => setShowFilterModal(false)} aria-label="Close filter" className="text-slate-400 hover:text-slate-600">
                  <X size={16} />
                </button>
              </div>

              <div className="flex flex-col gap-2">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-slate-600">Max Travel Time</span>
                  <b className="text-indigo-600 font-mono">{filters.maxTime} min</b>
                </div>
                <input
                  type="range"
                  min="55"
                  max="90"
                  value={filters.maxTime}
                  onChange={(e) => setFilters({ ...filters, maxTime: Number(e.target.value) })}
                  className="accent-indigo-600"
                />
              </div>

              <div className="flex flex-col gap-2">
                <div className="flex justify-between text-xs font-semibold">
                  <span className="text-slate-600">Max Distance</span>
                  <b className="text-indigo-600 font-mono">{filters.maxDistance} km</b>
                </div>
                <input
                  type="range"
                  min="7"
                  max="20"
                  step=".5"
                  value={filters.maxDistance}
                  onChange={(e) => setFilters({ ...filters, maxDistance: Number(e.target.value) })}
                  className="accent-indigo-600"
                />
              </div>

              <div className="filter-options flex flex-col gap-2 pt-2 border-t border-slate-200">
                <span className="text-xs font-bold text-slate-800 uppercase tracking-wider">Algorithm Source</span>
                {ALGORITHMS.map((algorithm) => (
                  <label key={algorithm} className="flex items-center gap-2 text-xs text-slate-700 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={filters.algorithms.includes(algorithm)}
                      onChange={() => toggleAlgorithm(algorithm)}
                      className="accent-indigo-600 rounded"
                    />
                    {algorithm}
                  </label>
                ))}
              </div>
            </div>
          )}

          {activeWorkspaceView === 'analytics' && (
            <section className="card chart-card p-6 flex flex-col gap-4">
              <div className="flex justify-between items-center">
                <div>
                  <h3 className="card-title">Trade-off Solution Space</h3>
                  <p className="text-xs text-slate-500 mt-1">{filteredPoints.length} non-dominated solutions available</p>
                </div>
                {showBaselineOverlay && (
                  <span className="px-3 py-1 bg-amber-50 text-amber-700 border border-amber-200 rounded-full text-xs font-semibold">
                    Baseline Shown
                  </span>
                )}
              </div>

              <div className="pareto-chart h-[440px] mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 10 }}>
                    <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                    <XAxis type="number" dataKey="distance_km" name="Distance" unit=" km" stroke="#64748b" />
                    <YAxis type="number" dataKey="time_min" name="Travel time" unit=" min" stroke="#64748b" />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                    <ReferenceLine x={BASELINE.distance_km} stroke="#64748b" strokeDasharray="6 5" opacity={showBaselineOverlay ? 1 : 0} />
                    <ReferenceLine y={BASELINE.time_min} stroke="#64748b" strokeDasharray="6 5" opacity={showBaselineOverlay ? 1 : 0} />
                    <Scatter data={filteredPoints} onClick={(event) => event?.payload && setSelectedTradeOffPoint(event.payload)}>
                      {filteredPoints.map((point, index) => (
                        <Cell
                          key={point.id}
                          fill={selectedTradeOffPoint?.id === point.id ? '#f97316' : POINT_COLORS[index % POINT_COLORS.length]}
                          stroke="#ffffff"
                          strokeWidth={2}
                        />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </section>
          )}

          {activeWorkspaceView === 'overview' && (
            <div className="workspace-view-grid grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="stat-card">
                <span>Active Routes</span>
                <strong>9</strong>
                <small className="text-xs text-emerald-600 font-semibold mt-1 block">All dispatch lanes live</small>
              </div>
              <div className="stat-card">
                <span>Cost Index</span>
                <strong>69.4</strong>
                <small className="text-xs text-emerald-600 font-semibold mt-1 block">12.8% below baseline</small>
              </div>
              <div className="stat-card">
                <span>Fleet Health</span>
                <strong>96%</strong>
                <small className="text-xs text-indigo-600 font-semibold mt-1 block">8 of 9 vehicles on route</small>
              </div>
            </div>
          )}

          {activeWorkspaceView === 'live-tracking' && (
            <div className="tracking-view grid grid-cols-1 md:grid-cols-12 gap-4">
              <div className="tracking-map md:col-span-8 h-[420px] rounded-xl overflow-hidden border border-slate-200 relative">
                <MapContainer center={[12.9716, 77.6412]} zoom={13} scrollWheelZoom className="h-full w-full">
                  <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="&copy; OpenStreetMap contributors" />
                  <TrackingMapFocus vehicle={selectedVehicle} />
                  {TRACKING_VEHICLES.map((vehicle) => (
                    <Marker
                      key={vehicle.vehicle}
                      position={[vehicle.lat, vehicle.lon]}
                      icon={vehicleIcon(vehicle, selectedVehicle.id === vehicle.id)}
                      eventHandlers={{ click: () => setSelectedVehicle(vehicle) }}
                    >
                      <Popup>
                        {vehicle.vehicle} · GPS live<br />
                        ETA {vehicle.eta} min
                      </Popup>
                    </Marker>
                  ))}
                  <CircleMarker center={[12.9716, 77.6412]} radius={5} pathOptions={{ color: '#4f46e5', fillColor: '#4f46e5', fillOpacity: 1 }} />
                </MapContainer>
                <span className="tracking-label absolute bottom-3 left-3 bg-white/90 backdrop-blur-md px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-800 z-10">
                  Bengaluru Zone · {selectedVehicle.vehicle} selected
                </span>
              </div>
              <div className="tracking-list md:col-span-4 flex flex-col gap-2 max-h-[420px] overflow-y-auto">
                {TRACKING_VEHICLES.map((vehicle) => (
                  <button
                    className={`tracking-vehicle p-3 rounded-xl border text-left flex items-center justify-between transition-all ${
                      selectedVehicle.id === vehicle.id
                        ? 'bg-indigo-50 border-indigo-400 shadow-sm'
                        : 'bg-white border-slate-200 hover:bg-slate-50'
                    }`}
                    key={vehicle.vehicle}
                    onClick={() => setSelectedVehicle(vehicle)}
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-2.5 h-2.5 rounded-full" style={{ background: POINT_COLORS[vehicle.id % POINT_COLORS.length] }} />
                      <div>
                        <b className="block text-xs font-bold text-slate-800">{vehicle.vehicle}</b>
                        <small className="text-[10px] text-slate-500">{vehicle.eta} min ETA</small>
                      </div>
                    </div>
                    <strong className="text-[10px] uppercase font-bold text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded">GPS Live</strong>
                  </button>
                ))}
              </div>
            </div>
          )}

          {activeWorkspaceView === 'fleet-status' && (
            <div className="fleet-table-wrap card p-6">
              <table className="fleet-table w-full">
                <thead>
                  <tr>
                    <th>Vehicle</th>
                    <th>Capacity Utilization</th>
                    <th>Driver Status</th>
                    <th>Fuel Level</th>
                  </tr>
                </thead>
                <tbody>
                  {FLEET.map((row) => (
                    <tr key={row.vehicle}>
                      <td className="font-bold text-slate-800">{row.vehicle}</td>
                      <td>
                        <div className="utilization flex items-center gap-2">
                          <div className="w-24 h-2 bg-slate-200 rounded-full overflow-hidden">
                            <div className="h-full bg-indigo-600" style={{ width: `${row.utilization}%` }} />
                          </div>
                          <b className="text-xs font-mono">{row.utilization}%</b>
                        </div>
                      </td>
                      <td>
                        <span className={row.driver === 'On route' ? 'fleet-live' : 'fleet-warn'}>{row.driver}</span>
                      </td>
                      <td className="font-mono">{row.level}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </main>

        {/* Right Detail Panel */}
        <aside className="card pareto-detail lg:col-span-3 p-6 flex flex-col gap-4">
          <h3 className="card-title text-xs uppercase tracking-wider text-slate-500">SELECTED TRADE-OFF POINT</h3>
          {selectedTradeOffPoint ? (
            <>
              <div className="insight p-3 rounded-lg bg-indigo-50/80 border border-indigo-100 text-xs font-semibold text-indigo-900">
                Configuration ID <b className="font-mono text-indigo-700">{selectedTradeOffPoint.id}</b>
              </div>

              <div className="metrics grid grid-cols-2 gap-3">
                <div className="metric p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold block">Travel Time</span>
                  <strong className="text-base font-mono text-slate-900">{selectedTradeOffPoint.time_min.toFixed(1)} min</strong>
                </div>
                <div className="metric p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold block">Distance</span>
                  <strong className="text-base font-mono text-slate-900">{selectedTradeOffPoint.distance_km.toFixed(1)} km</strong>
                </div>
                <div className="metric p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold block">Congestion</span>
                  <strong className="text-base font-mono text-slate-900">{selectedTradeOffPoint.congestion.toFixed(2)}</strong>
                </div>
                <div className="metric p-3 rounded-lg bg-slate-50 border border-slate-200">
                  <span className="text-[10px] text-slate-500 uppercase font-semibold block">CO2 Emission</span>
                  <strong className="text-base font-mono text-slate-900">{selectedTradeOffPoint.emissions_co2_kg.toFixed(2)} kg</strong>
                </div>
              </div>

              <div className="algorithm-metrics p-3 rounded-lg bg-slate-50 border border-slate-200 text-xs flex flex-col gap-2">
                <div className="flex justify-between">
                  <span className="text-slate-500">Algorithm</span>
                  <b className="font-bold text-slate-800">{selectedTradeOffPoint.algorithm}</b>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Iterations</span>
                  <b className="font-mono">{selectedTradeOffPoint.quantum_iterations.toLocaleString()}</b>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Confidence</span>
                  <b className="text-emerald-600 font-bold">{selectedTradeOffPoint.confidence}%</b>
                </div>
              </div>

              {showBaselineOverlay && (
                <div className="comparison-badge p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-bold text-center">
                  +23.6 min saved vs. baseline (-30.2%)
                </div>
              )}
            </>
          ) : (
            <p className="muted text-xs text-slate-400">No points match the current filters.</p>
          )}

          <div className="detail-actions flex flex-col gap-3 mt-auto pt-4 border-t border-slate-200">
            <button className="primary-btn flex items-center justify-center gap-2" onClick={handleApply} disabled={!selectedTradeOffPoint}>
              <CheckCircle2 size={15} /> Apply Configuration
            </button>
            <button
              className={`outline-btn flex items-center justify-center gap-2 ${showBaselineOverlay ? 'bg-slate-100 font-bold' : ''}`}
              onClick={() => setShowBaselineOverlay((value) => !value)}
            >
              ↔ {showBaselineOverlay ? 'Hide Baseline' : 'Compare Baseline'}
            </button>
          </div>
        </aside>
      </div>

      {toast && (
        <div className="pareto-toast fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 bg-emerald-600 text-white rounded-xl shadow-xl text-sm font-semibold">
          <CheckCircle2 size={16} /> {toast}
        </div>
      )}
    </div>
  );
}
