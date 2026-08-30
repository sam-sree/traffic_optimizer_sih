from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
import networkx as nx

@dataclass
class CustomerDemand:
    node_id: int
    demand_units: float = 10.0
    ready_time: float = 0.0          # Earliest arrival time in seconds
    due_time: float = 86400.0        # Latest arrival time in seconds (default 24h)
    service_time: float = 300.0      # Unloading service time in seconds (default 5 min)
    lat: Optional[float] = None
    lon: Optional[float] = None

@dataclass
class RoutingProblem:
    graph: nx.DiGraph
    traffic_simulator: Any          # DynamicTrafficSimulator instance
    depot_node: int
    customers: List[CustomerDemand]
    num_vehicles: int = 5
    vehicle_capacity: float = 100.0
    # Pareto objective weights: time, distance, congestion, emissions
    objective_weights: Dict[str, float] = field(default_factory=lambda: {
        "time": 0.4,
        "distance": 0.3,
        "congestion": 0.2,
        "emissions": 0.1
    })

@dataclass
class VehicleRoute:
    vehicle_id: int
    full_path_nodes: List[int]       # Step-by-step graph node sequence
    customer_sequence: List[int]     # Sequence of served customer node IDs
    total_time_sec: float = 0.0
    total_distance_m: float = 0.0
    total_congestion_cost: float = 0.0
    total_emissions_co2_g: float = 0.0
    feasible: bool = True
    violation_notes: List[str] = field(default_factory=list)

@dataclass
class RoutingSolution:
    solver_name: str
    problem: RoutingProblem
    routes: List[VehicleRoute]
    total_cost: float = 0.0
    total_time_sec: float = 0.0
    total_distance_m: float = 0.0
    total_congestion_cost: float = 0.0
    total_emissions_co2_g: float = 0.0
    wall_time_sec: float = 0.0
    convergence_curve: List[float] = field(default_factory=list) # Best objective cost per iteration
    is_feasible: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def compute_aggregates(self):
        """Re-evaluates global objective totals across all vehicle routes."""
        self.total_time_sec = sum(r.total_time_sec for r in self.routes)
        self.total_distance_m = sum(r.total_distance_m for r in self.routes)
        self.total_congestion_cost = sum(r.total_congestion_cost for r in self.routes)
        self.total_emissions_co2_g = sum(r.total_emissions_co2_g for r in self.routes)
        
        w = self.problem.objective_weights
        # Weighted scalar cost metric
        self.total_cost = (
            w.get("time", 0.4) * (self.total_time_sec / 3600.0) +
            w.get("distance", 0.3) * (self.total_distance_m / 1000.0) +
            w.get("congestion", 0.2) * self.total_congestion_cost +
            w.get("emissions", 0.1) * (self.total_emissions_co2_g / 1000.0)
        )
        self.is_feasible = all(r.feasible for r in self.routes)

class BaseSolver(ABC):
    """Abstract interface for all VRP and route optimization algorithms."""
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def solve(self, problem: RoutingProblem) -> RoutingSolution:
        pass
