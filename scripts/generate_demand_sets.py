import os
import sys
import json
import math
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.graph.ingestion import get_bengaluru_graph

def generate_named_profile(G, nodes, data_dir, name: str, size: int, demand_multiplier: float, window_hours: float, seed_offset: int):
    """
    Generates a named demand profile (e.g. "weekday_peak", "weekend_light")
    at a fixed customer count, with a demand multiplier (heavier/lighter order
    volume) and a time-window tightness (how many hours customers allow for
    delivery) - so the system can be demoed against more than one demand
    scenario instead of a single fixed dataset, showing it isn't tuned to
    just one case.
    """
    random.seed(1000 + seed_offset)
    depot = nodes[0]
    sampled_nodes = [nodes[(i % (len(nodes) - 1)) + 1] for i in range(size)]

    customers = []
    for idx, n in enumerate(sampled_nodes):
        c_data = G.nodes[n]
        base_demand = random.choice([10.0, 15.0, 20.0, 25.0])
        demand = round(base_demand * demand_multiplier, 1)
        ready = random.uniform(0.0, 7200.0)
        due = ready + window_hours * 3600.0
        customers.append({
            "id": idx + 1,
            "node_id": n,
            "demand_units": demand,
            "ready_time": ready,
            "due_time": due,
            "service_time": 300.0,
            "lat": c_data.get("y", 12.9716),
            "lon": c_data.get("x", 77.5946)
        })

    veh_cap = 80.0
    total_demand = sum(c["demand_units"] for c in customers)
    num_veh = max(3, math.ceil((total_demand * 1.20) / veh_cap))

    demand_data = {
        "instance_name": f"bengaluru_{name}",
        "profile_name": name,
        "num_nodes": size,
        "depot_node": depot,
        "num_vehicles": num_veh,
        "vehicle_capacity": veh_cap,
        "customers": customers
    }

    file_path = os.path.join(data_dir, f"demand_profile_{name}.json")
    with open(file_path, "w") as f:
        json.dump(demand_data, f, indent=2)
    print(f"  • Generated profile '{name}': {file_path} ({size} customers, {num_veh} vehicles, demand x{demand_multiplier}, {window_hours}h windows)")


def generate_demand_sets():
    print("Generating synthetic delivery demand sets (20, 50, 100, 300, 1000 nodes)...")
    G = get_bengaluru_graph()
    nodes = list(G.nodes())

    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'demand_sets'))
    os.makedirs(data_dir, exist_ok=True)

    sizes = [20, 50, 100, 300, 1000]

    for size in sizes:
        random.seed(42 + size)
        depot = nodes[0]
        
        # Sample or cycle nodes if size > available nodes in local subgraph
        sampled_nodes = [nodes[(i % (len(nodes) - 1)) + 1] for i in range(size)]

        customers = []
        for idx, n in enumerate(sampled_nodes):
            c_data = G.nodes[n]
            demand = random.choice([10.0, 15.0, 20.0, 25.0])
            ready = random.uniform(0.0, 7200.0)
            due = ready + random.uniform(7200.0, 21600.0)
            customers.append({
                "id": idx + 1,
                "node_id": n,
                "demand_units": demand,
                "ready_time": ready,
                "due_time": due,
                "service_time": 300.0,
                "lat": c_data.get("y", 12.9716),
                "lon": c_data.get("x", 77.5946)
            })

        # Size the fleet FROM actual generated demand, with 20% headroom, so the
        # instance is always solvable - a fixed size-based formula can silently
        # fall short of total demand depending on the random demand values drawn.
        veh_cap = 80.0
        total_demand = sum(c["demand_units"] for c in customers)
        num_veh = max(3, math.ceil((total_demand * 1.20) / veh_cap))

        demand_data = {
            "instance_name": f"bengaluru_{size}",
            "num_nodes": size,
            "depot_node": depot,
            "num_vehicles": num_veh,
            "vehicle_capacity": veh_cap,
            "customers": customers
        }

        file_path = os.path.join(data_dir, f"demand_{size}.json")
        with open(file_path, "w") as f:
            json.dump(demand_data, f, indent=2)
        print(f"  • Generated: {file_path} ({size} customers, {num_veh} vehicles)")

    print("Demand sets generated successfully!")

    # Named demand-variability profiles: same city/graph, different demand
    # scenarios (order volume, delivery-window tightness), to demonstrate the
    # system isn't tuned to a single fixed dataset.
    print("\nGenerating named demand-variability profiles (weekday peak, weekend light)...")
    generate_named_profile(G, nodes, data_dir, "weekday_peak", size=50, demand_multiplier=1.4, window_hours=3.0, seed_offset=1)
    generate_named_profile(G, nodes, data_dir, "weekend_light", size=50, demand_multiplier=0.7, window_hours=8.0, seed_offset=2)
    print("Demand-variability profiles generated successfully!")

if __name__ == "__main__":
    generate_demand_sets()
