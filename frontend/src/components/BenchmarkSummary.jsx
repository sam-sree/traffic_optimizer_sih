import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Download, Play } from 'lucide-react';

const BENCHMARK_DATA = [
  { n: 'N=20', QAOA: 2.1, VQE: 2.8, Annealing: 1.4 },
  { n: 'N=50', QAOA: 4.5, VQE: 6.7, Annealing: 3.4 },
  { n: 'N=100', QAOA: 7.8, VQE: 12.1, Annealing: 8.6 }
];

const MATRIX_ROWS = [
  ['● Hybrid QPSO (Quantum-Inspired)', '12,840 km', '42 iterations', '1.24s'],
  ['● QAOA (Quantum Approximate)', '14,230 km', '450 iterations', '5.50s'],
  ['● VQE (Variational Quantum)', '14,105 km', '620 iterations', '8.00s'],
  ['● Simulated Annealing', '14,890 km', '1,200 iterations', '6.00s'],
  ['● Genetic Algorithm', '14,650 km', '800 generations', '12.20s'],
  ['● Clarke-Wright Savings', '15,400 km', '1 iteration (heuristic)', '0.80s']
];

export default function BenchmarkSummary() {
  const exportCsv = () => {
    const rows = [['Algorithm', 'Cost (Avg Distance)', 'Time to Convergence', 'Total Runtime (N=100)'], ...MATRIX_ROWS];
    const link = document.createElement('a');
    link.href = URL.createObjectURL(new Blob([rows.map(r => r.join(',')).join('\n')], { type: 'text/csv' }));
    link.download = 'quantumroute-benchmarks.csv';
    link.click();
    URL.revokeObjectURL(link.href);
  };

  return (
    <div className="benchmark-page flex flex-col gap-6">
      <div className="page-head">
        <div>
          <h2>System Benchmarks</h2>
          <p>Comparative performance analysis of quantum-inspired and classical solvers.</p>
        </div>
        <div className="button-row flex gap-3">
          <button className="outline-btn" onClick={exportCsv}>
            <Download size={14} /> Export CSV
          </button>
          <button className="primary-btn">
            <Play size={14} /> Run Benchmark
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="card chart-card lg:col-span-2 p-6">
          <div className="mb-4">
            <h3 className="card-title">Runtime (Seconds) vs Node Scale</h3>
            <p className="text-xs text-slate-500 mt-1">Comparing execution scaling across problem dimensions.</p>
          </div>
          <div className="benchmark-chart h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={BENCHMARK_DATA}>
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                <XAxis dataKey="n" stroke="#64748b" />
                <YAxis stroke="#64748b" />
                <Tooltip />
                <Legend />
                <Bar dataKey="QAOA" fill="#6366f1" radius={[4, 4, 0, 0]} />
                <Bar dataKey="VQE" fill="#06b6d4" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Annealing" fill="#94a3b8" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>

        <section className="card detail-card p-6 flex flex-col gap-4">
          <h3 className="card-title">Benchmark Summary</h3>
          <div className="insight">
            <strong>Hybrid QPSO</strong> achieved optimal cost reduction with <b className="text-indigo-600">3.4x faster convergence</b> over classical VQE algorithms.
          </div>
          <div className="stats grid grid-cols-1 gap-3 mt-2">
            <div className="stat-card">
              <span>Top Speedup</span>
              <strong>3.4x</strong>
            </div>
            <div className="stat-card">
              <span>Avg Cost Saved</span>
              <strong>14.2%</strong>
            </div>
          </div>
        </section>
      </div>

      <section className="card table-card p-6">
        <h3 className="card-title mb-4">Algorithm Performance Comparison Matrix</h3>
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead>
              <tr>
                <th>Algorithm</th>
                <th>Cost (Avg Distance)</th>
                <th>Time to Convergence</th>
                <th>Total Runtime (N=100)</th>
              </tr>
            </thead>
            <tbody>
              {MATRIX_ROWS.map((row, idx) => (
                <tr key={idx}>
                  <td className="font-semibold text-slate-800">{row[0]}</td>
                  <td>{row[1]}</td>
                  <td>{row[2]}</td>
                  <td><span className="font-mono text-indigo-600 font-bold">{row[3]}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
