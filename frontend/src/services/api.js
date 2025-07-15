import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API functions

// Upload
export const uploadCSV = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  
  const response = await api.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  
  return response.data;
};

export const getSupportedFormats = async () => {
  const response = await api.get('/api/upload/formats');
  return response.data;
};

// Accounts
export const getAccounts = async (params = {}) => {
  const response = await api.get('/api/accounts', { params });
  return response.data;
};

export const getAccount = async (id) => {
  const response = await api.get(`/api/accounts/${id}`);
  return response.data;
};

export const updateAccount = async (id, data) => {
  const response = await api.put(`/api/accounts/${id}`, data);
  return response.data;
};

export const deleteAccount = async (id) => {
  const response = await api.delete(`/api/accounts/${id}`);
  return response.data;
};

export const bulkSelectAccounts = async (accountIds, action) => {
  const response = await api.post('/api/accounts/bulk-select', {
    account_ids: accountIds,
    action,
  });
  return response.data;
};

export const getAccountsSummary = async () => {
  const response = await api.get('/api/accounts/summary');
  return response.data;
};

// Deletion
export const startDeletion = async (accountIds) => {
  const response = await api.post('/api/deletion/start', {
    account_ids: accountIds,
  });
  return response.data;
};

export const getDeletionStatus = async (taskId) => {
  const response = await api.get(`/api/deletion/status/${taskId}`);
  return response.data;
};

export const confirmDeletion = async (taskId) => {
  const response = await api.post(`/api/deletion/confirm/${taskId}`);
  return response.data;
};

export const sendEmailDeletion = async (accountId) => {
  const response = await api.post(`/api/deletion/email/${accountId}`);
  return response.data;
};

export const getDeletionTasks = async (params = {}) => {
  const response = await api.get('/api/deletion/tasks', { params });
  return response.data;
};

// Audit
export const getAuditLogs = async (params = {}) => {
  const response = await api.get('/api/audit', { params });
  return response.data;
};

export const revealCredentials = async (logId) => {
  const response = await api.get(`/api/audit/${logId}/reveal`);
  return response.data;
};

export const getAuditActions = async () => {
  const response = await api.get('/api/audit/actions');
  return response.data;
};

export const getAuditSummary = async () => {
  const response = await api.get('/api/audit/summary');
  return response.data;
};

// Stats
export const getStats = async () => {
  const response = await api.get('/api/stats');
  return response.data;
};

// Health check
export const healthCheck = async () => {
  const response = await api.get('/health');
  return response.data;
};

// Settings
export const getEmailSettings = async () => {
  const response = await api.get('/api/settings/email');
  return response.data;
};

export const configureEmail = async (config) => {
  const response = await api.post('/api/settings/email', config);
  return response.data;
};

export const testEmailSettings = async (config) => {
  const response = await api.post('/api/settings/email/test', config);
  return response.data;
};

export const getSupportedEmailProviders = async () => {
  const response = await api.get('/api/settings/email/providers');
  return response.data;
};

export const deleteEmailSettings = async () => {
  const response = await api.delete('/api/settings/email');
  return response.data;
};

export default api;