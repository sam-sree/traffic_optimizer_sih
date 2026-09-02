import axios from 'axios';

const API_BASE = 'http://127.0.0.1:8000/api';

export const fetchGraphData = async () => {
  const res = await axios.get(`${API_BASE}/graph`);
  return res.data;
};

export const runSolve = async (payload) => {
  const res = await axios.post(`${API_BASE}/solve`, payload);
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
