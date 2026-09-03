import React, { useEffect, useState } from 'react';
import Navbar from './components/Navbar';
import MapView from './components/MapView';
import ConvergenceChart from './components/ConvergenceChart';
import ParetoExplorer from './components/ParetoExplorer';
import ReoptimizationPanel from './components/ReoptimizationPanel';
import BenchmarkSummary from './components/BenchmarkSummary';
import OptimizationResults from './components/OptimizationResults';
import { fetchGraphData, runSolve, runSolveFromCsv } from './api';

export default function App() {
  const [activeTab, setActiveTab] = useState('map');
  const [graphData, setGraphData] = useState(null);
  const [solution, setSolution] = useState(null);
  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState('');
  const [appliedScenario, setAppliedScenario] = useState(null);
  const refreshGraph = async () => {
    try {
      setGraphData(await fetchGraphData());
    } catch (err) {
      console.error('Failed to refresh graph data:', err);
      setApiError(err.response ? `Backend request failed (${err.response.status}).` : `Backend disconnected: ${err.message}`);
    }
  };

  useEffect(() => {
    refreshGraph();

  }, []);

  const handleSolve = async (payload) => {
    setLoading(true);
    setApiError('');
    try {
      const sol = await runSolve(payload);
      setSolution(sol);
      return sol;
    } catch (err) {
      console.error('Solve failed:', err);
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      setApiError(detail ? `Optimization failed (${status ?? 'error'}): ${detail}` : status ? `Optimization failed (${status}).` : `Backend disconnected: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleSolveFromCsv = async (file, options) => {
    setLoading(true);
    setApiError('');
    try {
      const sol = await runSolveFromCsv(file, options);
      setSolution(sol);
      return sol;
    } catch (err) {
      console.error('CSV solve failed:', err);
      const status = err.response?.status;
      const detail = err.response?.data?.detail;
      const detailText = typeof detail === 'object' ? JSON.stringify(detail.errors || detail) : detail;
      setApiError(detailText ? `Order import failed (${status ?? 'error'}): ${detailText}` : `Backend disconnected: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-shell">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} connected={Boolean(graphData)} />

      <main className="content">
        {activeTab === 'map' && (
          <MapView graphData={graphData} solution={solution} onSolve={handleSolve} onSolveFromCsv={handleSolveFromCsv} loading={loading} error={apiError} appliedScenario={appliedScenario} />
        )}
        {activeTab === 'results' && <OptimizationResults solution={solution} graphData={graphData} />}
        {activeTab === 'convergence' && <ConvergenceChart solution={solution} />}
        {activeTab === 'pareto' && <ParetoExplorer onApplyScenario={(scenario) => { setAppliedScenario(scenario); setActiveTab('map'); }} />}
        {activeTab === 'reoptimize' && <ReoptimizationPanel onGraphRefresh={refreshGraph} graphData={graphData} />}
        {activeTab === 'benchmarks' && <BenchmarkSummary />}
      </main>
    </div>
  );
}
