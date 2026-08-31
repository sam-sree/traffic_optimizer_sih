import os
import json
import time
import numpy as np
from typing import List, Dict, Any, Tuple

from backend.app.graph.ingestion import get_bengaluru_graph
from backend.app.graph.traffic_simulator import DynamicTrafficSimulator
from backend.app.solvers.base import RoutingProblem, CustomerDemand, RoutingSolution
from backend.app.solvers.classical.shortest_path import ShortestPathSolver
from backend.app.solvers.classical.ortools_solver import ORToolsSolver
from backend.app.solvers.classical.ga_solver import GASolver
from backend.app.solvers.classical.aco_solver import ACOSolver
from backend.app.solvers.qpso.qpso_solver import QPSOSolver
from backend.app.solvers.hybrid_orchestrator import HybridQuantumOrchestrator

class BenchmarkRunner:
    """
    Statistical Benchmarking Engine: Executes head-to-head experiments across
    all 6 algorithms and problem sizes, gathering mean +/- std metrics over multiple seeds.
    """
    def __init__(self, num_seeds: int = 5):
        self.num_seeds = num_seeds
        self.G = get_bengaluru_graph()
        self.sim = DynamicTrafficSimulator(self.G, initial_time_hours=8.5)

    def run_benchmark_suite(self, sizes: List[int] = [20, 50, 100]) -> Dict[str, Any]:
        data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'demand_sets'))
        suite_results = {}

        for size in sizes:
            file_path = os.path.join(data_dir, f"demand_{size}.json")
            if not os.path.exists(file_path):
                print(f"[BenchmarkRunner] Warning: Demand file {file_path} not found. Skipping size {size}.")
                continue

            with open(file_path, "r") as f:
                instance_data = json.load(f)

            problem = self._build_problem_from_json(instance_data)
            print(f"\n" + "=" * 70)
            print(f"[BenchmarkRunner] Running Benchmark Suite for N={size} nodes ({self.num_seeds} seeds per algorithm)...")
            print("=" * 70)

            instance_results = self._evaluate_instance(problem, size)
            suite_results[f"n_{size}"] = instance_results

        return suite_results

    def _build_problem_from_json(self, data: dict) -> RoutingProblem:
        customers = []
        for c in data["customers"]:
            customers.append(CustomerDemand(
                node_id=c["node_id"],
                demand_units=c["demand_units"],
                ready_time=c.get("ready_time", 0.0),
                due_time=c.get("due_time", 86400.0),
                service_time=c.get("service_time", 300.0),
                lat=c.get("lat"),
                lon=c.get("lon")
            ))
        return RoutingProblem(
            graph=self.G,
            traffic_simulator=self.sim,
            depot_node=data["depot_node"],
            customers=customers,
            num_vehicles=data["num_vehicles"],
            vehicle_capacity=data["vehicle_capacity"]
        )

    def _evaluate_instance(self, problem: RoutingProblem, size: int) -> Dict[str, Any]:
        algorithms = [
            ("Hybrid QPSO + Exact-Cluster", True),
            ("Quantum-Inspired PSO (QPSO)", True),
            ("Genetic Algorithm (GA)", True),
            ("Ant Colony Optimization (ACO)", True),
            ("Google OR-Tools CVRPTW", False),
            ("Dijkstra Nearest-Neighbor", False)
        ]

        instance_summary = {}

        for alg_name, is_stochastic in algorithms:
            print(f"  • Evaluating {alg_name}...")
            seeds_count = self.num_seeds if is_stochastic else 1
            
            costs = []
            times_sec = []
            dists_m = []
            runtimes_ms = []
            convergence_curves = []
            cluster_solvers_used_list = []

            for s in range(seeds_count):
                solver = self._instantiate_solver(alg_name, seed=42 + s, size=size)
                sol = solver.solve(problem)

                costs.append(sol.total_cost)
                times_sec.append(sol.total_time_sec)
                dists_m.append(sol.total_distance_m)
                runtimes_ms.append(sol.wall_time_sec * 1000.0)
                
                if sol.convergence_curve:
                    convergence_curves.append(sol.convergence_curve)
                if "cluster_solvers_used" in sol.metadata:
                    cluster_solvers_used_list.append(sol.metadata["cluster_solvers_used"])

            # Compute statistics
            avg_conv = []
            if convergence_curves:
                min_len = min(len(c) for c in convergence_curves)
                trimmed = [c[:min_len] for c in convergence_curves]
                avg_conv = list(np.mean(trimmed, axis=0))

            instance_summary[alg_name] = {
                "algorithm": alg_name,
                "is_stochastic": is_stochastic,
                "seeds_evaluated": seeds_count,
                "cost_mean": float(np.mean(costs)),
                "cost_std": float(np.std(costs)),
                "time_min_mean": float(np.mean(times_sec) / 60.0),
                "time_min_std": float(np.std(times_sec) / 60.0),
                "dist_km_mean": float(np.mean(dists_m) / 1000.0),
                "dist_km_std": float(np.std(dists_m) / 1000.0),
                "runtime_ms_mean": float(np.mean(runtimes_ms)),
                "runtime_ms_std": float(np.std(runtimes_ms)),
                "convergence_curve": avg_conv,
                "cluster_solvers_used_summary": cluster_solvers_used_list[0] if cluster_solvers_used_list else {}
            }

        return instance_summary

    def _instantiate_solver(self, alg_name: str, seed: int, size: int):
        # Search budget must scale with problem size (search-space dimensionality
        # grows with the number of customers) - fixed budgets starve larger instances.
        particles = max(30, size)
        iterations = max(70, size * 2)

        if alg_name == "Hybrid QPSO + Exact-Cluster":
            return HybridQuantumOrchestrator(max_cluster_size=10, qpso_particles=max(25, size), qpso_iterations=max(60, size * 2), seed=seed)
        elif alg_name == "Quantum-Inspired PSO (QPSO)":
            return QPSOSolver(num_particles=particles, max_iterations=iterations, seed=seed)
        elif alg_name == "Genetic Algorithm (GA)":
            return GASolver(pop_size=particles, generations=iterations, seed=seed)
        elif alg_name == "Ant Colony Optimization (ACO)":
            return ACOSolver(num_ants=max(20, size // 2), iterations=iterations, seed=seed)
        elif alg_name == "Google OR-Tools CVRPTW":
            return ORToolsSolver(time_limit_sec=1.5)
        elif alg_name == "Dijkstra Nearest-Neighbor":
            return ShortestPathSolver(use_astar=False)
        else:
            raise ValueError(f"Unknown algorithm: {alg_name}")
