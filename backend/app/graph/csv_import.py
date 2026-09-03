"""
Imports a real order list (CSV) into the routing problem, instead of using
generated/random demand. This is the "a company uploads today's actual
orders" entry point - the thing an operations team would use every morning,
as opposed to the pre-generated demand-set JSON files used for benchmarking.

Expected CSV columns (header row required):
    name            - optional, customer/order label for readability
    latitude        - required
    longitude       - required
    demand_units    - required (order size / package count / weight, in
                      whatever unit matches your vehicle_capacity)
    ready_time_min  - optional, minutes from the start of the planning
                      window when the order becomes available (default 0)
    due_time_min    - optional, minutes by which delivery must happen
                      (default 1440, i.e. end of a 24-hour window)
    service_time_min- optional, minutes spent at the stop (default 5)

Each row's (latitude, longitude) is snapped to the nearest node in the road
network graph, since the routing/solving logic operates on graph nodes, not
raw coordinates. This uses a simple Euclidean approximation on lat/lon,
which is accurate enough at city scale for snapping to a nearby road
intersection, but is NOT a substitute for a real geocoding/map-matching
service if addresses (rather than coordinates) need to be looked up -
that remains a stated next step, not something this module does.
"""

import csv
import io
import math
from typing import List, Dict, Any, Tuple
import networkx as nx

from backend.app.solvers.base import CustomerDemand


def _nearest_node(graph: nx.DiGraph, lat: float, lon: float) -> Tuple[int, float]:
    """Finds the graph node closest to (lat, lon) by simple Euclidean distance
    on coordinates. Returns (node_id, approx_distance_km)."""
    best_node = None
    best_dist_sq = float("inf")
    for n, d in graph.nodes(data=True):
        n_lat = d.get("y", d.get("lat", 12.9716))
        n_lon = d.get("x", d.get("lon", 77.5946))
        dist_sq = (n_lat - lat) ** 2 + (n_lon - lon) ** 2
        if dist_sq < best_dist_sq:
            best_dist_sq, best_node = dist_sq, n

    approx_km = math.sqrt(best_dist_sq) * 111.0
    return best_node, round(approx_km, 3)


def parse_customer_csv(csv_text: str, graph: nx.DiGraph) -> Dict[str, Any]:
    """
    Parses uploaded CSV text into a list of CustomerDemand objects, snapping
    each row to its nearest road-network node.
    """
    reader = csv.DictReader(io.StringIO(csv_text))
    customers: List[CustomerDemand] = []
    snap_report: List[Dict[str, Any]] = []
    errors: List[str] = []

    required = {"latitude", "longitude", "demand_units"}
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        errors.append(
            f"CSV must include header columns: {sorted(required)} "
            f"(optional: name, ready_time_min, due_time_min, service_time_min). "
            f"Found: {reader.fieldnames}"
        )
        return {"customers": [], "snap_report": [], "errors": errors}

    for i, row in enumerate(reader, start=2):
        try:
            lat = float(row["latitude"])
            lon = float(row["longitude"])
            demand = float(row["demand_units"])
        except (ValueError, KeyError):
            errors.append(f"Row {i}: missing or invalid latitude/longitude/demand_units - skipped.")
            continue

        ready_min = float(row.get("ready_time_min") or 0.0)
        due_min = float(row.get("due_time_min") or 1440.0)
        service_min = float(row.get("service_time_min") or 5.0)
        name = row.get("name") or f"Order {i - 1}"

        node_id, snap_km = _nearest_node(graph, lat, lon)

        customers.append(CustomerDemand(
            node_id=node_id,
            demand_units=demand,
            ready_time=ready_min * 60.0,
            due_time=due_min * 60.0,
            service_time=service_min * 60.0,
        ))
        snap_report.append({
            "name": name,
            "requested_lat": lat,
            "requested_lon": lon,
            "snapped_node_id": node_id,
            "snap_distance_km": snap_km,
        })

    return {"customers": customers, "snap_report": snap_report, "errors": errors}
