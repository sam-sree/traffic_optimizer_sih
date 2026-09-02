from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Optional

class SolveRequest(BaseModel):
    solver_name: str = "Hybrid QPSO + Exact-Cluster"
    num_nodes: int = Field(default=25, ge=1, le=317)
    num_vehicles: int = Field(default=5, ge=1, le=50)
    vehicle_capacity: float = Field(default=65.0, gt=0, le=10000)
    time_of_day_hours: float = Field(default=8.5, ge=0, lt=24)
    objective_weights: Dict[str, float] = Field(default_factory=lambda: {
        "time": 0.4, "distance": 0.3, "congestion": 0.2, "emissions": 0.1
    })

class IncidentRequest(BaseModel):
    u: Optional[int] = None
    v: Optional[int] = None
    severity: float = Field(default=4.5, gt=1.0, le=20.0)
    count: int = Field(default=3, ge=1, le=50)

    @model_validator(mode="after")
    def validate_edge_pair(self):
        if (self.u is None) != (self.v is None):
            raise ValueError("u and v must be provided together")
        return self

class ReoptimizeRequest(BaseModel):
    affected_edges: Optional[List[List[int]]] = None
    severity: float = Field(default=5.0, gt=1.0, le=20.0)

    @model_validator(mode="after")
    def validate_affected_edges(self):
        if self.affected_edges is not None and any(len(edge) != 2 for edge in self.affected_edges):
            raise ValueError("each affected edge must contain exactly [u, v]")
        return self
