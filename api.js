// api.js - Giao tiếp giữa Giao diện Web (UI) và MySQL Backend (NutriFitDB)
const API_BASE_URL = '/api';

const NutriFitAPI = {
  // 1. Kiểm tra kết nối SQL Server
  async checkConnection() {
    try {
      const res = await fetch(`${API_BASE_URL}/health`);
      if (!res.ok) throw new Error("HTTP error " + res.status);
      return await res.json();
    } catch (e) {
      console.warn("Không thể kết nối Backend MySQL:", e);
      return { status: "disconnected", error: e.message };
    }
  },

  // 2. Đăng nhập
  async login(email, password) {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });
      return await res.json();
    } catch (e) {
      return { success: false, message: "Lỗi kết nối máy chủ: " + e.message, isOffline: true };
    }
  },

  // 3. Đăng ký
  async register(email, password, fullname) {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, fullname })
      });
      return await res.json();
    } catch (e) {
      return { success: false, message: "Lỗi kết nối máy chủ: " + e.message };
    }
  },

  // 4. Lưu hồ sơ thể trạng
  async saveProfile(profileData) {
    try {
      const res = await fetch(`${API_BASE_URL}/profile/save`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileData)
      });
      return await res.json();
    } catch (e) {
      return { success: false, message: "Lỗi lưu hồ sơ: " + e.message };
    }
  },

  // 5. Lấy danh sách bài tập (có sẵn + do user tạo)
  async getWorkouts(userId) {
    try {
      const url = userId ? `${API_BASE_URL}/workouts?userId=${userId}` : `${API_BASE_URL}/workouts`;
      const res = await fetch(url);
      return await res.json();
    } catch (e) {
      return { success: false, message: e.message, workouts: [] };
    }
  },

  // 5.1. Thêm hoạt động tùy chỉnh do user tự nhập (feature.txt)
  async createCustomWorkout(workoutData) {
    try {
      const res = await fetch(`${API_BASE_URL}/workouts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(workoutData)
      });
      return await res.json();
    } catch (e) {
      return { success: false, message: "Lỗi kết nối máy chủ: " + e.message };
    }
  },

  // 5.1.1. Xóa hoạt động tùy chỉnh do user tự nhập
  async deleteCustomWorkout(workoutId, userId) {
    try {
      const res = await fetch(`${API_BASE_URL}/workouts/${workoutId}?userId=${userId || 1}`, {
        method: 'DELETE'
      });
      return await res.json();
    } catch (e) {
      return { success: false, message: e.message };
    }
  },

  // 5.2. Ghi nhận buổi tập đã hoàn thành vào lịch sử
  async logWorkout(logData) {
    try {
      const res = await fetch(`${API_BASE_URL}/workouts/log`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(logData)
      });
      return await res.json();
    } catch (e) {
      return { success: false, message: "Lỗi kết nối máy chủ: " + e.message };
    }
  },

  // 5.3. Lấy lịch sử các buổi tập đã lưu
  async getWorkoutLogs(userId) {
    try {
      const res = await fetch(`${API_BASE_URL}/workouts/logs?userId=${userId || 1}`);
      return await res.json();
    } catch (e) {
      return { success: false, message: e.message, logs: [] };
    }
  },

  // 5.4. Xóa một bản ghi lịch sử tập
  async deleteWorkoutLog(logId, userId) {
    try {
      const res = await fetch(`${API_BASE_URL}/workouts/log/${logId}?userId=${userId || 1}`, {
        method: 'DELETE'
      });
      return await res.json();
    } catch (e) {
      return { success: false, message: e.message };
    }
  },

  // 5.5. Lấy dữ liệu thống kê tần suất tập luyện 7 ngày để vẽ biểu đồ trực quan (feature.txt)
  async getWorkoutStats(userId) {
    try {
      const res = await fetch(`${API_BASE_URL}/workouts/stats?userId=${userId || 1}`);
      return await res.json();
    } catch (e) {
      return { success: false, message: e.message, stats: null };
    }
  },

  // 6. Lấy thực đơn gợi ý hôm nay (trưa + tối)
  async getTodayMeals(userId) {
    try {
      const res = await fetch(`${API_BASE_URL}/meals/today?userId=${userId || 1}`);
      return await res.json();
    } catch (e) {
      return { success: false, message: e.message, todayMeals: { lunch: null, dinner: null } };
    }
  },

  // 7. Sinh gợi ý thực đơn bằng AI Gemini Flash (hoặc chuyên gia)
  async generateMeal(userId, mealType, apiKey = '', forceRefresh = false) {
    try {
      const res = await fetch(`${API_BASE_URL}/meals/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: userId || 1, mealType, apiKey, forceRefresh })
      });
      return await res.json();
    } catch (e) {
      return { success: false, message: e.message };
    }
  },

  // 8. Chọn option (1, 2, 3) hoặc NÚT THỨ 4 (Suy nghĩ / quyết định sau)
  async selectMealOption(userId, mealType, selectedOption) {
    try {
      const res = await fetch(`${API_BASE_URL}/meals/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: userId || 1, mealType, selectedOption })
      });
      return await res.json();
    } catch (e) {
      return { success: false, message: e.message };
    }
  },

  // 9. Lấy lịch sử thực đơn các ngày trước
  async getMealHistory(userId) {
    try {
      const res = await fetch(`${API_BASE_URL}/meals/history?userId=${userId || 1}`);
      return await res.json();
    } catch (e) {
      return { success: false, message: e.message, history: [] };
    }
  }
};
