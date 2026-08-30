import time
import random
import numpy as np
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass

from backend.app.solvers.base import BaseSolver, RoutingProblem, RoutingSolution, VehicleRoute
from backend.app.solvers.classical.shortest_path import compute_all_pairs_matrix
from backend.app.solvers.qpso.quantum_ops import initialize_swarm, qpso_position_update, decode_random_key_to_routes

@dataclass
class ParetoPoint:
    objectives: np.ndarray       # [time_sec, distance_m, congestion_cost, emissions_co2_g]
    routes: List[VehicleRoute]
    position: np.ndarray
    crowding_distance: float = 0.0

def dominates(obj_a: np.ndarray, obj_b: np.ndarray) -> bool:
    """Returns True if objective vector A dominates B (minimization)."""
    return np.all(obj_a <= obj_b) and np.any(obj_a < obj_b)

def compute_crowding_distance(archive: List[ParetoPoint]):
    """Computes crowding distance metric for diversity preservation along Pareto front."""
    L = len(archive)
    if L == 0:
        return
    for p in archive:
        p.crowding_distance = 0.0

    num_objectives = len(archive[0].objectives)
    for m in range(num_objectives):
        archive.sort(key=lambda p: p.objectives[m])
        archive[0].crowding_distance = float('inf')
        archive[-1].crowding_distance = float('inf')

        obj_min = archive[0].objectives[m]
        obj_max = archive[-1].objectives[m]
        norm = max(1e-6, obj_max - obj_min)

        for i in range(1, L - 1):
            if archive[i].crowding_distance != float('inf'):
                archive[i].crowding_distance += (archive[i+1].objectives[m] - archive[i-1].objectives[m]) / norm

class MOQPSOSolver(BaseSolver):
    """
    Multi-Objective Quantum-Inspired PSO (MO-QPSO) Solver.
    Generates Pareto Front for 4 objectives: Time, Distance, Congestion, and Carbon Emissions.
    """
    def __init__(
        self,
        num_particles: int = 40,
        max_iterations: int = 120,
        archive_capacity: int = 50,
        seed: Optional[int] = 42
    ):
        super().__init__("Multi-Objective QPSO (MO-QPSO)")
        self.num_particles = num_particles
        self.max_iterations = max_iterations
        self.archive_capacity = archive_capacity
        self.seed = seed

    def solve_pareto_front(self, problem: RoutingProblem) -> Tuple[List[ParetoPoint], RoutingSolution]:
        start_time = time.time()
        if self.seed is not None:
            np.random.seed(self.seed)
            random.seed(self.seed)

        customer_ids = [c.node_id for c in problem.customers]
        dim = len(customer_ids)
        if dim == 0:
            return [], RoutingSolution(solver_name=self.name, problem=problem, routes=[])

        all_nodes = [problem.depot_node] + customer_ids
        cost_matrix, path_matrix = compute_all_pairs_matrix(
            problem.graph, problem.traffic_simulator, all_nodes, objective="time"
        )

        def eval_objectives(pos: np.ndarray) -> Tuple[np.ndarray, List[VehicleRoute], bool]:
            routes, _, feasible = decode_random_key_to_routes(pos, customer_ids, problem, cost_matrix, path_matrix)
            r_time = sum(r.total_time_sec for r in routes)
            r_dist = sum(r.total_distance_m for r in routes)
            r_cong = sum(r.total_congestion_cost for r in routes)
            r_emissions = sum(r.total_emissions_co2_g for r in routes)
            return np.array([r_time, r_dist, r_cong, r_emissions]), routes, feasible

        # 1. Swarm Initialization
        positions = initialize_swarm(self.num_particles, dim)
        p_bests = np.copy(positions)
        p_best_objs = []
        p_best_routes = []

        pareto_archive: List[ParetoPoint] = []

        for i in range(self.num_particles):
            objs, routes, feasible = eval_objectives(positions[i])
            p_best_objs.append(objs)
            p_best_routes.append(routes)
            pt = ParetoPoint(objectives=objs, routes=routes, position=np.copy(positions[i]))
            self._update_archive(pareto_archive, pt)

        # 2. Main MO-QPSO Iteration Loop
        for iter_idx in range(1, self.max_iterations):
            beta = 1.0 - 0.6 * (iter_idx / self.max_iterations)
            compute_crowding_distance(pareto_archive)

            for i in range(self.num_particles):
                # Select G_best from Pareto Archive via Crowding Distance Roulette Wheel
                g_best_pt = self._select_leader_from_archive(pareto_archive)
                g_best = g_best_pt.position

                # Update position using QPSO wave function sampling
                phi = np.random.uniform(0.0, 1.0, size=dim)
                p_i = phi * p_bests[i] + (1.0 - phi) * g_best
                m_best = np.mean(p_bests, axis=0)

                u = np.random.uniform(1e-5, 1.0 - 1e-5, size=dim)
                L = beta * np.abs(m_best - positions[i]) * np.log(1.0 / u)
                sign = np.where(np.random.uniform(0.0, 1.0, size=dim) > 0.5, 1.0, -1.0)
                positions[i] = np.clip(p_i + sign * L, -5.0, 5.0)

                # Evaluate new objectives
                objs, routes, feasible = eval_objectives(positions[i])

                # Update Personal Best (Dominance rules)
                if dominates(objs, p_best_objs[i]):
                    p_best_objs[i] = objs
                    p_bests[i] = np.copy(positions[i])
                    p_best_routes[i] = routes
                elif not dominates(p_best_objs[i], objs):
                    if random.random() < 0.5:
                        p_best_objs[i] = objs
                        p_bests[i] = np.copy(positions[i])
                        p_best_routes[i] = routes

                # Add to Pareto Archive
                pt = ParetoPoint(objectives=objs, routes=routes, position=np.copy(positions[i]))
                self._update_archive(pareto_archive, pt)

        # Build default solution from median Pareto tradeoff point
        compute_crowding_distance(pareto_archive)
        best_pt = pareto_archive[len(pareto_archive) // 2] if pareto_archive else ParetoPoint(
            objectives=p_best_objs[0], routes=p_best_routes[0], position=p_bests[0]
        )

        sol = RoutingSolution(
            solver_name=self.name,
            problem=problem,
            routes=best_pt.routes,
            wall_time_sec=time.time() - start_time,
            metadata={"pareto_front_size": len(pareto_archive)}
        )
        sol.compute_aggregates()
        return pareto_archive, sol

    def solve(self, problem: RoutingProblem) -> RoutingSolution:
        _, sol = self.solve_pareto_front(problem)
        return sol

    def _update_archive(self, archive: List[ParetoPoint], new_pt: ParetoPoint):
        """Maintains non-dominated set and truncates oversized archive via crowding distance."""
        # Check if new_pt is dominated by any existing point
        for pt in archive:
            if dominates(pt.objectives, new_pt.objectives):
                return # Rejected

        # Remove points dominated by new_pt
        archive[:] = [pt for pt in archive if not dominates(new_pt.objectives, pt.objectives)]
        archive.append(new_pt)

        # Truncate if exceeds capacity
        if len(archive) > self.archive_capacity:
            compute_crowding_distance(archive)
            archive.sort(key=lambda p: p.crowding_distance, reverse=True)
            archive[:] = archive[:self.archive_capacity]

    def _select_leader_from_archive(self, archive: List[ParetoPoint]) -> ParetoPoint:
        if not archive:
            raise ValueError("Pareto archive is empty")
        if len(archive) == 1:
            return archive[0]

        # Roulette selection biased towards higher crowding distance (diversity)
        dists = np.array([p.crowding_distance for p in archive])
        dists[np.isinf(dists)] = 1e6
        total = np.sum(dists)
        if total == 0:
            return random.choice(archive)
        probs = dists / total
        return np.random.choice(archive, p=probs)
