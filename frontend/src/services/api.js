import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor для добавления токена к запросам
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Interceptor для обработки ошибок авторизации
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Удаляем токен и перенаправляем на логин
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

// API методы для авторизации
export const authApi = {
  login: (username, password) =>
    api.post('/api/auth/login', { username, password }),
  getCurrentUser: () => api.get('/api/auth/me'),
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
  }
};

// API методы для Kaiten
export const kaitenApi = {
  getCards: (role) => api.get(`/api/kaiten/cards?role=${role}`),
  moveCard: (cardId, targetColumn, comment) =>
    api.post(`/api/kaiten/cards/${cardId}/move`, { target_column: targetColumn, comment }),
  getCardMembers: (cardId) => api.get(`/api/kaiten/cards/${cardId}/members`),
  getCardExecutor: (cardId) => api.get(`/api/kaiten/cards/${cardId}/executor`),
};

// API методы для файлов
export const filesApi = {
  getIncomingFiles: (cardId) => api.get(`/api/files/incoming/${cardId}`),
  getOutgoingFiles: (cardId) => api.get(`/api/files/outgoing/${cardId}`),
  getAllFiles: (cardId) => api.get(`/api/files/card/${cardId}/all`),
  getViewerUrl: (fileUrl) => api.post('/api/files/viewer', { file_url: fileUrl }),
};

// API методы для журнала
export const journalApi = {
  getEntries: (params) => api.get('/api/journal/entries', { params }),
  exportToXlsx: (params) => api.get('/api/journal/export/xlsx', { params, responseType: 'blob' }),
  createEntry: (data) => api.post('/api/journal/entries', data),
  updateEntry: (id, data) => api.put(`/api/journal/entries/${id}`, data),
  deleteEntry: (id) => api.delete(`/api/journal/entries/${id}`),
  getNextNumber: () => api.get('/api/journal/next-number'),
};

// API методы для outbox (регистрация и подписание)
export const outboxApi = {
  prepareRegistration: (cardId, selectedFileName) =>
    api.post('/api/outbox/prepare-registration', {
      card_id: cardId,
      selected_file_name: selectedFileName
    }),
  uploadClientSignature: (data) =>
    api.post('/api/outbox/upload-client-signature', data),
};

export default api;
