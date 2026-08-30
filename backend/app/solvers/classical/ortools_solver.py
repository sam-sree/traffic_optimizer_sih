import time
import math
from typing import List, Dict, Tuple, Optional
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from backend.app.solvers.base import BaseSolver, RoutingProblem, RoutingSolution, VehicleRoute, CustomerDemand
from backend.app.solvers.classical.shortest_path import compute_all_pairs_matrix

class ORToolsSolver(BaseSolver):
    """
    Classical baseline solver utilizing Google OR-Tools Routing Library for
    Capacitated Vehicle Routing Problem with Time Windows (CVRPTW).
    """
    def __init__(self, time_limit_sec: float = 3.0):
        super().__init__("Google OR-Tools CVRPTW")
        self.time_limit_sec = time_limit_sec

    def solve(self, problem: RoutingProblem) -> RoutingSolution:
        start_time = time.time()
        
        # 1. Map problem nodes: index 0 is depot, indices 1..N are customers
        node_list = [problem.depot_node] + [c.node_id for c in problem.customers]
        node_to_idx = {node: idx for idx, node in enumerate(node_list)}
        idx_to_node = {idx: node for idx, node in enumerate(node_list)}

        # 2. Compute cost and path matrices using Dijkstra under dynamic traffic
        cost_matrix, path_matrix = compute_all_pairs_matrix(
            problem.graph, problem.traffic_simulator, node_list, objective="time"
        )

        # Build OR-Tools data model
        data = {}
        # Convert travel time to integer seconds for OR-Tools solver
        time_matrix = []
        for i in range(len(node_list)):
            row = []
            for j in range(len(node_list)):
                u, v = idx_to_node[i], idx_to_node[j]
                row.append(int(round(cost_matrix[(u, v)])))
            time_matrix.append(row)
        data['time_matrix'] = time_matrix

        # Demands array
        demands = [0] # Depot demand is 0
        total_demand = 0.0
        for c in problem.customers:
            demands.append(int(round(c.demand_units)))
            total_demand += c.demand_units
        data['demands'] = demands
        
        needed_vehicles = max(problem.num_vehicles, int(math.ceil(total_demand / max(1.0, problem.vehicle_capacity))))
        data['vehicle_capacities'] = [int(round(problem.vehicle_capacity))] * needed_vehicles
        data['num_vehicles'] = needed_vehicles
        data['depot'] = 0

        # Time Windows
        time_windows = [(0, 86400)] # Depot window
        for c in problem.customers:
            ready = int(round(c.ready_time))
            due = int(round(c.due_time))
            time_windows.append((ready, due))
        data['time_windows'] = time_windows
        
        service_times = [0] + [int(round(c.service_time)) for c in problem.customers]
        data['service_times'] = service_times

        # 3. Create RoutingIndexManager and RoutingModel
        manager = pywrapcp.RoutingIndexManager(
            len(data['time_matrix']), data['num_vehicles'], data['depot']
        )
        routing = pywrapcp.RoutingModel(manager)

        # Travel time transit callback
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return data['time_matrix'][from_node][to_node] + data['service_times'][from_node]

        transit_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # Capacity Dimension
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0, # null capacity slack
            data['vehicle_capacities'], # vehicle maximum capacities
            True, # start cumul to zero
            'Capacity'
        )

        # Time Window Dimension
        routing.AddDimension(
            transit_callback_index,
            1800, # allow up to 30 min waiting slack time at customer
            86400, # max vehicle travel time (24h)
            False, # Don't force start cumul to zero
            'Time'
        )
        time_dimension = routing.GetDimensionOrDie('Time')
        for location_idx, (ready, due) in enumerate(data['time_windows']):
            index = manager.NodeToIndex(location_idx)
            time_dimension.CumulVar(index).SetRange(ready, due)

        # 4. Set Search Parameters
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = int(max(1, round(self.time_limit_sec)))

        # 5. Solve
        solution = routing.SolveWithParameters(search_parameters)

        routes = []
        if solution:
            for vehicle_id in range(data['num_vehicles']):
                index = routing.Start(vehicle_id)
                cust_seq = []
                full_path_nodes = []
                
                curr_node_idx = manager.IndexToNode(index)
                curr_graph_node = idx_to_node[curr_node_idx]
                full_path_nodes.append(curr_graph_node)

                while not routing.IsEnd(index):
                    node_idx = manager.IndexToNode(index)
                    if node_idx != 0:
                        cust_seq.append(idx_to_node[node_idx])

                    index = solution.Value(routing.NextVar(index))
                    next_node_idx = manager.IndexToNode(index)
                    next_graph_node = idx_to_node[next_node_idx]

                    # Stitch path in G
                    segment = path_matrix[(curr_graph_node, next_graph_node)]
                    full_path_nodes.extend(segment[1:])
                    curr_graph_node = next_graph_node

                if cust_seq: # Only record non-empty routes
                    veh_time, veh_dist, veh_cong, veh_emissions = 0.0, 0.0, 0.0, 0.0
                    for u, v in zip(full_path_nodes[:-1], full_path_nodes[1:]):
                        e_data = problem.graph.edges[u, v]
                        veh_time += problem.traffic_simulator.get_edge_weight(u, v, "time")
                        veh_dist += e_data.get("length", 0.0)
                        veh_cong += e_data.get("congestion_score", 0.0)
                        veh_emissions += e_data.get("emissions_co2_g", 0.0)

                    routes.append(VehicleRoute(
                        vehicle_id=vehicle_id,
                        full_path_nodes=full_path_nodes,
                        customer_sequence=cust_seq,
                        total_time_sec=veh_time,
                        total_distance_m=veh_dist,
                        total_congestion_cost=veh_cong,
                        total_emissions_co2_g=veh_emissions,
                        feasible=True
                    ))

        sol = RoutingSolution(
            solver_name=self.name,
            problem=problem,
            routes=routes,
            wall_time_sec=time.time() - start_time,
            metadata={"status": "OPTIMAL" if solution else "INFEASIBLE"}
        )
        sol.compute_aggregates()
        return sol
