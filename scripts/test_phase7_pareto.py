import os
import sys
import random

# Ensure backend package is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.graph.ingestion import get_bengaluru_graph
from backend.app.graph.traffic_simulator import DynamicTrafficSimulator
from backend.app.solvers.base import RoutingProblem, CustomerDemand
from backend.app.solvers.qpso.moqpso_solver import MOQPSOSolver

def run_phase7_tests():
    print("=" * 75)
    print("Phase 7: Multi-Objective Pareto Optimization (MO-QPSO) Verification")
    print("=" * 75)

    G = get_bengaluru_graph()
    sim = DynamicTrafficSimulator(G, initial_time_hours=8.5)
    
    nodes = list(G.nodes())
    random.seed(42)
    depot_node = nodes[0]
    customer_nodes = random.sample(nodes[1:], 20)

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
        vehicle_capacity=60.0
    )

    mo_solver = MOQPSOSolver(num_particles=30, max_iterations=80, archive_capacity=30, seed=42)
    pareto_archive, sol = mo_solver.solve_pareto_front(problem)

    print(f"[Phase 7] Extracted {len(pareto_archive)} Non-Dominated Pareto Trade-Off Points:")
    print("-" * 75)
    print(f"{'POINT':<6} | {'TIME (min)':<12} | {'DIST (km)':<10} | {'CONGESTION':<12} | {'CO2 (kg)':<10}")
    print("-" * 75)
    for idx, pt in enumerate(pareto_archive[:10]): # Display first 10
        t_min = pt.objectives[0] / 60.0
        d_km = pt.objectives[1] / 1000.0
        c_score = pt.objectives[2]
        e_kg = pt.objectives[3] / 1000.0
        print(f"#{idx+1:<5} | {t_min:<12.2f} | {d_km:<10.2f} | {c_score:<12.2f} | {e_kg:<10.2f}")
    print("-" * 75)

    assert len(pareto_archive) > 0, "Pareto Archive must contain non-dominated trade-off solutions!"

    print("\n" + "=" * 75)
    print("Phase 7 Verification Succeeded! Multi-objective Pareto front search validated.")
    print("=" * 75)

if __name__ == "__main__":
    run_phase7_tests()
