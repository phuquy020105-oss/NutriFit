// localStorage keeps display information; the backend cookie proves identity.
(function () {
  const SESSION_KEY = 'nutrifit_session_user';
  function normalizeUser(user) {
    if (!user || !Number.isInteger(user.id) || user.id <= 0) return null;
    return { id: user.id, email: user.email || '', fullname: user.full_name || user.fullname || 'Thành viên NutriFit' };
  }
  function normalizeProfile(p) {
    if (!p) return null;
    return {
      Gender: p.gender, Age: p.age, HeightCm: p.height, WeightKg: p.weight,
      Goal: p.goal, ActivityLevel: p.activity_level, Bmr: p.bmr, Tdee: p.tdee,
      TargetKcal: p.target_kcal, TargetWaterMl: p.target_water_ml, Bmi: p.bmi,
      TargetCarbs: p.target_carbs, TargetProtein: p.target_protein,
      TargetFat: p.target_fat, TargetFiber: p.target_fiber
    };
  }
  async function loadProfile(userId) {
    const result = await NutriFitAPI.getNutrition(userId);
    if (!result.success) return null;
    const core = await NutriFitAPI.getProfile(userId);
    return core.success ? normalizeProfile({ ...core.data, ...result.data }) : null;
  }
  async function authenticate(action, ...args) {
    const result = await NutriFitAPI[action](...args);
    if (!result.success) return result;
    const user = normalizeUser(result.user);
    if (!user) return { success: false, message: 'Backend trả về tài khoản không hợp lệ.' };
    const nutrition = await NutriFitAPI.getNutrition(user.id);
    if (!nutrition.success && nutrition.code !== 'PROFILE_REQUIRED') return { ...nutrition, success: false };
    const profile = nutrition.success ? await loadProfile(user.id) : null;
    if (nutrition.success && !profile) return { success: false, message: 'Đăng nhập thành công nhưng chưa tải được hồ sơ. Hãy thử lại.' };
    return { ...result, user, profile };
  }
  function saveSession(user, profile = null) {
    const normalized = normalizeUser(user);
    if (normalized) localStorage.setItem(SESSION_KEY, JSON.stringify({ user: normalized, profile }));
  }
  function clearSession() { localStorage.removeItem(SESSION_KEY); }
  function getSession() {
    try { return JSON.parse(localStorage.getItem(SESSION_KEY)); }
    catch (_) { clearSession(); return null; }
  }
  window.NutriFitAuth = {
    login: (...args) => authenticate('login', ...args), register: (...args) => authenticate('register', ...args),
    loadProfile, normalizeUser, normalizeProfile, saveSession, getSession, clearSession
  };
})();
