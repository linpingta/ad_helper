import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

// Response interceptor
api.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

// Dataset APIs
export const datasetAPI = {
  upload: (formData) => api.post('/dataset/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
  list: () => api.get('/dataset/list'),
  get: (id) => api.get(`/dataset/${id}`),
  clean: (id) => api.post('/dataset/clean', { dataset_id: id }),
  split: (id, splitRatio) => api.post('/dataset/split', { dataset_id: id, split_ratio: splitRatio }),
  delete: (id) => api.delete(`/dataset/${id}`)
}

// LoRA APIs
export const loraAPI = {
  train: (config) => api.post('/lora/train', config),
  status: () => api.get('/lora/status'),
  stop: () => api.post('/lora/stop'),
  list: () => api.get('/lora/models'),
  get: (id) => api.get(`/lora/${id}`),
  delete: (id) => api.delete(`/lora/${id}`)
}

// Generate APIs
export const generateAPI = {
  single: (data) => api.post('/generate/text', data),
  batch: (data) => api.post('/generate/batch', data),
  history: (params) => api.get('/generate/history', { params }),
  evaluate: (ids) => api.post('/generate/evaluate', ids),
  stats: () => api.get('/generate/stats')
}

// System APIs
export const systemAPI = {
  login: (credentials) => api.post('/system/login', credentials),
  logout: () => api.post('/system/logout'),
  me: () => api.get('/system/me'),
  hardware: () => api.get('/system/hardware'),
  logs: (params) => api.get('/system/logs', { params })
}

export default api
