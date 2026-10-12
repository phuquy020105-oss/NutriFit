// frontend/js/auth.js
// NutriFit - Authentication Service
// Giữ nguyên UI/logic cũ, chỉ thay lớp giao tiếp với Backend mới.

(function () {
  "use strict";

  const SESSION_KEY = "nutrifit_session_user";

  /**
   * Chuẩn hóa user từ Backend mới về format
   * mà code giao diện cũ đang sử dụng.
   *
   * Backend TV1:
   * {
   *   id,
   *   email,
   *   full_name
   * }
   *
   * Code cũ:
   * {
   *   id,
   *   email,
   *   fullname
   * }
   */
  function normalizeUser(user) {
    if (!user) {
      return null;
    }

    return {
      id: user.id,
      email: user.email || "",
      full_name: user.full_name || user.fullname || "",
      fullname: user.full_name || user.fullname || ""
    };
  }

  /**
   * Chuẩn hóa profile từ Backend mới về format
   * mà applyLoadedProfile() cũ đang sử dụng.
   */
  function normalizeProfile(profile) {
    if (!profile) {
      return null;
    }

    return {
      Gender: profile.gender ?? profile.Gender ?? "male",
      Age: profile.age ?? profile.Age ?? 24,
      HeightCm: profile.height ?? profile.HeightCm ?? 172,
      WeightKg: profile.weight ?? profile.WeightKg ?? 68,
      Goal: profile.goal ?? profile.Goal ?? "lose",

      Bmr: profile.bmr ?? profile.Bmr ?? 0,
      Tdee: profile.tdee ?? profile.Tdee ?? 0,
      TargetKcal:
        profile.target_kcal ??
        profile.TargetKcal ??
        0,

      TargetWaterMl:
        profile.target_water_ml ??
        profile.TargetWaterMl ??
        0
    };
  }

  /**
   * Lấy profile từ Backend.
   *
   * Backend TV1:
   * GET /api/profile/<user_id>
   */
  async function loadProfile(userId) {
    if (!userId) {
      return null;
    }

    try {
      const result =
        await window.NutriFitAPI.getProfile(userId);

      if (
        !result ||
        !result.success ||
        !result.data
      ) {
        return null;
      }

      return normalizeProfile(result.data);

    } catch (error) {
      console.warn(
        "Không thể tải profile:",
        error
      );

      return null;
    }
  }

  /**
   * LOGIN
   *
   * Gọi:
   * POST /api/auth/login
   *
   * Sau khi login thành công,
   * tự lấy thêm profile của user.
   */
  async function login(email, password) {
    const result =
      await window.NutriFitAPI.login(
        email,
        password
      );

    if (!result || !result.success) {
      return result || {
        success: false,
        message: "Không thể kết nối Backend."
      };
    }

    const user =
      normalizeUser(result.user);

    if (!user || !user.id) {
      return {
        success: false,
        message:
          "Backend trả về thông tin tài khoản không hợp lệ."
      };
    }

    // Backend login không trả profile,
    // nên lấy profile bằng API riêng.
    const profile =
      await loadProfile(user.id);

    return {
      ...result,
      success: true,
      user,
      profile
    };
  }

  /**
   * REGISTER
   *
   * Gọi:
   * POST /api/auth/register
   *
   * Lưu ý:
   * Backend mới yêu cầu full_name,
   * không phải fullname.
   */
  async function register(
    email,
    password,
    fullName
  ) {
    const result =
      await window.NutriFitAPI.register(
        email,
        password,
        fullName
      );

    if (!result || !result.success) {
      return result || {
        success: false,
        message: "Không thể kết nối Backend."
      };
    }

    const user =
      normalizeUser(result.user);

    if (!user || !user.id) {
      return {
        success: false,
        message:
          "Backend trả về thông tin tài khoản không hợp lệ."
      };
    }

    return {
      ...result,
      success: true,
      user,
      profile: null
    };
  }

  /**
   * Session helpers
   *
   * Hiện tại giữ nguyên key cũ:
   * nutrifit_session_user
   *
   * để không phá code giao diện cũ.
   */
  function saveSession(user, profile = null) {
    const normalizedUser =
      normalizeUser(user);

    if (!normalizedUser) {
      return;
    }

    localStorage.setItem(
      SESSION_KEY,
      JSON.stringify({
        user: normalizedUser,
        profile: profile
          ? normalizeProfile(profile)
          : null
      })
    );
  }

  function getSession() {
    const raw =
      localStorage.getItem(SESSION_KEY);

    if (!raw) {
      return null;
    }

    try {
      return JSON.parse(raw);
    } catch (error) {
      console.warn(
        "Session không hợp lệ:",
        error
      );

      localStorage.removeItem(
        SESSION_KEY
      );

      return null;
    }
  }

  function logout() {
    localStorage.removeItem(
      SESSION_KEY
    );
  }

  // Public API
  window.NutriFitAuth = {
    login,
    register,
    loadProfile,
    normalizeUser,
    normalizeProfile,
    saveSession,
    getSession,
    logout
  };
})();