// NutriFit Frontend
// Extracted from the existing UI logic; behavior preserved.

    let currentStep = 1;
    let currentWater = 0;
    let isEditingProfile = false;
    let currentAuthMode = 'login';
    let isDbConnected = false;

    // Danh sách tài khoản dự phòng khi offline
    let registeredUsers = [
      {
        email: "demo@nutrifit.vn",
        password: "123456",
        fullname: "Lê Phú Quý"
      },
      {
        email: "admin1",
        password: "123456",
        fullname: "admin1"
      },
      {
        email: "test",
        password: "123456",
        fullname: "Khoa"
      }
    ];

    let userProfile = {
      id: 1,
      fullname: "Lê Phú Quý",
      email: "demo@nutrifit.vn",
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
    function saveSession(userObj, profileObj) {
      try {
        localStorage.setItem('nutrifit_session_user', JSON.stringify({
          user: userObj,
          profile: profileObj
        }));
      } catch (e) {
        console.warn("Không thể lưu session:", e);
      }
    }

    function checkAutoLogin() {
      const raw = localStorage.getItem('nutrifit_session_user');
      if (!raw) return false;
      try {
        const session = JSON.parse(raw);
        if (session && session.user && session.user.id) {
          userProfile.id = session.user.id;
          userProfile.fullname = session.user.fullname || "Thành viên NutriFit";
          userProfile.email = session.user.email || "";

          if (session.profile) {
            applyLoadedProfile(session.profile);
          } else {
            updateDashboardUI();
          }

          switchScreen('screen-dashboard');
          return true;
        }
      } catch (e) {
        console.error("Lỗi parse session:", e);
      }
      return false;
    }

    function handleLogout() {
      localStorage.removeItem('nutrifit_session_user');
      switchScreen('screen-auth');
    }

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
      checkAutoLogin();
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
        loadWorkoutsFromDB();
        loadTodayMeals();
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
        passHint.innerText = "(Tối thiểu 6 ký tự)";
      } else {
        tabLogin.className = "flex-1 py-2 text-xs font-bold rounded-lg bg-white text-slate-900 shadow-sm transition-all";
        tabRegister.className = "flex-1 py-2 text-xs font-bold rounded-lg text-slate-500 hover:text-slate-900 transition-all";
        nameField.classList.add('hidden');
        submitBtn.innerHTML = `<span>Đăng nhập vào hệ thống</span><i data-lucide="arrow-right" class="w-4 h-4"></i>`;
        passHint.innerText = "(Mẫu: 123456)";
      }
      lucide.createIcons();
    }

    // XỬ LÝ ĐĂNG NHẬP / ĐĂNG KÝ VỚI SQL SERVER
    async function handleAuth(e) {
      e.preventDefault();
      hideAuthAlert();

      const email = document.getElementById('input-email').value.trim();
      const password = document.getElementById('input-password').value;
      const fullname = document.getElementById('input-fullname').value.trim();
      const submitBtn = document.getElementById('btn-auth-submit');

      const originalBtnText = submitBtn.innerHTML;
      submitBtn.innerHTML = `<span>Đang đăng nhập...</span><i data-lucide="loader" class="w-4 h-4 animate-spin"></i>`;
      lucide.createIcons();

      try {
        if (currentAuthMode === 'login') {
          // Thử đăng nhập qua SQL Server Backend
          let result = await NutriFitAuth.login(email, password);

          if (!result.success) {
            // NẾU MÁY CHỦ CHƯA BẬT (Backend offline) -> Tự động kiểm tra danh sách tài khoản dự phòng
            if (result.isOffline || (result.message && (result.message.includes('kết nối máy chủ') || result.message.includes('Failed to fetch')))) {
              const matchedLocal = registeredUsers.find(u => 
                u.email.toLowerCase() === email.toLowerCase() || 
                (u.fullname && u.fullname.toLowerCase() === email.toLowerCase())
              );
              if (matchedLocal && matchedLocal.password === password) {
                userProfile.id = 1;
                userProfile.fullname = matchedLocal.fullname;
                userProfile.email = matchedLocal.email;
                saveSession({ id: 1, email: matchedLocal.email, fullname: matchedLocal.fullname }, null);
                showAuthAlert("Đăng nhập thành công (Chế độ Ngoại tuyến)!", true);
                setTimeout(() => {
                  switchScreen('screen-dashboard');
                }, 600);
                return;
              } else {
                submitBtn.innerHTML = originalBtnText;
                showAuthAlert("Máy chủ Backend chưa bật! Hãy chạy lệnh 'python server.py' trong terminal hoặc đăng nhập bằng tài khoản: demo@nutrifit.vn / mật khẩu: 123456", false);
                return;
              }
            }

            submitBtn.innerHTML = originalBtnText;
            showAuthAlert(result.message || "Tài khoản hoặc mật khẩu không chính xác!", false);
            const pwdInput = document.getElementById('input-password');
            pwdInput.classList.add('border-rose-500', 'bg-rose-50/30');
            setTimeout(() => pwdInput.classList.remove('border-rose-500', 'bg-rose-50/30'), 1500);
            return;
          }

          // Đăng nhập thành công từ SQL Server
          userProfile.id = result.user.id;
          userProfile.fullname = result.user.fullname;
          userProfile.email = result.user.email;

          // Lưu session tự động
          saveSession(result.user, result.profile);

          // Nếu có Profile lưu sẵn trong SQL Server, áp dụng luôn vào Dashboard
          if (result.profile) {
            applyLoadedProfile(result.profile);
            switchScreen('screen-dashboard');
          } else {
            isEditingProfile = false;
            currentStep = 1;
            updateStepUI();
            switchScreen('screen-onboarding');
          }

        } else {
          // Đăng ký mới vào SQL Server
          if (password.length < 6) {
            submitBtn.innerHTML = originalBtnText;
            showAuthAlert("Mật khẩu phải có độ dài từ 6 ký tự trở lên!", false);
            return;
          }

          let regResult = await NutriFitAuth.register(email, password, fullname);
          if (!regResult.success) {
            submitBtn.innerHTML = originalBtnText;
            showAuthAlert(regResult.message, false);
            return;
          }

          userProfile.id = regResult.user.id;
          userProfile.fullname = regResult.user.fullname;
          userProfile.email = regResult.user.email;

          // Lưu session
          saveSession(regResult.user, null);

          isEditingProfile = false;
          currentStep = 1;
          updateStepUI();
          switchScreen('screen-onboarding');
        }
      } catch (err) {
        showAuthAlert("Lỗi: " + err.message, false);
      } finally {
        submitBtn.innerHTML = originalBtnText;
        lucide.createIcons();
      }
    }
