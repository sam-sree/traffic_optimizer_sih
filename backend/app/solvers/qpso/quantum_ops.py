import math
import random
import numpy as np
from typing import List, Tuple, Dict, Any
from backend.app.solvers.base import RoutingProblem, VehicleRoute, CustomerDemand

def initialize_swarm(num_particles: int, dim: int, bounds: Tuple[float, float] = (-5.0, 5.0)) -> np.ndarray:
    """Initializes particle position matrix of size (num_particles, dim)."""
    return np.random.uniform(bounds[0], bounds[1], size=(num_particles, dim))

def compute_mean_best(p_bests: np.ndarray) -> np.ndarray:
    """Computes mean best position mbest = (1/M) * sum(P_i)."""
    return np.mean(p_bests, axis=0)

def qpso_position_update(
    positions: np.ndarray,
    p_bests: np.ndarray,
    g_best: np.ndarray,
    beta: float,
    bounds: Tuple[float, float] = (-5.0, 5.0)
) -> np.ndarray:
    """
    Updates particle positions using Quantum Delta Potential Well wave function sampling:
    X_{i,d}^{t+1} = p_{i,d} +/- beta * |mbest_d - X_{i,d}^t| * ln(1/u_{i,d})
    """
    num_particles, dim = positions.shape
    m_best = compute_mean_best(p_bests)
    new_positions = np.zeros_like(positions)

    for i in range(num_particles):
        phi = np.random.uniform(0.0, 1.0, size=dim)
        # Stochastic local attractor point
        p_i = phi * p_bests[i] + (1.0 - phi) * g_best

        u = np.random.uniform(1e-5, 1.0 - 1e-5, size=dim)
        L = beta * np.abs(m_best - positions[i]) * np.log(1.0 / u)

        # Quantum random phase (+/- sign flip)
        sign = np.where(np.random.uniform(0.0, 1.0, size=dim) > 0.5, 1.0, -1.0)
        new_pos = p_i + sign * L

        # Clip within bounding hypercube
        new_positions[i] = np.clip(new_pos, bounds[0], bounds[1])

    return new_positions

def decode_random_key_to_routes(
    continuous_position: np.ndarray,
    customer_ids: List[int],
    problem: RoutingProblem,
    cost_matrix: Dict[Tuple[int, int], float],
    path_matrix: Dict[Tuple[int, int], List[int]]
) -> Tuple[List[VehicleRoute], float, bool]:
    """
    Decodes continuous position vector into discrete customer permutation via Random Key sorting,
    and constructs capacity-constrained vehicle routes.
    Returns (routes, total_scalar_cost, feasibility_flag).
    """
    # Sort customer IDs according to continuous position values
    order = np.argsort(continuous_position)
    sorted_customers = [customer_ids[idx] for idx in order]

    cust_map = {c.node_id: c for c in problem.customers}

    routes = []
    unassigned = list(sorted_customers)
    veh_id = 0

    total_time, total_dist, total_cong, total_emissions = 0.0, 0.0, 0.0, 0.0
    all_feasible = True

    while unassigned and veh_id < problem.num_vehicles:
        curr_cap = problem.vehicle_capacity
        cust_seq = []
        full_path = [problem.depot_node]
        current_node = problem.depot_node

        idx = 0
        while idx < len(unassigned):
            c_id = unassigned[idx]
            c_demand = cust_map[c_id].demand_units

            if c_demand <= curr_cap:
                curr_cap -= c_demand
                cust_seq.append(c_id)
                segment = path_matrix[(current_node, c_id)]
                full_path.extend(segment[1:])
                current_node = c_id
                unassigned.pop(idx)
            else:
                idx += 1

        # Return to depot
        return_segment = path_matrix[(current_node, problem.depot_node)]
        full_path.extend(return_segment[1:])

        # Evaluate route cost metrics
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

    if unassigned:
        all_feasible = False # Unserved customers penalty

    w = problem.objective_weights
    scalar_cost = (
        w.get("time", 0.4) * (total_time / 3600.0) +
        w.get("distance", 0.3) * (total_dist / 1000.0) +
        w.get("congestion", 0.2) * total_cong +
        w.get("emissions", 0.1) * (total_emissions / 1000.0)
    )

    if not all_feasible:
        scalar_cost += 1000.0 * len(unassigned) # Penalty for unserved customers

    return routes, scalar_cost, all_feasible
