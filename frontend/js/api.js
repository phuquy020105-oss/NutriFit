// Profile routes are outside /api; all authenticated requests use the same cookie.
const API_BASE_URL = 'http://127.0.0.1:5000';
async function request(endpoint, options = {}) {
  try {
    const response = await fetch(API_BASE_URL + endpoint, {
      ...options, credentials: options.credentials || 'include',
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }
    });
    const data = await response.json().catch(() => ({}));
    const result = { ...data, ok: response.ok, httpStatus: response.status };
    if (response.status === 401 && endpoint.startsWith('/api/') && !endpoint.startsWith('/api/auth/')) {
      document.dispatchEvent(new Event('nutrifit:session-expired'));
    }
    return result;
  } catch (_) {
    return { ok: false, success: false, httpStatus: 0, isOffline: true,
      message: 'Không thể kết nối Backend tại 127.0.0.1:5000.' };
  }
}
const post = (endpoint, data = {}) => request(endpoint, { method: 'POST', body: JSON.stringify(data) });
const NutriFitAPI = {
  checkConnection: () => request('/api/health', { credentials: 'omit' }),
  register: (email, password, fullName) => post('/api/auth/register', { email, password, full_name: fullName }),
  login: (email, password) => post('/api/auth/login', { email, password }),
  saveProfile(profile) {
    return post('/save', {
      user_id: profile.user_id ?? profile.userId,
      gender: profile.gender, age: profile.age, height: profile.height, weight: profile.weight,
      activity_level: profile.activity_level ?? profile.activity, goal: profile.goal
    });
  },
  getProfile: userId => request('/' + encodeURIComponent(userId)),
  calculateNutrition: profile => post('/api/nutrition/calculate', profile),
  getNutrition: userId => request('/api/nutrition/me' + (userId ? '?userId=' + encodeURIComponent(userId) : '')),
  getNutritionSummary: () => request('/api/nutrition/summary'),
  logout: () => post('/api/nutrition/logout'),
  getTodayMeals: () => request('/api/meals/today'),
  generateMeal: (mealType, forceRefresh = false, revision = null, preferences = {}) => post('/api/meals/generate', {
    mealType, forceRefresh, ...(revision ? { revision } : {}), preferences
  }),
  replaceMeal: (mealType, revision, requestText, preferences = {}) => post('/api/meals/replace', {
    mealType, revision, request: requestText, preferences
  }),
  selectMealOption: (mealType, selectedOption, revision) => post('/api/meals/select', { mealType, selectedOption, revision }),
  getMealHistory: (page = 1) => request('/api/meals/history?page=' + page + '&limit=20')
};
window.NutriFitAPI = NutriFitAPI;
