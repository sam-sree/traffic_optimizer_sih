import os
import pickle
import math
import random
import networkx as nx

# Global constants for fallback Bengaluru coordinates
DEFAULT_BENGALURU_LAT = 12.9716
DEFAULT_BENGALURU_LON = 77.5946
DEFAULT_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "cached_graphs")

def get_bengaluru_graph(place_name="Indiranagar, Bengaluru, Karnataka, India", cache_filename="bengaluru_indiranagar.pkl", force_reload=False):
    """
    Ingests and returns a NetworkX DiGraph representing the road network.
    Checks local cache first. If absent or force_reload is True, fetches via OSMnx,
    pre-processes edge attributes (free_flow_time, capacity, length), and caches the graph.
    Includes a fallback synthetic Bengaluru spatial network generator if offline/network fails.
    """
    os.makedirs(DEFAULT_CACHE_DIR, exist_ok=True)
    cache_path = os.path.join(DEFAULT_CACHE_DIR, cache_filename)

    if not force_reload and os.path.exists(cache_path):
        try:
            with open(cache_path, "rb") as f:
                G = pickle.load(f)
            print(f"[GraphIngestion] Successfully loaded graph from cache: {cache_path} ({G.number_of_nodes()} nodes, {G.number_of_edges()} edges)")
            return G
        except Exception as e:
            print(f"[GraphIngestion] Warning: Failed to read cache ({e}). Re-ingesting graph...")

    G = None
    try:
        import osmnx as ox
        print(f"[GraphIngestion] Fetching OSMnx graph for '{place_name}'...")
        # Configure OSMnx
        ox.settings.use_cache = True
        ox.settings.log_console = False

        raw_G = ox.graph_from_place(place_name, network_type="drive", simplify=True)
        # Convert MultiDiGraph to DiGraph for deterministic optimization routing
        G = ox.convert.to_digraph(raw_G, weight="length")
        
        # Ensure strongly connected
        if not nx.is_strongly_connected(G):
            largest_scc = max(nx.strongly_connected_components(G), key=len)
            G = G.subgraph(largest_scc).copy()

        print(f"[GraphIngestion] Successfully fetched OSM graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    except Exception as err:
        print(f"[GraphIngestion] OSMnx fetch failed or offline ({err}). Generating synthetic spatial Bengaluru road network...")
        G = _generate_synthetic_bengaluru_graph(num_nodes=120, center_lat=DEFAULT_BENGALURU_LAT, center_lon=DEFAULT_BENGALURU_LON)

    # Process edge attributes
    G = preprocess_graph_attributes(G)

    # Save to cache
    try:
        with open(cache_path, "wb") as f:
            pickle.dump(G, f)
        print(f"[GraphIngestion] Cached graph to {cache_path}")
    except Exception as err:
        print(f"[GraphIngestion] Failed to cache graph: {err}")

    return G

def preprocess_graph_attributes(G):
    """
    Enriches all edges in G with standardized attributes:
    - length (meters)
    - maxspeed (km/h)
    - free_flow_speed (m/s)
    - free_flow_time (seconds)
    - capacity (vehicles/hour)
    - congestion_factor (initial=1.0)
    Ensures nodes have x (lon) and y (lat) attributes.
    """
    for node, data in G.nodes(data=True):
        if 'x' not in data or 'y' not in data:
            # Assign fallback grid coordinates if missing
            data['x'] = data.get('lon', DEFAULT_BENGALURU_LON + (node % 10) * 0.002)
            data['y'] = data.get('lat', DEFAULT_BENGALURU_LAT + (node // 10) * 0.002)

    for u, v, data in G.edges(data=True):
        # Length in meters
        if 'length' not in data or not data['length']:
            u_data = G.nodes[u]
            v_data = G.nodes[v]
            # Haversine estimation
            data['length'] = _haversine_distance(u_data['y'], u_data['x'], v_data['y'], v_data['x'])

        # Maxspeed in km/h
        raw_speed = data.get('maxspeed', 30)
        if isinstance(raw_speed, list):
            raw_speed = raw_speed[0]
        try:
            speed_kmh = float(str(raw_speed).replace('km/h', '').strip())
        except (ValueError, AttributeError):
            speed_kmh = 35.0
        
        data['maxspeed_kmh'] = speed_kmh
        speed_ms = max(5.0, speed_kmh * 1000.0 / 3600.0)
        data['free_flow_speed_ms'] = speed_ms
        data['free_flow_time'] = float(data['length']) / speed_ms
        data['capacity'] = data.get('capacity', 800.0) # default vehicles/hr
        data['congestion_factor'] = 1.0
        data['current_travel_time'] = data['free_flow_time']

    return G

def _haversine_distance(lat1, lon1, lat2, lon2):
    """Computes distance in meters between two lat/lon points."""
    R = 6371000.0 # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def _generate_synthetic_bengaluru_graph(num_nodes=120, center_lat=DEFAULT_BENGALURU_LAT, center_lon=DEFAULT_BENGALURU_LON):
    """
    Generates a realistic spatial road network graph centered around Bengaluru coordinates.
    Creates node clusters, main arterial corridors, and local grid connections.
    """
    random.seed(42)
    G = nx.DiGraph()
    
    # Place nodes in realistic spatial clusters (simulating Indiranagar / Koramangala sub-districts)
    nodes = []
    num_clusters = 5
    cluster_centers = [
        (center_lat + (random.random() - 0.5) * 0.04, center_lon + (random.random() - 0.5) * 0.04)
        for _ in range(num_clusters)
    ]
    
    for i in range(num_nodes):
        c_lat, c_lon = cluster_centers[i % num_clusters]
        lat = c_lat + (random.gauss(0, 0.006))
        lon = c_lon + (random.gauss(0, 0.006))
        G.add_node(i, y=lat, x=lon, lat=lat, lon=lon)
        nodes.append(i)

    # Connect nodes using k-nearest neighbors (spatial Delaunay / k-NN topology)
    for i in nodes:
        i_lat, i_lon = G.nodes[i]['y'], G.nodes[i]['x']
        # Find k nearest neighbors
        dists = []
        for j in nodes:
            if i == j:
                continue
            j_lat, j_lon = G.nodes[j]['y'], G.nodes[j]['x']
            d = _haversine_distance(i_lat, i_lon, j_lat, j_lon)
            dists.append((d, j))
        
        dists.sort()
        # Connect to 4 nearest neighbors bi-directionally
        for d, j in dists[:4]:
            speed = 50.0 if d > 1000 else 30.0 # arterial vs local street
            G.add_edge(i, j, length=d, maxspeed=speed)
            G.add_edge(j, i, length=d, maxspeed=speed)

    # Ensure strong connectivity
    if not nx.is_strongly_connected(G):
        components = list(nx.strongly_connected_components(G))
        for idx in range(len(components) - 1):
            u = list(components[idx])[0]
            v = list(components[idx+1])[0]
            d = _haversine_distance(G.nodes[u]['y'], G.nodes[u]['x'], G.nodes[v]['y'], G.nodes[v]['x'])
            G.add_edge(u, v, length=d, maxspeed=40.0)
            G.add_edge(v, u, length=d, maxspeed=40.0)

    print(f"[SyntheticGraph] Created Bengaluru spatial graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G

if __name__ == "__main__":
    g = get_bengaluru_graph()
    print("Graph test completed successfully!")
