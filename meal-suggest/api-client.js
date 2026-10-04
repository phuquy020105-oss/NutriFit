// meal-suggest/api-client.js — Client riêng của module gợi ý thực đơn.
// Không phụ thuộc ../api.js để module chạy độc lập hoàn toàn.
// Chỉ gọi đúng 4 endpoint backend đã có: today / generate / select / history.

const MealSuggestAPI = (() => {
  const BASE = '/api';

  async function safeFetch(url, options) {
    try {
      const res = await fetch(url, options);
      return await res.json();
    } catch (e) {
      return { success: false, message: 'Lỗi kết nối máy chủ: ' + e.message };
    }
  }

  return {
    getTodayMeals(userId) {
      return safeFetch(`${BASE}/meals/today?userId=${userId || 1}`)
        .then((r) => {
          if (!r.todayMeals) r.todayMeals = { lunch: null, dinner: null };
          return r;
        });
    },
    generateMeal(userId, mealType, apiKey = '', forceRefresh = false) {
      return safeFetch(`${BASE}/meals/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: userId || 1, mealType, apiKey, forceRefresh })
      });
    },
    selectMealOption(userId, mealType, selectedOption) {
      return safeFetch(`${BASE}/meals/select`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ userId: userId || 1, mealType, selectedOption })
      });
    },
    getMealHistory(userId) {
      return safeFetch(`${BASE}/meals/history?userId=${userId || 1}`)
        .then((r) => {
          if (!r.history) r.history = [];
          return r;
        });
    }
  };
})();
