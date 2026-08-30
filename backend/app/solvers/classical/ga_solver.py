import time
import random
import numpy as np
from typing import List, Dict, Tuple, Optional

from backend.app.solvers.base import BaseSolver, RoutingProblem, RoutingSolution, VehicleRoute
from backend.app.solvers.classical.shortest_path import compute_all_pairs_matrix
from backend.app.solvers.qpso.quantum_ops import decode_random_key_to_routes

class GASolver(BaseSolver):
    """
    Genetic Algorithm (GA) baseline solver for VRP.
    Uses Order Crossover (OX), inversion mutation, tournament selection, and elitism.
    """
    def __init__(
        self,
        pop_size: int = 50,
        generations: int = 120,
        crossover_prob: float = 0.85,
        mutation_prob: float = 0.2,
        tournament_size: int = 4,
        seed: Optional[int] = None
    ):
        super().__init__("Genetic Algorithm (GA)")
        self.pop_size = pop_size
        self.generations = generations
        self.crossover_prob = crossover_prob
        self.mutation_prob = mutation_prob
        self.tournament_size = tournament_size
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

        # Helper to decode permutation into routes and scalar cost
        def evaluate_individual(perm: List[int]) -> Tuple[float, List[VehicleRoute]]:
            # Convert discrete perm to continuous keys for decoder compatibility
            pos = np.zeros(N)
            for rank, c_id in enumerate(perm):
                idx = customer_ids.index(c_id)
                pos[idx] = rank
            routes, cost, _ = decode_random_key_to_routes(pos, customer_ids, problem, cost_matrix, path_matrix)
            return cost, routes

        # 1. Initialize Population
        population = [random.sample(customer_ids, N) for _ in range(self.pop_size)]
        evals = [evaluate_individual(ind) for ind in population]
        costs = [e[0] for e in evals]

        best_cost_idx = np.argmin(costs)
        best_cost = costs[best_cost_idx]
        best_perm = population[best_cost_idx]
        best_routes = evals[best_cost_idx][1]

        convergence_curve = [best_cost]

        # 2. Main Generation Loop
        for gen in range(1, self.generations):
            new_pop = []
            
            # Elitism: retain best 2 individuals
            elite_indices = np.argsort(costs)[:2]
            for idx in elite_indices:
                new_pop.append(list(population[idx]))

            # Fill rest of population
            while len(new_pop) < self.pop_size:
                # Tournament Selection
                p1 = self._tournament_select(population, costs)
                p2 = self._tournament_select(population, costs)

                # Order Crossover (OX)
                if random.random() < self.crossover_prob:
                    c1, c2 = self._order_crossover(p1, p2)
                else:
                    c1, c2 = list(p1), list(p2)

                # Inversion Mutation
                if random.random() < self.mutation_prob:
                    c1 = self._inversion_mutation(c1)
                if random.random() < self.mutation_prob:
                    c2 = self._inversion_mutation(c2)

                new_pop.append(c1)
                if len(new_pop) < self.pop_size:
                    new_pop.append(c2)

            population = new_pop
            evals = [evaluate_individual(ind) for ind in population]
            costs = [e[0] for e in evals]

            curr_best_idx = np.argmin(costs)
            if costs[curr_best_idx] < best_cost:
                best_cost = costs[curr_best_idx]
                best_perm = population[curr_best_idx]
                best_routes = evals[curr_best_idx][1]

            convergence_curve.append(best_cost)

        sol = RoutingSolution(
            solver_name=self.name,
            problem=problem,
            routes=best_routes,
            wall_time_sec=time.time() - start_time,
            convergence_curve=convergence_curve,
            metadata={"pop_size": self.pop_size, "generations": self.generations}
        )
        sol.compute_aggregates()
        return sol

    def _tournament_select(self, pop: List[List[int]], costs: List[float]) -> List[int]:
        selected_indices = random.sample(range(len(pop)), self.tournament_size)
        best_idx = min(selected_indices, key=lambda idx: costs[idx])
        return pop[best_idx]

    def _order_crossover(self, parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:
        N = len(parent1)
        if N <= 2:
            return list(parent1), list(parent2)
        
        idx1, idx2 = sorted(random.sample(range(N), 2))

        def ox_child(p1, p2):
            child = [None] * N
            child[idx1:idx2] = p1[idx1:idx2]
            p1_set = set(child[idx1:idx2])
            
            p2_fill = [item for item in p2 if item not in p1_set]
            fill_idx = 0
            for i in range(N):
                if child[i] is None:
                    child[i] = p2_fill[fill_idx]
                    fill_idx += 1
            return child

        return ox_child(parent1, parent2), ox_child(parent2, parent1)

    def _inversion_mutation(self, perm: List[int]) -> List[int]:
        N = len(perm)
        if N <= 2:
            return list(perm)
        idx1, idx2 = sorted(random.sample(range(N), 2))
        mutated = list(perm)
        mutated[idx1:idx2] = reversed(mutated[idx1:idx2])
        return mutated
