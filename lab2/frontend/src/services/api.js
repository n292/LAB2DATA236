import axios from "axios";

const API_BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000/api";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const requestUrl = error?.config?.url || "";

    const isAuthRoute =
      requestUrl.includes("/auth/login") || requestUrl.includes("/auth/signup");

    if (status === 401 && !isAuthRoute) {
      localStorage.removeItem("access_token");
      localStorage.removeItem("user_id");
      localStorage.removeItem("user_role");
      window.dispatchEvent(new Event("authChanged"));
      window.location.href = "/login";
    }

    return Promise.reject(error);
  }
);

// Auth APIs
export const authAPI = {
  signup: (name, email, password, role = "user") =>
    apiClient.post("/auth/signup", { name, email, password, role }),

  login: (email, password) =>
    apiClient.post("/auth/login", { email, password }),
};

// Users APIs
export const usersAPI = {
  getProfile: (userId) =>
    apiClient.get(`/users/${userId}`),

  updateProfile: (userId, data) =>
    apiClient.put(`/users/${userId}`, data),

  getPreferences: (userId) =>
    apiClient.get(`/users/${userId}/preferences`),

  setPreferences: (userId, preferences) =>
    apiClient.post(`/users/${userId}/preferences`, preferences),
};

// Restaurants APIs
export const restaurantsAPI = {
  search: (params) =>
    apiClient.get("/restaurants/", { params }),

  getDetails: (restaurantId) =>
    apiClient.get(`/restaurants/${restaurantId}`),

  getByUser: (userId, params) =>
    apiClient.get(`/restaurants/user/${userId}`, { params }),

  create: (data) =>
    apiClient.post("/restaurants/", data),

  update: (restaurantId, data) =>
    apiClient.put(`/restaurants/${restaurantId}`, data),

  delete: (restaurantId) =>
    apiClient.delete(`/restaurants/${restaurantId}`),

  getOwnerDashboard: () =>
    apiClient.get("/restaurants/owner/dashboard"),

  claim: (restaurantId) =>
    apiClient.post(`/restaurants/${restaurantId}/claim`),

  unclaim: (restaurantId) =>
    apiClient.post(`/restaurants/${restaurantId}/unclaim`),
};

// Reviews APIs
export const reviewsAPI = {
  getByRestaurant: (restaurantId, params) =>
    apiClient.get(`/reviews/restaurant/${restaurantId}`, { params }),

  getByUser: (userId, params) =>
    apiClient.get(`/reviews/user/${userId}`, { params }),

  create: (restaurantId, userId, data) =>
    apiClient.post(`/reviews/restaurant/${restaurantId}`, data, {
      params: { user_id: userId },
    }),

  update: (reviewId, data) =>
    apiClient.put(`/reviews/${reviewId}`, data),

  delete: (reviewId) =>
    apiClient.delete(`/reviews/${reviewId}`),
};

// Favorites APIs
export const favoritesAPI = {
  getByUser: (userId, params) =>
    apiClient.get(`/favorites/user/${userId}`, { params }),

  add: (restaurantId, userId) =>
    apiClient.post("/favorites/", { restaurant_id: restaurantId }, {
      params: { user_id: userId },
    }),

  remove: (favoriteId) =>
    apiClient.delete(`/favorites/${favoriteId}`),

  check: (userId, restaurantId) =>
    apiClient.get(`/favorites/check/${userId}/${restaurantId}`),
};

// AI Assistant APIs
export const aiAssistantAPI = {
  chat: (message, conversationHistory = null, userId) =>
    apiClient.post(
      "/ai-assistant/chat",
      { message, conversation_history: conversationHistory },
      { params: { user_id: userId } }
    ),
};

export default apiClient;