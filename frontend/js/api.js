// NutriFit API client: giữ contract Auth/Profile/Nutrition, bổ sung contract TV4.
const API_BASE_URL = String(window.NUTRIFIT_API_BASE_URL || 'http://127.0.0.1:5000').replace(/\/+$/, '');

async function request(endpoint, options = {}) {
  try {
    const fetchOptions = {
      ...options,
      credentials: options.credentials ?? 'include',
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      }
    };
    const response = await fetch(`${API_BASE_URL}${endpoint}`, fetchOptions);
    const data = await response.json().catch(() => ({}));
    const result = { ...data, ok: response.ok, httpStatus: response.status };

    if (response.status === 401 && endpoint.startsWith('/api/') && !endpoint.startsWith('/api/auth/')) {
      document.dispatchEvent(new Event('nutrifit:session-expired'));
    }
    return result;
  } catch (error) {
    console.error(`API Error [${endpoint}]`, error);
    return {
      ok: false,
      success: false,
      httpStatus: 0,
      isOffline: true,
      message: 'Không thể kết nối Backend tại 127.0.0.1:5000.',
      error: error?.message || String(error)
    };
  }
}

const get = (endpoint, options = {}) => request(endpoint, { ...options, method: 'GET' });
const post = (endpoint, data = {}, options = {}) => request(endpoint, {
  ...options,
  method: 'POST',
  body: JSON.stringify(data)
});
const queryString = values => {
  const params = new URLSearchParams();
  Object.entries(values || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') params.set(key, String(value));
  });
  const text = params.toString();
  return text ? `?${text}` : '';
};

const NutriFitAPI = {
  // SYSTEM
  checkConnection: () => get('/api/health', { credentials: 'omit' }),

  // AUTH / PROFILE (giữ nguyên route contract hiện tại của core)
  register: (email, password, fullName) => post('/api/auth/register', { email, password, full_name: fullName }),
  login: (email, password) => post('/api/auth/login', { email, password }),
  saveProfile(profile) {
    return post('/save', {
      user_id: profile.user_id ?? profile.userId,
      gender: profile.gender,
      age: profile.age,
      height: profile.height,
      weight: profile.weight,
      activity_level: profile.activity_level ?? profile.activity,
      goal: profile.goal
    });
  },
  getProfile: userId => get('/' + encodeURIComponent(userId)),

  // NUTRITION / MEALS V3-V4
  calculateNutrition: profile => post('/api/nutrition/calculate', profile),
  getNutrition: userId => get('/api/nutrition/me' + queryString(userId ? { userId } : {})),
  getNutritionSummary: () => get('/api/nutrition/summary'),
  logout: () => post('/api/nutrition/logout'),
  getTodayMeals: () => get('/api/meals/today'),
  generateMeal: (mealType, forceRefresh = false, revision = null, preferences = {}, settings = {}) => post('/api/meals/generate', {
    mealType, forceRefresh, ...(revision ? { revision } : {}), preferences, ...settings, plannerVersion: 'v4'
  }),
  replaceMeal: (mealType, revision, requestText, preferences = {}, settings = {}) => post('/api/meals/replace', {
    mealType, revision, request: requestText, preferences, ...settings, plannerVersion: 'v4'
  }),
  selectMealOption: (mealType, selectedOption, revision) => post('/api/meals/select', { mealType, selectedOption, revision }),
  getMealHistory: (page = 1) => get(`/api/meals/history?page=${encodeURIComponent(page)}&limit=20`),
  getFoodCatalog: () => get('/api/nutrition/catalog'),
  getDailyIntake: date => get('/api/nutrition/daily' + queryString(date ? { date } : {})),
  componentSuggestions: data => post('/api/meals/component-suggestions', data),
  replaceComponent: data => post('/api/meals/replace-component', data),
  addIntake: data => post('/api/nutrition/intake', data),
  updateIntake: (id, data) => post(`/api/nutrition/intake/${encodeURIComponent(id)}/update`, data),
  deleteIntake: (id, version) => post(`/api/nutrition/intake/${encodeURIComponent(id)}/delete`, { version }),

  // PREMIUM QUICK FOOD: search -> select -> preview -> confirm.
  searchQuickFood: (query, limit = 10) => get('/api/nutrition/quick-food/search' + queryString({ q: query, limit })),
  previewQuickFood: (dishId, grams) => post('/api/nutrition/quick-food/preview', { dish_id: dishId, grams }),
  confirmQuickFood: payload => post('/api/nutrition/quick-food/confirm', payload),

  // WORKOUTS / PROGRESS: map the TV4 API shape to the existing UI model.
  async getWorkouts(userId) {
    const result = await get('/api/workouts/catalog' + queryString(userId ? { user_id: userId } : {}));
    if (!result.success) return { ...result, workouts: [] };
    const groups = Array.isArray(result.data) ? result.data : [];
    const workouts = groups.flatMap(group => (group.workouts || []).map(workout => ({
      id: workout.id,
      name: workout.name,
      category: group.name || 'Vận động',
      categoryId: group.category_id,
      durationMinutes: Number(workout.duration_minutes) || 0,
      caloriesBurned: Number(workout.calories_burned) || 0,
      isCustom: Boolean(workout.is_custom)
    })));
    return { ...result, groups, workouts };
  },
  getWorkoutCategories: () => get('/api/workouts/categories'),
  createCustomWorkout(workoutData) {
    const categoryRaw = workoutData.category_id ?? workoutData.categoryId ?? workoutData.category;
    const categoryId = categoryRaw !== '' && categoryRaw !== undefined && categoryRaw !== null && Number.isFinite(Number(categoryRaw))
      ? Number(categoryRaw) : null;
    return post('/api/workouts/custom', {
      user_id: workoutData.user_id ?? workoutData.userId,
      name: workoutData.name,
      duration_minutes: workoutData.duration_minutes ?? workoutData.durationMinutes,
      calories_burned: workoutData.calories_burned ?? workoutData.caloriesBurned,
      ...(categoryId ? { category_id: categoryId } : {}),
      ...(workoutData.met ? { met: workoutData.met } : {})
    });
  },
  deleteCustomWorkout: (workoutId, userId) => request('/api/workouts/custom/' + encodeURIComponent(workoutId) + queryString({ user_id: userId }), { method: 'DELETE' }),
  logWorkout(logData) {
    return post('/api/workouts/log', {
      user_id: logData.user_id ?? logData.userId,
      workout_id: logData.workout_id ?? logData.workoutId,
      duration_minutes: logData.duration_minutes ?? logData.durationMinutes,
      ...(logData.date || logData.loggedDate ? { date: logData.date || logData.loggedDate } : {})
    });
  },
  async getWorkoutLogs(userId) {
    const result = await get('/api/workouts/logs' + queryString({ user_id: userId }));
    if (!result.success) return { ...result, logs: [] };
    const rows = Array.isArray(result.data) ? result.data : [];
    const logs = rows.map(row => ({
      logId: row.log_id,
      workoutId: row.workout_id,
      workoutName: row.workout_name,
      date: row.date,
      durationMinutes: row.duration_minutes,
      caloriesBurned: row.calories_burned,
      isCustom: Boolean(row.is_custom)
    }));
    return { ...result, logs };
  },
  deleteWorkoutLog: (logId, userId) => request('/api/workouts/log/' + encodeURIComponent(logId) + queryString({ user_id: userId }), { method: 'DELETE' }),
  async getWorkoutStats(userId) {
    if (!userId) return { success: false, stats: null, message: 'Thiếu thông tin tài khoản.' };
    const result = await get('/api/progress/weekly/' + encodeURIComponent(userId));
    if (!result.success || !result.data) return { ...result, stats: null };
    const data = result.data;
    const totals = data.totals || {};
    return {
      ...result,
      stats: {
        from: data.from,
        to: data.to,
        days: (data.days || []).map(day => ({
          date: day.date,
          label: day.label,
          duration: Number(day.minutes) || 0,
          calories: Number(day.calories) || 0,
          count: Number(day.sessions) || 0
        })),
        summary: {
          totalSessions: Number(totals.sessions) || 0,
          totalMinutes: Number(totals.minutes) || 0,
          totalCalories: Number(totals.calories) || 0,
          activeDays: Number(totals.active_days) || 0
        },
        goal: data.goal || {}
      }
    };
  },

  // STREET FOOD catalog / recommendation
  getStreetFood: filters => get('/api/street-food' + queryString({
    meal_type: filters?.meal_type ?? filters?.mealType ?? 'all',
    max_price: filters?.max_price ?? filters?.maxPrice,
    max_kcal: filters?.max_kcal ?? filters?.maxKcal,
    q: filters?.q ?? filters?.query
  })),
  recommendStreetFood: options => post('/api/street-food/recommend', {
    budget: options?.budget,
    max_kcal: options?.max_kcal ?? options?.maxKcal,
    meal_type: options?.meal_type ?? options?.mealType ?? 'all',
    limit: options?.limit ?? 6
  })
};

window.NutriFitAPI = NutriFitAPI;
