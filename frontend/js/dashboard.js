// NutriFit Frontend
// Extracted from the existing UI logic; behavior preserved.

    function updateDashboardUI() {
      const goalNames = { lose: 'Giảm mỡ', maintain: 'Cân Bằng', gain: 'Tăng cơ' };

      document.getElementById('dash-fullname').innerText = userProfile.fullname;
      document.getElementById('dash-greeting-name').innerText = userProfile.fullname;
      document.getElementById('dash-avatar').innerText = userProfile.fullname.split(' ').pop().substring(0, 2).toUpperCase();

      if (document.getElementById('dash-goal-badge')) document.getElementById('dash-goal-badge').innerText = `Chế độ: ${goalNames[userProfile.goal] || 'Cân Bằng'}`;
      if (document.getElementById('dash-goal-tag')) document.getElementById('dash-goal-tag').innerText = goalNames[userProfile.goal] || 'Cân Bằng';

      if (document.getElementById('dash-target-kcal')) document.getElementById('dash-target-kcal').innerText = Number(userProfile.targetKcal).toLocaleString('vi-VN');
      if (document.getElementById('dash-remaining-kcal')) document.getElementById('dash-remaining-kcal').innerText = Number(userProfile.targetKcal).toLocaleString('vi-VN');
      if (document.getElementById('dash-progress-pct')) document.getElementById('dash-progress-pct').innerText = "0%";
      if (document.getElementById('dash-progress-ring')) document.getElementById('dash-progress-ring').setAttribute('stroke-dasharray', '0, 100');

      if (document.getElementById('dash-carb')) document.getElementById('dash-carb').innerText = `0/${userProfile.carbs}g`;
      if (document.getElementById('dash-protein')) document.getElementById('dash-protein').innerText = `0/${userProfile.protein}g`;
      if (document.getElementById('dash-fat')) document.getElementById('dash-fat').innerText = `0/${userProfile.fat}g`;
      if (document.getElementById('dash-fiber')) document.getElementById('dash-fiber').innerText = `0/${userProfile.fiber}g`;

      if (document.getElementById('dash-water-target')) document.getElementById('dash-water-target').innerText = Number(userProfile.waterTarget).toLocaleString('vi-VN');
      if (document.getElementById('dash-water-current')) document.getElementById('dash-water-current').innerText = "0";
      currentWater = 0;

      document.getElementById('profile-stat-weight').innerText = `${userProfile.weight} kg`;
      document.getElementById('profile-stat-height').innerText = `${userProfile.height} cm`;

      // Cập nhật giá trị BMI và đánh giá thể trạng chuẩn khoa học WHO
      const bmiVal = parseFloat(userProfile.bmi) || 0;
      const bmiEl = document.getElementById('profile-stat-bmi');
      const badgeEl = document.getElementById('profile-stat-bmi-badge');
      if (bmiEl) bmiEl.innerText = userProfile.bmi;
      if (badgeEl) {
        if (bmiVal < 18.5) {
          badgeEl.innerText = "Thiếu cân";
          badgeEl.className = "text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-amber-100 text-amber-800";
        } else if (bmiVal < 23.0) {
          badgeEl.innerText = "Cân đối";
          badgeEl.className = "text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-emerald-100 text-emerald-800";
        } else if (bmiVal < 25.0) {
          badgeEl.innerText = "Thừa cân";
          badgeEl.className = "text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-orange-100 text-orange-800";
        } else {
          badgeEl.innerText = "Béo phì";
          badgeEl.className = "text-[10px] font-bold px-1.5 py-0.5 rounded-md bg-rose-100 text-rose-800";
        }
      }

      document.getElementById('profile-stat-age').innerText = `${userProfile.age} tuổi`;
      document.getElementById('profile-stat-gender').innerText = userProfile.gender === 'male' ? 'Nam' : 'Nữ';
      document.getElementById('profile-stat-goal').innerText = goalNames[userProfile.goal] || 'Cân Bằng';

      document.getElementById('profile-bmr').innerText = Number(userProfile.bmr).toLocaleString('vi-VN');
      document.getElementById('profile-tdee').innerText = Number(userProfile.tdee).toLocaleString('vi-VN');
      document.getElementById('profile-target-kcal').innerText = Number(userProfile.targetKcal).toLocaleString('vi-VN');
      document.getElementById('profile-water').innerText = Number(userProfile.waterTarget).toLocaleString('vi-VN');
    }

    function addWaterQuick() {
      currentWater += 250;
      document.getElementById('dash-water-current').innerText = currentWater.toLocaleString('vi-VN');
    }
