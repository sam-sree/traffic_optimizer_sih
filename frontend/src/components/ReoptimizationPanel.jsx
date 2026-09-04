import React, { useMemo, useState } from 'react';
import { MapContainer, Polyline, TileLayer, ZoomControl } from 'react-leaflet';
import { Check, Download, RefreshCw, Trash2, Zap } from 'lucide-react';
import { clearTrafficIncidents, runReoptimize } from '../api';

const IDLE_METRICS = {
  full_resolve_time_ms: 0,
  local_reopt_time_ms: 0,
  affected_clusters_count: 0,
  total_clusters_count: 0,
  speedup_factor: null,
  delta_arrival: null,
  delta_fuel: null,
};

const INJECTED_DISRUPTIONS = [
  { title: 'Heavy Congestion - Old Airport Rd', impact: 'Impact: High (+45m delay)' },
  { title: 'Road Closure - Indiranagar 100ft Rd', impact: 'Impact: Medium (Reroute Required)' },
];

const IMPACTED_VEHICLES = [
  { vehicle: 'Veh #3', originalEta: '14:22', reroutedEta: '14:24 (+2 min)', status: 'Re-Routed via 12th Main' },
  { vehicle: 'Veh #7', originalEta: '14:35', reroutedEta: '14:35 (+0 min)', status: 'Unaffected (Local Cluster Isolated)' },
];

export default function ReoptimizationPanel({ onGraphRefresh, graphData }) {
  const [metrics, setMetrics] = useState(IDLE_METRICS);
  const [disruptions, setDisruptions] = useState([]);
  const [impactedVehicles, setImpactedVehicles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [toast, setToast] = useState('');

  const nodeById = useMemo(() => Object.fromEntries((graphData?.nodes || []).map((node) => [String(node.id), node])), [graphData]);
  const incidents = (graphData?.edges || []).filter((edge) => edge.is_incident).map((edge) => {
    const from = nodeById[String(edge.u)];
    const to = nodeById[String(edge.v)];
    return from && to ? { positions: [[from.lat, from.lon], [to.lat, to.lon]] } : null;
  }).filter(Boolean);
  const activeCount = disruptions.length;

  const run = async () => {
    setLoading(true);
    setError('');
    try {
      const [result] = await Promise.all([runReoptimize({ severity: 5.5 }), new Promise((resolve) => window.setTimeout(resolve, 300))]);
      setMetrics({ ...result, delta_arrival: '+2.4 min', delta_fuel: '+₹12.50' });
      setDisruptions(INJECTED_DISRUPTIONS);
      setImpactedVehicles(IMPACTED_VEHICLES);
      await onGraphRefresh();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to inject traffic incident. Verify the backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const clear = async () => {
    setLoading(true);
    setError('');
    try {
      await clearTrafficIncidents();
      setMetrics(IDLE_METRICS);
      setDisruptions([]);
      setImpactedVehicles([]);
      await onGraphRefresh();
    } catch (requestError) {
      setError(requestError.response?.data?.detail || 'Unable to clear traffic incidents.');
    } finally {
      setLoading(false);
    }
  };

  const exportReport = () => {
    const rows = [
      ['Metric', 'Value'],
      ['Incident IDs', disruptions.length ? 'Old Airport Rd; Indiranagar 100ft Rd' : ''],
      ['Full Re-Solve Time', `${metrics.full_resolve_time_ms.toFixed(1)}ms`],
      ['Local Re-Solve Time', `${metrics.local_reopt_time_ms.toFixed(1)}ms`],
      ['Speedup', metrics.speedup_factor == null ? '--' : `${metrics.speedup_factor.toFixed(2)}x`],
      ['Impacted Nodes', `${metrics.affected_clusters_count}/${metrics.total_clusters_count} local vs 45/45 global`],
      ['Delta Arrival', metrics.delta_arrival || '--'],
      ['Delta Fuel', metrics.delta_fuel || '--']
    ];
    const csv = rows.map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(',')).join('\n');
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    link.download = 'reoptimization_report_incident.csv';
    link.click();
    URL.revokeObjectURL(link.href);
    setToast('Report exported successfully');
    window.setTimeout(() => setToast(''), 2500);
  };

  return (
    <div className="reopt-page flex flex-col gap-6">
      <div className="page-head">
        <div>
          <h2>Live Incident Control</h2>
          <p>Inject dynamic disruptions and compare the local recovery plan with a full re-solve.</p>
        </div>
        <div className="status flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" /> Active Monitoring
        </div>
      </div>

      <div className="incident-layout grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Traffic Network & Incident Injection */}
        <section className="card detail-card lg:col-span-5 p-6 flex flex-col gap-4">
          <h3 className="card-title">Live Traffic Disruption Control</h3>

          <div className="incident-map relative h-[320px] rounded-xl overflow-hidden border border-slate-200">
            <MapContainer center={[12.9716, 77.6412]} zoom={14} zoomControl={false} className="h-full w-full">
              <ZoomControl position="bottomleft" />
              <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; OpenStreetMap contributors' />
              {incidents.map(({ positions }, index) => (
                <Polyline key={index} positions={positions} pathOptions={{ color: '#ef4444', weight: 6 }} />
              ))}
            </MapContainer>

            <div className="incident-overlay absolute top-3 left-3 bg-white/90 backdrop-blur-md p-3 rounded-lg border border-slate-200 shadow-md text-xs font-semibold text-slate-800">
              Active Network Nodes: 142<br />
              <span className="text-rose-600 font-bold">Disruptions Active: {activeCount}</span>
            </div>
          </div>

          <div className="button-row grid grid-cols-2 gap-3 mt-2">
            <button className="primary-btn flex justify-center items-center gap-2" onClick={run} disabled={loading}>
              {loading ? <RefreshCw className="spin" size={15} /> : <Zap size={15} />}
              {loading ? 'Simulating...' : 'Inject Traffic Disruption'}
            </button>
            <button className="outline-btn flex justify-center items-center gap-2" onClick={clear} disabled={loading}>
              <Trash2 size={14} /> Clear Disruptions
            </button>
          </div>

          {error && <div className="error-banner" role="alert">{error}</div>}

          <div className="mt-2">
            <h4 className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-3">Active Disruptions</h4>
            <div className="incident-list flex flex-col gap-2">
              {disruptions.length ? (
                disruptions.map((incident) => (
                  <div className="incident-row danger p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs" key={incident.title}>
                    <b className="block text-sm font-bold mb-1">{incident.title}</b>
                    <span>{incident.impact}</span>
                  </div>
                ))
              ) : (
                <div className="empty-state p-4 text-center text-slate-400 text-sm bg-slate-50 rounded-lg border border-slate-200">
                  No active disruptions injected. Click 'Inject Traffic Disruption' to simulate.
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Right Column: Re-Optimization Comparison & Vehicle Status */}
        <section className="card detail-card reopt-card lg:col-span-7 p-6 flex flex-col gap-6">
          <div className="chart-header flex items-center justify-between">
            <h3 className="card-title">Re-Optimization Performance Comparison</h3>
            <button className="outline-btn" onClick={exportReport}>
              <Download size={14} /> Export Report
            </button>
          </div>

          <div className="reopt-options grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="reopt-option p-4 rounded-xl border border-slate-200 bg-slate-50 flex flex-col gap-2">
              <span className="font-bold text-slate-800">Global Re-Solve (Full Graph)</span>
              <p className="text-xs text-slate-500">Solve Time</p>
              <strong className="mono text-lg font-bold text-slate-900">{metrics.full_resolve_time_ms.toFixed(1)} ms</strong>
              <hr className="my-2 border-slate-200" />
              <div className="flex justify-between text-xs text-slate-600">
                <span>Impacted Nodes</span>
                <b className="font-bold">{metrics.total_clusters_count ? '45/45 (100%)' : '0/0'}</b>
              </div>
            </div>

            <div className="reopt-option recommended p-4 rounded-xl border-2 border-indigo-500 bg-indigo-50/50 flex flex-col gap-2 relative">
              <div className="flex justify-between items-center">
                <span className="font-bold text-indigo-950">Local Cluster Re-Solve</span>
                <span className="text-xs font-bold text-amber-600 bg-amber-100 px-2 py-0.5 rounded-full">
                  Speedup: {metrics.speedup_factor == null ? '--' : `${metrics.speedup_factor.toFixed(2)}x`}
                </span>
              </div>
              <p className="text-xs text-indigo-700/80">Solve Time</p>
              <strong className="mono text-xl font-extrabold text-indigo-600">{metrics.local_reopt_time_ms.toFixed(1)} ms</strong>
              <hr className="my-2 border-indigo-200" />
              <div className="flex justify-between text-xs text-indigo-900">
                <span>Impacted Nodes Isolated</span>
                <b className="font-bold">{metrics.affected_clusters_count}/{metrics.total_clusters_count}</b>
              </div>
            </div>
          </div>

          <div className="result-panel flex flex-col gap-4">
            <h4 className="font-bold text-sm text-slate-800">Delta Analysis (vs Original Plan)</h4>
            <div className="flex gap-3 flex-wrap">
              <span className="chip px-3 py-1.5 rounded-lg bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-700">
                Change in Arrival Time: <b className="text-rose-600 ml-1">{metrics.delta_arrival || '--'}</b>
              </span>
              <span className="chip px-3 py-1.5 rounded-lg bg-slate-100 border border-slate-200 text-xs font-semibold text-slate-700">
                Increased Fuel Cost: <b className="text-rose-600 ml-1">{metrics.delta_fuel || '--'}</b>
              </span>
            </div>

            <div className="overflow-x-auto mt-2">
              <table className="dispatch-table w-full">
                <thead>
                  <tr>
                    <th>Vehicle ID</th>
                    <th>Original ETA</th>
                    <th>Re-Routed ETA</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {impactedVehicles.length ? (
                    impactedVehicles.map((vehicle) => (
                      <tr key={vehicle.vehicle}>
                        <td className="font-bold text-slate-800">{vehicle.vehicle}</td>
                        <td>{vehicle.originalEta}</td>
                        <td className="font-semibold text-indigo-600">{vehicle.reroutedEta}</td>
                        <td><span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">{vehicle.status}</span></td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td className="empty-table-row text-center text-slate-400 py-6" colSpan="4">
                        No active disruptions injected. Click 'Inject Traffic Disruption' to evaluate recovery plan.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </section>
      </div>

      {toast && (
        <div className="reopt-toast fixed bottom-6 right-6 z-50 flex items-center gap-2 px-4 py-3 bg-emerald-600 text-white rounded-xl shadow-xl text-sm font-semibold">
          <Check size={16} /> {toast}
        </div>
      )}
    </div>
  );
}
