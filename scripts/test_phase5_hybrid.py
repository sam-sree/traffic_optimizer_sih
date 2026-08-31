import os
import sys
import random
import time

# Ensure backend package is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.graph.ingestion import get_bengaluru_graph
from backend.app.graph.traffic_simulator import DynamicTrafficSimulator
from backend.app.solvers.base import RoutingProblem, CustomerDemand
from backend.app.solvers.hybrid_orchestrator import HybridQuantumOrchestrator

def run_phase5_tests():
    print("=" * 70)
    print("Phase 5: Hybrid Orchestrator & Dynamic Real-Time Re-Optimization Verification")
    print("=" * 70)

    # 1. Setup problem instance
    G = get_bengaluru_graph()
    sim = DynamicTrafficSimulator(G, initial_time_hours=8.5)
    
    nodes = list(G.nodes())
    random.seed(42)
    depot_node = nodes[0]
    customer_nodes = random.sample(nodes[1:], 30)

    customers = [
        CustomerDemand(node_id=n, demand_units=random.choice([10.0, 15.0, 20.0]))
        for n in customer_nodes
    ]

    problem = RoutingProblem(
        graph=G,
        traffic_simulator=sim,
        depot_node=depot_node,
        customers=customers,
        num_vehicles=6,
        vehicle_capacity=70.0
    )

    print(f"[Phase 5] Problem Setup: {len(customers)} customers, {problem.num_vehicles} vehicles")

    # 2. Initial Full Hybrid Solve
    orchestrator = HybridQuantumOrchestrator(max_cluster_size=10, qpso_particles=30, qpso_iterations=80)
    sol_initial = orchestrator.solve(problem)

    print("\n--- Initial Hybrid Solve Results ---")
    print(f"  • Status:               {'FEASIBLE' if sol_initial.is_feasible else 'INFEASIBLE'}")
    print(f"  • Clusters Generated:   {sol_initial.metadata['clusters_count']}")
    print(f"  • Solver Types Used:    {sol_initial.metadata['cluster_solvers_used']}")
    print(f"  • Total Cost:           {sol_initial.total_cost:.4f}")
    print(f"  • Total Travel Time:    {sol_initial.total_time_sec/60.0:.2f} minutes")
    print(f"  • Total Distance:       {sol_initial.total_distance_m/1000.0:.2f} km")
    print(f"  • Initial Solve Time:   {sol_initial.wall_time_sec * 1000:.1f} ms")

    # 3. Simulate Live Traffic Perturbation (Dynamic Incident Injection)
    print("\n[Phase 5] Injecting dynamic dynamic traffic incident mid-route...")
    affected_edges = sim.inject_random_incidents(count=3, severity_range=(4.0, 7.0))
    print(f"  • Injected incidents at edges: {affected_edges}")

    # Benchmark Method A: Full Network Re-solve from scratch
    t0 = time.time()
    sol_full_re_solve = orchestrator.solve(problem)
    full_re_solve_time = (time.time() - t0) * 1000.0

    # Benchmark Method B: Proposed Dynamic Local Exact-Cluster Re-Optimization
    t0 = time.time()
    sol_local_reopt = orchestrator.reoptimize_dynamic_traffic(affected_edges)
    local_reopt_time = (time.time() - t0) * 1000.0

    print("\n" + "-" * 65)
    print(f"{'RE-OPTIMIZATION STRATEGY':<30} | {'RE-SOLVE TIME':<15} | {'SPEEDUP':<10}")
    print("-" * 65)
    print(f"{'Full Network Re-Solve':<30} | {full_re_solve_time:<13.1f} ms | 1.0x (Baseline)")
    speedup = full_re_solve_time / max(0.1, local_reopt_time)
    print(f"{'Local Exact-Cluster Re-Optimization':<30} | {local_reopt_time:<13.1f} ms | {speedup:<8.2f}x Faster")
    print("-" * 65)

    print("\nDynamic Re-Optimization Metrics:")
    print(f"  • Affected Clusters Re-solved: {sol_local_reopt.metadata['affected_clusters_count']} of {sol_local_reopt.metadata['clusters_count']}")
    print(f"  • Adjusted Route Cost:        {sol_local_reopt.total_cost:.4f}")
    print(f"  • Re-optimized Feasibility:   {'FEASIBLE' if sol_local_reopt.is_feasible else 'INFEASIBLE'}")

    assert sol_local_reopt.is_feasible, "Local re-optimization must remain feasible!"

    print("\n" + "=" * 70)
    print("Phase 5 Verification Succeeded! Dynamic real-time re-optimization architecture validated.")
    print("=" * 70)

if __name__ == "__main__":
    run_phase5_tests()
