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
from backend.app.solvers.qpso.qpso_solver import QPSOSolver

def run_phase3_tests():
    print("=" * 70)
    print("Phase 3: Quantum-Inspired PSO (QPSO) Verification")
    print("=" * 70)

    # 1. Load Graph and Traffic Simulator
    G = get_bengaluru_graph()
    sim = DynamicTrafficSimulator(G, initial_time_hours=8.5)
    
    nodes = list(G.nodes())
    random.seed(42)
    depot_node = nodes[0]
    customer_nodes = random.sample(nodes[1:], 15)

    customers = []
    for c_node in customer_nodes:
        demand = random.choice([10.0, 15.0, 20.0])
        customers.append(CustomerDemand(
            node_id=c_node,
            demand_units=demand,
            ready_time=0.0,
            due_time=86400.0
        ))

    problem = RoutingProblem(
        graph=G,
        traffic_simulator=sim,
        depot_node=depot_node,
        customers=customers,
        num_vehicles=5,
        vehicle_capacity=60.0
    )

    print(f"[Phase 3] Benchmark Setup: {len(customers)} customers, {problem.num_vehicles} vehicles")

    # 2. Run Baselines
    dijkstra = ShortestPathSolver().solve(problem)
    ortools = ORToolsSolver(time_limit_sec=2.0).solve(problem)

    # 3. Run QPSO Solver
    qpso_solver = QPSOSolver(num_particles=40, max_iterations=120, seed=42)
    qpso = qpso_solver.solve(problem)

    print("\n" + "-" * 60)
    print(f"{'SOLVER':<30} | {'COST':<8} | {'TIME (min)':<10} | {'DIST (km)':<10} | {'WALL TIME':<10}")
    print("-" * 60)
    print(f"{dijkstra.solver_name:<30} | {dijkstra.total_cost:<8.4f} | {dijkstra.total_time_sec/60.0:<10.2f} | {dijkstra.total_distance_m/1000.0:<10.2f} | {dijkstra.wall_time_sec*1000:<8.1f} ms")
    print(f"{ortools.solver_name:<30} | {ortools.total_cost:<8.4f} | {ortools.total_time_sec/60.0:<10.2f} | {ortools.total_distance_m/1000.0:<10.2f} | {ortools.wall_time_sec*1000:<8.1f} ms")
    print(f"{qpso.solver_name:<30} | {qpso.total_cost:<8.4f} | {qpso.total_time_sec/60.0:<10.2f} | {qpso.total_distance_m/1000.0:<10.2f} | {qpso.wall_time_sec*1000:<8.1f} ms")
    print("-" * 60)

    print("\nQPSO Convergence Profile:")
    print(f"  • Initial Swarm Cost:   {qpso.convergence_curve[0]:.4f}")
    print(f"  • Final Best Cost:      {qpso.convergence_curve[-1]:.4f}")
    print(f"  • Cost Improvement:     {((qpso.convergence_curve[0] - qpso.convergence_curve[-1]) / qpso.convergence_curve[0]) * 100:.2f}%")

    assert qpso.is_feasible, "QPSO solution must be feasible!"
    assert qpso.total_cost < dijkstra.total_cost, "QPSO should outperform simple nearest neighbor!"

    print("\n" + "=" * 70)
    print("Phase 3 Verification Succeeded! QPSO quantum delta potential well algorithm validated.")
    print("=" * 70)

if __name__ == "__main__":
    run_phase3_tests()
