import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// API методы для Kaiten
export const kaitenApi = {
  getCards: (role) => api.get(`/api/kaiten/cards?role=${role}`),
  moveCard: (cardId, targetColumn, comment) =>
    api.post(`/api/kaiten/cards/${cardId}/move`, { target_column: targetColumn, comment }),
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
  getNextNumber: () => api.get('/api/journal/next-number'),
};

export default api;
