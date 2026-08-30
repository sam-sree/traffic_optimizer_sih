import numpy as np
from typing import Tuple, List, Dict, Callable

def build_intra_cluster_tsp_qubo(
    cost_matrix: np.ndarray,
    penalty_weight: float = 50.0
) -> Tuple[np.ndarray, Callable[[np.ndarray], List[int]]]:
    """
    Transforms an N x N intra-cluster distance/travel time matrix into a QUBO matrix Q (size N^2 x N^2).
    Minimizes: x^T Q x, where x_it is binary (node i visited at step t).
    Returns (Q, decode_function).
    """
    N = cost_matrix.shape[0]
    K = N * N # Total binary variables
    Q = np.zeros((K, K), dtype=float)

    def var_idx(i: int, t: int) -> int:
        return i * N + t

    # 1. Travel cost objective: sum_{i,j,t} c_{ij} * x_{i,t} * x_{j, (t+1)%N}
    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            c_ij = cost_matrix[i, j]
            for t in range(N):
                t_next = (t + 1) % N
                u = var_idx(i, t)
                v = var_idx(j, t_next)
                if u > v:
                    u, v = v, u
                Q[u, v] += c_ij / 2.0
                Q[v, u] += c_ij / 2.0

    # 2. Penalty A: Each node i visited exactly once -> A * (sum_t x_{i,t} - 1)^2
    A = penalty_weight
    for i in range(N):
        for t1 in range(N):
            u = var_idx(i, t1)
            # Linear diagonal term: A * (-2 * x + x^2) = -A * x
            Q[u, u] -= A
            for t2 in range(t1 + 1, N):
                v = var_idx(i, t2)
                # Off-diagonal cross term: 2 * A * x1 * x2
                Q[u, v] += A
                Q[v, u] += A

    # 3. Penalty B: Each step t has exactly one node -> B * (sum_i x_{i,t} - 1)^2
    B = penalty_weight
    for t in range(N):
        for i1 in range(N):
            u = var_idx(i1, t)
            # Diagonal term
            Q[u, u] -= B
            for i2 in range(i1 + 1, N):
                v = var_idx(i2, t)
                # Off-diagonal cross term
                Q[u, v] += B
                Q[v, u] += B

    def decode_bitstring_to_tour(bitstring: np.ndarray) -> List[int]:
        """Decodes binary array x into ordered node permutation tour."""
        grid = bitstring.reshape((N, N))
        tour = []
        for t in range(N):
            step_nodes = grid[:, t]
            if np.sum(step_nodes) == 1:
                tour.append(int(np.argmax(step_nodes)))
            else:
                # Heuristic extraction if non-ideal bitstring
                best_n = int(np.argmax(step_nodes))
                tour.append(best_n)

        # Fix duplicate or missing nodes
        seen = set()
        cleaned_tour = []
        for node in tour:
            if node not in seen:
                seen.add(node)
                cleaned_tour.append(node)
        
        for missing in range(N):
            if missing not in seen:
                cleaned_tour.append(missing)

        return cleaned_tour

    return Q, decode_bitstring_to_tour
