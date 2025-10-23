import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add token to requests if available
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Auth API
export const authAPI = {
  register: async (data: { email: string; username: string; password: string }) => {
    const response = await api.post('/auth/register', data);
    return response.data;
  },

  login: async (email: string, password: string) => {
    const formData = new FormData();
    formData.append('username', email); // OAuth2 uses 'username' field
    formData.append('password', password);

    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
    }

    return response.data;
  },

  logout: () => {
    localStorage.removeItem('access_token');
  },

  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// Games API
export const gamesAPI = {
  getGames: async (skip = 0, limit = 100) => {
    const response = await api.get(`/games?skip=${skip}&limit=${limit}`);
    return response.data;
  },

  getGame: async (gameId: number) => {
    const response = await api.get(`/games/${gameId}`);
    return response.data;
  },

  importGames: async (platform: string, username: string, maxGames = 100) => {
    const response = await api.post('/games/import', {
      platform,
      username,
      max_games: maxGames,
    });
    return response.data;
  },

  connectPlatform: async (platform: string, username: string, token?: string) => {
    const response = await api.post('/games/connect-platform', {
      platform,
      username,
      token,
    });
    return response.data;
  },
};

export default api;
