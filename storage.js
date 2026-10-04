// storage.js - Dữ liệu dùng chung cho cả nhóm

// 1. Dữ liệu mẫu 
const DEFAULT_USER = {
  id: "usr_default",
  fullname: "Nguyễn Văn Nam",
  email: "nam@caloer.vn",
  profile: {
    gender: "male",         // 'male' hoặc 'female'
    age: 24,                // Tuổi
    height: 170,            // cm
    weight: 68,             // kg
    goal: "lose",           // 'lose' (giảm cân), 'maintain' (giữ cân), 'gain' (tăng cân)
    activity: 1.2,          // Hệ số vận động
    bmi: 23.5,              // Chỉ số khối cơ thể
    bmr: 1540,              // Trao đổi chất cơ bản (kcal)
    tdee: 1850,             // Tổng calo tiêu hao mỗi ngày (kcal)
    targetKcal: 1350,       // CALO MỤC TIÊU CẦN NẠP MỖI NGÀY (kcal)
    macro: {
      carbs: 152,           // gram Tinh bột
      protein: 84,          // gram Chất đạm
      fat: 45               // gram Chất béo
    },
    waterTargetMl: 2400     // Lượng nước cần uống mỗi ngày (ml)
  }
};

// 2. Hàm bạn dùng: Lưu thông tin sau khi người dùng nhập thể trạng
function saveUserProfile(userObject) {
  localStorage.setItem('caloer_current_user', JSON.stringify(userObject));
  console.log("Đã lưu thành công:", userObject);
}

// 3. Hàm gọi lấy profile cho các chức năng sau
function getUserProfile() {
  const savedData = localStorage.getItem('caloer_current_user');
  if (savedData) {
    try {
      return JSON.parse(savedData);
    } catch (e) {
      console.error("Lỗi đọc dữ liệu:", e);
    }
  }
  return DEFAULT_USER;
}