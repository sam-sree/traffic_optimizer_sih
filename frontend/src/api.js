import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api';

const requestConfig = { headers: { 'Content-Type': 'application/json' } };

export const fetchGraphData = async () => {
  const res = await axios.get(`${API_BASE}/graph`);
  return res.data;
};

export const runSolve = async (payload) => {
  const res = await axios.post(`${API_BASE}/solve`, {
    ...payload,
    solver_name: payload.algorithm,
    num_vehicles: Number(payload.fleet_size),
    vehicle_capacity: Number(payload.vehicle_capacity),
    time_of_day_hours: 8.5,
    objective_weights: {
      time: Number(payload.priority_weight),
      distance: Number(payload.distance_sensitivity),
      congestion: 0.2,
      emissions: 0.1
    }
  }, requestConfig);
  return res.data;
};

export const runSolveFromCsv = async (file, { solverName, numVehicles, vehicleCapacity, depotLat, depotLon }) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('solver_name', solverName);
  formData.append('num_vehicles', numVehicles);
  formData.append('vehicle_capacity', vehicleCapacity);
  formData.append('depot_latitude', depotLat);
  formData.append('depot_longitude', depotLon);
  const res = await axios.post(`${API_BASE}/solve_csv`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return res.data;
};

export const runReoptimize = async (payload) => {
  const res = await axios.post(`${API_BASE}/reoptimize`, payload);
  return res.data;
};

export const fetchParetoFront = async () => {
  const res = await axios.get(`${API_BASE}/pareto`);
  return res.data;
};

export const fetchBenchmarkResults = async () => {
  const res = await axios.get(`${API_BASE}/benchmarks`);
  return res.data;
};

export const injectTrafficIncident = async (payload) => {
  const res = await axios.post(`${API_BASE}/incidents/inject`, payload);
  return res.data;
};

export const clearTrafficIncidents = async () => {
  const res = await axios.post(`${API_BASE}/incidents/clear`);
  return res.data;
};
