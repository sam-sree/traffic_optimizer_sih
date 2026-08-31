"""
Builds a real, clickable Google Maps directions URL for a solved vehicle
route, so a driver could actually navigate the route today - not just view
it as a chart in the dashboard.
"""

from typing import List
import networkx as nx
from backend.app.solvers.base import VehicleRoute


def build_google_maps_url(route: VehicleRoute, graph: nx.DiGraph, depot_node: int) -> str:
    """
    Builds a Google Maps directions URL: depot -> each customer stop in
    visiting order -> back to depot. Uses only the customer stops (not every
    intermediate road-network node from full_path_nodes) since Google Maps
    has a practical waypoint limit and turn-by-turn road-level detail isn't
    needed for a "here's where to go" link - Maps will compute its own
    driving directions between the stops.
    """
    stop_nodes: List[int] = [depot_node] + list(route.customer_sequence) + [depot_node]

    coords = []
    for n in stop_nodes:
        d = graph.nodes[n]
        lat = d.get("y", d.get("lat", 12.9716))
        lon = d.get("x", d.get("lon", 77.5946))
        coords.append(f"{lat},{lon}")

    return "https://www.google.com/maps/dir/" + "/".join(coords)
