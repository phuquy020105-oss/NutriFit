// NutriFit Frontend
// Extracted from the existing UI logic; behavior preserved.

    window.lucide = window.lucide || { createIcons() {} };
    let currentStep = 1;
    let currentWater = 0;
    let isEditingProfile = false;
    let currentAuthMode = 'login';
    let isDbConnected = false;
    let userProfile = {
      id: null,
      fullname: "Thành viên NutriFit",
      email: "",
      gender: "male",
      age: 24,
      height: 172,
      weight: 68,
      activity: 1.2,
      goal: "lose",
      targetKcal: 0,
      bmr: 0,
      tdee: 0,
      bmi: 23.0,
      carbs: 0,
      protein: 0,
      fat: 0,
      fiber: 30,
      waterTarget: 2400
    };

    // Cập nhật ngày tháng năm thực tế hiện tại
    function updateRealTimeDate() {
      const now = new Date();
      const weekdays = ['Chủ Nhật', 'Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu', 'Thứ Bảy'];
      const dayName = weekdays[now.getDay()];
      const day = now.getDate();
      const month = now.getMonth() + 1;
      const year = now.getFullYear();

      const realDateSpan = document.getElementById('dash-real-date');
      const fullDateSpan = document.getElementById('dash-current-full-date');

      if (realDateSpan) {
        realDateSpan.innerText = `Hôm nay, ${dayName} ngày ${day} Tháng ${month} • Hãy theo dõi dinh dưỡng và vận động đầy đủ nhé!`;
      }
      if (fullDateSpan) {
        fullDateSpan.innerText = `${dayName}, ${day}/${month}/${year}`;
      }
    }

    // Quản lý phiên đăng nhập (Tránh bị bắt đăng nhập lại khi F5)
    function saveSession(user, profile) {
      NutriFitAuth.saveSession(user, profile);
    }

    function clearUserState() {
      NutriFitAuth.clearSession();
      Object.assign(userProfile, {
        id: null, fullname: 'Thành viên NutriFit', email: '',
        gender: 'male', age: 24, height: 172, weight: 68, activity: 1.2, goal: 'lose',
        bmr: 0, tdee: 0, targetKcal: 0, carbs: 0, protein: 0, fat: 0, fiber: 0, bmi: 0, waterTarget: 0
      });
      document.getElementById('inp-height').value = 172;
      document.getElementById('inp-weight').value = 68;
      document.getElementById('inp-age-range').value = 24;
      document.getElementById('age-val').innerText = '24 tuổi';
      document.querySelectorAll('input[name="goal"]').forEach(el => { el.checked = el.value === 'lose'; });
      document.querySelectorAll('input[name="act"]').forEach(el => { el.checked = el.value === '1.2'; });
      todayMealsCache = { breakfast: null, lunch: null, dinner: null };
      mealPreferences = { breakfast: {}, lunch: {}, dinner: {} };
      mealTargets = {};
      renderMealPreferences();
      document.getElementById('meal-replace-request').value = '';
      currentWater = 0;
      if (typeof clearV4State === 'function') clearV4State();
    }

    async function checkAutoLogin() {
      const cached = NutriFitAuth.getSession();
      const user = NutriFitAuth.normalizeUser(cached?.user);
      if (!user) return false;
      const result = await NutriFitAPI.getNutrition(user.id);
      if (result.isOffline) {
        showAuthAlert(result.message);
        return false;
      }
      if (!result.success && result.code !== 'PROFILE_REQUIRED') {
        clearUserState();
        return false;
      }
      Object.assign(userProfile, user);
      if (result.success) {
        const profile = NutriFitAuth.normalizeProfile(result.data);
        saveSession(user, profile);
        applyLoadedProfile(profile);
        switchScreen('screen-dashboard');
      } else {
        saveSession(user, null);
        isEditingProfile = false;
        currentStep = 1;
        updateStepUI();
        switchScreen('screen-onboarding');
      }
      return true;
    }

    async function handleLogout() {
      const result = await NutriFitAPI.logout();
      if (!result.success && result.httpStatus !== 401) {
        alert(result.message || 'Chưa thể đăng xuất. Hãy thử lại.');
        return;
      }
      clearUserState();
      switchScreen('screen-auth');
    }

    document.addEventListener('nutrifit:session-expired', () => {
      clearUserState();
      switchScreen('screen-auth');
      showAuthAlert('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
    });

    // Đổi màu và gạch chân nút chức năng đầu trang khi user chọn hoặc cuộn tới
    function setActiveNav(targetId) {
      const navItems = [
        { id: 'section-profile', btn: 'nav-item-profile' },
        { id: 'section-meals', btn: 'nav-item-meals' },
        { id: 'section-single-dishes', btn: 'nav-item-single-dishes' },
        { id: 'section-workouts', btn: 'nav-item-workouts' }
      ];

      navItems.forEach(item => {
        const el = document.getElementById(item.btn);
        if (!el) return;
        if (item.id === targetId) {
          el.className = "nav-link text-brand-600 font-bold border-b-2 border-brand-500 pb-1 transition-all";
        } else {
          el.className = "nav-link text-slate-500 hover:text-slate-800 transition-colors pb-1 border-b-2 border-transparent";
        }
      });
    }

    // Tự động đổi màu nút điều hướng đầu trang khi người dùng cuộn chuột
    let scrollSpyInitialized = false;
    function initScrollSpy() {
      if (scrollSpyInitialized) return;
      scrollSpyInitialized = true;
      const sectionIds = ['section-profile', 'section-meals', 'section-single-dishes', 'section-workouts'];

      window.addEventListener('scroll', () => {
        const scrollPosition = window.scrollY + 200; // bù trừ chiều cao sticky header
        for (const secId of sectionIds) {
          const secEl = document.getElementById(secId);
          if (secEl) {
            const top = secEl.offsetTop;
            const height = secEl.offsetHeight;
            if (scrollPosition >= top && scrollPosition < top + height) {
              setActiveNav(secId);
              break;
            }
          }
        }
      });
    }

    // Khởi chạy khi tải trang
    document.addEventListener("DOMContentLoaded", async () => {
      lucide.createIcons();
      updateRealTimeDate();
      await checkDbStatus();
      initScrollSpy();

      // Tự động kiểm tra đăng nhập khi F5
      await checkAutoLogin();
    });

    async function checkDbStatus() {
      if (typeof NutriFitAPI === 'undefined') return;
      try {
        const res = await NutriFitAPI.checkConnection();
        isDbConnected = (res.status === 'connected');
      } catch (err) {
        isDbConnected = false;
      }
    }

    function switchScreen(screenId) {
      document.getElementById('screen-auth').classList.add('hidden');
      document.getElementById('screen-onboarding').classList.add('hidden');
      document.getElementById('screen-onboarding').classList.remove('flex');
      document.getElementById('screen-dashboard').classList.add('hidden');

      const target = document.getElementById(screenId);
      target.classList.remove('hidden');
      if (screenId === 'screen-onboarding') target.classList.add('flex');
      lucide.createIcons();

      if (screenId === 'screen-dashboard') {
        loadTodayMeals();
        loadDashboardSummary();
      }
    }

    // Hiển thị thông báo lỗi / thành công ở Auth
    function showAuthAlert(msg, isSuccess = false) {
      const alertBox = document.getElementById('auth-alert');
      const alertMsg = document.getElementById('auth-alert-msg');
      const alertIcon = document.getElementById('auth-alert-icon');

      alertMsg.innerText = msg;
      alertBox.classList.remove('hidden');

      if (isSuccess) {
        alertBox.className = "mb-4 p-3 rounded-xl text-xs font-semibold flex items-center gap-2 bg-emerald-50 text-emerald-800 border border-emerald-200";
        alertIcon.setAttribute('data-lucide', 'check-circle');
      } else {
        alertBox.className = "mb-4 p-3 rounded-xl text-xs font-semibold flex items-center gap-2 bg-rose-50 text-rose-700 border border-rose-200 animate-pulse";
        alertIcon.setAttribute('data-lucide', 'alert-circle');
      }
      lucide.createIcons();
    }

    function hideAuthAlert() {
      document.getElementById('auth-alert').classList.add('hidden');
    }

    // Chuyển qua lại giữa tab Đăng nhập và Đăng ký
    function toggleAuthTab(mode) {
      currentAuthMode = mode;
      hideAuthAlert();
      const tabLogin = document.getElementById('tab-login');
      const tabRegister = document.getElementById('tab-register');
      const nameField = document.getElementById('fullname-field');
      const submitBtn = document.getElementById('btn-auth-submit');
      const passHint = document.getElementById('pass-hint');

      if (mode === 'register') {
        tabRegister.className = "flex-1 py-2 text-xs font-bold rounded-lg bg-white text-slate-900 shadow-sm transition-all";
        tabLogin.className = "flex-1 py-2 text-xs font-bold rounded-lg text-slate-500 hover:text-slate-900 transition-all";
        nameField.classList.remove('hidden');
        submitBtn.innerHTML = `<span>Tạo tài khoản & Thiết lập thể trạng</span><i data-lucide="arrow-right" class="w-4 h-4"></i>`;
        passHint.innerText = '';
      } else {
        tabLogin.className = "flex-1 py-2 text-xs font-bold rounded-lg bg-white text-slate-900 shadow-sm transition-all";
        tabRegister.className = "flex-1 py-2 text-xs font-bold rounded-lg text-slate-500 hover:text-slate-900 transition-all";
        nameField.classList.add('hidden');
        submitBtn.innerHTML = `<span>Đăng nhập vào hệ thống</span><i data-lucide="arrow-right" class="w-4 h-4"></i>`;
        passHint.innerText = '';
      }
      lucide.createIcons();
    }

    async function handleAuth(e) {
      e.preventDefault();
      hideAuthAlert();
      const email = document.getElementById('input-email').value.trim();
      const password = document.getElementById('input-password').value;
      const fullname = document.getElementById('input-fullname').value.trim();
      const button = document.getElementById('btn-auth-submit');
      const original = button.innerHTML;
      button.disabled = true;
      try {
        const result = currentAuthMode === 'login'
          ? await NutriFitAuth.login(email, password)
          : await NutriFitAuth.register(email, password, fullname);
        if (!result.success) {
          showAuthAlert(result.message || 'Không thể đăng nhập.');
          return;
        }
        todayMealsCache = { breakfast: null, lunch: null, dinner: null };
        mealPreferences = { breakfast: {}, lunch: {}, dinner: {} };
        mealTargets = {};
        renderMealPreferences();
        document.getElementById('meal-replace-request').value = '';
        Object.assign(userProfile, result.user);
        saveSession(result.user, result.profile);
        document.getElementById('input-password').value = '';
        if (result.profile) {
          applyLoadedProfile(result.profile);
          switchScreen('screen-dashboard');
        } else {
          isEditingProfile = false;
          currentStep = 1;
          updateStepUI();
          switchScreen('screen-onboarding');
        }
      } finally {
        button.disabled = false;
        button.innerHTML = original;
        lucide.createIcons();
      }
    }
