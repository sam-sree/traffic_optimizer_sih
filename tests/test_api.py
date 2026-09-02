from fastapi.testclient import TestClient

from backend.app.api.main import app


client = TestClient(app)


def test_root_and_graph_are_available():
    root = client.get("/")
    graph = client.get("/api/graph")

    assert root.status_code == 200
    assert root.json()["status"] == "ONLINE"
    assert graph.status_code == 200
    assert len(graph.json()["nodes"]) > 0
    assert len(graph.json()["edges"]) > 0


def test_dijkstra_solve_returns_route_payload():
    response = client.post("/api/solve", json={
        "solver_name": "Dijkstra Nearest-Neighbor",
        "num_nodes": 10,
        "num_vehicles": 3,
        "vehicle_capacity": 65.0,
        "time_of_day_hours": 8.5,
    })

    assert response.status_code == 200
    payload = response.json()
    assert payload["is_feasible"] is True
    assert len(payload["routes"]) == 3
    assert payload["total_distance_km"] > 0


def test_solve_rejects_invalid_problem_configuration():
    response = client.post("/api/solve", json={"num_nodes": 0, "num_vehicles": 0})

    assert response.status_code == 422
    assert {error["loc"][-1] for error in response.json()["detail"]} == {"num_nodes", "num_vehicles"}


def test_solve_rejects_unknown_solver():
    response = client.post("/api/solve", json={"solver_name": "not-a-solver"})

    assert response.status_code == 422
    assert "Unsupported solver_name" in response.json()["detail"]


def test_incident_validation_and_clear():
    incomplete = client.post("/api/incidents/inject", json={"u": 1})
    unknown_edge = client.post("/api/incidents/inject", json={"u": -1, "v": -2})
    cleared = client.post("/api/incidents/clear")

    assert incomplete.status_code == 422
    assert unknown_edge.status_code == 422
    assert cleared.status_code == 200
    assert cleared.json()["active_incidents"] == 0
