import os
import sys
import matplotlib
matplotlib.use('Agg') # Non-interactive backend for server/script execution
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np

# Ensure backend package is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.graph.ingestion import get_bengaluru_graph
from backend.app.graph.traffic_simulator import DynamicTrafficSimulator

def visualize_graph_and_traffic():
    print("=" * 70)
    print("Phase 1: QuantumRoute — Graph Ingestion & Dynamic Traffic Visualization")
    print("=" * 70)

    # 1. Ingest graph
    G = get_bengaluru_graph(place_name="Indiranagar, Bengaluru, Karnataka, India")
    print(f"[Phase 1] Loaded Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    # 2. Setup dynamic traffic simulation
    sim = DynamicTrafficSimulator(G, initial_time_hours=8.5) # Rush hour 08:30 AM
    print(f"[Phase 1] Traffic Simulation initialized at t={sim.current_time_hours}h (Morning Rush Peak)")

    # 3. Inject dynamic traffic incident
    incidents = sim.inject_random_incidents(count=4, severity_range=(3.0, 6.0))
    print(f"[Phase 1] Injected {len(incidents)} dynamic traffic incidents at edges: {incidents}")

    # Output directory
    out_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'cached_graphs'))
    os.makedirs(out_dir, exist_ok=True)
    png_path = os.path.join(out_dir, 'bengaluru_traffic_visualization.png')
    html_path = os.path.join(out_dir, 'bengaluru_traffic_map.html')

    # 4. Generate Matplotlib static 4-panel diagnostic plot
    fig, axes = plt.subplots(2, 2, figsize=(16, 14), facecolor='#0f172a')
    fig.suptitle("QuantumRoute: Bengaluru Road Network & Dynamic Traffic Simulation (Phase 1)", 
                 fontsize=18, fontweight='bold', color='#f8fafc', y=0.96)

    # Extract spatial coordinates
    pos = {n: (data['x'], data['y']) for n, data in G.nodes(data=True)}
    node_x = [data['x'] for _, data in G.nodes(data=True)]
    node_y = [data['y'] for _, data in G.nodes(data=True)]

    # Panel 1: Dynamic Speed Map (km/h)
    ax1 = axes[0, 0]
    ax1.set_facecolor('#1e293b')
    ax1.set_title("Network Graph: Dynamic Edge Speeds (km/h)", color='#e2e8f0', fontsize=13, fontweight='bold')
    
    speeds = [data.get('current_speed_kmh', 30.0) for _, _, data in G.edges(data=True)]
    norm_speed = plt.Normalize(vmin=5, vmax=60)
    cmap_speed = cm.magma # Fast = Yellow/Light, Slow/Congested = Dark Red/Purple

    for u, v, data in G.edges(data=True):
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        spd = data.get('current_speed_kmh', 30.0)
        color = cmap_speed(norm_speed(spd))
        width = 2.5 if (u, v) in sim.active_incidents else 1.2
        ax1.plot([x1, x2], [y1, y2], color=color, linewidth=width, alpha=0.85)

    ax1.scatter(node_x, node_y, c='#38bdf8', s=12, zorder=5, alpha=0.9, label='Road Intersections')
    ax1.set_xlabel("Longitude (°E)", color='#94a3b8')
    ax1.set_ylabel("Latitude (°N)", color='#94a3b8')
    ax1.tick_params(colors='#94a3b8')
    cbar1 = fig.colorbar(cm.ScalarMappable(norm=norm_speed, cmap=cmap_speed), ax=ax1)
    cbar1.set_label('Speed (km/h)', color='#e2e8f0')
    cbar1.ax.yaxis.set_tick_params(color='#94a3b8')
    plt.setp(plt.getp(cbar1.ax, 'yticklabels'), color='#94a3b8')

    # Panel 2: Congestion Heatmap & Incidents
    ax2 = axes[0, 1]
    ax2.set_facecolor('#1e293b')
    ax2.set_title("Traffic Congestion Score & Dynamic Incident Hotspots", color='#e2e8f0', fontsize=13, fontweight='bold')

    congestions = [data.get('congestion_score', 0.0) for _, _, data in G.edges(data=True)]
    norm_cong = plt.Normalize(vmin=0, vmax=max(2.0, max(congestions) if congestions else 1.0))
    cmap_cong = cm.YlOrRd

    for u, v, data in G.edges(data=True):
        x1, y1 = pos[u]
        x2, y2 = pos[v]
        cong = data.get('congestion_score', 0.0)
        color = cmap_cong(norm_cong(cong))
        ax2.plot([x1, x2], [y1, y2], color=color, linewidth=1.2, alpha=0.8)

    # Highlight incident locations
    inc_x, inc_y = [], []
    for (u, v) in sim.active_incidents.keys():
        inc_x.append((pos[u][0] + pos[v][0]) / 2)
        inc_y.append((pos[u][1] + pos[v][1]) / 2)
    if inc_x:
        ax2.scatter(inc_x, inc_y, c='#ef4444', s=120, marker='*', zorder=10, label='Incident Disruptions (3.5x-6x delay)')

    ax2.scatter(node_x, node_y, c='#64748b', s=8, zorder=3, alpha=0.5)
    ax2.legend(facecolor='#0f172a', edgecolor='#334155', labelcolor='#f8fafc', loc='upper left')
    ax2.set_xlabel("Longitude (°E)", color='#94a3b8')
    ax2.set_ylabel("Latitude (°N)", color='#94a3b8')
    ax2.tick_params(colors='#94a3b8')
    cbar2 = fig.colorbar(cm.ScalarMappable(norm=norm_cong, cmap=cmap_cong), ax=ax2)
    cbar2.set_label('Congestion Penalty Score C(e,t)', color='#e2e8f0')
    cbar2.ax.yaxis.set_tick_params(color='#94a3b8')
    plt.setp(plt.getp(cbar2.ax, 'yticklabels'), color='#94a3b8')

    # Panel 3: Speed Distribution Histogram
    ax3 = axes[1, 0]
    ax3.set_facecolor('#1e293b')
    ax3.set_title("Edge Speed Distribution (km/h)", color='#e2e8f0', fontsize=13, fontweight='bold')
    n, bins, patches = ax3.hist(speeds, bins=25, color='#38bdf8', edgecolor='#0284c7', alpha=0.85)
    ax3.set_xlabel("Speed (km/h)", color='#94a3b8')
    ax3.set_ylabel("Edge Count", color='#94a3b8')
    ax3.tick_params(colors='#94a3b8')
    ax3.grid(True, linestyle='--', alpha=0.2, color='#94a3b8')

    # Panel 4: Dynamic Diurnal Rush Hour Profile
    ax4 = axes[1, 1]
    ax4.set_facecolor('#1e293b')
    ax4.set_title("24-Hour Diurnal Traffic Congestion Multiplier", color='#e2e8f0', fontsize=13, fontweight='bold')
    hours = np.linspace(0, 24, 200)
    multipliers = [sim.get_rush_hour_multiplier(h) for h in hours]
    ax4.plot(hours, multipliers, color='#a855f7', linewidth=2.5, label='Traffic Congestion Multiplier')
    ax4.axvline(x=sim.current_time_hours, color='#38bdf8', linestyle='--', linewidth=2, label=f'Current Time ({sim.current_time_hours}h)')
    ax4.scatter([8.5, 18.5], [sim.get_rush_hour_multiplier(8.5), sim.get_rush_hour_multiplier(18.5)], 
                color='#f43f5e', s=80, zorder=5, label='Morning/Evening Peaks')
    ax4.set_xlabel("Time of Day (Hours)", color='#94a3b8')
    ax4.set_ylabel("Congestion Multiplier μ_rush(t)", color='#94a3b8')
    ax4.tick_params(colors='#94a3b8')
    ax4.legend(facecolor='#0f172a', edgecolor='#334155', labelcolor='#f8fafc', loc='upper right')
    ax4.grid(True, linestyle='--', alpha=0.2, color='#94a3b8')

    plt.tight_layout(rect=[0, 0.03, 1, 0.94])
    plt.savefig(png_path, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"[Phase 1] Static visualization PNG saved to: {png_path}")

    # 5. Generate interactive Folium HTML map if folium is installed
    try:
        import folium
        center_lat = np.mean(node_y)
        center_lon = np.mean(node_x)
        m = folium.Map(location=[center_lat, center_lon], zoom_start=14, tiles="CartoDB dark_matter")

        for u, v, data in G.edges(data=True):
            lat1, lon1 = pos[u][1], pos[u][0]
            lat2, lon2 = pos[v][1], pos[v][0]
            spd = data.get('current_speed_kmh', 30.0)
            
            # Color code polyline
            if (u, v) in sim.active_incidents:
                color = '#ef4444' # Red incident
                weight = 5
            elif spd < 15:
                color = '#f97316' # Orange heavy traffic
                weight = 3
            elif spd < 30:
                color = '#eab308' # Yellow moderate
                weight = 2
            else:
                color = '#22c55e' # Green free flow
                weight = 2

            popup_text = f"Edge: ({u} -> {v})<br>Speed: {spd:.1f} km/h<br>Travel Time: {data['current_travel_time']:.1f}s"
            folium.PolyLine(locations=[[lat1, lon1], [lat2, lon2]], color=color, weight=weight, opacity=0.8, popup=popup_text).add_to(m)

        # Mark incident nodes
        for (u, v) in sim.active_incidents.keys():
            lat, lon = (pos[u][1] + pos[v][1]) / 2, (pos[u][0] + pos[v][0]) / 2
            folium.Marker(
                location=[lat, lon],
                popup=f"Traffic Incident (Severity: {sim.active_incidents[(u, v)]['severity']}x)",
                icon=folium.Icon(color="red", icon="warning-sign")
            ).add_to(m)

        m.save(html_path)
        print(f"[Phase 1] Interactive Folium HTML map saved to: {html_path}")
    except Exception as err:
        print(f"[Phase 1] Folium HTML map export skipped/failed ({err})")

    summary = sim.get_network_summary()
    print("-" * 70)
    print("PHASE 1 SUMMARY STATISTICS:")
    print(f"  • Total Nodes:               {G.number_of_nodes()}")
    print(f"  • Total Directed Edges:       {G.number_of_edges()}")
    print(f"  • Average Network Speed:     {summary['avg_speed_kmh']:.2f} km/h")
    print(f"  • Minimum Speed (Bottleneck): {summary['min_speed_kmh']:.2f} km/h")
    print(f"  • Active Dynamic Incidents:  {summary['active_incidents_count']}")
    print("=" * 70)
    print("Phase 1 Execution Completed Successfully!")

if __name__ == "__main__":
    visualize_graph_and_traffic()
