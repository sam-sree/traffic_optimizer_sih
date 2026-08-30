import time
import random
import numpy as np
from typing import List, Dict, Tuple, Optional

from backend.app.solvers.base import BaseSolver, RoutingProblem, RoutingSolution, VehicleRoute
from backend.app.solvers.classical.shortest_path import compute_all_pairs_matrix
from backend.app.solvers.qpso.quantum_ops import decode_random_key_to_routes

class ACOSolver(BaseSolver):
    """
    Ant Colony Optimization (ACO) baseline solver for VRP.
    Uses artificial ants, distance heuristic visibility, and rank-based pheromone evaporation/deposition.
    """
    def __init__(
        self,
        num_ants: int = 30,
        iterations: int = 100,
        alpha: float = 1.0,
        beta: float = 2.5,
        rho: float = 0.1,
        Q_const: float = 100.0,
        seed: Optional[int] = None
    ):
        super().__init__("Ant Colony Optimization (ACO)")
        self.num_ants = num_ants
        self.iterations = iterations
        self.alpha = alpha
        self.beta = beta
        self.rho = rho
        self.Q_const = Q_const
        self.seed = seed

    def solve(self, problem: RoutingProblem) -> RoutingSolution:
        start_time = time.time()
        if self.seed is not None:
            random.seed(self.seed)
            np.random.seed(self.seed)

        customer_ids = [c.node_id for c in problem.customers]
        N = len(customer_ids)
        if N == 0:
            return RoutingSolution(solver_name=self.name, problem=problem, routes=[])

        # Precompute cost matrix and path matrix
        all_nodes = [problem.depot_node] + customer_ids
        cost_matrix, path_matrix = compute_all_pairs_matrix(
            problem.graph, problem.traffic_simulator, all_nodes, objective="time"
        )

        # Build N x N distance & visibility heuristic matrix
        dist_mat = np.zeros((N, N))
        eta_mat = np.zeros((N, N))
        for i in range(N):
            for j in range(N):
                if i != j:
                    u, v = customer_ids[i], customer_ids[j]
                    d = max(0.1, cost_matrix[(u, v)])
                    dist_mat[i, j] = d
                    eta_mat[i, j] = 1.0 / d

        # Initialize Pheromone Matrix tau
        tau = np.full((N, N), 1.0)

        best_cost = float('inf')
        best_perm = []
        best_routes = []
        convergence_curve = []

        # Function to decode permutation to routes
        def decode_perm(perm: List[int]) -> Tuple[float, List[VehicleRoute]]:
            pos = np.zeros(N)
            for rank, c_id in enumerate(perm):
                idx = customer_ids.index(c_id)
                pos[idx] = rank
            routes, cost, _ = decode_random_key_to_routes(pos, customer_ids, problem, cost_matrix, path_matrix)
            return cost, routes

        # Main ACO Loop
        for iter_idx in range(self.iterations):
            ant_perms = []
            ant_costs = []
            ant_routes = []

            # 1. Ant Tour Construction
            for ant in range(self.num_ants):
                start_node_idx = random.randint(0, N - 1)
                tour_indices = [start_node_idx]
                unvisited = set(range(N)) - {start_node_idx}

                curr = start_node_idx
                while unvisited:
                    unvisited_list = list(unvisited)
                    # Compute transition probabilities P_{curr, u} = tau^\alpha * eta^\beta
                    probs = []
                    for u in unvisited_list:
                        p = (tau[curr, u] ** self.alpha) * (eta_mat[curr, u] ** self.beta)
                        probs.append(p)
                    
                    total_p = sum(probs)
                    if total_p == 0:
                        next_idx = random.choice(unvisited_list)
                    else:
                        probs = [p / total_p for p in probs]
                        next_idx = np.random.choice(unvisited_list, p=probs)

                    tour_indices.append(next_idx)
                    unvisited.remove(next_idx)
                    curr = next_idx

                perm = [customer_ids[idx] for idx in tour_indices]
                cost, routes = decode_perm(perm)

                ant_perms.append(tour_indices)
                ant_costs.append(cost)
                ant_routes.append(routes)

                if cost < best_cost:
                    best_cost = cost
                    best_perm = perm
                    best_routes = routes

            convergence_curve.append(best_cost)

            # 2. Pheromone Evaporation
            tau = (1.0 - self.rho) * tau

            # 3. Rank-Based Pheromone Deposition (Top 5 ants + Global Best)
            rank_indices = np.argsort(ant_costs)[:min(5, self.num_ants)]
            for rank_pos, idx in enumerate(rank_indices):
                weight = (5 - rank_pos) # Rank weight
                tour_idx = ant_perms[idx]
                delta_tau = (weight * self.Q_const) / max(1.0, ant_costs[idx])
                for u, v in zip(tour_idx[:-1], tour_idx[1:]):
                    tau[u, v] += delta_tau
                    tau[v, u] += delta_tau

        sol = RoutingSolution(
            solver_name=self.name,
            problem=problem,
            routes=best_routes,
            wall_time_sec=time.time() - start_time,
            convergence_curve=convergence_curve,
            metadata={"num_ants": self.num_ants, "iterations": self.iterations}
        )
        sol.compute_aggregates()
        return sol
