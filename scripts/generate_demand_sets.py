import os
import sys
import json
import random

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.graph.ingestion import get_bengaluru_graph

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

        num_veh = max(3, size // 5)
        veh_cap = 80.0

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

if __name__ == "__main__":
    generate_demand_sets()
