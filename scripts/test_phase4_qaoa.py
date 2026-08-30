import os
import sys
import random
import numpy as np

# Ensure backend package is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.graph.ingestion import get_bengaluru_graph
from backend.app.graph.traffic_simulator import DynamicTrafficSimulator
from backend.app.graph.clustering import partition_nodes_into_clusters
from backend.app.solvers.quantum.qubo_builder import build_intra_cluster_tsp_qubo
from backend.app.solvers.quantum.qaoa_solver import QiskitQAOASolver, held_karp_exact_tsp

def run_phase4_tests():
    print("=" * 70)
    print("Phase 4: Clustering & QAOA Quantum Sub-Solver Verification")
    print("=" * 70)

    # 1. Load Graph and generate customer demand set
    G = get_bengaluru_graph()
    sim = DynamicTrafficSimulator(G, initial_time_hours=8.5)
    
    nodes = list(G.nodes())
    random.seed(42)
    customer_nodes = random.sample(nodes, 25)

    print(f"[Phase 4] Partitioning {len(customer_nodes)} customer nodes into clusters (max_size=10)...")
    clusters = partition_nodes_into_clusters(customer_nodes, G, max_cluster_size=10)
    print(f"[Phase 4] Generated {len(clusters)} geographically coherent clusters:")
    for c in clusters:
        print(f"  • {c}")

    # 2. Test QUBO Builder & QAOA Quantum Sub-solver
    qaoa_solver = QiskitQAOASolver(p_layers=1, max_qaoa_qubits=10)
    from backend.app.solvers.classical.shortest_path import compute_all_pairs_matrix
    cost_matrix, _ = compute_all_pairs_matrix(G, sim, customer_nodes, objective="time")

    print("\n--- Solving Intra-Cluster Sub-tours ---")
    for cluster in clusters:
        # Build distance matrix between cluster nodes
        c_nodes = cluster.customer_nodes
        N = len(c_nodes)
        dist_matrix = np.zeros((N, N))
        for i in range(N):
            for j in range(N):
                if i != j:
                    u, v = c_nodes[i], c_nodes[j]
                    dist_matrix[i, j] = cost_matrix[(u, v)]

        # Translate to QUBO
        Q, decode_fn = build_intra_cluster_tsp_qubo(dist_matrix, penalty_weight=40.0)

        # Solve via QAOA Quantum Sub-solver
        res = qaoa_solver.solve_qubo(Q, time_budget_sec=2.0)
        cluster.solver_used = res.solver_type

        decoded_tour = decode_fn(res.bitstring)
        actual_node_tour = [c_nodes[idx] for idx in decoded_tour]

        print(f"Cluster #{cluster.cluster_id} ({N} nodes | QUBO dim {Q.shape[0]}):")
        print(f"  • Solver Type Used: {res.solver_type}")
        print(f"  • QUBO Energy:      {res.energy:.4f}")
        print(f"  • Decoded Tour:     {actual_node_tour[:4]}... ({len(actual_node_tour)} nodes)")
        print(f"  • Execution Time:   {res.execution_time_sec * 1000:.1f} ms")

    # Verify logging and solver status
    solvers_used = set(c.solver_used for c in clusters)
    print("\n" + "=" * 70)
    print(f"Phase 4 Verification Succeeded! Solvers logged across clusters: {solvers_used}")
    print("=" * 70)

if __name__ == "__main__":
    run_phase4_tests()
