import React from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker } from 'react-leaflet';
import { Download } from 'lucide-react';

const COLORS = ['#3020ad', '#4c9ddd', '#35aa7c', '#e88a35', '#9557c3', '#d14f72'];

export default function OptimizationResults({ solution, graphData }) {
  const routes = solution?.routes || [];
  const nodes = graphData?.nodes || [];
  const nodeById = Object.fromEntries(nodes.map((node) => [String(node.id), node]));
  const stops = routes.reduce((total, route) => total + route.customer_sequence.length, 0);

  const exportCsv = () => {
    const rows = [['Vehicle', 'Stops', 'Distance (km)', 'Time (min)', 'Status']];
    routes.forEach((route) => rows.push([route.vehicle_id, route.customer_sequence.length, route.total_distance_km.toFixed(2), route.total_time_min.toFixed(2), route.feasible ? 'Feasible' : 'Review']));
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([rows.map((row) => row.join(',')).join('\n')], { type: 'text/csv' }));
    link.download = 'quantumroute-results.csv';
    link.click();
    URL.revokeObjectURL(link.href);
  };

  return <div className="results-page">
    <div className="page-head"><div><h2>Optimization Results</h2><p>{solution ? `${solution.solver_name} completed in ${solution.wall_time_ms.toFixed(0)} ms.` : 'Run an optimization to load live routing results.'}</p></div><button className="outline-btn" onClick={exportCsv} disabled={!solution}><Download size={14} /> Export CSV</button></div>
    <div className="stats"><div className="stat-card"><span>Total Distance</span><strong>{solution ? `${solution.total_distance_km.toFixed(1)} km` : '-'}</strong></div><div className="stat-card"><span>Vehicles Used</span><strong>{routes.length}</strong></div><div className="stat-card"><span>Nodes Delivered</span><strong>{stops}</strong></div><div className="stat-card"><span>Route Time</span><strong>{solution ? `${solution.total_time_min.toFixed(1)} min` : '-'}</strong></div><div className="stat-card"><span>Objective Value</span><strong>{solution ? solution.total_cost.toFixed(1) : '-'}</strong></div></div>
    <div className="result-layout"><section className="card result-map"><div className="results-map-heading">Full Network and Vehicle Routes</div><div className="results-map-canvas"><MapContainer center={[12.9716, 77.5946]} zoom={12} scrollWheelZoom><TileLayer attribution={'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'} url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />{graphData?.edges?.map((edge, index) => { const from = nodeById[String(edge.u)]; const to = nodeById[String(edge.v)]; return from && to ? <Polyline key={`edge-${index}`} positions={[[from.lat, from.lon], [to.lat, to.lon]]} pathOptions={{ color: '#9aa1ad', weight: 1, opacity: .4 }} /> : null; })}{nodes.map((node) => <CircleMarker key={node.id} center={[node.lat, node.lon]} radius={2.5} pathOptions={{ color: '#3020ad', fillColor: '#fff', fillOpacity: .9, weight: 1 }} />)}{routes.map((route, index) => <Polyline key={`route-${route.vehicle_id ?? index}`} positions={route.path_coords || []} pathOptions={{ color: COLORS[index % COLORS.length], weight: 4 }} />)}</MapContainer></div></section><section className="card table-card"><h3 className="card-title">Route Breakdown</h3><table className="data-table"><thead><tr><th>Vehicle</th><th>Stops</th><th>Distance</th><th>Status</th></tr></thead><tbody>{routes.map((route, index) => <tr key={route.vehicle_id ?? index}><td><span className="route-color-dot" style={{ background: COLORS[index % COLORS.length] }} />Vehicle {route.vehicle_id}</td><td>{route.customer_sequence.length}</td><td>{route.total_distance_km.toFixed(1)} km</td><td>{route.feasible ? 'Feasible' : 'Review'}</td></tr>)}</tbody></table></section></div>
  </div>;
}
