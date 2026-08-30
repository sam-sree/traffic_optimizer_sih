from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Tuple, List, Dict, Any
import numpy as np

@dataclass
class QUBOResult:
    bitstring: np.ndarray       # 1D binary array solution vector x
    energy: float              # QUBO Hamiltonian energy x^T Q x
    solver_type: str           # "QAOA_SIMULATOR" or "CLASSICAL_FALLBACK"
    execution_time_sec: float
    metadata: Dict[str, Any]

class QuantumSolver(ABC):
    """
    Abstract Hardware-Agnostic Interface for Quantum Solvers.
    Isolates quantum execution so the backend simulator (Qiskit Aer) can later be
    swapped for real quantum processing units (IBM Quantum / Qiskit Runtime QPU)
    without modifying solver orchestration logic.
    """
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def solve_qubo(
        self,
        Q: np.ndarray,
        time_budget_sec: float = 3.0,
        shots: int = 1024
    ) -> QUBOResult:
        """
        Solves the QUBO optimization problem: min x^T Q x where x in {0, 1}^N.
        Must fall back to exact classical solver if quantum simulation exceeds time budget.
        """
        pass
