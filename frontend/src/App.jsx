import React, { useEffect, useState } from 'react';
import Navbar from './components/Navbar';
import MapView from './components/MapView';
import ConvergenceChart from './components/ConvergenceChart';
import ParetoExplorer from './components/ParetoExplorer';
import ReoptimizationPanel from './components/ReoptimizationPanel';
import BenchmarkSummary from './components/BenchmarkSummary';
import { fetchGraphData, runSolve } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('map');
  const [graphData, setGraphData] = useState(null);
  const [solution, setSolution] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchGraphData()
      .then((data) => setGraphData(data))
      .catch((err) => console.error('Failed to fetch graph data:', err));

    // Run default initial solve
    handleSolve({
      solver_name: 'Hybrid QPSO + Exact-Cluster',
      num_nodes: 25,
      num_vehicles: 5,
      vehicle_capacity: 65.0,
      time_of_day_hours: 8.5
    });
  }, []);

  const handleSolve = async (payload) => {
    setLoading(true);
    try {
      const sol = await runSolve(payload);
      setSolution(sol);
    } catch (err) {
      console.error('Solve failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', background: '#080c14' }}>
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} networkSummary={graphData?.summary} />

      <main style={{ flex: 1 }}>
        {activeTab === 'map' && (
          <MapView graphData={graphData} solution={solution} onSolve={handleSolve} loading={loading} />
        )}
        {activeTab === 'convergence' && <ConvergenceChart solution={solution} />}
        {activeTab === 'pareto' && <ParetoExplorer />}
        {activeTab === 'reoptimize' && <ReoptimizationPanel />}
        {activeTab === 'benchmarks' && <BenchmarkSummary />}
      </main>
    </div>
  );
}
