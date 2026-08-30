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

def run_phase2_tests():
    print("=" * 70)
    print("Phase 2: Classical Baselines Verification (Dijkstra/A* & OR-Tools)")
    print("=" * 70)

    # 1. Load Graph and Traffic Simulator
    G = get_bengaluru_graph()
    sim = DynamicTrafficSimulator(G, initial_time_hours=8.5)
    
    # Select depot and customer nodes
    nodes = list(G.nodes())
    random.seed(42)
    depot_node = nodes[0]
    customer_nodes = random.sample(nodes[1:], 12)

    customers = []
    for c_node in customer_nodes:
        demand = random.choice([10.0, 15.0, 20.0, 25.0])
        ready = random.uniform(0.0, 3600.0)      # Ready within first hour
        due = ready + random.uniform(7200.0, 14400.0) # Due in 2-4 hours
        customers.append(CustomerDemand(
            node_id=c_node,
            demand_units=demand,
            ready_time=ready,
            due_time=due
        ))

    problem = RoutingProblem(
        graph=G,
        traffic_simulator=sim,
        depot_node=depot_node,
        customers=customers,
        num_vehicles=4,
        vehicle_capacity=60.0
    )

    print(f"[Phase 2] Problem Setup:")
    print(f"  • Depot Node:        {depot_node}")
    print(f"  • Customer Nodes:    {len(customers)} customers")
    print(f"  • Fleet Size:        {problem.num_vehicles} vehicles (Capacity: {problem.vehicle_capacity} units)")

    # 2. Run Dijkstra Baseline
    dijkstra_solver = ShortestPathSolver(use_astar=False)
    sol_dijkstra = dijkstra_solver.solve(problem)
    print("\n--- Solver 1: Dijkstra Nearest-Neighbor ---")
    print(f"  • Status:           {'FEASIBLE' if sol_dijkstra.is_feasible else 'INFEASIBLE'}")
    print(f"  • Total Cost:       {sol_dijkstra.total_cost:.4f}")
    print(f"  • Total Time:       {sol_dijkstra.total_time_sec / 60.0:.2f} minutes")
    print(f"  • Total Distance:   {sol_dijkstra.total_distance_m / 1000.0:.2f} km")
    print(f"  • Routes Count:     {len(sol_dijkstra.routes)}")
    print(f"  • Wall Time:        {sol_dijkstra.wall_time_sec * 1000:.2f} ms")

    # 3. Run OR-Tools Baseline
    ortools_solver = ORToolsSolver(time_limit_sec=2.0)
    sol_ortools = ortools_solver.solve(problem)
    print("\n--- Solver 2: Google OR-Tools CVRPTW ---")
    print(f"  • Status:           {'FEASIBLE' if sol_ortools.is_feasible else 'INFEASIBLE'}")
    print(f"  • Total Cost:       {sol_ortools.total_cost:.4f}")
    print(f"  • Total Time:       {sol_ortools.total_time_sec / 60.0:.2f} minutes")
    print(f"  • Total Distance:   {sol_ortools.total_distance_m / 1000.0:.2f} km")
    print(f"  • Routes Count:     {len(sol_ortools.routes)}")
    print(f"  • Wall Time:        {sol_ortools.wall_time_sec * 1000:.2f} ms")

    # Verification assertions
    assert sol_dijkstra.is_feasible, "Dijkstra solution must be feasible!"
    assert sol_ortools.is_feasible, "OR-Tools solution must be feasible!"
    assert len(sol_ortools.routes) > 0, "OR-Tools must produce at least 1 route!"
    
    print("\n" + "=" * 70)
    print("Phase 2 Verification Succeeded! Classical baselines anchor correctness.")
    print("=" * 70)

if __name__ == "__main__":
    run_phase2_tests()
