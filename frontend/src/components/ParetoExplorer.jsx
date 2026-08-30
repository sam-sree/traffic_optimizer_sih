import React, { useEffect, useState } from 'react';
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { fetchParetoFront } from '../api';
import { Layers, RefreshCw } from 'lucide-react';

export default function ParetoExplorer() {
  const [points, setPoints] = useState([]);
  const [selectedPoint, setSelectedPoint] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadPareto = async () => {
    setLoading(true);
    try {
      const data = await fetchParetoFront();
      setPoints(data.pareto_points || []);
      if (data.pareto_points && data.pareto_points.length > 0) {
        setSelectedPoint(data.pareto_points[0]);
      }
    } catch (err) {
      console.error("Failed to load Pareto front", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadPareto();
  }, []);

  return (
    <div style={{ margin: '0 20px', height: 'calc(100vh - 120px)', display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px' }}>
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <h2 style={{ fontSize: '1.2rem', color: '#fcf8f8' }}>4-Objective Pareto Front Explorer</h2>
            <p style={{ fontSize: '0.85rem', color: '#a89a9c' }}>
              Multi-Objective QPSO non-dominated trade-off solutions between Travel Time and Distance/Emissions.
            </p>
          </div>
          <button onClick={loadPareto} className="glow-btn" style={{ padding: '8px 14px', fontSize: '0.82rem' }}>
            {loading ? <RefreshCw className="animate-spin" size={14} /> : <Layers size={14} />} Refresh Pareto
          </button>
        </div>

        <div style={{ flex: 1, width: '100%', minHeight: 350 }}>
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#3f1922" />
              <XAxis type="number" dataKey="time_min" name="Travel Time" unit=" min" stroke="#a89a9c" />
              <YAxis type="number" dataKey="distance_km" name="Distance" unit=" km" stroke="#a89a9c" />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#180d10', borderColor: '#3f1922', borderRadius: '8px' }} />
              <Scatter name="Pareto Points" data={points} onClick={(p) => setSelectedPoint(p.payload)}>
                {points.map((entry, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={selectedPoint?.id === entry.id ? '#f97316' : '#ef4444'}
                    stroke={selectedPoint?.id === entry.id ? '#ffffff' : '#ef4444'}
                    strokeWidth={2}
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Detail panel */}
      <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <h3 style={{ fontSize: '1.05rem', color: '#f97316' }}>Selected Trade-off Point</h3>
        {selectedPoint ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ background: '#180d10', padding: '14px', borderRadius: '8px', border: '1px solid #3f1922' }}>
              <span style={{ fontSize: '0.78rem', color: '#a89a9c' }}>Total Travel Time</span>
              <p style={{ fontSize: '1.2rem', fontWeight: 700, color: '#fcf8f8' }}>{selectedPoint.time_min.toFixed(1)} minutes</p>
            </div>
            <div style={{ background: '#180d10', padding: '14px', borderRadius: '8px', border: '1px solid #3f1922' }}>
              <span style={{ fontSize: '0.78rem', color: '#a89a9c' }}>Total Distance</span>
              <p style={{ fontSize: '1.2rem', fontWeight: 700, color: '#fcf8f8' }}>{selectedPoint.distance_km.toFixed(1)} km</p>
            </div>
            <div style={{ background: '#180d10', padding: '14px', borderRadius: '8px', border: '1px solid #3f1922' }}>
              <span style={{ fontSize: '0.78rem', color: '#a89a9c' }}>Congestion Score</span>
              <p style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f59e0b' }}>{selectedPoint.congestion.toFixed(2)}</p>
            </div>
            <div style={{ background: '#180d10', padding: '14px', borderRadius: '8px', border: '1px solid #3f1922' }}>
              <span style={{ fontSize: '0.78rem', color: '#a89a9c' }}>Estimated Carbon Emissions</span>
              <p style={{ fontSize: '1.2rem', fontWeight: 700, color: '#f97316' }}>{selectedPoint.emissions_co2_kg.toFixed(2)} kg CO₂</p>
            </div>
          </div>
        ) : (
          <p style={{ color: '#a89a9c' }}>Select a point on the scatter plot to view multi-objective metrics.</p>
        )}
      </div>
    </div>
  );
}
