# System Architecture & Hardware Scaling Roadmap

## 1. Hybrid Classical-Quantum Decomposition Architecture

The QuantumRoute platform decouples large-scale dynamic transportation routing into a two-level hybrid hierarchy:

```
                  +-----------------------------------+
                  |  OSMnx Road Network Graph G=(V,E) |
                  |   Time-Dependent Traffic Simulator|
                  +-----------------------------------+
                                    |
                                    v
                  +-----------------------------------+
                  |   Cluster-First Spatial Partition |
                  |  (Constrained K-Means / METIS)    |
                  +-----------------------------------+
                                    |
                  +-----------------+-----------------+
                  |                                   |
                  v                                   v
      +------------------------+          +------------------------+
      |  Cluster #1 (<=12 n)   |          |  Cluster #K (<=12 n)   |
      +------------------------+          +------------------------+
                  |                                   |
                  v                                   v
      +------------------------+          +------------------------+
      | Qiskit QAOA Sub-Solver |          | Qiskit QAOA Sub-Solver |
      | (Held-Karp Fallback)   |          | (Held-Karp Fallback)   |
      +------------------------+          +------------------------+
                  |                                   |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  | Quantum-Inspired PSO Global Stage |
                  | Cluster Sequencing & Fleet Stitch |
                  +-----------------------------------+
                                    |
                                    v
                  +-----------------------------------+
                  | Dynamic Real-Time Re-Optimizer    |
                  | (Local QAOA + QPSO Re-stitch)     |
                  +-----------------------------------+
```

---

## 2. Hardware Scaling Roadmap (Transitioning to Real QPU Hardware)

The quantum simulation layer is completely isolated behind the abstract `QuantumSolver` interface:

```python
class QuantumSolver(ABC):
    @abstractmethod
    def solve_qubo(self, Q: np.ndarray, time_budget_sec: float) -> QUBOResult:
        pass
```

### Path to Swap Simulator for IBM Quantum / Qiskit Runtime QPU
To transition from local Qiskit Aer simulation to real QPU hardware (e.g. IBM Eagle / Heron 127+ Qubit QPUs):

1. **Instantiate Qiskit Runtime Service**:
   ```python
   from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
   service = QiskitRuntimeService(channel="ibm_quantum", token="YOUR_IBM_QUANTUM_TOKEN")
   backend = service.least_busy(operational=True, simulator=False)
   ```
2. **Implement `IBMQuantumQPUSolver(QuantumSolver)`**:
   - Transpile Ising Pauli Hamiltonian $H$ using `qiskit.transpiler.preset_passmanagers.generate_preset_pass_manager(optimization_level=3, backend=backend)`.
   - Submit QAOA circuit execution job using `SamplerV2(mode=backend).run([qaoa_circuit], shots=2048)`.
   - Retrieve bitstrings and return `QUBOResult` with `solver_type="IBM_HERON_QPU"`.

Because the hybrid orchestrator depends solely on the abstract `QuantumSolver` contract, **zero changes** are required in graph clustering, QPSO route stitching, or the FastAPI backend when deploying to physical quantum hardware.
