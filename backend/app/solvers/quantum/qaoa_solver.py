import time
import numpy as np
from typing import Tuple, List

def held_karp_exact_tsp(cost_matrix: np.ndarray) -> Tuple[List[int], float]:
    """
    Exact Held-Karp dynamic programming solver for small TSP instances (N <= 12).
    Returns (best_tour, min_cost). Guaranteed optimal for the given cost matrix.
    """
    N = cost_matrix.shape[0]
    if N == 1:
        return [0], 0.0
    if N == 2:
        return [0, 1], cost_matrix[0, 1] + cost_matrix[1, 0]

    memo = {}

    def solve_dp(mask: int, u: int) -> Tuple[float, int]:
        if mask == (1 << N) - 1:
            return cost_matrix[u, 0], 0  # Return to start node 0

        state = (mask, u)
        if state in memo:
            return memo[state]

        min_cost = float('inf')
        best_next = -1

        for v in range(N):
            if not (mask & (1 << v)):
                new_cost = cost_matrix[u, v] + solve_dp(mask | (1 << v), v)[0]
                if new_cost < min_cost:
                    min_cost = new_cost
                    best_next = v

        memo[state] = (min_cost, best_next)
        return min_cost, best_next

    total_cost, _ = solve_dp(1, 0)

    # Reconstruct tour
    tour = [0]
    curr_mask = 1
    curr_u = 0
    while len(tour) < N:
        _, next_u = memo[(curr_mask, curr_u)]
        tour.append(next_u)
        curr_mask |= (1 << next_u)
        curr_u = next_u

    return tour, total_cost


class ClusterTSPSolver:
    """
    Exact intra-cluster sub-tour solver used by the Hybrid Orchestrator.

    Clusters are capped at a small size (<=10-12 nodes) specifically so that an
    exact algorithm (Held-Karp dynamic programming) is tractable and guarantees
    the optimal sub-tour for each cluster - no approximation needed at this scale.

    Note: an earlier version of this file claimed to run a QAOA quantum-circuit
    simulation via Qiskit for this step. It didn't actually build or execute any
    quantum circuit - it generated random bits and reported that as the result,
    falling back to this exact Held-Karp solver whenever the "budget" was
    exceeded (which was almost always, for any cluster above ~3 nodes). That
    fabricated path has been removed. This solver now always uses the real,
    correct, exact algorithm directly.
    """
    def __init__(self):
        self.name = "Exact Cluster Sub-tour Solver (Held-Karp)"

    def solve_cluster(self, dist_matrix: np.ndarray) -> Tuple[List[int], float, float]:
        """
        Solve a single cluster's TSP sub-tour exactly.
        Returns (tour_as_local_indices, tour_cost, wall_time_sec).
        """
        start_time = time.time()
        tour, cost = held_karp_exact_tsp(dist_matrix)
        elapsed = time.time() - start_time
        return tour, cost, elapsed
