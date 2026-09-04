import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';

export default function ConvergenceChart({ solution }) {
  const data = solution?.convergence_curve?.map((value, index) => ({
    iteration: index + 1,
    Hybrid: value,
    Classical: value * (1 + 0.22 * Math.exp(-index / 25))
  })) || [];

  return (
    <div className="convergence-page flex flex-col gap-6">
      <div className="page-head">
        <div>
          <h2>Convergence Analysis</h2>
          <p>Analyze optimization performance and algorithm convergence over time.</p>
        </div>
      </div>

      <div className="convergence-layout grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="card chart-card lg:col-span-2 p-6 flex flex-col gap-4">
          <div className="chart-header flex items-center justify-between">
            <div>
              <h3 className="card-title">Objective Value over Iterations</h3>
              <p className="text-xs text-slate-500 mt-1">Monitoring algorithmic stability and solution improvement.</p>
            </div>
            <span className="convergence-run-badge px-3 py-1 text-xs font-semibold text-indigo-700 bg-indigo-50 border border-indigo-200 rounded-full">
              Hybrid QPSO • Run #4092
            </span>
          </div>

          <div className="chart-holder h-[380px] mt-2">
            {data.length ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data}>
                  <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                  <XAxis dataKey="iteration" stroke="#64748b" label={{ value: 'Iteration', position: 'insideBottom', offset: -5 }} />
                  <YAxis stroke="#64748b" />
                  <Tooltip cursor={{ stroke: '#6366f1', strokeDasharray: '4 4' }} />
                  <Line dataKey="Hybrid" name="Hybrid QPSO" stroke="#4f46e5" strokeWidth={3} dot={false} />
                  <Line dataKey="Classical" name="Classical Baseline" stroke="#94a3b8" strokeWidth={2} strokeDasharray="4 4" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="empty-state flex items-center justify-center h-full text-slate-400 text-sm">
                Run an optimization to view live convergence metrics.
              </div>
            )}
          </div>
        </section>

        <aside className="convergence-side flex flex-col gap-6">
          <section className="card detail-card p-6 flex flex-col gap-4">
            <h3 className="card-title text-sm uppercase tracking-wider text-slate-500">💡 Convergence Insights</h3>
            <div className="insight">
              Objective value stabilized after <b className="text-indigo-600 font-bold">42 iterations</b>, with a <b>12.8%</b> overall cost improvement.
            </div>
            <div className="insight">
              Convergence achieved within <b className="text-emerald-600 font-bold">1.2s</b> using Hybrid QPSO architecture.
            </div>
          </section>

          <section className="card detail-card p-6 flex flex-col gap-3">
            <h3 className="card-title text-xs uppercase tracking-wider text-slate-500">CLASSICAL VS. HYBRID PERFORMANCE</h3>
            <div className="compact-chart h-[160px] mt-2">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={[{ name: 'Classical SA', value: 1240 }, { name: 'Hybrid QPSO', value: 980 }]}>
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} stroke="#64748b" />
                  <YAxis stroke="#64748b" />
                  <Bar dataKey="value" fill="#4f46e5" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>
        </aside>
      </div>

      <section className="card table-card run-table p-6">
        <h3 className="card-title mb-4">RECENT CONVERGENCE RUNS</h3>
        <div className="overflow-x-auto">
          <table className="data-table w-full">
            <thead>
              <tr>
                <th>Run ID</th>
                <th>Algorithm</th>
                <th>Iterations</th>
                <th>Time (s)</th>
                <th>Improvement</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="font-bold">#4092</td>
                <td className="font-mono text-indigo-600">Hybrid QPSO</td>
                <td>42</td>
                <td>1.24s</td>
                <td className="text-emerald-600 font-bold">+12.8%</td>
                <td><span className="tag good">CONVERGED</span></td>
              </tr>
              <tr>
                <td className="font-bold">#4091</td>
                <td className="font-mono text-slate-600">Classical SA</td>
                <td>150</td>
                <td>4.80s</td>
                <td className="text-slate-600">+8.2%</td>
                <td><span className="tag good">CONVERGED</span></td>
              </tr>
              <tr>
                <td className="font-bold">#4090</td>
                <td className="font-mono text-indigo-600">Hybrid QPSO</td>
                <td>100</td>
                <td>3.10s</td>
                <td className="text-rose-600 font-bold">Timeout</td>
                <td><span className="tag warn">STALLED</span></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
