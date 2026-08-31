# QuantumRoute: Comprehensive Algorithm Benchmark & Scalability Report

This report presents empirical performance, solution quality, and scalability metrics for the **Hybrid Classical-Quantum Decomposition Architecture** against classical and quantum-inspired baselines on identical road network instances in Bengaluru, India.

## Problem Scale: N = 20 Customer Nodes

| Algorithm | Cost (Mean ± Std) | Travel Time (min) | Distance (km) | Wall-Clock Runtime (ms) |
| :--- | :--- | :--- | :--- | :--- |
| **Hybrid QPSO + Exact-Cluster** | 42.3510 ± 0.9018 | 193.48 min | 43.97 km | 1607.7 ms |
| **Quantum-Inspired PSO (QPSO)** | 37.6789 ± 0.6935 | 174.97 min | 39.77 km | 318.4 ms |
| **Genetic Algorithm (GA)** | 40.1062 ± 2.0945 | 182.36 min | 41.44 km | 241.7 ms |
| **Ant Colony Optimization (ACO)** | 33.2121 ± 0.0226 | 152.01 min | 34.55 km | 472.6 ms |
| **Google OR-Tools CVRPTW** | 32.5565 | 149.80 min | 34.05 km | 2092.0 ms |
| **Dijkstra Nearest-Neighbor** | 44.4639 | 202.94 min | 46.12 km | 86.2 ms |

## Problem Scale: N = 50 Customer Nodes

| Algorithm | Cost (Mean ± Std) | Travel Time (min) | Distance (km) | Wall-Clock Runtime (ms) |
| :--- | :--- | :--- | :--- | :--- |
| **Hybrid QPSO + Exact-Cluster** | 116.2518 ± 4.3461 | 535.35 min | 122.88 km | 2568.6 ms |
| **Quantum-Inspired PSO (QPSO)** | 116.2518 ± 4.3461 | 535.35 min | 122.88 km | 1966.5 ms |
| **Genetic Algorithm (GA)** | 96.4323 ± 3.9106 | 444.52 min | 102.63 km | 1701.9 ms |
| **Ant Colony Optimization (ACO)** | 64.9857 ± 0.8745 | 294.74 min | 67.80 km | 3494.1 ms |
| **Google OR-Tools CVRPTW** | 67.9029 | 304.25 min | 69.96 km | 2556.4 ms |
| **Dijkstra Nearest-Neighbor** | 79.2790 | 359.77 min | 82.58 km | 435.0 ms |

## Problem Scale: N = 100 Customer Nodes

| Algorithm | Cost (Mean ± Std) | Travel Time (min) | Distance (km) | Wall-Clock Runtime (ms) |
| :--- | :--- | :--- | :--- | :--- |
| **Hybrid QPSO + Exact-Cluster** | 253.3162 ± 1.5074 | 1164.38 min | 267.04 km | 16540.3 ms |
| **Quantum-Inspired PSO (QPSO)** | 253.3162 ± 1.5074 | 1164.38 min | 267.04 km | 14075.9 ms |
| **Genetic Algorithm (GA)** | 188.3810 ± 8.1024 | 875.83 min | 200.27 km | 12237.8 ms |
| **Ant Colony Optimization (ACO)** | 117.6082 ± 0.6569 | 528.54 min | 120.26 km | 42515.6 ms |
| **Google OR-Tools CVRPTW** | 117.9295 | 540.92 min | 123.75 km | 4127.6 ms |
| **Dijkstra Nearest-Neighbor** | 135.1480 | 616.87 min | 142.19 km | 2920.2 ms |

## Key Architectural Findings
1. **Cluster Sub-Solver**: Intra-cluster sub-tours are solved exactly via Held-Karp dynamic programming, which is tractable at the cluster sizes used here (<= 10-12 nodes) and guarantees the optimal sub-tour for each cluster.
2. **Dynamic Re-Optimization**: Local re-solving affected clusters only (instead of the full network) after a traffic disruption is architecturally faster than a full re-solve, since unaffected clusters keep their cached sub-tours - see the reoptimize benchmark for measured speedup on a specific run.
3. **Solution Quality**: See the tables above for how each algorithm's solution quality and runtime actually compare at each problem scale - results vary by scale and are reported as measured, not assumed.
