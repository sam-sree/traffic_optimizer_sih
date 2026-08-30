import os
import sys
import random

# Ensure backend package is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.graph.ingestion import get_bengaluru_graph
from backend.app.graph.traffic_simulator import DynamicTrafficSimulator
from backend.app.solvers.base import RoutingProblem, CustomerDemand
from backend.app.solvers.classical.shortest_path import ShortestPathSolver
from backend.app.solvers.classical.ortools_solver import ORToolsSolver
from backend.app.solvers.classical.ga_solver import GASolver
from backend.app.solvers.classical.aco_solver import ACOSolver
from backend.app.solvers.qpso.qpso_solver import QPSOSolver
from backend.app.solvers.hybrid_orchestrator import HybridQuantumOrchestrator

def run_phase6_head_to_head():
    print("=" * 80)
    print("Phase 6: Full 6-Algorithm Head-to-Head Benchmark Verification")
    print("=" * 80)

    # 1. Load Graph and Traffic Simulator
    G = get_bengaluru_graph()
    sim = DynamicTrafficSimulator(G, initial_time_hours=8.5)
    
    nodes = list(G.nodes())
    random.seed(42)
    depot_node = nodes[0]
    customer_nodes = random.sample(nodes[1:], 25)

    customers = [
        CustomerDemand(node_id=n, demand_units=random.choice([10.0, 15.0, 20.0]))
        for n in customer_nodes
    ]

    problem = RoutingProblem(
        graph=G,
        traffic_simulator=sim,
        depot_node=depot_node,
        customers=customers,
        num_vehicles=5,
        vehicle_capacity=65.0
    )

    print(f"[Phase 6] Instance: 25 customers, {problem.num_vehicles} vehicles (Capacity: {problem.vehicle_capacity} u)")

    solvers = [
        HybridQuantumOrchestrator(max_cluster_size=10, qpso_particles=30, qpso_iterations=80, seed=42),
        QPSOSolver(num_particles=40, max_iterations=100, seed=42),
        GASolver(pop_size=40, generations=100, seed=42),
        ACOSolver(num_ants=25, iterations=80, seed=42),
        ORToolsSolver(time_limit_sec=2.0),
        ShortestPathSolver(use_astar=False)
    ]

    results = []
    for s in solvers:
        res = s.solve(problem)
        results.append(res)

    print("\n" + "=" * 80)
    print(f"{'ALGORITHM':<32} | {'COST':<8} | {'TIME (min)':<10} | {'DIST (km)':<10} | {'WALL TIME':<10}")
    print("=" * 80)
    for r in results:
        status_flag = "" if r.is_feasible else " (INFEASIBLE)"
        name = r.solver_name + status_flag
        print(f"{name:<32} | {r.total_cost:<8.4f} | {r.total_time_sec/60.0:<10.2f} | {r.total_distance_m/1000.0:<10.2f} | {r.wall_time_sec*1000:<8.1f} ms")
    print("=" * 80)

    # Verification assertions
    for r in results:
        assert r.is_feasible, f"Solver {r.solver_name} failed feasibility check!"

    print("\nPhase 6 Verification Succeeded! All 6 head-to-head algorithms validated.")
    print("=" * 80)

if __name__ == "__main__":
    run_phase6_head_to_head()
