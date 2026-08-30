import math
import heapq
import time
from typing import Dict, Tuple, List, Optional
import networkx as nx
from backend.app.solvers.base import BaseSolver, RoutingProblem, RoutingSolution, VehicleRoute

def haversine_heuristic(u: int, v: int, G: nx.DiGraph) -> float:
    """Haversine lower bound distance in meters for A* heuristic search."""
    u_data, v_data = G.nodes[u], G.nodes[v]
    R = 6371000.0
    phi1, phi2 = math.radians(u_data['y']), math.radians(v_data['y'])
    dphi = math.radians(v_data['y'] - u_data['y'])
    dlambda = math.radians(v_data['x'] - u_data['x'])
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    dist_m = 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    # Convert meters to estimated min travel time (assuming 60 km/h = 16.67 m/s max speed)
    return dist_m / 16.67

def dijkstra_path(G: nx.DiGraph, traffic_sim, source: int, target: int, objective: str = "time") -> Tuple[float, List[int]]:
    """
    Computes single pair shortest path using Dijkstra's algorithm under current dynamic edge weights.
    Returns (total_weight, node_path).
    """
    if source == target:
        return 0.0, [source]

    distances = {source: 0.0}
    predecessors = {}
    pq = [(0.0, source)]

    while pq:
        dist, current = heapq.heappop(pq)

        if current == target:
            break
        if dist > distances.get(current, float('inf')):
            continue

        for neighbor in G.neighbors(current):
            weight = traffic_sim.get_edge_weight(current, neighbor, objective=objective)
            new_dist = dist + weight

            if new_dist < distances.get(neighbor, float('inf')):
                distances[neighbor] = new_dist
                predecessors[neighbor] = current
                heapq.heappush(pq, (new_dist, neighbor))

    if target not in predecessors:
        # Fallback to networkx shortest path
        try:
            path = nx.shortest_path(G, source, target, weight='free_flow_time')
            weight = sum(traffic_sim.get_edge_weight(u, v, objective) for u, v in zip(path[:-1], path[1:]))
            return weight, path
        except nx.NetworkXNoPath:
            return float('inf'), []

    path = []
    curr = target
    while curr in predecessors:
        path.append(curr)
        curr = predecessors[curr]
    path.append(source)
    path.reverse()
    return distances[target], path

def compute_all_pairs_matrix(G: nx.DiGraph, traffic_sim, nodes: List[int], objective: str = "time") -> Tuple[Dict[Tuple[int, int], float], Dict[Tuple[int, int], List[int]]]:
    """
    Precomputes dynamic shortest path cost matrix and node paths between all pairs in `nodes`.
    Used by VRP solvers (OR-Tools, QPSO, GA, ACO) to operate on customer distance matrices.
    """
    cost_matrix = {}
    path_matrix = {}
    for u in nodes:
        for v in nodes:
            if u == v:
                cost_matrix[(u, v)] = 0.0
                path_matrix[(u, v)] = [u]
            else:
                cost, path = dijkstra_path(G, traffic_sim, u, v, objective=objective)
                cost_matrix[(u, v)] = cost
                path_matrix[(u, v)] = path
    return cost_matrix, path_matrix

class ShortestPathSolver(BaseSolver):
    """Simple Nearest-Neighbor baseline solver using Dijkstra shortest paths."""
    def __init__(self, use_astar: bool = False):
        name = "A* Nearest-Neighbor" if use_astar else "Dijkstra Nearest-Neighbor"
        super().__init__(name)
        self.use_astar = use_astar

    def solve(self, problem: RoutingProblem) -> RoutingSolution:
        start_time = time.time()
        nodes = [problem.depot_node] + [c.node_id for c in problem.customers]
        cost_matrix, path_matrix = compute_all_pairs_matrix(problem.graph, problem.traffic_simulator, nodes, "time")

        unvisited = set(c.node_id for c in problem.customers)
        routes = []
        veh_id = 0

        while unvisited and veh_id < problem.num_vehicles:
            current = problem.depot_node
            current_cap = problem.vehicle_capacity
            cust_seq = []
            full_path = [current]
            veh_time = 0.0
            veh_dist = 0.0
            veh_cong = 0.0
            veh_emissions = 0.0

            while unvisited:
                # Find nearest feasible unvisited customer
                best_cust = None
                best_cost = float('inf')
                for c_id in unvisited:
                    c_demand = next(c.demand_units for c in problem.customers if c.node_id == c_id)
                    if c_demand <= current_cap:
                        cost = cost_matrix[(current, c_id)]
                        if cost < best_cost:
                            best_cost = cost
                            best_cust = c_id

                if best_cust is None:
                    break

                c_demand = next(c.demand_units for c in problem.customers if c.node_id == best_cust)
                current_cap -= c_demand
                cust_seq.append(best_cust)
                unvisited.remove(best_cust)

                segment_path = path_matrix[(current, best_cust)]
                full_path.extend(segment_path[1:])
                current = best_cust

            # Return to depot
            return_path = path_matrix[(current, problem.depot_node)]
            full_path.extend(return_path[1:])

            # Compute route metrics
            for u, v in zip(full_path[:-1], full_path[1:]):
                e_data = problem.graph.edges[u, v]
                veh_time += problem.traffic_simulator.get_edge_weight(u, v, "time")
                veh_dist += e_data.get("length", 0.0)
                veh_cong += e_data.get("congestion_score", 0.0)
                veh_emissions += e_data.get("emissions_co2_g", 0.0)

            routes.append(VehicleRoute(
                vehicle_id=veh_id,
                full_path_nodes=full_path,
                customer_sequence=cust_seq,
                total_time_sec=veh_time,
                total_distance_m=veh_dist,
                total_congestion_cost=veh_cong,
                total_emissions_co2_g=veh_emissions,
                feasible=True
            ))
            veh_id += 1

        sol = RoutingSolution(
            solver_name=self.name,
            problem=problem,
            routes=routes,
            wall_time_sec=time.time() - start_time
        )
        sol.compute_aggregates()
        return sol
