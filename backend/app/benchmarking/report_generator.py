import os
import json
import csv
from typing import Dict, Any

def generate_benchmark_reports(suite_results: Dict[str, Any]):
    """
    Generates docs/benchmark_report.md and exports machine-readable JSON and CSV
    data for backend API and frontend dashboard consumption.
    """
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    docs_dir = os.path.join(root_dir, 'docs')
    data_dir = os.path.join(root_dir, 'data')
    os.makedirs(docs_dir, exist_ok=True)
    os.makedirs(data_dir, exist_ok=True)

    json_path = os.path.join(data_dir, 'benchmark_results.json')
    csv_path = os.path.join(data_dir, 'benchmark_results.csv')
    md_path = os.path.join(docs_dir, 'benchmark_report.md')

    # 1. Export JSON
    with open(json_path, 'w') as f:
        json.dump(suite_results, f, indent=2)
    print(f"[ReportGenerator] Exported benchmark JSON to: {json_path}")

    # 2. Export CSV
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "InstanceSize", "Algorithm", "IsStochastic", "SeedsEvaluated",
            "CostMean", "CostStd", "TravelTimeMinMean", "TravelTimeMinStd",
            "DistanceKmMean", "DistanceKmStd", "RuntimeMsMean", "RuntimeMsStd"
        ])
        for inst_key, alg_map in suite_results.items():
            size_num = inst_key.replace("n_", "")
            for alg_name, metrics in alg_map.items():
                writer.writerow([
                    size_num, alg_name, metrics["is_stochastic"], metrics["seeds_evaluated"],
                    f"{metrics['cost_mean']:.4f}", f"{metrics['cost_std']:.4f}",
                    f"{metrics['time_min_mean']:.2f}", f"{metrics['time_min_std']:.2f}",
                    f"{metrics['dist_km_mean']:.2f}", f"{metrics['dist_km_std']:.2f}",
                    f"{metrics['runtime_ms_mean']:.1f}", f"{metrics['runtime_ms_std']:.1f}"
                ])
    print(f"[ReportGenerator] Exported benchmark CSV to: {csv_path}")

    # 3. Export docs/benchmark_report.md
    with open(md_path, 'w') as f:
        f.write("# QuantumRoute: Comprehensive Algorithm Benchmark & Scalability Report\n\n")
        f.write("This report presents empirical performance, solution quality, and scalability metrics for the **Hybrid Classical-Quantum Decomposition Architecture** against classical and quantum-inspired baselines on identical road network instances in Bengaluru, India.\n\n")

        for inst_key, alg_map in suite_results.items():
            size_num = inst_key.replace("n_", "")
            f.write(f"## Problem Scale: N = {size_num} Customer Nodes\n\n")
            f.write("| Algorithm | Cost (Mean ± Std) | Travel Time (min) | Distance (km) | Wall-Clock Runtime (ms) |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")

            for alg_name, m in alg_map.items():
                cost_str = f"{m['cost_mean']:.4f} ± {m['cost_std']:.4f}" if m['is_stochastic'] else f"{m['cost_mean']:.4f}"
                time_str = f"{m['time_min_mean']:.2f} min"
                dist_str = f"{m['dist_km_mean']:.2f} km"
                runtime_str = f"{m['runtime_ms_mean']:.1f} ms"
                f.write(f"| **{alg_name}** | {cost_str} | {time_str} | {dist_str} | {runtime_str} |\n")

            f.write("\n")

        f.write("## Key Architectural Findings\n")
        f.write("1. **Cluster Sub-Solver**: Intra-cluster sub-tours are solved exactly via Held-Karp dynamic programming, which is tractable at the cluster sizes used here (<= 10-12 nodes) and guarantees the optimal sub-tour for each cluster.\n")
        f.write("2. **Dynamic Re-Optimization**: Local re-solving affected clusters only (instead of the full network) after a traffic disruption is architecturally faster than a full re-solve, since unaffected clusters keep their cached sub-tours - see the reoptimize benchmark for measured speedup on a specific run.\n")
        f.write("3. **Solution Quality**: See the tables above for how each algorithm's solution quality and runtime actually compare at each problem scale - results vary by scale and are reported as measured, not assumed.\n")

    print(f"[ReportGenerator] Generated benchmark Markdown report at: {md_path}")
