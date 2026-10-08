// NutriFit Frontend
// Extracted from the existing UI logic; behavior preserved.

    // QUẢN LÝ BÀI TẬP, LẬP LỊCH TẬP & BIỂU ĐỒ TẦN SUẤT (FEATURE.TXT)
    // ========================================================================
    let allWorkoutsCache = [];
    let currentWorkoutFilter = 'all'; // 'all', 'default', 'custom'
    let workoutChartInstance = null;
    let currentChartMetric = 'duration'; // 'duration', 'calories', 'count'
    let workoutStatsCache = null;

    // 1. Tải danh mục bài tập và số liệu thống kê tần suất từ SQL Server
    async function loadWorkoutsFromDB() {
      await Promise.all([
        loadWorkoutsList(),
        loadWorkoutStats()
      ]);
    }

    async function loadWorkoutsList() {
      const container = document.getElementById('workouts-list-container');
      if (!container) return;

      const res = await NutriFitAPI.getWorkouts(userProfile.id || 1);
      if (res.success && res.workouts) {
        allWorkoutsCache = res.workouts;
        renderWorkoutsList();
      } else {
        container.innerHTML = `<div class="col-span-full py-8 text-center text-rose-500 text-xs font-semibold">Lỗi tải danh mục bài tập: ${res.message || 'Không thể kết nối máy chủ.'}</div>`;
      }
    }

    // Lọc danh mục bài tập
    function filterWorkouts(filter) {
      currentWorkoutFilter = filter;
      const btnAll = document.getElementById('filter-btn-all');
      const btnDef = document.getElementById('filter-btn-default');
      const btnCust = document.getElementById('filter-btn-custom');

      const activeClass = "px-3 py-1 bg-white text-slate-800 rounded-lg shadow-sm transition-all";
      const inactiveClass = "px-3 py-1 text-slate-600 hover:text-slate-900 rounded-lg transition-all";

      if (btnAll) btnAll.className = filter === 'all' ? activeClass : inactiveClass;
      if (btnDef) btnDef.className = filter === 'default' ? activeClass : inactiveClass;
      if (btnCust) btnCust.className = filter === 'custom' ? activeClass : inactiveClass;

      renderWorkoutsList();
    }

    // Hiển thị danh sách thẻ bài tập
    function renderWorkoutsList() {
      const container = document.getElementById('workouts-list-container');
      if (!container) return;

      let list = allWorkoutsCache;
      if (currentWorkoutFilter === 'default') {
        list = allWorkoutsCache.filter(w => !w.isCustom);
      } else if (currentWorkoutFilter === 'custom') {
        list = allWorkoutsCache.filter(w => w.isCustom);
      }

      if (list.length === 0) {
        container.innerHTML = `
          <div class="col-span-full py-12 text-center bg-slate-50 border border-dashed border-slate-200 rounded-3xl space-y-3">
            <span class="w-12 h-12 rounded-2xl bg-purple-100 text-purple-600 inline-flex items-center justify-center"><i data-lucide="dumbbell" class="w-6 h-6"></i></span>
            <h4 class="font-bold text-sm text-slate-700">Chưa có hoạt động nào trong mục này</h4>
            <p class="text-xs text-slate-400 max-w-sm mx-auto">Bạn có thể nhấn nút <b>"+ Thêm hoạt động mới"</b> để tự thêm bài tập riêng của mình.</p>
            <button onclick="openCustomWorkoutModal()" class="px-5 py-2 bg-purple-600 hover:bg-purple-700 text-white font-bold rounded-xl text-xs shadow-sm">
              + Tạo bài tập đầu tiên
            </button>
          </div>
        `;
        lucide.createIcons();
        return;
      }

      container.innerHTML = list.map(w => {
        const isCustom = w.isCustom;
        const categoryColor = isCustom ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-purple-50 text-purple-700 border-purple-200';
        return `
          <div class="border border-slate-200/80 rounded-2xl p-5 hover:border-purple-500 hover:shadow-lg transition-all flex flex-col justify-between space-y-4 bg-white relative group">
            <div class="space-y-3">
              <div class="flex items-center justify-between gap-2">
                <span class="text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-full border ${categoryColor}">
                  ${isCustom ? '⭐ Tự tạo' : 'Hệ thống'} • ${w.category || 'Vận động'}
                </span>
                <span class="text-xs font-black text-rose-600 flex items-center gap-1">
                  <i data-lucide="flame" class="w-3.5 h-3.5"></i>
                  ${w.caloriesBurned} kcal
                </span>
              </div>
              <div>
                <h4 class="font-black text-sm text-slate-800 line-clamp-1">${w.name}</h4>
                <p class="text-xs text-slate-400 mt-0.5 flex items-center gap-1">
                  <i data-lucide="clock" class="w-3 h-3"></i> Thời gian: <b class="text-slate-600 font-bold">${w.durationMinutes} phút</b>
                </p>
              </div>
              <div class="p-2.5 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
                <span>Ước tính tiêu hao:</span>
                <span class="font-bold text-slate-700">~${Math.round((w.caloriesBurned / w.durationMinutes) * 10) / 10} kcal/phút</span>
              </div>
            </div>
            
            <div class="pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
              ${isCustom ? `
                <button onclick="handleDeleteCustomWorkout(${w.id}, '${w.name.replace(/'/g, "\\'")}')" 
                        class="text-slate-400 hover:text-rose-600 p-1.5 rounded-lg hover:bg-rose-50 transition-all flex items-center gap-1 text-[11px] font-medium" 
                        title="Xóa hoạt động này khỏi danh mục">
                  <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                  <span>Xóa</span>
                </button>
              ` : `<span></span>`}
              <button onclick="handleLogWorkout(${w.id}, ${w.durationMinutes}, ${w.caloriesBurned}, '${w.name.replace(/'/g, "\\'")}')" 
                      class="px-3.5 py-1.5 bg-purple-50 hover:bg-purple-600 text-purple-700 hover:text-white rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all shadow-sm">
                <i data-lucide="check" class="w-3.5 h-3.5"></i>
                <span>Ghi nhận tập</span>
              </button>
            </div>
          </div>
        `;
      }).join('');

      lucide.createIcons();
    }

    // 2. Tải và cập nhật thống kê tần suất tập luyện 7 ngày
    async function loadWorkoutStats() {
      const res = await NutriFitAPI.getWorkoutStats(userProfile.id || 1);
      if (res.success && res.stats) {
        workoutStatsCache = res.stats;
        updateWorkoutSummaryMetrics(res.stats.summary);
        renderWorkoutChart();
      }
    }

    // Cập nhật 4 thẻ chỉ số nhanh
    function updateWorkoutSummaryMetrics(summary) {
      if (!summary) return;
      document.getElementById('stat-workout-sessions').innerText = `${summary.totalSessions || 0} buổi`;
      document.getElementById('stat-workout-minutes').innerText = `${summary.totalMinutes || 0} phút`;
      document.getElementById('stat-workout-calories').innerText = `${Number(summary.totalCalories || 0).toLocaleString('vi-VN')} kcal`;
      document.getElementById('stat-workout-activedays').innerText = `${summary.activeDays || 0}/7 ngày`;
    }

    // Chuyển đổi chỉ số trên biểu đồ: 'duration' | 'calories' | 'count'
    function switchChartMetric(metric) {
      currentChartMetric = metric;
      const btnDur = document.getElementById('chart-btn-duration');
      const btnCal = document.getElementById('chart-btn-calories');
      const btnCnt = document.getElementById('chart-btn-count');

      const active = "px-3 py-1 rounded-lg bg-white text-slate-900 shadow-sm transition-all";
      const inactive = "px-3 py-1 rounded-lg text-slate-600 hover:text-slate-900 transition-all";

      if (btnDur) btnDur.className = metric === 'duration' ? active : inactive;
      if (btnCal) btnCal.className = metric === 'calories' ? active : inactive;
      if (btnCnt) btnCnt.className = metric === 'count' ? active : inactive;

      renderWorkoutChart();
    }

    // Vẽ biểu đồ tần suất bằng Chart.js
    function renderWorkoutChart() {
      if (!workoutStatsCache || !workoutStatsCache.days) return;
      const canvas = document.getElementById('workoutFrequencyChart');
      if (!canvas) return;

      const days = workoutStatsCache.days;
      const labels = days.map(d => d.label);

      let dataValues = [];
      let labelText = '';
      let barColor = '';
      let hoverColor = '';

      if (currentChartMetric === 'duration') {
        dataValues = days.map(d => d.duration);
        labelText = 'Thời gian tập (phút)';
        barColor = 'rgba(147, 51, 234, 0.85)'; // purple-600
        hoverColor = 'rgba(126, 34, 206, 1)';
      } else if (currentChartMetric === 'calories') {
        dataValues = days.map(d => d.calories);
        labelText = 'Calo tiêu hao (kcal)';
        barColor = 'rgba(244, 63, 94, 0.85)'; // rose-500
        hoverColor = 'rgba(225, 29, 72, 1)';
      } else {
        dataValues = days.map(d => d.count);
        labelText = 'Số buổi tập (buổi)';
        barColor = 'rgba(16, 185, 129, 0.85)'; // emerald-500
        hoverColor = 'rgba(5, 150, 105, 1)';
      }

      if (workoutChartInstance) {
        workoutChartInstance.destroy();
      }

      const ctx = canvas.getContext('2d');
      workoutChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [{
            label: labelText,
            data: dataValues,
            backgroundColor: barColor,
            hoverBackgroundColor: hoverColor,
            borderRadius: 8,
            borderSkipped: false,
            maxBarThickness: 36
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              backgroundColor: '#0f172a',
              titleFont: { family: 'Inter', size: 12, weight: 'bold' },
              bodyFont: { family: 'Inter', size: 12 },
              padding: 10,
              cornerRadius: 10,
              callbacks: {
                label: function(context) {
                  const val = context.parsed.y;
                  if (currentChartMetric === 'duration') return `⏱️ Thời gian: ${val} phút`;
                  if (currentChartMetric === 'calories') return `🔥 Năng lượng: ${val} kcal`;
                  return `📊 Số buổi: ${val} buổi`;
                }
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              grid: {
                color: '#f1f5f9',
                drawBorder: false
              },
              ticks: {
                font: { family: 'Inter', size: 11 },
                color: '#94a3b8'
              }
            },
            x: {
              grid: { display: false },
              ticks: {
                font: { family: 'Inter', size: 11, weight: '600' },
                color: '#64748b'
              }
            }
          }
        }
      });
    }

    // 3. Ghi nhận một buổi tập luyện
    async function handleLogWorkout(workoutId, duration, calories, name) {
      const res = await NutriFitAPI.logWorkout({
        userId: userProfile.id || 1,
        workoutId: workoutId,
        durationMinutes: duration,
        caloriesBurned: calories
      });

      if (res.success) {
        showToast("Ghi nhận tập luyện thành công!", `Đã lưu: ${name} (${duration} phút, ${calories} kcal).`);
        // Làm mới dữ liệu biểu đồ và số liệu thống kê
        await loadWorkoutStats();
      } else {
        alert("Lỗi: " + (res.message || "Không thể lưu buổi tập."));
      }
    }

    // 4. Quản lý Modal Thêm hoạt động tùy chỉnh
    function openCustomWorkoutModal() {
      const modal = document.getElementById('modal-custom-workout');
      document.getElementById('form-custom-workout').reset();
      modal.classList.remove('hidden');
      modal.classList.add('flex');
      lucide.createIcons();
    }

    function closeCustomWorkoutModal() {
      const modal = document.getElementById('modal-custom-workout');
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }

    async function handleCreateCustomWorkout(e) {
      e.preventDefault();
      const name = document.getElementById('inp-custom-name').value.trim();
      const duration = parseInt(document.getElementById('inp-custom-duration').value);
      const calories = parseFloat(document.getElementById('inp-custom-calories').value);
      const category = document.getElementById('inp-custom-category').value;
      const submitBtn = document.getElementById('btn-submit-custom-workout');

      if (!name) {
        alert("Vui lòng nhập tên hoạt động!");
        return;
      }
      if (!duration || duration <= 0) {
        alert("Thời gian tập luyện phải lớn hơn 0 phút!");
        return;
      }
      if (!calories || calories <= 0) {
        alert("Lượng calo đốt được phải lớn hơn 0 kcal!");
        return;
      }

      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = `<i data-lucide="loader" class="w-4 h-4 animate-spin"></i><span>Đang lưu...</span>`;
      lucide.createIcons();

      const res = await NutriFitAPI.createCustomWorkout({
        userId: userProfile.id || 1,
        name: name,
        durationMinutes: duration,
        caloriesBurned: calories,
        category: category
      });

      submitBtn.innerHTML = originalText;
      lucide.createIcons();

      if (res.success) {
        closeCustomWorkoutModal();
        showToast("Thêm bài tập thành công!", `Hoạt động '${name}' đã được thêm vào danh mục.`);
        await loadWorkoutsList();
      } else {
        alert("Lỗi khi thêm bài tập: " + (res.message || "Không rõ nguyên nhân."));
      }
    }

    async function handleDeleteCustomWorkout(workoutId, name) {
      if (!confirm(`Bạn có chắc chắn muốn xóa bài tập "${name}" khỏi danh mục không?`)) {
        return;
      }
      const res = await NutriFitAPI.deleteCustomWorkout(workoutId, userProfile.id || 1);
      if (res.success) {
        showToast("Đã xóa hoạt động!", `Đã gỡ bỏ bài tập "${name}".`);
        await loadWorkoutsList();
        await loadWorkoutStats();
      } else {
        alert("Lỗi khi xóa bài tập: " + (res.message || "Không rõ nguyên nhân."));
      }
    }

    // 5. Quản lý Modal Lịch sử tập luyện
    async function openWorkoutHistoryModal() {
      const modal = document.getElementById('modal-workout-history');
      const content = document.getElementById('modal-workout-logs-content');
      const hint = document.getElementById('workout-logs-total-hint');

      content.innerHTML = `<div class="py-8 text-center text-slate-400 text-xs">Đang tải lịch sử tập luyện...</div>`;
      modal.classList.remove('hidden');
      modal.classList.add('flex');
      lucide.createIcons();

      const res = await NutriFitAPI.getWorkoutLogs(userProfile.id || 1);
      if (!res.success || !res.logs || res.logs.length === 0) {
        content.innerHTML = `
          <div class="py-12 text-center bg-slate-50 border border-dashed border-slate-200 rounded-2xl space-y-2">
            <span class="w-10 h-10 rounded-xl bg-purple-100 text-purple-600 inline-flex items-center justify-center"><i data-lucide="calendar-x" class="w-5 h-5"></i></span>
            <p class="font-bold text-xs text-slate-700">Chưa có buổi tập nào được ghi nhận</p>
            <p class="text-[11px] text-slate-400">Hãy nhấn "Ghi nhận tập" tại các bài tập để lưu lịch trình nhé!</p>
          </div>
        `;
        if (hint) hint.innerText = "Tổng số buổi tập: 0";
      } else {
        if (hint) hint.innerText = `Tổng số buổi tập: ${res.logs.length} buổi`;
        content.innerHTML = res.logs.map(log => `
          <div class="p-3.5 rounded-2xl border border-slate-200 bg-white hover:border-purple-300 transition-all flex items-center justify-between gap-3 text-xs">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center shrink-0">
                <i data-lucide="dumbbell" class="w-5 h-5"></i>
              </div>
              <div>
                <div class="flex items-center gap-2">
                  <span class="font-extrabold text-slate-800 text-sm">${log.workoutName}</span>
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded-full ${log.isCustom ? 'bg-amber-50 text-amber-700' : 'bg-purple-50 text-purple-700'}">
                    ${log.isCustom ? 'Tự tạo' : 'Mặc định'}
                  </span>
                </div>
                <div class="flex items-center gap-3 text-[11px] text-slate-400 mt-0.5">
                  <span>📅 ${log.date} ${log.createdAt ? `(${log.createdAt})` : ''}</span>
                  <span>⏱️ <b>${log.durationMinutes} phút</b></span>
                  <span class="text-rose-600 font-bold">🔥 ${log.caloriesBurned} kcal</span>
                </div>
              </div>
            </div>
            <button onclick="handleDeleteWorkoutLog(${log.logId})" title="Xóa buổi tập này" 
                    class="w-8 h-8 rounded-xl bg-slate-50 hover:bg-rose-50 text-slate-400 hover:text-rose-600 flex items-center justify-center transition-all shrink-0">
              <i data-lucide="trash-2" class="w-4 h-4"></i>
            </button>
          </div>
        `).join('');
      }

      lucide.createIcons();
    }

    function closeWorkoutHistoryModal() {
      const modal = document.getElementById('modal-workout-history');
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }

    async function handleDeleteWorkoutLog(logId) {
      if (!confirm("Bạn có chắc chắn muốn xóa bản ghi buổi tập này?")) return;
      const res = await NutriFitAPI.deleteWorkoutLog(logId, userProfile.id || 1);
      if (res.success) {
        showToast("Đã xóa bản ghi!", "Dữ liệu tần suất tập đã được đồng bộ lại.");
        await openWorkoutHistoryModal();
        await loadWorkoutStats();
      } else {
        alert("Lỗi khi xóa: " + res.message);
      }
    }

    // 6. Toast Notification đa dụng
    let toastTimeout = null;
    function showToast(title, desc) {
      const toast = document.getElementById('toast-workout');
      if (!toast) return;

      document.getElementById('toast-workout-title').innerText = title;
      document.getElementById('toast-workout-desc').innerText = desc;

      toast.classList.remove('hidden');
      if (toastTimeout) clearTimeout(toastTimeout);
      toastTimeout = setTimeout(() => {
        toast.classList.add('hidden');
      }, 3500);
      lucide.createIcons();
    }
