import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'multipart/form-data',
  },
});

export const checkHealth = async () => {
  const response = await apiClient.get('/api/health');
  return response.data;
};

export const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/api/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const analyzeImage = async (imageId) => {
  const response = await apiClient.post(`/api/analyze/${imageId}`);
  return response.data;
};

export const trainModel = async (epochs = 5) => {
  const response = await apiClient.post(`/api/train?epochs=${epochs}`);
  return response.data;
};

export const getResults = async (imageId) => {
  const response = await apiClient.get(`/api/results/${imageId}`);
  return response.data;
};

export const getGeoJsonUrl = (imageId) => {
  return `${API_BASE_URL}/api/geojson/${imageId}`;
};

export const getImageUrl = (pathOrUrl) => {
  if (!pathOrUrl) return '';
  if (pathOrUrl.startsWith('http')) return pathOrUrl;
  return `${API_BASE_URL}${pathOrUrl}`;
};
