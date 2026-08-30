import math
import numpy as np
from typing import List, Dict, Tuple, Any
from sklearn.cluster import KMeans
import networkx as nx

class Cluster:
    def __init__(self, cluster_id: int, center_node: int, customer_nodes: List[int]):
        self.cluster_id = cluster_id
        self.center_node = center_node
        self.customer_nodes = customer_nodes
        self.solver_used = "UNSOLVED"

    def __repr__(self):
        return f"<Cluster #{self.cluster_id}: {len(self.customer_nodes)} nodes (Solver: {self.solver_used})>"

def partition_nodes_into_clusters(
    customer_nodes: List[int],
    G: nx.DiGraph,
    max_cluster_size: int = 12
) -> List[Cluster]:
    """
    Partitions customer nodes into geographically coherent clusters, each containing <= max_cluster_size nodes.
    Ensures sub-tours are tractable for QUBO / QAOA quantum simulation.
    """
    if len(customer_nodes) <= max_cluster_size:
        # Small enough to fit in a single quantum cluster
        center = customer_nodes[0]
        return [Cluster(cluster_id=0, center_node=center, customer_nodes=list(customer_nodes))]

    # Extract spatial coordinates
    coords = []
    for node in customer_nodes:
        data = G.nodes[node]
        coords.append([data.get('y', 12.97), data.get('x', 77.59)])
    coords = np.array(coords)

    # Determine number of clusters
    k = math.ceil(len(customer_nodes) / max_cluster_size)
    kmeans = KMeans(n_clusters=k, random_state=42, n_init=10).fit(coords)
    labels = kmeans.labels_

    clusters_dict: Dict[int, List[int]] = {i: [] for i in range(k)}
    for idx, c_id in enumerate(customer_nodes):
        cluster_idx = labels[idx]
        clusters_dict[cluster_idx].append(c_id)

    # Enforce maximum size constraint by splitting oversized clusters
    final_clusters = []
    cluster_counter = 0

    for c_idx, node_group in clusters_dict.items():
        if not node_group:
            continue
        
        while len(node_group) > max_cluster_size:
            chunk = node_group[:max_cluster_size]
            node_group = node_group[max_cluster_size:]
            center = chunk[0]
            final_clusters.append(Cluster(cluster_id=cluster_counter, center_node=center, customer_nodes=chunk))
            cluster_counter += 1

        if node_group:
            center = node_group[0]
            final_clusters.append(Cluster(cluster_id=cluster_counter, center_node=center, customer_nodes=node_group))
            cluster_counter += 1

    return final_clusters
