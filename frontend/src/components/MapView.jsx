import React, { useEffect, useState } from 'react';
import { CircleMarker, MapContainer, Polyline, Popup, TileLayer } from 'react-leaflet';
import { Play, RefreshCw } from 'lucide-react';

const COLORS = ['#3020ad', '#168a7a', '#de7b27', '#b64070', '#3976bd', '#6f52a0'];

export default function MapView({ graphData, solution, onSolve, loading, error, appliedScenario }) {
  const [selectedAlgorithm, setSelectedAlgorithm] = useState('Hybrid QPSO + Exact-Cluster');
  const [deliveryNodes, setDeliveryNodes] = useState(20);
  const [vehicleFleet, setVehicleFleet] = useState(5);
  const [depotLocation, setDepotLocation] = useState('Indiranagar Central Hub');
  const [vehicleCapacity, setVehicleCapacity] = useState(65);
  const [maxDistance, setMaxDistance] = useState(150);
  const [priorityWeight, setPriorityWeight] = useState(0.85);
  const [distanceSensitivity, setDistanceSensitivity] = useState(1.2);

  useEffect(() => {
    if (!appliedScenario) return;
    setSelectedAlgorithm(appliedScenario.algorithm);
    setPriorityWeight(appliedScenario.priorityWeight);
    setDistanceSensitivity(appliedScenario.distanceSensitivity);
  }, [appliedScenario]);

  const executeRouteOptimization = () => onSolve({
    algorithm: selectedAlgorithm,
    num_nodes: Number(deliveryNodes),
    fleet_size: Number(vehicleFleet),
    depot: depotLocation,
    vehicle_capacity: Number(vehicleCapacity),
    max_distance: Number(maxDistance),
    priority_weight: Number(priorityWeight),
    distance_sensitivity: Number(distanceSensitivity)
  });

  return (
    <div className="route-workspace">
      <div className="page-head"><div><h2>Route Visualizer</h2><p>Configure a vehicle routing problem and inspect optimized delivery routes.</p></div></div>
      <div className="layout-map">
        <section className="control-card w-[340px]">
          <h3 className="card-title">Problem Configuration &amp; Constraints</h3>
          <div className="field"><label htmlFor="algorithm">Algorithm</label><select id="algorithm" value={selectedAlgorithm} onChange={event => setSelectedAlgorithm(event.target.value)}><option>Hybrid QPSO + Exact-Cluster</option><option>Ant Colony Optimization (ACO)</option><option>Quantum-Inspired PSO (QPSO)</option><option>Genetic Algorithm (GA)</option><option>Google OR-Tools CVRPTW</option><option>Dijkstra Nearest-Neighbor</option></select></div>
          <div className="two-field"><div className="field"><label htmlFor="delivery-nodes">Delivery Nodes</label><input id="delivery-nodes" type="number" min="1" max="317" value={deliveryNodes} onChange={event => setDeliveryNodes(event.target.value)} /></div><div className="field"><label htmlFor="vehicle-fleet">Vehicle Fleet</label><input id="vehicle-fleet" type="number" min="1" max="50" value={vehicleFleet} onChange={event => setVehicleFleet(event.target.value)} /></div></div>
          <hr className="form-rule" />
          <div className="field"><label htmlFor="depot">Depot Location</label><select id="depot" value={depotLocation} onChange={event => setDepotLocation(event.target.value)}><option>Indiranagar Central Hub</option><option>Peenya Industrial Area</option><option>Koramangala Distribution Hub</option></select></div>
          <div className="two-field"><div className="field"><label htmlFor="capacity">Vehicle Capacity</label><input id="capacity" type="number" min="1" value={vehicleCapacity} onChange={event => setVehicleCapacity(event.target.value)} /></div><div className="field"><label htmlFor="distance">Max Distance (km)</label><input id="distance" type="number" min="1" value={maxDistance} onChange={event => setMaxDistance(event.target.value)} /></div></div>
          <div className="range-field"><div><label htmlFor="priority">Priority Weight</label><span>{priorityWeight.toFixed(2)}</span></div><input id="priority" type="range" min="0" max="1" step="0.05" value={priorityWeight} onChange={event => setPriorityWeight(Number(event.target.value))} /></div>
          <div className="range-field"><div><label htmlFor="sensitivity">Distance Sensitivity</label><span>{distanceSensitivity.toFixed(2)}</span></div><input id="sensitivity" type="range" min="0.5" max="3" step="0.1" value={distanceSensitivity} onChange={event => setDistanceSensitivity(Number(event.target.value))} /></div>
          {error && <div className="error-banner" role="alert">{error}</div>}
          <button className="execute-btn" onClick={executeRouteOptimization} disabled={loading}>{loading ? <><RefreshCw className="spin" size={16} />Optimizing Routes...</> : <><Play size={16} />Execute Route Optimization</>}</button>
          {solution && <div className="solution-summary"><div className="solution-summary-head"><strong>Latest solution</strong><span className={solution.is_feasible ? 'solution-valid' : 'solution-review'}>{solution.is_feasible ? 'Feasible' : 'Review'}</span></div><div className="solution-metrics"><div><small>Total cost</small><b>{solution.total_cost?.toFixed?.(2) ?? solution.total_cost}</b></div><div><small>Route time</small><b>{solution.total_time_min?.toFixed?.(1) ?? '-'} min</b></div><div><small>Distance</small><b>{solution.total_distance_km?.toFixed?.(1) ?? '-'} km</b></div></div><div className="vehicle-colors">{solution.routes?.map((route, index) => <span key={route.vehicle_id ?? index}><i style={{ background: COLORS[index % COLORS.length] }} />Vehicle {route.vehicle_id}</span>)}</div></div>}
        </section>
        <section className="map-panel" aria-label="Interactive route map">
          <MapContainer center={[12.9716, 77.5946]} zoom={12} className="h-full min-h-[600px]">
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' />
            {solution?.routes?.map((route, index) => <Polyline key={route.vehicle_id ?? index} positions={route.path_coords || []} pathOptions={{ color: COLORS[index % COLORS.length], weight: 4 }} />)}
            {graphData?.nodes?.map(node => <CircleMarker key={node.id} center={[node.lat, node.lon]} radius={solution ? 4 : 3} pathOptions={{ color: '#3020ad', fillColor: '#fff', fillOpacity: 1 }}><Popup>Delivery node {node.id}</Popup></CircleMarker>)}
          </MapContainer>
          <div className="map-legend"><strong>Legend</strong><span><i className="legend-dot depot" />Main Depot</span><span><i className="legend-dot node" />Delivery Node</span>{solution?.routes?.map((route, index) => <span key={route.vehicle_id ?? index}><i className="legend-line" style={{ background: COLORS[index % COLORS.length] }} />Vehicle {route.vehicle_id}</span>)}</div>
        </section>
      </div>
    </div>
  );
}
