"""
Computes on-time delivery / SLA compliance metrics for a solved routing
solution, as a post-processing pass over the already-computed routes.

This is deliberately implemented as a post-hoc analysis (walking the route's
existing full_path_nodes and edge travel times) rather than baked into each
solver's internal search loop - it works uniformly across every solver
(Dijkstra, GA, ACO, QPSO, OR-Tools, Hybrid) without needing to modify any of
them, since they all already produce a VehicleRoute with a full path and a
customer_sequence.

Simplifying assumption stated explicitly: each vehicle is assumed to depart
the depot at time 0 (start of the planning window) and travel continuously,
accumulating travel time plus each customer's service_time as it goes. Real
operations may have staggered vehicle start times - this assumes a common
start for comparability across solvers, not a claim about real dispatch
timing.
"""

from typing import Dict, List, Any
from backend.app.solvers.base import RoutingProblem, VehicleRoute, RoutingSolution


def compute_route_sla(route: VehicleRoute, problem: RoutingProblem) -> Dict[str, Any]:
    """
    Walks a single vehicle's route, accumulating travel + service time, and
    checks each customer's arrival time against their [ready_time, due_time]
    window. Returns per-customer lateness details and route-level summary.
    """
    cust_map = {c.node_id: c for c in problem.customers}
    current_time = 0.0
    current_node = problem.depot_node

    customer_results: List[Dict[str, Any]] = []

    # full_path_nodes is the step-by-step graph path; we only need to know
    # cumulative travel time up to each customer node as we pass through it.
    path = route.full_path_nodes
    idx = 0
    remaining_customers = set(route.customer_sequence)

    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        current_time += problem.traffic_simulator.get_edge_weight(u, v, "time")
        current_node = v

        if current_node in remaining_customers:
            cust = cust_map[current_node]
            arrival_time = current_time
            is_late = arrival_time > cust.due_time
            late_by_sec = max(0.0, arrival_time - cust.due_time)
            customer_results.append({
                "node_id": current_node,
                "arrival_time_min": round(arrival_time / 60.0, 1),
                "due_time_min": round(cust.due_time / 60.0, 1),
                "on_time": not is_late,
                "late_by_min": round(late_by_sec / 60.0, 1),
            })
            # Service time is spent at the customer before continuing
            current_time += cust.service_time
            remaining_customers.discard(current_node)

    on_time_count = sum(1 for c in customer_results if c["on_time"])
    total = len(customer_results)

    return {
        "vehicle_id": route.vehicle_id,
        "customers": customer_results,
        "on_time_count": on_time_count,
        "total_customers": total,
        "on_time_rate_pct": round((on_time_count / total) * 100.0, 1) if total > 0 else 100.0,
    }


def compute_solution_sla(solution: RoutingSolution) -> Dict[str, Any]:
    """
    Aggregates on-time performance across every vehicle route in a solution.
    """
    per_route = [compute_route_sla(r, solution.problem) for r in solution.routes]

    total_customers = sum(r["total_customers"] for r in per_route)
    total_on_time = sum(r["on_time_count"] for r in per_route)
    all_late = [
        c["late_by_min"]
        for r in per_route
        for c in r["customers"]
        if not c["on_time"]
    ]

    return {
        "on_time_rate_pct": round((total_on_time / total_customers) * 100.0, 1) if total_customers > 0 else 100.0,
        "total_customers": total_customers,
        "on_time_count": total_on_time,
        "late_count": total_customers - total_on_time,
        "avg_lateness_min_when_late": round(sum(all_late) / len(all_late), 1) if all_late else 0.0,
        "max_lateness_min": round(max(all_late), 1) if all_late else 0.0,
        "per_vehicle": per_route,
    }
