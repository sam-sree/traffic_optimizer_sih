import time
import numpy as np
from typing import List, Dict, Tuple, Optional
from backend.app.solvers.base import BaseSolver, RoutingProblem, RoutingSolution, VehicleRoute
from backend.app.solvers.classical.shortest_path import compute_all_pairs_matrix
from backend.app.solvers.qpso.quantum_ops import (
    initialize_swarm,
    qpso_position_update,
    decode_random_key_to_routes
)

class QPSOSolver(BaseSolver):
    """
    Quantum-Inspired Particle Swarm Optimization (QPSO) solver for VRP.
    Uses Delta Potential Well Quantum Wave Function Sampling (no classical velocity vector).
    """
    def __init__(self, num_particles: int = 40, max_iterations: int = 150, beta_start: float = 1.0, beta_end: float = 0.4, seed: Optional[int] = None):
        super().__init__("Quantum-Inspired PSO (QPSO)")
        self.num_particles = num_particles
        self.max_iterations = max_iterations
        self.beta_start = beta_start
        self.beta_end = beta_end
        self.seed = seed

    def solve(self, problem: RoutingProblem) -> RoutingSolution:
        start_time = time.time()
        if self.seed is not None:
            np.random.seed(self.seed)

        customer_ids = [c.node_id for c in problem.customers]
        dim = len(customer_ids)
        if dim == 0:
            return RoutingSolution(solver_name=self.name, problem=problem, routes=[])

        # Precompute cost matrix and path matrix
        all_nodes = [problem.depot_node] + customer_ids
        cost_matrix, path_matrix = compute_all_pairs_matrix(
            problem.graph, problem.traffic_simulator, all_nodes, objective="time"
        )

        # 1. Initialize Swarm
        positions = initialize_swarm(self.num_particles, dim)
        p_bests = np.copy(positions)
        p_best_costs = np.full(self.num_particles, float('inf'))

        g_best = None
        g_best_cost = float('inf')
        g_best_routes = []

        convergence_curve = []

        # Evaluate initial swarm
        for i in range(self.num_particles):
            routes, cost, feasible = decode_random_key_to_routes(
                positions[i], customer_ids, problem, cost_matrix, path_matrix
            )
            p_best_costs[i] = cost
            if cost < g_best_cost:
                g_best_cost = cost
                g_best = np.copy(positions[i])
                g_best_routes = routes

        convergence_curve.append(g_best_cost)

        # 2. Main Optimization Loop
        for iter_idx in range(1, self.max_iterations):
            # Contraction-Expansion coefficient decay
            beta = self.beta_start - (self.beta_start - self.beta_end) * (iter_idx / self.max_iterations)

            # Update swarm positions via Quantum Delta Potential Well wave function
            positions = qpso_position_update(positions, p_bests, g_best, beta)

            # Evaluate new positions
            for i in range(self.num_particles):
                routes, cost, feasible = decode_random_key_to_routes(
                    positions[i], customer_ids, problem, cost_matrix, path_matrix
                )
                
                # Update Personal Best
                if cost < p_best_costs[i]:
                    p_best_costs[i] = cost
                    p_bests[i] = np.copy(positions[i])

                # Update Swarm Global Best
                if cost < g_best_cost:
                    g_best_cost = cost
                    g_best = np.copy(positions[i])
                    g_best_routes = routes

            convergence_curve.append(g_best_cost)

        sol = RoutingSolution(
            solver_name=self.name,
            problem=problem,
            routes=g_best_routes,
            wall_time_sec=time.time() - start_time,
            convergence_curve=convergence_curve,
            metadata={"num_particles": self.num_particles, "iterations": self.max_iterations}
        )
        sol.compute_aggregates()
        return sol
