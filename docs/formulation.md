# Mathematical Formulation: Capacitated Vehicle Routing Problem with Time Windows (CVRPTW) & QUBO Mapping

## 1. Classical Integer Linear Programming (ILP) Formulation

Let the transportation road network be modeled as a directed graph $G = (V, E)$, where $V = \{0, 1, \dots, N\}$ with node $0$ as the central depot and $V_C = \{1, \dots, N\}$ as customer delivery locations. A fleet of $K$ identical vehicles, each of capacity $C$, is stationed at the depot.

### Decision Variables
- $x_{i, j}^k \in \{0, 1\}$: Binary variable indicating if vehicle $k$ travels directly on directed edge $(i, j) \in E$.
- $s_i^k \ge 0$: Continuous arrival time of vehicle $k$ at node $i$.
- $u_i^k \ge 0$: Cumulative load carried by vehicle $k$ after visiting node $i$.

### Multi-Objective Objective Function
$$\min Z = w_1 \sum_{k=1}^K \sum_{(i,j) \in E} t_{i,j}(t) x_{i,j}^k + w_2 \sum_{k=1}^K \sum_{(i,j) \in E} d_{i,j} x_{i,j}^k + w_3 \sum_{k=1}^K \sum_{(i,j) \in E} C_{i,j}(t) x_{i,j}^k + w_4 \sum_{k=1}^K \sum_{(i,j) \in E} E_{i,j}(t) x_{i,j}^k$$

where:
- $t_{i,j}(t)$: Time-dependent travel time reflecting dynamic traffic congestion $\mu_{\text{rush}}(t) \cdot \mu_{\text{incident}}(e)$.
- $d_{i,j}$: Haversine physical road distance in meters.
- $C_{i,j}(t)$: Congestion score penalty.
- $E_{i,j}(t)$: Carbon emissions proxy in grams CO₂.

### Constraints
1. **Single Visit Constraint**: Every customer node is served exactly once:
   $$\sum_{k=1}^K \sum_{j \in V, j \neq i} x_{i,j}^k = 1, \quad \forall i \in V_C$$
2. **Depot Flow Conservation**: Every vehicle leaves and returns to the depot:
   $$\sum_{j \in V_C} x_{0,j}^k = 1, \quad \sum_{i \in V_C} x_{i,0}^k = 1, \quad \forall k \in \{1, \dots, K\}$$
3. **Flow Continuity**:
   $$\sum_{i \in V, i \neq j} x_{i,j}^k = \sum_{l \in V, l \neq j} x_{j,l}^k, \quad \forall j \in V_C, \forall k$$
4. **Capacity Constraint**:
   $$\sum_{i \in V_C} q_i \sum_{j \in V} x_{i,j}^k \le C, \quad \forall k$$
5. **Time Window & Sub-tour Elimination**:
   $$s_i^k + t_{i,j}(t) + \text{service}_i - s_j^k \le M (1 - x_{i,j}^k), \quad a_i \le s_i^k \le b_i$$

---

## 2. Cluster-First QUBO Mapping for Quantum Sub-Solver

For an intra-cluster sub-tour of $N_c \le 12$ nodes, we formulate the sub-tour as a **Quadratic Unconstrained Binary Optimization (QUBO)** matrix $Q$:

$$\min_{x \in \{0,1\}^K} x^T Q x$$

where $x_{i, t} \in \{0, 1\}$ is $1$ if cluster node $i$ is visited at step $t \in \{0, \dots, N_c-1\}$. Total binary variables $K = N_c^2$.

### QUBO Hamiltonian Terms
$$H(x) = H_{\text{cost}}(x) + A \cdot H_{\text{visit}}(x) + B \cdot H_{\text{step}}(x)$$

1. **Intra-Cluster Distance Objective**:
   $$H_{\text{cost}}(x) = \sum_{i=0}^{N_c-1} \sum_{j=0}^{N_c-1} \sum_{t=0}^{N_c-1} c_{i,j} \cdot x_{i,t} \cdot x_{j, (t+1) \bmod N_c}$$

2. **Penalty A (Every Node Visited Once)**:
   $$H_{\text{visit}}(x) = \sum_{i=0}^{N_c-1} \left( \sum_{t=0}^{N_c-1} x_{i,t} - 1 \right)^2$$

3. **Penalty B (Every Step Has One Node)**:
   $$H_{\text{step}}(x) = \sum_{t=0}^{N_c-1} \left( \sum_{i=0}^{N_c-1} x_{i,t} - 1 \right)^2$$
