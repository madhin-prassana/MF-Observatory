import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Funds
export const getAllFunds = (params = {}) => {
  return api.get('/funds/', { params });
};

export const getFundByCode = (schemeCode) => {
  return api.get(`/funds/${schemeCode}`);
};

export const compareFunds = (schemeCodes) => {
  return api.post('/funds/compare', schemeCodes);
};

export const getFundStats = () => {
  return api.get('/funds/stats/summary');
};

// Predictions
export const getPredictions = (schemeCode) => {
  return api.get(`/predictions/${schemeCode}`);
};

export const getHistoricalNav = (schemeCode) => {
  return api.get(`/predictions/${schemeCode}/historical`);
};

export const getModelComparison = () => {
  return api.get('/predictions/stats/comparison');
};

// Clusters
export const getAllClusters = () => {
  return api.get('/clusters/');
};

export const getClusterFunds = (clusterId) => {
  return api.get(`/clusters/${clusterId}`);
};

// Anomalies
export const getAllAnomalies = () => {
  return api.get('/anomalies/');
};

export const getFundAnomalyStatus = (schemeCode) => {
  return api.get(`/anomalies/${schemeCode}`);
};

export default api;