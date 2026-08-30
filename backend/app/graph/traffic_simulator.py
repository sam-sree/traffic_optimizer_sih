import math
import random
import copy
from typing import Dict, Tuple, List, Optional

class DynamicTrafficSimulator:
    """
    Simulates dynamic dynamic traffic congestion profiles and dynamic incident disruptions
    over a transportation road network graph G.
    """
    def __init__(self, G, initial_time_hours: float = 8.5):
        """
        :param G: NetworkX DiGraph preprocessed by graph/ingestion.py
        :param initial_time_hours: Time of day in decimal hours (e.g., 8.5 = 08:30 AM)
        """
        self.G = G
        self.current_time_hours = initial_time_hours
        self.active_incidents: Dict[Tuple[int, int], dict] = {}
        self.edge_flows: Dict[Tuple[int, int], float] = {}
        
        # Initialize edge dynamic attributes
        self.update_traffic_state(self.current_time_hours)

    def get_rush_hour_multiplier(self, time_hours: float) -> float:
        """
        Computes time-of-day traffic volume multiplier.
        Morning peak: 8:30 AM (8.5h), Evening peak: 6:30 PM (18.5h)
        """
        morning_peak = 1.2 * math.exp(-((time_hours - 8.5) / 1.5) ** 2)
        evening_peak = 1.5 * math.exp(-((time_hours - 18.5) / 1.8) ** 2)
        return 1.0 + morning_peak + evening_peak

    def inject_incident(self, u: int, v: int, severity_factor: float = 3.5, duration_hours: float = 1.0) -> dict:
        """
        Injects a dynamic dynamic traffic incident on edge (u, v).
        :param severity_factor: Multiplier for travel time (e.g. 3.5x delay)
        :param duration_hours: Active duration of the incident
        """
        incident = {
            "edge": (u, v),
            "severity": severity_factor,
            "start_time": self.current_time_hours,
            "end_time": self.current_time_hours + duration_hours,
            "active": True
        }
        self.active_incidents[(u, v)] = incident
        # Also inject reverse edge if present
        if self.G.has_edge(v, u):
            self.active_incidents[(v, u)] = copy.deepcopy(incident)
            self.active_incidents[(v, u)]["edge"] = (v, u)

        # Trigger traffic update
        self.update_traffic_state(self.current_time_hours)
        return incident

    def inject_random_incidents(self, count: int = 3, severity_range: Tuple[float, float] = (2.5, 5.0)) -> List[Tuple[int, int]]:
        """Injects random dynamic traffic disruptions into the network."""
        edges = list(self.G.edges())
        selected = random.sample(edges, min(count, len(edges)))
        affected = []
        for u, v in selected:
            sev = random.uniform(severity_range[0], severity_range[1])
            self.inject_incident(u, v, severity_factor=sev, duration_hours=2.0)
            affected.append((u, v))
        return affected

    def clear_incidents(self):
        """Clears all active traffic disruptions."""
        self.active_incidents.clear()
        self.update_traffic_state(self.current_time_hours)

    def update_traffic_state(self, time_hours: float):
        """
        Re-computes time-dependent travel time, dynamic congestion score, dynamic speed,
        and carbon emissions proxy for every edge at time_hours.
        """
        self.current_time_hours = time_hours
        rush_factor = self.get_rush_hour_multiplier(time_hours)

        # Clean expired incidents
        expired = [k for k, v in self.active_incidents.items() if time_hours >= v["end_time"]]
        for k in expired:
            del self.active_incidents[k]

        for u, v, data in self.G.edges(data=True):
            free_time = data.get("free_flow_time", 10.0)
            length = data.get("length", 100.0)
            capacity = data.get("capacity", 800.0)

            # Incident multiplier
            incident_mult = 1.0
            if (u, v) in self.active_incidents:
                incident_mult = self.active_incidents[(u, v)]["severity"]

            # Edge flow volume delay (Bureau of Public Roads BPR function)
            flow = self.edge_flows.get((u, v), 0.0)
            bpr_factor = 1.0 + 0.15 * ((flow / max(1.0, capacity)) ** 4)

            # Combined time-dependent travel time (seconds)
            current_travel_time = free_time * rush_factor * bpr_factor * incident_mult
            data["current_travel_time"] = current_travel_time

            # Effective dynamic speed (km/h)
            current_speed_ms = length / max(0.1, current_travel_time)
            current_speed_kmh = current_speed_ms * 3.6
            data["current_speed_kmh"] = current_speed_kmh

            # Dynamic congestion score C(e, t)
            congestion_score = max(0.0, (current_travel_time - free_time) / max(0.1, free_time))
            data["congestion_score"] = congestion_score

            # Carbon emissions proxy E(e, t) in grams CO2
            # E = distance_km * (base_emission + congestion_penalty + speed_inefficiency)
            dist_km = length / 1000.0
            speed_penalty = 120.0 / max(5.0, current_speed_kmh) # higher emissions at crawl speed
            emissions_g = dist_km * (150.0 + 40.0 * congestion_score + speed_penalty)
            data["emissions_co2_g"] = emissions_g

    def get_edge_weight(self, u: int, v: int, objective: str = "time") -> float:
        """
        Returns edge weight for specific routing objective: 'time', 'distance', 'congestion', or 'emissions'.
        """
        if u == v:
            return 0.0
        if self.G.has_edge(u, v):
            data = self.G.edges[u, v]
            if objective == "time":
                return data.get("current_travel_time", data.get("free_flow_time", 1.0))
            elif objective == "distance":
                return data.get("length", 1.0)
            elif objective == "congestion":
                return data.get("congestion_score", 0.0) * data.get("current_travel_time", 1.0)
            elif objective == "emissions":
                return data.get("emissions_co2_g", 1.0)
            else:
                return data.get("current_travel_time", 1.0)
        else:
            # Fallback to shortest path weight if non-adjacent nodes
            from backend.app.solvers.classical.shortest_path import dijkstra_path
            cost, _ = dijkstra_path(self.G, self, u, v, objective=objective)
            return cost

    def get_network_summary(self) -> dict:
        """Returns statistical summary of current network dynamic traffic state."""
        speeds = [d["current_speed_kmh"] for _, _, d in self.G.edges(data=True)]
        congestions = [d["congestion_score"] for _, _, d in self.G.edges(data=True)]
        return {
            "current_time_hours": self.current_time_hours,
            "avg_speed_kmh": sum(speeds) / max(1, len(speeds)),
            "min_speed_kmh": min(speeds) if speeds else 0,
            "max_congestion_score": max(congestions) if congestions else 0,
            "active_incidents_count": len(self.active_incidents)
        }

if __name__ == "__main__":
    from backend.app.graph.ingestion import get_bengaluru_graph
    g = get_bengaluru_graph()
    sim = DynamicTrafficSimulator(g, initial_time_hours=8.5)
    print("Initial state:", sim.get_network_summary())
    sim.inject_random_incidents(count=3)
    print("Post incident state:", sim.get_network_summary())
