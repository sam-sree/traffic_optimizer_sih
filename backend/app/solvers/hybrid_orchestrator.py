import time
import numpy as np
from typing import List, Dict, Tuple, Optional, Set, Any

from backend.app.solvers.base import BaseSolver, RoutingProblem, RoutingSolution, VehicleRoute
from backend.app.solvers.classical.shortest_path import compute_all_pairs_matrix
from backend.app.graph.clustering import partition_nodes_into_clusters, Cluster
from backend.app.solvers.quantum.qaoa_solver import ClusterTSPSolver
from backend.app.solvers.qpso.quantum_ops import initialize_swarm, qpso_position_update

class HybridQuantumOrchestrator(BaseSolver):
    """
    Cluster-Decomposition Hybrid Architecture:
    1. Cluster-First Decomposition into <= 10-12 node sub-clusters.
    2. Exact Held-Karp sub-solver for intra-cluster sub-tours (guaranteed optimal
       at this scale - see ClusterTSPSolver for why an exact method is used here
       instead of an approximate one).
    3. Quantum-Inspired PSO (QPSO) for global cluster sequencing & vehicle route stitching.
    4. Dynamic Real-Time Re-Optimization: local sub-tour re-solve only on affected
       clusters + QPSO re-stitching, so a traffic disruption doesn't require a
       full network re-solve.
    """
    def __init__(
        self,
        max_cluster_size: int = 10,
        qpso_particles: int = 30,
        qpso_iterations: int = 100,
        seed: Optional[int] = 42,
        **kwargs  # accepts and ignores legacy params (p_layers, max_qaoa_qubits) for backward compatibility
    ):
        super().__init__("Hybrid QPSO + Exact-Cluster")
        self.max_cluster_size = max_cluster_size
        self.cluster_solver = ClusterTSPSolver()
        self.qpso_particles = qpso_particles
        self.qpso_iterations = qpso_iterations
        self.seed = seed

        # State cache for fast dynamic re-optimization
        self.last_problem: Optional[RoutingProblem] = None
        self.clusters: List[Cluster] = []
        self.cluster_tours: Dict[int, List[int]] = {}  # cluster_id -> ordered node sequence
        self.cluster_solvers_used: Dict[int, str] = {}  # cluster_id -> solver type string

    def solve(self, problem: RoutingProblem) -> RoutingSolution:
        """Full end-to-end hybrid solve from scratch."""
        start_time = time.time()
        self.last_problem = problem
        customer_nodes = [c.node_id for c in problem.customers]

        if not customer_nodes:
            return RoutingSolution(solver_name=self.name, problem=problem, routes=[])

        # Step 1: Cluster-first spatial decomposition
        raw_clusters = partition_nodes_into_clusters(customer_nodes, problem.graph, max_cluster_size=self.max_cluster_size)
        # Spatial clustering (KMeans on lat/lon) has no notion of vehicle capacity,
        # so a geographically tight cluster can still carry more total demand than
        # a single vehicle can hold. Since clusters are treated as atomic units when
        # assigned to a vehicle, an over-capacity cluster could never be assigned to
        # ANY vehicle and would be silently dropped along with every customer in it.
        # This pass guarantees every cluster fits within one vehicle's capacity.
        self.clusters = self._enforce_capacity_safe_clusters(raw_clusters, problem)

        # Precompute all-pairs shortest path matrix across customer nodes + depot
        all_nodes = [problem.depot_node] + customer_nodes
        cost_matrix, path_matrix = compute_all_pairs_matrix(
            problem.graph, problem.traffic_simulator, all_nodes, objective="time"
        )

        # Step 2: Exact sub-solver stage (solve intra-cluster TSP sub-tours)
        self._solve_all_clusters(cost_matrix)

        # Step 3: Quantum-inspired Global Solver (QPSO global route stitching)
        routes, convergence_curve = self._stitch_global_routes_with_qpso(problem, cost_matrix, path_matrix)

        sol = RoutingSolution(
            solver_name=self.name,
            problem=problem,
            routes=routes,
            wall_time_sec=time.time() - start_time,
            convergence_curve=convergence_curve,
            metadata={
                "clusters_count": len(self.clusters),
                "cluster_solvers_used": dict(self.cluster_solvers_used),
                "reoptimized": False
            }
        )
        sol.compute_aggregates()
        return sol

    def _enforce_capacity_safe_clusters(self, clusters: List[Cluster], problem: RoutingProblem) -> List[Cluster]:
        """
        Splits any cluster whose total demand exceeds a single vehicle's capacity
        into smaller chunks that each fit within capacity. Spatial clustering has
        no demand awareness, so this is required for correctness, not just an
        optimization - without it, an over-capacity cluster is silently dropped
        entirely (see the note in solve() for why).
        """
        cust_map = {c.node_id: c for c in problem.customers}
        safe_clusters: List[Cluster] = []
        next_id = 0

        for cluster in clusters:
            chunk: List[int] = []
            chunk_demand = 0.0
            for n in cluster.customer_nodes:
                d = cust_map[n].demand_units
                if chunk and (chunk_demand + d) > problem.vehicle_capacity:
                    safe_clusters.append(Cluster(cluster_id=next_id, center_node=chunk[0], customer_nodes=chunk))
                    next_id += 1
                    chunk, chunk_demand = [], 0.0
                chunk.append(n)
                chunk_demand += d
            if chunk:
                safe_clusters.append(Cluster(cluster_id=next_id, center_node=chunk[0], customer_nodes=chunk))
                next_id += 1

        return safe_clusters

    def reoptimize_dynamic_traffic(self, affected_edges: List[Tuple[int, int]]) -> RoutingSolution:
        """
        Dynamic Real-Time Re-Optimization:
        1. Identifies which cluster(s) contain nodes/edges affected by live traffic disruption.
        2. Re-runs the exact sub-solver ONLY for affected cluster(s).
        3. Fast QPSO re-stitches global routes.
        Returns re-optimized RoutingSolution.
        """
        start_time = time.time()
        if self.last_problem is None or not self.clusters:
            raise ValueError("Cannot re-optimize before running initial solve()")

        problem = self.last_problem
        affected_nodes = set()
        for u, v in affected_edges:
            affected_nodes.add(u)
            affected_nodes.add(v)

        # Identify affected clusters
        affected_cluster_ids = set()
        for cluster in self.clusters:
            if any(n in affected_nodes for n in cluster.customer_nodes):
                affected_cluster_ids.add(cluster.cluster_id)

        # Re-compute distance matrix under updated traffic state
        customer_nodes = [c.node_id for c in problem.customers]
        all_nodes = [problem.depot_node] + customer_nodes
        cost_matrix, path_matrix = compute_all_pairs_matrix(
            problem.graph, problem.traffic_simulator, all_nodes, objective="time"
        )

        # Step 2: Local exact re-solve ONLY for affected clusters
        recomputed_count = self._solve_all_clusters(cost_matrix, only_cluster_ids=affected_cluster_ids)

        # Step 3: QPSO Global Re-stitching
        routes, convergence_curve = self._stitch_global_routes_with_qpso(problem, cost_matrix, path_matrix)

        sol = RoutingSolution(
            solver_name=self.name,
            problem=problem,
            routes=routes,
            wall_time_sec=time.time() - start_time,
            convergence_curve=convergence_curve,
            metadata={
                "clusters_count": len(self.clusters),
                "affected_clusters_count": len(affected_cluster_ids),
                "recomputed_clusters_count": recomputed_count,
                "cluster_solvers_used": dict(self.cluster_solvers_used),
                "reoptimized": True
            }
        )
        sol.compute_aggregates()
        return sol

    def _solve_all_clusters(
        self,
        cost_matrix: Dict[Tuple[int, int], float],
        only_cluster_ids: Optional[Set[int]] = None
    ) -> int:
        """
        Solves each cluster's intra-cluster sub-tour exactly (Held-Karp).
        If only_cluster_ids is given, only re-solves those clusters (used for
        fast local re-optimization) - all other clusters keep their cached tour.
        Returns the number of clusters actually (re)computed.
        """
        recomputed_count = 0
        for cluster in self.clusters:
            if only_cluster_ids is not None and cluster.cluster_id not in only_cluster_ids:
                continue  # keep cached tour for unaffected clusters

            c_nodes = cluster.customer_nodes
            N = len(c_nodes)
            if N <= 1:
                self.cluster_tours[cluster.cluster_id] = list(c_nodes)
                self.cluster_solvers_used[cluster.cluster_id] = "TRIVIAL"
                cluster.solver_used = "TRIVIAL"
                continue

            # Build intra-cluster distance matrix
            dist_mat = np.zeros((N, N))
            for i in range(N):
                for j in range(N):
                    if i != j:
                        u, v = c_nodes[i], c_nodes[j]
                        dist_mat[i, j] = cost_matrix[(u, v)]

            tour, _cost, _elapsed = self.cluster_solver.solve_cluster(dist_mat)

            cluster.solver_used = "EXACT_HELD_KARP"
            self.cluster_solvers_used[cluster.cluster_id] = "EXACT_HELD_KARP"

            actual_tour = [c_nodes[idx] for idx in tour]
            self.cluster_tours[cluster.cluster_id] = actual_tour
            recomputed_count += 1

        return recomputed_count

    def _stitch_global_routes_with_qpso(
        self,
        problem: RoutingProblem,
        cost_matrix: Dict[Tuple[int, int], float],
        path_matrix: Dict[Tuple[int, int], List[int]]
    ) -> Tuple[List[VehicleRoute], List[float]]:
        """
        Uses QPSO to decide CLUSTER visiting order and vehicle assignment, then
        expands each cluster's already-computed exact sub-tour to build the full
        vehicle routes.

        NOTE on a bug this fixes: an earlier version of this method ignored
        self.cluster_tours entirely and just called a full QPSOSolver.solve(problem)
        - i.e. it re-solved the ENTIRE customer-level routing problem from scratch,
        throwing away the exact cluster sub-tours computed in step 2. That meant
        (a) the "hybrid" architecture provided no actual speed advantage over
        plain QPSO, since every re-optimization re-ran QPSO at full customer
        granularity regardless of which clusters changed, and (b) the hybrid
        solver inherited plain QPSO's weaker solution quality on top of wasted
        cluster computation. Fixed by having QPSO operate over cluster units
        (typically 3-10 of them) instead of individual customers (dozens+) -
        this is what makes the "decompose into clusters" architecture actually
        pay off in both speed and quality.
        """
        cluster_ids = list(self.cluster_tours.keys())
        num_clusters = len(cluster_ids)

        if num_clusters == 0:
            return [], []

        cust_map = {c.node_id: c for c in problem.customers}

        # Precompute each cluster's fixed entry/exit node and total demand.
        # The cluster's internal visiting order is already fixed (from the
        # exact Held-Karp sub-solve) - QPSO only decides the order clusters
        # are visited in and which vehicle serves which cluster(s).
        cluster_info = {}
        for cid in cluster_ids:
            tour = self.cluster_tours[cid]
            cluster_info[cid] = {
                "tour": tour,
                "entry": tour[0],
                "exit": tour[-1],
                "demand": sum(cust_map[n].demand_units for n in tour if n in cust_map),
            }

        def decode_cluster_positions(position: np.ndarray) -> Tuple[List[VehicleRoute], float, bool]:
            order = np.argsort(position)
            sorted_clusters = [cluster_ids[idx] for idx in order]

            routes = []
            unassigned = list(sorted_clusters)
            veh_id = 0
            total_time, total_dist, total_cong, total_emissions = 0.0, 0.0, 0.0, 0.0

            while unassigned and veh_id < problem.num_vehicles:
                curr_cap = problem.vehicle_capacity
                cust_seq: List[int] = []
                full_path = [problem.depot_node]
                current_node = problem.depot_node

                idx = 0
                while idx < len(unassigned):
                    cid = unassigned[idx]
                    info = cluster_info[cid]
                    if info["demand"] <= curr_cap:
                        curr_cap -= info["demand"]
                        # Travel from current position to this cluster's entry node
                        seg = path_matrix[(current_node, info["entry"])]
                        full_path.extend(seg[1:])
                        # Traverse the cluster's fixed internal tour edge-by-edge
                        tour = info["tour"]
                        for a, b in zip(tour[:-1], tour[1:]):
                            seg2 = path_matrix[(a, b)]
                            full_path.extend(seg2[1:])
                        cust_seq.extend(tour)
                        current_node = info["exit"]
                        unassigned.pop(idx)
                    else:
                        idx += 1  # cluster doesn't fit on this vehicle, try next

                # Return to depot
                return_segment = path_matrix[(current_node, problem.depot_node)]
                full_path.extend(return_segment[1:])

                r_time, r_dist, r_cong, r_emissions = 0.0, 0.0, 0.0, 0.0
                for u, v in zip(full_path[:-1], full_path[1:]):
                    e_data = problem.graph.edges[u, v]
                    r_time += problem.traffic_simulator.get_edge_weight(u, v, "time")
                    r_dist += e_data.get("length", 0.0)
                    r_cong += e_data.get("congestion_score", 0.0)
                    r_emissions += e_data.get("emissions_co2_g", 0.0)

                total_time += r_time
                total_dist += r_dist
                total_cong += r_cong
                total_emissions += r_emissions

                routes.append(VehicleRoute(
                    vehicle_id=veh_id,
                    full_path_nodes=full_path,
                    customer_sequence=cust_seq,
                    total_time_sec=r_time,
                    total_distance_m=r_dist,
                    total_congestion_cost=r_cong,
                    total_emissions_co2_g=r_emissions,
                    feasible=True
                ))
                veh_id += 1

            all_feasible = not unassigned
            w = problem.objective_weights
            scalar_cost = (
                w.get("time", 0.4) * (total_time / 3600.0) +
                w.get("distance", 0.3) * (total_dist / 1000.0) +
                w.get("congestion", 0.2) * total_cong +
                w.get("emissions", 0.1) * (total_emissions / 1000.0)
            )
            if not all_feasible:
                scalar_cost += 1000.0 * len(unassigned)

            return routes, scalar_cost, all_feasible

        # Run QPSO over the small cluster-sequencing space (num_clusters dims,
        # typically 3-10) instead of the full customer space (dozens+).
        if self.seed is not None:
            np.random.seed(self.seed)

        dim = num_clusters
        num_particles = min(self.qpso_particles, max(10, dim * 4))
        iterations = min(self.qpso_iterations, max(20, dim * 8))

        positions = initialize_swarm(num_particles, dim)
        p_bests = np.copy(positions)
        p_best_costs = np.full(num_particles, float('inf'))
        g_best = None
        g_best_cost = float('inf')
        g_best_routes: List[VehicleRoute] = []
        convergence_curve = []

        for i in range(num_particles):
            routes, cost, _ = decode_cluster_positions(positions[i])
            p_best_costs[i] = cost
            if cost < g_best_cost:
                g_best_cost, g_best, g_best_routes = cost, np.copy(positions[i]), routes
        convergence_curve.append(g_best_cost)

        for iter_idx in range(1, iterations):
            beta = 1.0 - 0.6 * (iter_idx / iterations)  # 1.0 -> 0.4 decay, same schedule as QPSOSolver
            positions = qpso_position_update(positions, p_bests, g_best, beta)
            for i in range(num_particles):
                routes, cost, _ = decode_cluster_positions(positions[i])
                if cost < p_best_costs[i]:
                    p_best_costs[i], p_bests[i] = cost, np.copy(positions[i])
                if cost < g_best_cost:
                    g_best_cost, g_best, g_best_routes = cost, np.copy(positions[i]), routes
            convergence_curve.append(g_best_cost)

        return g_best_routes, convergence_curve
