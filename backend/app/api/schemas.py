from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class SolveRequest(BaseModel):
    solver_name: str = "Hybrid QPSO + QAOA-Cluster"
    num_nodes: int = 25
    num_vehicles: int = 5
    vehicle_capacity: float = 65.0
    time_of_day_hours: float = 8.5
    objective_weights: Dict[str, float] = Field(default_factory=lambda: {
        "time": 0.4, "distance": 0.3, "congestion": 0.2, "emissions": 0.1
    })

class IncidentRequest(BaseModel):
    u: Optional[int] = None
    v: Optional[int] = None
    severity: float = 4.5
    count: int = 3

class ReoptimizeRequest(BaseModel):
    affected_edges: Optional[List[List[int]]] = None
    severity: float = 5.0
