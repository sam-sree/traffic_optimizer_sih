import React, { useState } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup } from 'react-leaflet';
import { Play, Sparkles, RefreshCw } from 'lucide-react';

const VEHICLE_COLORS = [
  '#06b6d4', // Cyan
  '#10b981', // Emerald Green
  '#f59e0b', // Amber Yellow
  '#ec4899', // Hot Pink
  '#8b5cf6', // Violet
  '#ef4444', // Red
  '#f97316', // Orange
  '#84cc16', // Lime Green
  '#3b82f6', // Bright Blue
  '#d946ef'  // Magenta
];

export default function MapView({ graphData, solution, onSolve, loading }) {
  const [selectedSolver, setSelectedSolver] = useState('Hybrid QPSO + Exact-Cluster');
  const [numNodes, setNumNodes] = useState(25);
  const [numVehicles, setNumVehicles] = useState(5);

  const centerLat = 12.9716;
  const centerLon = 77.5946;

  const handleSolveClick = () => {
    onSolve({
      solver_name: selectedSolver,
      num_nodes: numNodes,
      num_vehicles: numVehicles,
      vehicle_capacity: 65.0,
      time_of_day_hours: 8.5
    });
  };

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '20px', margin: '0 20px', height: 'calc(100vh - 120px)' }}>
      {/* Control Panel */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '18px' }}>
        <h2 style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fcf8f8', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={18} color="#ef4444" /> Route Configuration
        </h2>

        <div>
          <label style={{ fontSize: '0.82rem', color: '#a89a9c', display: 'block', marginBottom: '6px' }}>Select Algorithm</label>
          <select
            value={selectedSolver}
            onChange={(e) => setSelectedSolver(e.target.value)}
            style={{ width: '100%', background: '#180d10', color: '#fcf8f8', border: '1px solid #3f1922', padding: '10px', borderRadius: '8px', fontSize: '0.88rem' }}
          >
            <option value="Hybrid QPSO + Exact-Cluster">Hybrid QPSO + Exact-Cluster (Proposed)</option>
            <option value="Quantum-Inspired PSO (QPSO)">Plain QPSO Baseline</option>
            <option value="Genetic Algorithm (GA)">Genetic Algorithm (GA)</option>
            <option value="Ant Colony Optimization (ACO)">Ant Colony Optimization (ACO)</option>
            <option value="Google OR-Tools CVRPTW">Google OR-Tools CVRPTW</option>
            <option value="Dijkstra Nearest-Neighbor">Dijkstra Nearest-Neighbor</option>
          </select>
        </div>

        <div>
          <label style={{ fontSize: '0.82rem', color: '#a89a9c', display: 'block', marginBottom: '6px' }}>Delivery Nodes: {numNodes}</label>
          <input
            type="range"
            min="10"
            max="100"
            step="5"
            value={numNodes}
            onChange={(e) => setNumNodes(Number(e.target.value))}
            style={{ width: '100%', accentColor: '#ef4444' }}
          />
        </div>

        <div>
          <label style={{ fontSize: '0.82rem', color: '#a89a9c', display: 'block', marginBottom: '6px' }}>Vehicle Fleet Size: {numVehicles}</label>
          <input
            type="range"
            min="2"
            max="12"
            value={numVehicles}
            onChange={(e) => setNumVehicles(Number(e.target.value))}
            style={{ width: '100%', accentColor: '#f97316' }}
          />
        </div>

        <button
          onClick={handleSolveClick}
          disabled={loading}
          className="glow-btn"
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', width: '100%', marginTop: '8px' }}
        >
          {loading ? <RefreshCw className="animate-spin" size={18} /> : <Play size={18} />}
          {loading ? 'Optimizing Routes...' : 'Execute Route Optimization'}
        </button>

        {solution && (
          <div style={{ marginTop: '16px', background: '#180d10', padding: '16px', borderRadius: '10px', border: '1px solid #3f1922' }}>
            <h3 style={{ fontSize: '0.9rem', color: '#f97316', marginBottom: '10px' }}>Solution Results</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.82rem' }}>
              <div>
                <span style={{ color: '#a89a9c' }}>Total Cost:</span>
                <p style={{ fontWeight: 700, color: '#fcf8f8' }}>{solution.total_cost.toFixed(2)}</p>
              </div>
              <div>
                <span style={{ color: '#a89a9c' }}>Travel Time:</span>
                <p style={{ fontWeight: 700, color: '#fcf8f8' }}>{solution.total_time_min.toFixed(1)} min</p>
              </div>
              <div>
                <span style={{ color: '#a89a9c' }}>Distance:</span>
                <p style={{ fontWeight: 700, color: '#fcf8f8' }}>{solution.total_distance_km.toFixed(1)} km</p>
              </div>
              <div>
                <span style={{ color: '#a89a9c' }}>Wall Time:</span>
                <p style={{ fontWeight: 700, color: '#f97316' }}>{solution.wall_time_ms.toFixed(1)} ms</p>
              </div>
            </div>

            {solution.cost_inr && (
              <div style={{ marginTop: '12px', borderTop: '1px solid #3f1922', paddingTop: '10px' }}>
                <span style={{ fontSize: '0.78rem', color: '#a89a9c', display: 'block', marginBottom: '6px' }}>
                  Estimated Real-World Cost
                </span>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.82rem' }}>
                  <div>
                    <span style={{ color: '#a89a9c' }}>Fuel:</span>
                    <p style={{ fontWeight: 700, color: '#fcf8f8' }}>₹{solution.cost_inr.fuel_cost_inr.toFixed(2)}</p>
                  </div>
                  <div>
                    <span style={{ color: '#a89a9c' }}>Driver Time:</span>
                    <p style={{ fontWeight: 700, color: '#fcf8f8' }}>₹{solution.cost_inr.labor_cost_inr.toFixed(2)}</p>
                  </div>
                </div>
                {solution.savings_vs_baseline && (
                  <div style={{ marginTop: '10px', background: '#0d1811', padding: '10px', borderRadius: '8px', border: '1px solid #1f3f22' }}>
                    <span style={{ fontSize: '0.78rem', color: '#a89a9c' }}>Savings vs. unoptimized routing:</span>
                    <p style={{ fontWeight: 700, color: '#22c55e', fontSize: '1.1rem' }}>
                      ₹{solution.savings_vs_baseline.savings_inr.toFixed(2)} ({solution.savings_vs_baseline.savings_pct.toFixed(1)}%)
                    </p>
                  </div>
                )}
                <p style={{ fontSize: '0.68rem', color: '#6b6062', marginTop: '8px' }}>
                  Estimate assumes ₹{solution.cost_inr.assumptions.fuel_cost_per_km_inr}/km fuel cost and
                  ₹{solution.cost_inr.assumptions.driver_wage_per_hour_inr}/hour driver wage - adjust for your own fleet's actual figures.
                </p>
              </div>
            )}

            {solution.sla_report && (
              <div style={{ marginTop: '12px', borderTop: '1px solid #3f1922', paddingTop: '10px' }}>
                <span style={{ fontSize: '0.78rem', color: '#a89a9c', display: 'block', marginBottom: '6px' }}>
                  On-Time Delivery (SLA)
                </span>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                  <p style={{
                    fontWeight: 700,
                    fontSize: '1.3rem',
                    color: solution.sla_report.on_time_rate_pct >= 95 ? '#22c55e' : solution.sla_report.on_time_rate_pct >= 80 ? '#f97316' : '#ef4444'
                  }}>
                    {solution.sla_report.on_time_rate_pct.toFixed(1)}%
                  </p>
                  <span style={{ fontSize: '0.75rem', color: '#a89a9c' }}>
                    {solution.sla_report.on_time_count}/{solution.sla_report.total_customers} on time
                  </span>
                </div>
                {solution.sla_report.late_count > 0 && (
                  <p style={{ fontSize: '0.72rem', color: '#a89a9c', marginTop: '2px' }}>
                    Avg. lateness (when late): {solution.sla_report.avg_lateness_min_when_late.toFixed(1)} min
                  </p>
                )}
              </div>
            )}

            {solution.sustainability && (
              <div style={{ marginTop: '12px', borderTop: '1px solid #3f1922', paddingTop: '10px' }}>
                <span style={{ fontSize: '0.78rem', color: '#a89a9c', display: 'block', marginBottom: '6px' }}>
                  Fleet-Scale Sustainability Impact (projected)
                </span>
                <p style={{ fontWeight: 700, color: '#22c55e', fontSize: '1.1rem' }}>
                  {solution.sustainability.annual_co2_saved_tons.toFixed(1)} tons CO₂/year saved
                </p>
                <p style={{ fontSize: '0.68rem', color: '#6b6062', marginTop: '4px' }}>
                  Projected at a {solution.sustainability.assumptions.target_fleet_size}-vehicle fleet operating
                  {' '}{solution.sustainability.assumptions.operating_days_per_year} days/year - a stated projection, not a measured result.
                </p>
              </div>
            )}

            {/* Vehicle legend */}
            <div style={{ marginTop: '12px', borderTop: '1px solid #3f1922', paddingTop: '10px' }}>
              <span style={{ fontSize: '0.78rem', color: '#a89a9c', display: 'block', marginBottom: '6px' }}>Vehicle Route Legend:</span>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {solution?.routes?.map((route, rIdx) => (
                  <div key={`legend-${rIdx}`} style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem', background: '#0d0608', padding: '3px 8px', borderRadius: '4px' }}>
                    <div style={{ width: 10, height: 10, borderRadius: '50%', backgroundColor: VEHICLE_COLORS[rIdx % VEHICLE_COLORS.length] }} />
                    <span>Veh #{route.vehicle_id + 1}</span>
                    {route.maps_url && (
                      <a href={route.maps_url} target="_blank" rel="noopener noreferrer" style={{ color: '#f97316', textDecoration: 'none', marginLeft: '2px' }} title="Open this route in Google Maps">
                        ↗
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Map Renderer */}
      <div className="glass-panel" style={{ position: 'relative', overflow: 'hidden' }}>
        <MapContainer center={[centerLat, centerLon]} zoom={13} scrollWheelZoom={true}>
          <TileLayer
            attribution='&copy; <a href="https://carto.com/">CARTO</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />

          {/* Render base graph edges */}
          {graphData?.edges?.map((edge, idx) => (
            <Polyline
              key={`edge-${idx}`}
              positions={[
                [graphData.nodes[edge.u]?.lat || centerLat, graphData.nodes[edge.u]?.lon || centerLon],
                [graphData.nodes[edge.v]?.lat || centerLat, graphData.nodes[edge.v]?.lon || centerLon]
              ]}
              pathOptions={{
                color: edge.is_incident ? '#ef4444' : edge.speed_kmh < 15 ? '#ea580c' : '#2b1419',
                weight: edge.is_incident ? 4 : 1,
                opacity: edge.is_incident ? 0.95 : 0.35
              }}
            />
          ))}

          {/* Render optimized vehicle routes with distinct colors */}
          {solution?.routes?.map((route, rIdx) => (
            <Polyline
              key={`route-${rIdx}`}
              positions={route.path_coords}
              pathOptions={{
                color: VEHICLE_COLORS[rIdx % VEHICLE_COLORS.length],
                weight: 5,
                opacity: 0.9
              }}
            >
              <Popup>
                <div>
                  <strong style={{ color: VEHICLE_COLORS[rIdx % VEHICLE_COLORS.length] }}>Vehicle #{route.vehicle_id + 1} Route</strong><br />
                  Time: {route.total_time_min.toFixed(1)} min<br />
                  Distance: {route.total_distance_km.toFixed(1)} km
                </div>
              </Popup>
            </Polyline>
          ))}

          {/* Render graph intersections & customer markers */}
          {graphData?.nodes?.map((node) => (
            <CircleMarker
              key={`node-${node.id}`}
              center={[node.lat, node.lon]}
              radius={node.id === 0 ? 8 : 4}
              pathOptions={{
                fillColor: node.id === 0 ? '#ef4444' : '#f97316',
                color: '#ffffff',
                weight: 1,
                fillOpacity: 0.9
              }}
            >
              <Popup>
                <span>{node.id === 0 ? 'Depot Hub #0' : `Customer Node #${node.id}`}</span>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
