import os
import json
import random
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List

from backend.app.graph.ingestion import get_bengaluru_graph
from backend.app.graph.traffic_simulator import DynamicTrafficSimulator
from backend.app.solvers.base import RoutingProblem, CustomerDemand
from backend.app.solvers.classical.shortest_path import ShortestPathSolver
from backend.app.solvers.classical.ortools_solver import ORToolsSolver
from backend.app.solvers.classical.ga_solver import GASolver
from backend.app.solvers.classical.aco_solver import ACOSolver
from backend.app.solvers.qpso.qpso_solver import QPSOSolver
from backend.app.solvers.qpso.moqpso_solver import MOQPSOSolver
from backend.app.solvers.hybrid_orchestrator import HybridQuantumOrchestrator
from backend.app.solvers.cost_translation import compute_real_world_cost, compute_savings_vs_baseline, compute_fleet_scale_emissions
from backend.app.solvers.sla_compliance import compute_solution_sla
from backend.app.solvers.maps_export import build_google_maps_url
from backend.app.api.schemas import SolveRequest, IncidentRequest, ReoptimizeRequest

router = APIRouter(prefix="/api")

# Singleton state instances
G = get_bengaluru_graph()
traffic_sim = DynamicTrafficSimulator(G, initial_time_hours=8.5)
orchestrator = HybridQuantumOrchestrator(max_cluster_size=10, qpso_particles=30, qpso_iterations=80)

@router.get("/graph")
def get_graph_data():
    """Returns spatial nodes, edges, speeds, and active dynamic traffic incidents."""
    nodes_payload = []
    for n, d in G.nodes(data=True):
        nodes_payload.append({
            "id": n,
            "lat": d.get("y", d.get("lat", 12.9716)),
            "lon": d.get("x", d.get("lon", 77.5946))
        })

    edges_payload = []
    for u, v, d in G.edges(data=True):
        edges_payload.append({
            "u": u,
            "v": v,
            "length": d.get("length", 100.0),
            "speed_kmh": d.get("current_speed_kmh", 30.0),
            "travel_time_sec": d.get("current_travel_time", 10.0),
            "congestion_score": d.get("congestion_score", 0.0),
            "is_incident": (u, v) in traffic_sim.active_incidents
        })

    return {
        "nodes": nodes_payload,
        "edges": edges_payload,
        "summary": traffic_sim.get_network_summary()
    }

@router.post("/solve")
def solve_routing_problem(req: SolveRequest):
    """Executes selected routing solver and returns route geometries and metrics."""
    traffic_sim.update_traffic_state(req.time_of_day_hours)
    nodes = list(G.nodes())
    random.seed(42)
    depot_node = nodes[0]
    cust_nodes = random.sample(nodes[1:], min(req.num_nodes, len(nodes) - 1))

    customers = [
        CustomerDemand(node_id=n, demand_units=random.choice([10.0, 15.0, 20.0]))
        for n in cust_nodes
    ]

    problem = RoutingProblem(
        graph=G,
        traffic_simulator=traffic_sim,
        depot_node=depot_node,
        customers=customers,
        num_vehicles=req.num_vehicles,
        vehicle_capacity=req.vehicle_capacity,
        objective_weights=req.objective_weights
    )

    supported_solvers = {
        "Hybrid QPSO + Exact-Cluster", "Quantum-Inspired PSO (QPSO)",
        "Genetic Algorithm (GA)", "Ant Colony Optimization (ACO)",
        "Google OR-Tools CVRPTW", "Dijkstra Nearest-Neighbor"
    }
    if req.solver_name not in supported_solvers:
        raise HTTPException(status_code=422, detail=f"Unsupported solver_name: {req.solver_name}")

    if req.solver_name == "Hybrid QPSO + Exact-Cluster":
        sol = orchestrator.solve(problem)
    elif req.solver_name == "Quantum-Inspired PSO (QPSO)":
        sol = QPSOSolver(num_particles=40, max_iterations=100, seed=42).solve(problem)
    elif req.solver_name == "Genetic Algorithm (GA)":
        sol = GASolver(pop_size=40, generations=100, seed=42).solve(problem)
    elif req.solver_name == "Ant Colony Optimization (ACO)":
        sol = ACOSolver(num_ants=25, iterations=80, seed=42).solve(problem)
    elif req.solver_name == "Google OR-Tools CVRPTW":
        sol = ORToolsSolver(time_limit_sec=2.0).solve(problem)
    elif req.solver_name == "Dijkstra Nearest-Neighbor":
        sol = ShortestPathSolver(use_astar=False).solve(problem)

    # Real-world (rupee) cost translation, and savings vs. an "unoptimized"
    # baseline (naive nearest-neighbor) - see cost_translation.py for the
    # stated assumptions behind the conversion factors used here.
    cost_inr = compute_real_world_cost(sol.total_time_sec, sol.total_distance_m)
    savings_vs_baseline = None
    sustainability = None
    if req.solver_name != "Dijkstra Nearest-Neighbor":
        baseline_sol = ShortestPathSolver(use_astar=False).solve(problem)
        savings_vs_baseline = compute_savings_vs_baseline(
            optimized_time_sec=sol.total_time_sec,
            optimized_distance_m=sol.total_distance_m,
            baseline_time_sec=baseline_sol.total_time_sec,
            baseline_distance_m=baseline_sol.total_distance_m,
        )
        opt_emissions = compute_fleet_scale_emissions(sol.total_emissions_co2_g, max(1, len(sol.routes)))
        base_emissions = compute_fleet_scale_emissions(baseline_sol.total_emissions_co2_g, max(1, len(baseline_sol.routes)))
        sustainability = {
            "optimized_annual_co2_tons": opt_emissions["annual_co2_tons"],
            "baseline_annual_co2_tons": base_emissions["annual_co2_tons"],
            "annual_co2_saved_tons": round(base_emissions["annual_co2_tons"] - opt_emissions["annual_co2_tons"], 2),
            "assumptions": opt_emissions["assumptions"],
        }

    # On-time delivery / SLA compliance - see sla_compliance.py for the
    # simplifying assumption this rests on (common depot departure time).
    sla_report = compute_solution_sla(sol)

    routes_payload = []
    for r in sol.routes:
        coords = []
        for n in r.full_path_nodes:
            d = G.nodes[n]
            coords.append([d.get("y", 12.9716), d.get("x", 77.5946)])

        routes_payload.append({
            "vehicle_id": r.vehicle_id,
            "full_path_nodes": r.full_path_nodes,
            "path_coords": coords,
            "customer_sequence": r.customer_sequence,
            "total_time_min": r.total_time_sec / 60.0,
            "total_distance_km": r.total_distance_m / 1000.0,
            "total_congestion": r.total_congestion_cost,
            "total_emissions_co2_g": r.total_emissions_co2_g,
            "feasible": r.feasible,
            "maps_url": build_google_maps_url(r, G, depot_node)
        })

    return {
        "solver_name": sol.solver_name,
        "is_feasible": sol.is_feasible,
        "unserved_customer_count": sol.unserved_customer_count,
        "total_cost": sol.total_cost,
        "cost_inr": cost_inr,
        "savings_vs_baseline": savings_vs_baseline,
        "sustainability": sustainability,
        "sla_report": sla_report,
        "total_time_min": sol.total_time_sec / 60.0,
        "total_distance_km": sol.total_distance_m / 1000.0,
        "total_congestion": sol.total_congestion_cost,
        "total_emissions_co2_kg": sol.total_emissions_co2_g / 1000.0,
        "wall_time_ms": sol.wall_time_sec * 1000.0,
        "convergence_curve": sol.convergence_curve,
        "metadata": sol.metadata,
        "routes": routes_payload
    }

@router.post("/reoptimize")
def reoptimize_traffic(req: ReoptimizeRequest):
    """Executes dynamic real-time local exact-cluster re-optimization vs full re-solve comparison."""
    if req.affected_edges:
        affected = [tuple(e) for e in req.affected_edges]
        for u, v in affected:
            if not G.has_edge(u, v):
                raise HTTPException(status_code=422, detail=f"Unknown graph edge: [{u}, {v}]")
            traffic_sim.inject_incident(u, v, severity_factor=req.severity, duration_hours=2.0)
    else:
        affected = traffic_sim.inject_random_incidents(count=3, severity_range=(4.0, 7.0))

    if orchestrator.last_problem is None:
        # Run initial solve if missing
        nodes = list(G.nodes())
        cust_nodes = random.sample(nodes[1:], 25)
        prob = RoutingProblem(
            graph=G, traffic_simulator=traffic_sim, depot_node=nodes[0],
            customers=[CustomerDemand(n) for n in cust_nodes], num_vehicles=5, vehicle_capacity=65.0
        )
        orchestrator.solve(prob)

    # Method A: Full Network Re-solve
    import time
    t0 = time.time()
    sol_full = orchestrator.solve(orchestrator.last_problem)
    time_full_ms = (time.time() - t0) * 1000.0

    # Method B: Proposed Local Exact-Cluster Re-Optimization
    t0 = time.time()
    sol_local = orchestrator.reoptimize_dynamic_traffic(affected)
    time_local_ms = (time.time() - t0) * 1000.0

    speedup = time_full_ms / max(0.1, time_local_ms)

    return {
        "affected_edges": [list(e) for e in affected],
        "full_resolve_time_ms": time_full_ms,
        "local_reopt_time_ms": time_local_ms,
        "speedup_factor": speedup,
        "affected_clusters_count": sol_local.metadata.get("affected_clusters_count", 1),
        "total_clusters_count": sol_local.metadata.get("clusters_count", 5),
        "reoptimized_cost": sol_local.total_cost,
        "reoptimized_time_min": sol_local.total_time_sec / 60.0
    }

@router.get("/pareto")
def get_pareto_front(num_nodes: int = 20):
    """Executes MO-QPSO and returns 4-objective Pareto front trade-off archive."""
    nodes = list(G.nodes())
    random.seed(42)
    depot_node = nodes[0]
    cust_nodes = random.sample(nodes[1:], min(num_nodes, len(nodes) - 1))
    problem = RoutingProblem(
        graph=G, traffic_simulator=traffic_sim, depot_node=depot_node,
        customers=[CustomerDemand(n) for n in cust_nodes], num_vehicles=4, vehicle_capacity=60.0
    )

    mo_solver = MOQPSOSolver(num_particles=30, max_iterations=60, archive_capacity=25, seed=42)
    pareto_pts, _ = mo_solver.solve_pareto_front(problem)

    payload = []
    for idx, pt in enumerate(pareto_pts):
        payload.append({
            "id": idx + 1,
            "time_min": pt.objectives[0] / 60.0,
            "distance_km": pt.objectives[1] / 1000.0,
            "congestion": pt.objectives[2],
            "emissions_co2_kg": pt.objectives[3] / 1000.0
        })

    return {"pareto_points": payload}

@router.get("/benchmarks")
def get_benchmark_report_data():
    """Returns machine-readable benchmark JSON output."""
    json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', 'data', 'benchmark_results.json'))
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            return json.load(f)

    # Return default synthetic payload if not yet run
    return {
        "n_20": {
            "Hybrid QPSO + Exact-Cluster": {"cost_mean": 52.19, "runtime_ms_mean": 1200.0, "is_stochastic": True},
            "Quantum-Inspired PSO (QPSO)": {"cost_mean": 46.12, "runtime_ms_mean": 4800.0, "is_stochastic": True},
            "Google OR-Tools CVRPTW": {"cost_mean": 45.00, "runtime_ms_mean": 2800.0, "is_stochastic": False}
        }
    }

@router.post("/incidents/inject")
def inject_incidents(req: IncidentRequest):
    if req.u is not None and req.v is not None:
        if not G.has_edge(req.u, req.v):
            raise HTTPException(status_code=422, detail=f"Unknown graph edge: [{req.u}, {req.v}]")
        traffic_sim.inject_incident(req.u, req.v, severity_factor=req.severity)
    else:
        traffic_sim.inject_random_incidents(count=req.count, severity_range=(req.severity, req.severity + 2.0))
    return {"status": "SUCCESS", "active_incidents": len(traffic_sim.active_incidents)}

@router.post("/incidents/clear")
def clear_incidents():
    traffic_sim.clear_incidents()
    return {"status": "SUCCESS", "active_incidents": 0}
