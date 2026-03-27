import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
  timeout: 60000,
})

// Response interceptor - handle 401
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('dataai-auth')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api

// Dataset APIs
export const datasetsApi = {
  upload: (formData) => api.post('/api/datasets/upload', formData),
  list: () => api.get('/api/datasets/'),
  get: (id) => api.get(`/api/datasets/${id}`),
  stats: (id) => api.get(`/api/datasets/${id}/stats`),
  delete: (id) => api.delete(`/api/datasets/${id}`),
}

// AI APIs
export const aiApi = {
  query: (payload) => api.post('/api/ai/query', payload),
  models: () => api.get('/api/ai/models'),
}

// Dashboard APIs
export const dashboardApi = {
  get: (id) => api.get(`/api/dashboard/${id}`),
  histogram: (id, col) => api.get(`/api/dashboard/charts/${id}/histogram?column=${col}`),
  scatter: (id, x, y) => api.get(`/api/dashboard/charts/${id}/scatter?x_col=${x}&y_col=${y}`),
  correlation: (id) => api.get(`/api/dashboard/charts/${id}/correlation`),
  bar: (id, x, y) => api.get(`/api/dashboard/charts/${id}/bar?x_col=${x}&y_col=${y}`),
}

// Prediction APIs
export const predictionApi = {
  train: (payload) => api.post('/api/predict/train', payload),
  list: (datasetId) => api.get(`/api/predict/${datasetId}`),
}

// Graph APIs
export const graphApi = {
  build: (payload) => api.post('/api/graph/build', payload),
  query: (payload) => api.post('/api/graph/query', payload),
  stats: () => api.get('/api/graph/stats'),
  network: (label) => api.get(`/api/graph/network?label=${label}`),
}

// Processing APIs
export const processApi = {
  clean: (payload) => api.post('/api/process/clean', payload),
  aggregate: (id, groupBy, aggCol, func) =>
    api.get(`/api/process/aggregate/${id}?group_by=${groupBy}&agg_column=${aggCol}&agg_func=${func}`),
  correlations: (id) => api.get(`/api/process/correlations/${id}`),
}

// Simulation APIs
export const simulationApi = {
  run: (payload) => api.post('/api/simulate/', payload),
}

// Anomaly APIs
export const anomalyApi = {
  detect: (id, col, method, threshold) =>
    api.get(`/api/anomaly/${id}?column=${col}&method=${method}&threshold=${threshold}`),
}

// History APIs
export const historyApi = {
  get: (limit = 50) => api.get(`/api/history/?limit=${limit}`),
}

// Export APIs
export const exportApi = {
  excel: (id) => api.get(`/api/export/excel/${id}`, { responseType: 'blob' }),
  csv: (id) => api.get(`/api/export/csv/${id}`, { responseType: 'blob' }),
}

// Evaluation APIs
export const evalApi = {
  evaluate: (queryId) => api.post(`/api/evaluate/?query_id=${queryId}`),
  dashboard: () => api.get('/api/evaluate/dashboard'),
}

// Monitor APIs
export const monitorApi = {
  logs: () => api.get('/api/monitor/logs'),
  summary: () => api.get('/api/monitor/summary'),
}

// Admin APIs
export const adminApi = {
  users: () => api.get('/api/admin/users'),
  stats: () => api.get('/api/admin/stats'),
  deleteDataset: (id) => api.delete(`/api/admin/dataset/${id}`),
}
