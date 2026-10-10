// NutriFit Frontend
// Extracted from the existing UI logic; behavior preserved.

    // ========================================================================
    // LOGIC GỢI Ý MÓN ĂN VIỆT NAM (GEMINI FLASH AI & NÚT THỨ 4 SUY NGHĨ)
    // ========================================================================
    let currentMealMode = 'lunch';
    let todayMealsCache = { breakfast: null, lunch: null, dinner: null };
    let mealPreferences = { breakfast: {}, lunch: {}, dinner: {} };
    let mealTargets = {};
    const mealModes = {
      breakfast: { label: 'Bữa sáng', icon: '🌅', description: 'Nhanh gọn, món nước hoặc cân bằng.' },
      lunch: { label: 'Bữa trưa', icon: '☀️', description: 'Thực đơn đa dạng nguồn đạm và rau.' },
      dinner: { label: 'Bữa tối', icon: '🌙', description: 'Ưu tiên món hấp/luộc, ít dầu.' }
    };
    const mealFoodLabels = { fish: 'cá', seafood: 'hải sản', egg: 'trứng', milk: 'sữa', chicken: 'gà', beef: 'bò', pork: 'heo', soy: 'đậu phụ', wheat: 'bánh mì', oats: 'yến mạch', rice: 'cơm', noodles: 'bún', banana: 'chuối', sweet_potato: 'khoai lang' };
    function escapeMealText(value) {
      return String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
    }
    function mealComponents(option) {
      if (Array.isArray(option.components) && option.components.length) return option.components;
      return ['carb', 'protein', 'soup', 'veggie', 'dessert'].filter(key => option[key]).map(key => ({ type: key.toUpperCase(), name: option[key] }));
    }
    function renderMealComponents(option) {
      const labels = { MAIN: '🍽️ Món chính', SIDE: '🥗 Ăn kèm', DRINK: '🥛 Đồ uống', CARB: '🍚 Tinh bột', PROTEIN: '🥩 Món mặn', SOUP: '🥣 Canh', VEGGIE: '🥗 Rau', DESSERT: '🍌 Tráng miệng' };
      return mealComponents(option).map(c => '<div class="flex items-start gap-2"><span class="text-emerald-700 font-bold shrink-0">' + (labels[c.type] || '🍽️ Thành phần') + ':</span><span class="font-semibold text-slate-800">' + escapeMealText(c.name) + '</span></div>').join('');
    }
    function readMealPreferences() {
      const terms = id => document.getElementById(id).value.split(',').map(v => v.trim()).filter(Boolean);
      const preferences = { ...mealPreferences[currentMealMode], avoid: terms('meal-avoid'), dislikes: terms('meal-dislikes'), prefer: terms('meal-prefer') };
      delete preferences.maxPrepMinutes;
      delete preferences.preferEasy;
      if (currentMealMode === 'breakfast') {
        preferences.preferEasy = document.getElementById('meal-prefer-easy').checked;
        const minutes = document.getElementById('meal-prep-minutes').value;
        if (minutes) preferences.maxPrepMinutes = Number(minutes);
      }
      mealPreferences[currentMealMode] = preferences;
      return preferences;
    }
    function renderMealPreferences() {
      const p = mealPreferences[currentMealMode] || {};
      const label = list => (list || []).map(v => mealFoodLabels[v] || v).join(', ');
      document.getElementById('meal-avoid').value = label(p.avoid);
      document.getElementById('meal-dislikes').value = label(p.dislikes);
      document.getElementById('meal-prefer').value = label(p.prefer);
      document.getElementById('meal-prefer-easy').checked = !!p.preferEasy;
      document.getElementById('meal-prep-minutes').value = p.maxPrepMinutes || '';
      document.getElementById('meal-breakfast-prep').classList.toggle('hidden', currentMealMode !== 'breakfast');
    }

    // Tải thực đơn hôm nay khi mở Dashboard
    async function loadTodayMeals() {
      const res = await NutriFitAPI.getTodayMeals();
      if (res.success && res.todayMeals) {
        todayMealsCache = res.todayMeals;
        renderCurrentMealMode();
      } else if (res.httpStatus !== 401) {
        showMealToast(res.message || 'Không thể tải thực đơn hôm nay.', 'error');
      }
    }

    // Three tabs share the same server cache, selection and revision flow.
    function switchMealMode(mode) {
      if (!mealModes[mode]) return;
      readMealPreferences();
      currentMealMode = mode;
      for (const key of Object.keys(mealModes)) {
        document.getElementById('btn-mode-' + key).className = 'px-4 py-1.5 text-xs font-bold rounded-lg flex items-center gap-1.5 transition-all ' +
          (mode === key ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900');
      }
      const info = mealModes[mode];
      document.getElementById('meal-banner-icon').textContent = info.icon;
      document.getElementById('meal-banner-title').textContent = 'Chế độ: ' + info.label;
      const kcal = mealTargets[mode];
      document.getElementById('meal-banner-desc').innerHTML = 'Mục tiêu từ hồ sơ: <b id="meal-banner-kcal" class="text-brand-600">' +
        (kcal ? '~' + kcal + ' kcal' : '—') + '</b>. ' + info.description;
      renderMealPreferences();
      renderCurrentMealMode();
    }

    // Hiển thị dữ liệu thực đơn theo chế độ hiện tại
    function renderCurrentMealMode() {
      const mealData = todayMealsCache[currentMealMode];
      const source = document.getElementById('meal-source-label');
      if (source) source.textContent = !mealData ? '' :
        (mealData.source === 'gemini' ? 'Gemini chọn thực đơn' : 'Thực đơn dự phòng') + ' · Dinh dưỡng ước tính';
      const container = document.getElementById('meal-options-container');
      const boxThink = document.getElementById('box-think-later');
      const statusAlert = document.getElementById('meal-status-alert');
      const statusText = document.getElementById('meal-status-text');
      const statusBadge = document.getElementById('meal-status-badge');
      const statusIcon = document.getElementById('meal-status-icon');
      const btnGenText = document.getElementById('btn-generate-text');
      const btnRefresh = document.getElementById('btn-refresh-meals');

      if (!mealData || !mealData.options || mealData.options.length === 0) {
        // Chưa có thực đơn
        container.innerHTML = `
          <div class="col-span-full py-12 text-center bg-slate-50 border border-dashed border-slate-200 rounded-3xl space-y-3">
            <span class="w-12 h-12 rounded-2xl bg-emerald-100 text-brand-600 inline-flex items-center justify-center"><i data-lucide="utensils" class="w-6 h-6"></i></span>
            <h4 class="font-bold text-sm text-slate-700">Chưa có gợi ý thực đơn cho ${mealModes[currentMealMode].label}</h4>
            <p class="text-xs text-slate-400 max-w-md mx-auto">Nhấn nút <b>"Gợi ý 3 thực đơn ngay"</b> để nhận ba thực đơn phù hợp mục tiêu từ hồ sơ. Có thực đơn dự phòng khi AI không khả dụng.</p>
            <button onclick="generateMealSuggestions(false)" class="px-5 py-2.5 bg-brand-500 hover:bg-brand-600 text-white font-bold rounded-xl text-xs shadow-sm">
              Khám phá thực đơn ngay
            </button>
          </div>
        `;
        boxThink.classList.add('hidden');
        statusAlert.classList.add('hidden');
        if (btnRefresh) btnRefresh.classList.add('hidden');
        document.getElementById('meal-macro-legend')?.classList.add('hidden');
        btnGenText.innerText = `Gợi ý 3 thực đơn ngay`;
        lucide.createIcons();
        return;
      }

      // Đã có 3 options
      btnGenText.innerText = 'Tải lại thực đơn đã lưu';
      boxThink.classList.remove('hidden');
      statusAlert.classList.remove('hidden');
      if (btnRefresh) btnRefresh.classList.remove('hidden');
      document.getElementById('meal-macro-legend')?.classList.remove('hidden');

      // Cập nhật trạng thái
      if (mealData.selectedOption) {
        statusAlert.className = "p-3 rounded-xl text-xs font-semibold flex items-center justify-between bg-emerald-50 text-emerald-800 border border-emerald-200";
        statusIcon.setAttribute('data-lucide', 'check-circle');
        statusText.innerHTML = `Bạn đã chốt lựa chọn <b>Option ${mealData.selectedOption}: ${escapeMealText(mealData.options[mealData.selectedOption - 1]?.title)}</b>`;
        statusBadge.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-200 text-emerald-900";
        statusBadge.innerText = "Đã chốt món";
      } else {
        statusAlert.className = "p-3 rounded-xl text-xs font-semibold flex items-center justify-between bg-amber-50 text-amber-800 border border-amber-200";
        statusIcon.setAttribute('data-lucide', 'hourglass');
        statusText.innerHTML = `Trạng thái: <b>Đang suy nghĩ / cân nhắc</b>. Hệ thống giữ nguyên 3 lựa chọn ban đầu cho bạn.`;
        statusBadge.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-200 text-amber-900";
        statusBadge.innerText = "Đang chờ";
      }

      // Render flexible components and keep legacy rows readable.
      container.innerHTML = mealData.options.map((opt, index) => {
        const optNum = index + 1;
        const isSelected = mealData.selectedOption === optNum;

        // Xác định huy hiệu đa dạng
        let tagColor = "bg-emerald-50 text-emerald-700 border-emerald-200";
        if (optNum === 2) tagColor = "bg-blue-50 text-blue-700 border-blue-200";
        if (optNum === 3) tagColor = "bg-purple-50 text-purple-700 border-purple-200";

        return `
          <div class="border-2 ${isSelected ? 'border-brand-500 ring-4 ring-emerald-500/10 shadow-lg' : 'border-slate-200 hover:border-brand-400'} rounded-3xl p-5 bg-white flex flex-col justify-between space-y-4 transition-all relative">
            ${isSelected ? '<span class="absolute -top-3 right-4 bg-brand-500 text-white text-[10px] font-black px-3 py-0.5 rounded-full shadow-sm flex items-center gap-1"><i data-lucide="check" class="w-3 h-3"></i> Đã chọn thực đơn này</span>' : ''}

            <div class="space-y-3.5">
              <!-- Header Card -->
              <div class="flex items-center justify-between gap-2">
                <span class="text-[11px] font-extrabold uppercase px-2.5 py-0.5 rounded-lg border ${tagColor}">
                  Lựa chọn ${optNum}
                </span>
                <div class="text-right">
                  <span class="text-base font-black text-slate-800">${opt.calories}</span>
                  <span class="text-[11px] text-slate-400">kcal</span>
                </div>
              </div>

              <!-- Tiêu đề thực đơn -->
              <div>
                <h4 class="font-extrabold text-sm text-slate-800 line-clamp-2">${escapeMealText(opt.title)}</h4>
                <div class="flex items-center gap-2 text-[11px] text-slate-600 mt-1.5 flex-wrap">
                  <span class="px-2 py-0.5 rounded-lg bg-amber-50 text-amber-900 border border-amber-200/80 font-semibold flex items-center gap-1" title="Carbohydrate - Tinh bột nạp năng lượng">
                    <span>🌾</span> <span>C (Tinh bột):</span> <b class="font-bold text-slate-900">${opt.macros?.carbs || 0}g</b>
                  </span>
                  <span class="px-2 py-0.5 rounded-lg bg-rose-50 text-rose-900 border border-rose-200/80 font-semibold flex items-center gap-1" title="Protein - Đạm nuôi cơ và no lâu">
                    <span>🥩</span> <span>P (Đạm):</span> <b class="font-bold text-slate-900">${opt.macros?.protein || 0}g</b>
                  </span>
                  <span class="px-2 py-0.5 rounded-lg bg-emerald-50 text-emerald-900 border border-emerald-200/80 font-semibold flex items-center gap-1" title="Fat - Chất béo lành mạnh">
                    <span>🥑</span> <span>F (Chất béo):</span> <b class="font-bold text-slate-900">${opt.macros?.fat || 0}g</b>
                  </span>
                </div>
              </div>

              <div class="p-3.5 bg-slate-50/80 rounded-2xl border border-slate-100 space-y-2 text-xs">
                ${renderMealComponents(opt)}
              </div>

              <!-- ĐẶC TRƯNG TIÊU HÓA & LỜI KHUYÊN (YÊU CẦU 2 & 3) -->
              <div class="space-y-1">
                <div class="flex items-center gap-1.5 text-[11px] font-bold ${currentMealMode === 'lunch' ? 'text-amber-700' : 'text-teal-700'}">
                  <i data-lucide="${currentMealMode === 'lunch' ? 'zap' : 'shield-check'}" class="w-3.5 h-3.5 shrink-0"></i>
                  <span>${escapeMealText(opt.reason || opt.digestibility || 'Thực đơn theo khẩu phần tham khảo.')}</span>
                </div>
                <p class="text-[11px] text-slate-500 italic">
                  💡 ${escapeMealText(opt.nutritionNotes || 'Dinh dưỡng ước tính; đây là kế hoạch ăn.')}
                </p>
              </div>
            </div>

            <!-- Nút Chọn Thực Đơn -->
            <div class="pt-3 border-t border-slate-100">
              <button onclick="handleSelectMeal(${optNum})" class="w-full py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${isSelected ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/20' : 'bg-slate-900 hover:bg-slate-800 text-white'}">
                <i data-lucide="${isSelected ? 'check-check' : 'plus-circle'}" class="w-4 h-4"></i>
                <span>${isSelected ? 'Đang áp dụng thực đơn này' : `Chọn Lựa chọn ${optNum}`}</span>
              </button>
            </div>
          </div>
        `;
      }).join('');

      lucide.createIcons();
    }


    let mealToastTimeout = null;

    function hideMealToast() {
      clearTimeout(mealToastTimeout);
      mealToastTimeout = null;
      document.getElementById('toast-meal')?.classList.add('hidden');
    }

    function showMealToast(message, kind = 'success') {
      const toast = document.getElementById('toast-meal');
      if (!toast) return;
      hideMealToast();
      document.getElementById('toast-meal-message').textContent = message;
      toast.dataset.kind = kind;
      toast.setAttribute('role', kind === 'error' ? 'alert' : 'status');
      const icon = toast.querySelector('span');
      if (icon) icon.textContent = kind === 'error' ? '!' : '✓';
      toast.classList.remove('hidden');
      mealToastTimeout = setTimeout(hideMealToast, 4000);
    }

    async function handleMealError(result) {
      if (result.httpStatus === 401) return;
      if (result.code === 'STALE_MEAL') {
        await loadTodayMeals();
        await loadDashboardSummary();
        showMealToast('Thực đơn đã thay đổi. Đã tải lại dữ liệu mới nhất; hãy chọn lại.', 'error');
      } else if (result.code === 'MEAL_DECIDED') {
        showMealToast('Thực đơn đã chốt. Chọn Nghĩ sau trước khi làm mới.', 'error');
      } else {
        showMealToast(result.message || 'Không thể cập nhật thực đơn.', 'error');
      }
    }

    async function generateMealSuggestions(forceRefresh = false) {
      hideMealToast();
      const mode = currentMealMode;
      const meal = todayMealsCache[mode];
      const button = document.getElementById(forceRefresh ? 'btn-refresh-meals' : 'btn-generate-ai');
      if (button) button.disabled = true;
      try {
        const result = await NutriFitAPI.generateMeal(mode, forceRefresh, forceRefresh ? meal?.revision : null, readMealPreferences());
        if (!result.success) { await handleMealError(result); return; }
        todayMealsCache[mode] = result.data;
        renderCurrentMealMode();
        await loadDashboardSummary();
        showMealToast(result.meta?.cached
          ? 'Đã tải lại thực đơn của bạn!'
          : forceRefresh ? 'Đã cập nhật 3 thực đơn mới!' : 'Đã tạo 3 thực đơn cho bạn!');
      } finally {
        if (button) button.disabled = false;
      }
    }

    async function replaceMealSuggestions() {
      hideMealToast();
      const mode = currentMealMode;
      const meal = todayMealsCache[mode];
      if (!meal?.revision) { showMealToast('Hãy tạo hoặc tải thực đơn trước khi đổi món.', 'error'); return; }
      const text = document.getElementById('meal-replace-request').value.trim();
      if (!text) { showMealToast('Hãy nhập yêu cầu đổi món.', 'error'); return; }
      const button = document.getElementById('btn-replace-meal');
      button.disabled = true;
      try {
        const result = await NutriFitAPI.replaceMeal(mode, meal.revision, text, readMealPreferences());
        if (!result.success) { await handleMealError(result); return; }
        todayMealsCache[mode] = result.data;
        mealPreferences[mode] = result.meta?.applied_preferences || mealPreferences[mode];
        if (currentMealMode === mode) renderMealPreferences();
        renderCurrentMealMode();
        await loadDashboardSummary();
        showMealToast('Đã cập nhật 3 thực đơn mới!');
      } finally { button.disabled = false; }
    }

    async function selectMeal(selectedOption) {
      hideMealToast();
      const mode = currentMealMode;
      const meal = todayMealsCache[mode];
      if (!meal?.revision) { showMealToast('Hãy tạo hoặc tải thực đơn trước khi chọn.', 'error'); return; }
      const result = await NutriFitAPI.selectMealOption(mode, selectedOption, meal.revision);
      if (!result.success) { await handleMealError(result); return; }
      todayMealsCache[mode] = result.data;
      renderCurrentMealMode();
      await loadDashboardSummary();
      showMealToast(selectedOption === null
        ? 'Đã lưu lựa chọn Nghĩ sau!'
        : 'Đã chọn thực đơn thành công!');
    }

    async function handleSelectMeal(optionNum) { await selectMeal(optionNum); }
    async function handleThinkLater() { await selectMeal(null); }

    // MODAL LỊCH SỬ THỰC ĐƠN
    async function openMealHistoryModal() {
      const res = await NutriFitAPI.getMealHistory();
      if (!res.success) {
        if (res.httpStatus !== 401) showMealToast(res.message || 'Không thể tải lịch sử.', 'error');
        return;
      }
      const modal = document.getElementById('modal-history');
      const content = document.getElementById('modal-history-content');

      if (!res.history || res.history.length === 0) {
        content.innerHTML = `<div class="py-8 text-center text-slate-400 text-xs">Chưa có lịch sử thực đơn nào được lưu lại.</div>`;
      } else {
        content.innerHTML = res.history.map(item => {
          const isDecided = item.status === 'decided' && item.chosenMeal;
          return `
            <div class="p-4 rounded-2xl border border-slate-200 bg-slate-50 space-y-2 text-xs">
              <div class="flex items-center justify-between">
                <span class="font-extrabold text-slate-800">📅 ${escapeMealText(item.date)} • ${mealModes[item.mealType]?.icon || '🍽️'} ${escapeMealText(mealModes[item.mealType]?.label || item.mealType)}</span>
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${isDecided ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
                  ${isDecided ? `Đã chọn Option ${item.selectedOption}` : 'Chưa quyết định (Nghĩ sau)'}
                </span>
              </div>
              ${isDecided ? `
                <div class="bg-white p-3 rounded-xl border border-slate-100 space-y-1">
                  <p class="font-bold text-slate-800 text-sm">${escapeMealText(item.chosenMeal.title)} (${item.chosenMeal.calories} kcal)</p>
                  <p class="text-slate-500 text-[11px]">${mealComponents(item.chosenMeal).map(c => escapeMealText(c.name)).join(' • ')}</p>
                </div>
              ` : `
                <p class="text-slate-500 italic text-[11px]">Bạn đang để ở trạng thái chờ suy nghĩ thêm, 3 options ngày hôm đó vẫn được bảo toàn.</p>
              `}
            </div>
          `;
        }).join('');
      }

      modal.classList.remove('hidden');
      modal.classList.add('flex');
      lucide.createIcons();
    }

    function closeMealHistoryModal() {
      const modal = document.getElementById('modal-history');
      modal.classList.add('hidden');
      modal.classList.remove('flex');
    }
