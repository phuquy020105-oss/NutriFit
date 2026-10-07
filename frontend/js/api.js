// frontend/js/api.js
// Lớp trung gian giao tiếp giữa Frontend và Flask Backend.

const API_BASE_URL = 'http://127.0.0.1:5000/api';

async function request(endpoint, options = {}) {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      ...options
    });

    const data = await response.json().catch(() => ({}));

    return {
      ok: response.ok,
      status: response.status,
      ...data
    };
  } catch (error) {
    console.error(`API Error [${endpoint}]`, error);

    return {
      ok: false,
      success: false,
      message: 'Không thể kết nối tới Backend.',
      error: error.message,
      isOffline: true
    };
  }
}

const NutriFitAPI = {
  // =========================
  // SYSTEM
  // =========================

  async checkConnection() {
    return request('/health', {
      method: 'GET',
      headers: {}
    });
  },

  // =========================
  // AUTH
  // =========================

  async register(email, password, fullName) {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password,
        full_name: fullName
      })
    });
  },

  async login(email, password) {
    return request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        email,
        password
      })
    });
  },

  // =========================
  // PROFILE
  // =========================

  async saveProfile(profileData) {
    return request('/profile/save', {
      method: 'POST',
      body: JSON.stringify(profileData)
    });
  },

  async getProfile(userId) {
    return request(`/profile/${userId}`, {
      method: 'GET',
      headers: {}
    });
  },

  // =========================
  // WORKOUT
  // Giữ lại API cũ để sẵn sàng
  // tích hợp khi TV4 bàn giao Backend.
  // =========================

  async getWorkouts(userId) {
    const query = userId
      ? `?userId=${encodeURIComponent(userId)}`
      : '';

    return request(`/workouts${query}`, {
      method: 'GET',
      headers: {}
    });
  },

  async createCustomWorkout(workoutData) {
    return request('/workouts', {
      method: 'POST',
      body: JSON.stringify(workoutData)
    });
  },

  async deleteCustomWorkout(workoutId, userId) {
    const query = userId
      ? `?userId=${encodeURIComponent(userId)}`
      : '';

    return request(`/workouts/${workoutId}${query}`, {
      method: 'DELETE',
      headers: {}
    });
  },

  async logWorkout(logData) {
    return request('/workouts/log', {
      method: 'POST',
      body: JSON.stringify(logData)
    });
  },

  async getWorkoutLogs(userId) {
    const query = userId
      ? `?userId=${encodeURIComponent(userId)}`
      : '';

    return request(`/workouts/logs${query}`, {
      method: 'GET',
      headers: {}
    });
  },

  async deleteWorkoutLog(logId, userId) {
    const query = userId
      ? `?userId=${encodeURIComponent(userId)}`
      : '';

    return request(`/workouts/log/${logId}${query}`, {
      method: 'DELETE',
      headers: {}
    });
  },

  async getWorkoutStats(userId) {
    const query = userId
      ? `?userId=${encodeURIComponent(userId)}`
      : '';

    return request(`/workouts/stats${query}`, {
      method: 'GET',
      headers: {}
    });
  },

  // =========================
  // MEALS
  // Giữ lại API cũ để sẵn sàng
  // tích hợp khi TV3 bàn giao Backend.
  // =========================

  async getTodayMeals(userId) {
    const query = userId
      ? `?userId=${encodeURIComponent(userId)}`
      : '';

    return request(`/meals/today${query}`, {
      method: 'GET',
      headers: {}
    });
  },

  async generateMeal(userId, mealType, apiKey = '', forceRefresh = false) {
    return request('/meals/generate', {
      method: 'POST',
      body: JSON.stringify({
        userId,
        mealType,
        apiKey,
        forceRefresh
      })
    });
  },

  async selectMealOption(userId, mealType, selectedOption) {
    return request('/meals/select', {
      method: 'POST',
      body: JSON.stringify({
        userId,
        mealType,
        selectedOption
      })
    });
  },

  async getMealHistory(userId) {
    const query = userId
      ? `?userId=${encodeURIComponent(userId)}`
      : '';

    return request(`/meals/history${query}`, {
      method: 'GET',
      headers: {}
    });
  }
};

window.NutriFitAPI = NutriFitAPI;