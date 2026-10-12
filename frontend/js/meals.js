// NutriFit Frontend
// Extracted from the existing UI logic; behavior preserved.

    // ========================================================================
    // LOGIC GỢI Ý MÓN ĂN VIỆT NAM (GEMINI FLASH AI & NÚT THỨ 4 SUY NGHĨ)
    // ========================================================================
    let currentMealMode = 'lunch'; // 'lunch' hoặc 'dinner'
    let todayMealsCache = { lunch: null, dinner: null };

    // Tải thực đơn hôm nay khi mở Dashboard
    async function loadTodayMeals() {
      checkSavedApiKey();
      renderSingleMode();
      const res = await NutriFitAPI.getTodayMeals(userProfile.id || 1);
      if (res.success && res.todayMeals) {
        todayMealsCache = res.todayMeals;
        renderCurrentMealMode();
      }
    }

    // Chuyển đổi giữa Bữa Trưa (Ăn no) và Bữa Tối (Dễ tiêu)
    function switchMealMode(mode) {
      currentMealMode = mode;
      const btnLunch = document.getElementById('btn-mode-lunch');
      const btnDinner = document.getElementById('btn-mode-dinner');
      const bannerIcon = document.getElementById('meal-banner-icon');
      const bannerTitle = document.getElementById('meal-banner-title');
      const bannerDesc = document.getElementById('meal-banner-desc');
      const bannerKcal = document.getElementById('meal-banner-kcal');

      const targetKcal = Number(userProfile.targetKcal) || 1500;

      if (mode === 'lunch') {
        btnLunch.className = "px-4 py-1.5 text-xs font-bold rounded-lg bg-white text-slate-900 shadow-sm flex items-center gap-1.5 transition-all";
        btnDinner.className = "px-4 py-1.5 text-xs font-bold rounded-lg text-slate-500 hover:text-slate-900 flex items-center gap-1.5 transition-all";
        bannerIcon.innerText = "☀️";
        bannerTitle.innerText = "Chế độ: Bữa Trưa (Năng lượng dồi dào, ăn no làm việc chiều)";
        const lKcal = Math.round(targetKcal * 0.40);
        bannerKcal.innerText = `~${lKcal} kcal`;
        bannerDesc.innerHTML = `Định mức calo khuyến nghị: <b class="text-brand-600">~${lKcal} kcal</b> (38-42% calo ngày). 3 lựa chọn đa dạng nguồn đạm (Gia súc, Thủy hải sản, Gia cầm) & đổi vị tinh bột.`;
      } else {
        btnDinner.className = "px-4 py-1.5 text-xs font-bold rounded-lg bg-white text-slate-900 shadow-sm flex items-center gap-1.5 transition-all";
        btnLunch.className = "px-4 py-1.5 text-xs font-bold rounded-lg text-slate-500 hover:text-slate-900 flex items-center gap-1.5 transition-all";
        bannerIcon.innerText = "🌙";
        bannerTitle.innerText = "Chế độ: Bữa Tối (Thanh đạm, dễ tiêu hóa, tránh đầy bụng ban đêm)";
        const dKcal = Math.round(targetKcal * 0.30);
        bannerKcal.innerText = `~${dKcal} kcal`;
        bannerDesc.innerHTML = `Định mức calo khuyến nghị: <b class="text-teal-600">~${dKcal} kcal</b> (28-32% calo ngày). Món hấp/luộc, đạm dễ tiêu, canh thanh nhiệt giúp ngủ sâu giấc.`;
      }

      renderCurrentMealMode();
    }

    // Hiển thị dữ liệu thực đơn theo chế độ hiện tại
    function renderCurrentMealMode() {
      const mealData = todayMealsCache[currentMealMode];
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
            <h4 class="font-bold text-sm text-slate-700">Chưa có gợi ý thực đơn cho ${currentMealMode === 'lunch' ? 'Bữa trưa' : 'Bữa tối'}</h4>
            <p class="text-xs text-slate-400 max-w-md mx-auto">Nhấn nút <b>"Gợi ý 3 thực đơn ngay"</b> để AI Gemini phân tích thể trạng của bạn và đề xuất 3 thực đơn chuẩn vị Việt Nam.</p>
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
      btnGenText.innerText = `Làm mới 3 thực đơn`;
      boxThink.classList.remove('hidden');
      statusAlert.classList.remove('hidden');
      if (btnRefresh) btnRefresh.classList.remove('hidden');
      document.getElementById('meal-macro-legend')?.classList.remove('hidden');

      // Cập nhật trạng thái
      if (mealData.selectedOption) {
        statusAlert.className = "p-3 rounded-xl text-xs font-semibold flex items-center justify-between bg-emerald-50 text-emerald-800 border border-emerald-200";
        statusIcon.setAttribute('data-lucide', 'check-circle');
        statusText.innerHTML = `Bạn đã chốt lựa chọn <b>Option ${mealData.selectedOption}: ${mealData.options[mealData.selectedOption - 1]?.title}</b>`;
        statusBadge.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-200 text-emerald-900";
        statusBadge.innerText = "Đã chốt món";
      } else {
        statusAlert.className = "p-3 rounded-xl text-xs font-semibold flex items-center justify-between bg-amber-50 text-amber-800 border border-amber-200";
        statusIcon.setAttribute('data-lucide', 'hourglass');
        statusText.innerHTML = `Trạng thái: <b>Đang suy nghĩ / cân nhắc</b>. Hệ thống giữ nguyên 3 lựa chọn ban đầu cho bạn.`;
        statusBadge.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-200 text-amber-900";
        statusBadge.innerText = "Đang chờ";
      }

      // Render 3 Option Cards (Đủ 5 thành phần chuẩn Việt Nam)
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
                <h4 class="font-extrabold text-sm text-slate-800 line-clamp-2">${opt.title}</h4>
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

              <!-- KHUNG 5 THÀNH PHẦN CHUẨN GIA ĐÌNH VIỆT NAM (YÊU CẦU 1) -->
              <div class="p-3.5 bg-slate-50/80 rounded-2xl border border-slate-100 space-y-2 text-xs">
                <div class="flex items-start gap-2">
                  <span class="text-amber-600 font-bold shrink-0">🍚 Món chính:</span>
                  <span class="font-semibold text-slate-800">${opt.carb}</span>
                </div>
                <div class="flex items-start gap-2">
                  <span class="text-rose-600 font-bold shrink-0">🥩 Món mặn:</span>
                  <span class="font-semibold text-slate-800">${opt.protein}</span>
                </div>
                <div class="flex items-start gap-2">
                  <span class="text-blue-600 font-bold shrink-0">🥣 Món canh:</span>
                  <span class="font-semibold text-slate-800">${opt.soup}</span>
                </div>
                <div class="flex items-start gap-2">
                  <span class="text-emerald-600 font-bold shrink-0">🥗 Món rau:</span>
                  <span class="font-semibold text-slate-800">${opt.veggie}</span>
                </div>
                <div class="flex items-start gap-2">
                  <span class="text-yellow-600 font-bold shrink-0">🍌 Tráng miệng:</span>
                  <span class="font-semibold text-slate-800">${opt.dessert}</span>
                </div>
              </div>

              <!-- ĐẶC TRƯNG TIÊU HÓA & LỜI KHUYÊN (YÊU CẦU 2 & 3) -->
              <div class="space-y-1">
                <div class="flex items-center gap-1.5 text-[11px] font-bold ${currentMealMode === 'lunch' ? 'text-amber-700' : 'text-teal-700'}">
                  <i data-lucide="${currentMealMode === 'lunch' ? 'zap' : 'shield-check'}" class="w-3.5 h-3.5 shrink-0"></i>
                  <span>${opt.digestibility || (currentMealMode === 'lunch' ? 'Ăn no, năng lượng bền' : 'Dễ tiêu, thanh nhẹ bụng')}</span>
                </div>
                <p class="text-[11px] text-slate-500 italic">
                  💡 ${opt.nutritionNotes || 'Được chuyên gia dinh dưỡng cân đối tỉ lệ calo & vi chất.'}
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

    // ========================================================================
    // CHỨC NĂNG RIÊNG BIỆT: MÓN LẺ MUA NGOÀI QUÁN (ĐƯỜNG PHỐ & TIỆM CƠM)
    // ========================================================================
    let singleMealMode = 'lunch'; // 'lunch' | 'dinner'
    let singleMaxPrice = 0;
    let singlePriceError = false;
    let singlePriceErrorMessage = '';
    let singleCache = { lunch: null, dinner: null };
    let singleAiOrder = { lunch: null, dinner: null };
    let singleAiReasons = { lunch: [], dinner: [] };
    let singleAiPoolKey = { lunch: '', dinner: '' };
    let singleSuggestOffset = { lunch: 0, dinner: 0 };

    function singleFmtPrice(v) {
      const n = Number(v) || 0;
      return n > 0 ? `${n.toLocaleString('vi-VN')}đ` : 'chưa rõ giá';
    }

    function openNearbyMap(title) {
      if (!title) return;
      const q = encodeURIComponent(`${title} gần đây`);
      window.open(`https://www.google.com/maps/search/?api=1&query=${q}`, '_blank', 'noopener');
    }

    // Ràng buộc logic chặt chẽ khi nhập ngân sách tối đa
    function handleSinglePriceInput(rawVal) {
      const inputEl = document.getElementById('single-max-price-input');
      const hintEl = document.getElementById('single-price-hint');
      if (!inputEl || !hintEl) return;

      const trimmed = String(rawVal ?? '').trim();

      // Trường hợp để trống: không giới hạn ngân sách
      if (trimmed === '') {
        singleMaxPrice = 0;
        singlePriceError = false;
        singlePriceErrorMessage = '';
        inputEl.className = "w-48 pl-7 pr-3 py-2 border border-slate-200 rounded-xl text-xs font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-500 transition-all";
        hintEl.className = "text-[11px] font-semibold text-slate-400 mt-1 pl-1";
        hintEl.innerHTML = "Không giới hạn ngân sách";
        return;
      }

      // Kiểm tra ký tự âm hoặc chữ/ký tự lạ
      if (trimmed.includes('-') || !/^\d+$/.test(trimmed)) {
        setSinglePriceInvalid(inputEl, hintEl, "Số tiền không được là số âm hoặc chứa ký tự đặc biệt");
        return;
      }

      const val = parseInt(trimmed, 10);

      if (isNaN(val) || val <= 0) {
        setSinglePriceInvalid(inputEl, hintEl, "Vui lòng nhập số tiền lớn hơn 0");
        return;
      }

      if (val < 10000) {
        setSinglePriceInvalid(inputEl, hintEl, "Mức giá tối thiểu 10.000đ/phần cho món mua ngoài thực tế");
        return;
      }

      if (val > 500000) {
        setSinglePriceInvalid(inputEl, hintEl, "Ngân sách tối đa cho một phần ăn là 500.000đ");
        return;
      }

      // Hợp lệ
      singleMaxPrice = val;
      singlePriceError = false;
      singlePriceErrorMessage = '';
      inputEl.className = "w-48 pl-7 pr-3 py-2 border border-emerald-400 bg-emerald-50/30 rounded-xl text-xs font-bold text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 transition-all";
      hintEl.className = "text-[11px] font-bold text-emerald-600 mt-1 pl-1";
      hintEl.innerHTML = `✓ Giới hạn: ≤ ${val.toLocaleString('vi-VN')}đ/phần`;
    }

    function setSinglePriceInvalid(inputEl, hintEl, msg) {
      singlePriceError = true;
      singlePriceErrorMessage = msg;
      inputEl.className = "w-48 pl-7 pr-3 py-2 border border-rose-500 bg-rose-50/50 rounded-xl text-xs font-bold text-rose-600 focus:outline-none focus:ring-2 focus:ring-rose-500 transition-all";
      hintEl.className = "text-[11px] font-bold text-rose-500 mt-1 pl-1";
      hintEl.innerHTML = `⚠️ ${msg}`;
    }

    function clearSinglePriceFilter() {
      const inputEl = document.getElementById('single-max-price-input');
      if (inputEl) inputEl.value = '';
      handleSinglePriceInput('');
      renderSingleMode();
    }

    function switchSingleMealMode(mode) {
      singleMealMode = mode;
      const btnLunch = document.getElementById('btn-single-mode-lunch');
      const btnDinner = document.getElementById('btn-single-mode-dinner');
      const icon = document.getElementById('single-banner-icon');
      const title = document.getElementById('single-banner-title');
      const desc = document.getElementById('single-banner-desc');
      const kcal = document.getElementById('single-banner-kcal');
      const targetKcal = Number(userProfile.targetKcal) || 1500;

      if (mode === 'lunch') {
        if (btnLunch) btnLunch.className = "px-4 py-1.5 text-xs font-bold rounded-lg bg-white text-slate-900 shadow-sm flex items-center gap-1.5 transition-all";
        if (btnDinner) btnDinner.className = "px-4 py-1.5 text-xs font-bold rounded-lg text-slate-500 hover:text-slate-900 flex items-center gap-1.5 transition-all";
        if (icon) icon.innerText = "☀️";
        if (title) title.innerText = "Chế độ: Bữa Trưa (Món nhanh, năng lượng dồi dào)";
        const lKcal = Math.round(targetKcal * 0.40);
        if (kcal) kcal.innerText = `~${lKcal} kcal`;
        if (desc) desc.innerHTML = `Định mức calo khuyến nghị: <b id="single-banner-kcal" class="text-amber-600">~${lKcal} kcal</b> (38-42% calo ngày). Món mua ngoài giàu đạm & tinh bột bền để làm việc chiều.`;
      } else {
        if (btnDinner) btnDinner.className = "px-4 py-1.5 text-xs font-bold rounded-lg bg-white text-slate-900 shadow-sm flex items-center gap-1.5 transition-all";
        if (btnLunch) btnLunch.className = "px-4 py-1.5 text-xs font-bold rounded-lg text-slate-500 hover:text-slate-900 flex items-center gap-1.5 transition-all";
        if (icon) icon.innerText = "🌙";
        if (title) title.innerText = "Chế độ: Bữa Tối (Dễ tiêu, thanh đạm, tránh đầy bụng)";
        const dKcal = Math.round(targetKcal * 0.30);
        if (kcal) kcal.innerText = `~${dKcal} kcal`;
        if (desc) desc.innerHTML = `Định mức calo khuyến nghị: <b id="single-banner-kcal" class="text-teal-600">~${dKcal} kcal</b> (28-32% calo ngày). Món thanh nhẹ, ít dầu mỡ giúp ngủ sâu giấc.`;
      }

      renderSingleMode();
    }

    function singleEnrich(m) {
      const targetKcal = Number(userProfile.targetKcal) || 1500;
      const cal = Math.round(targetKcal * (m.cal_pct || 0.40));
      return Object.assign({}, m, {
        calories: cal,
        macros: {
          carbs: Math.round((cal * 0.50) / 4),
          protein: Math.round((cal * 0.25) / 4),
          fat: Math.round((cal * 0.25) / 9)
        }
      });
    }

    function singlePool(mealMode) {
      const mm = mealMode || singleMealMode;
      if (typeof MS_SINGLE_DISHES === 'undefined') return [];
      let list = MS_SINGLE_DISHES.map((m) => singleEnrich(m))
        .filter((m) => m.mealType === mm || m.mealType === 'all');
      if (singleMaxPrice > 0) {
        list = list.filter((m) => Number(m.price || 0) > 0 && Number(m.price) <= singleMaxPrice);
      }
      list.sort((a, b) => (a.price || 0) - (b.price || 0) || a.calories - b.calories);
      return list;
    }

    function renderSingleMode() {
      const data = singleCache[singleMealMode];
      const container = document.getElementById('single-dishes-container');
      const boxThink = document.getElementById('box-single-think-later');
      const statusAlert = document.getElementById('single-status-alert');
      const statusText = document.getElementById('single-status-text');
      const statusBadge = document.getElementById('single-status-badge');
      const statusIcon = document.getElementById('single-status-icon');
      const btnGenText = document.getElementById('btn-single-generate-text');
      const btnRefresh = document.getElementById('btn-single-refresh');
      const macroLegend = document.getElementById('single-macro-legend');
      const mealName = singleMealMode === 'lunch' ? 'Bữa trưa' : 'Bữa tối';

      if (!container) return;

      if (!data || !data.options || data.options.length === 0) {
        container.innerHTML = `
          <div class="col-span-full py-12 text-center bg-slate-50 border border-dashed border-slate-200 rounded-3xl space-y-3">
            <span class="w-12 h-12 rounded-2xl bg-amber-100 text-amber-600 inline-flex items-center justify-center text-2xl">🍢</span>
            <h4 class="font-bold text-sm text-slate-700">Chưa có gợi ý món mua ngoài cho ${mealName} hôm nay</h4>
            <p class="text-xs text-slate-400 max-w-md mx-auto">
              ${singleMaxPrice > 0 ? `Ngân sách hiện tại: ≤ ${singleFmtPrice(singleMaxPrice)}/phần.` : 'Món lẻ lọc theo giá tiền + calo, tiện lợi khi ăn ngoài.'}
              Nhấn nút <b>"Gợi ý 3 món mua ngoài"</b> để xem danh sách món phù hợp.
            </p>
            <button onclick="generateSingleSuggestions(false)" class="px-5 py-2.5 bg-amber-500 hover:bg-amber-600 text-white font-bold rounded-xl text-xs shadow-sm">
              Khám phá món mua ngoài ngay
            </button>
          </div>`;
        if (boxThink) boxThink.classList.add('hidden');
        if (statusAlert) statusAlert.classList.add('hidden');
        if (btnRefresh) btnRefresh.classList.add('hidden');
        if (macroLegend) macroLegend.classList.add('hidden');
        if (btnGenText) btnGenText.innerText = 'Gợi ý 3 món mua ngoài';
        lucide.createIcons();
        return;
      }

      if (btnGenText) btnGenText.innerText = 'Đổi 3 món khác';
      if (boxThink) boxThink.classList.remove('hidden');
      if (statusAlert) statusAlert.classList.remove('hidden');
      if (btnRefresh) btnRefresh.classList.remove('hidden');
      if (macroLegend) macroLegend.classList.remove('hidden');

      if (data.selectedOption) {
        const chosen = data.options[data.selectedOption - 1];
        statusAlert.className = "p-3 rounded-xl text-xs font-semibold flex items-center justify-between bg-emerald-50 text-emerald-800 border border-emerald-200";
        statusIcon.setAttribute('data-lucide', 'check-circle');
        statusText.innerHTML = `Bạn đã chốt món mua ngoài <b>Lựa chọn ${data.selectedOption}${chosen ? ': ' + chosen.title : ''}</b>`;
        statusBadge.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-200 text-emerald-900";
        statusBadge.innerText = "Đã chốt món";
      } else {
        statusAlert.className = "p-3 rounded-xl text-xs font-semibold flex items-center justify-between bg-amber-50 text-amber-800 border border-amber-200";
        statusIcon.setAttribute('data-lucide', 'hourglass');
        statusText.innerHTML = `Trạng thái: <b>Đang suy nghĩ / cân nhắc</b>. Hệ thống giữ nguyên danh sách 3 món gợi ý cho bạn.`;
        statusBadge.className = "px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-200 text-amber-900";
        statusBadge.innerText = "Đang chờ";
      }

      container.innerHTML = data.options.map((opt, index) => {
        const optNum = index + 1;
        const isSelected = data.selectedOption === optNum;
        let tagColor = "bg-amber-50 text-amber-700 border-amber-200";
        if (optNum === 2) tagColor = "bg-blue-50 text-blue-700 border-blue-200";
        if (optNum === 3) tagColor = "bg-purple-50 text-purple-700 border-purple-200";

        return `
          <div class="border-2 ${isSelected ? 'border-amber-500 ring-4 ring-amber-500/10 shadow-lg' : 'border-slate-200 hover:border-amber-400'} rounded-3xl p-5 bg-white flex flex-col justify-between space-y-4 transition-all relative">
            ${isSelected ? '<span class="absolute -top-3 right-4 bg-amber-500 text-white text-[10px] font-black px-3 py-0.5 rounded-full shadow-sm flex items-center gap-1"><i data-lucide="check" class="w-3 h-3"></i> Đã chọn món này</span>' : ''}
            <div class="space-y-3.5">
              <div class="flex items-center justify-between gap-2">
                <span class="text-[11px] font-extrabold uppercase px-2.5 py-0.5 rounded-lg border ${tagColor}">
                  Lựa chọn ${optNum}
                </span>
                <div class="text-right">
                  <span class="text-base font-black text-slate-800">${opt.calories}</span>
                  <span class="text-[11px] text-slate-400">kcal</span>
                </div>
              </div>
              <div>
                <h4 class="font-extrabold text-sm text-slate-800 line-clamp-2">${opt.title}</h4>
                ${opt.price ? `<div class="mt-1.5 text-[11px] font-bold text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2 py-1 w-fit">💰 Giá tham khảo: ${singleFmtPrice(opt.price)}/phần</div>` : ''}
                <div class="flex items-center gap-2 text-[11px] text-slate-600 mt-1.5 flex-wrap">
                  <span class="px-2 py-0.5 rounded-lg bg-amber-50 text-amber-900 border border-amber-200/80 font-semibold">🌾 C: <b class="font-bold text-slate-900">${opt.macros?.carbs || 0}g</b></span>
                  <span class="px-2 py-0.5 rounded-lg bg-rose-50 text-rose-900 border border-rose-200/80 font-semibold">🥩 P: <b class="font-bold text-slate-900">${opt.macros?.protein || 0}g</b></span>
                  <span class="px-2 py-0.5 rounded-lg bg-emerald-50 text-emerald-900 border border-emerald-200/80 font-semibold">🥑 F: <b class="font-bold text-slate-900">${opt.macros?.fat || 0}g</b></span>
                </div>
              </div>
              <div class="p-3.5 bg-slate-50/80 rounded-2xl border border-slate-100 space-y-2 text-xs">
                <div class="flex items-start gap-2"><span class="text-rose-600 font-bold shrink-0">🍖 Có gì:</span><span class="font-semibold text-slate-800">${opt.protein || '—'}</span></div>
                <div class="flex items-start gap-2"><span class="text-amber-600 font-bold shrink-0">🍚 Tinh bột:</span><span class="font-semibold text-slate-800">${opt.carb || '—'}</span></div>
                <div class="flex items-start gap-2"><span class="text-blue-600 font-bold shrink-0">🥣 Nước chấm/dùng:</span><span class="font-semibold text-slate-800">${opt.soup || '—'}</span></div>
                <div class="flex items-start gap-2"><span class="text-emerald-600 font-bold shrink-0">🥗 Ăn kèm:</span><span class="font-semibold text-slate-800">${opt.veggie || '—'}</span></div>
              </div>
              <p class="text-[11px] text-slate-500 italic">💡 ${opt.nutritionNotes || 'Món mua ngoài quán, nhớ ăn kèm rau.'}</p>
              ${opt.aiReason ? `<p class="text-[11px] font-semibold text-violet-700 bg-violet-50 border border-violet-200 rounded-lg px-2 py-1">✨ AI gợi ý: ${opt.aiReason}</p>` : ''}
            </div>
            <div class="pt-3 border-t border-slate-100 space-y-2">
              <button onclick="openNearbyMap('${String(opt.title || '').replace(/'/g, "\\'")}')" class="w-full py-2 rounded-xl text-xs font-bold bg-blue-50 border border-blue-200 text-blue-700 hover:bg-blue-100 transition-all flex items-center justify-center gap-1.5"><i data-lucide="map-pin" class="w-3.5 h-3.5"></i> Quán gần nhất</button>
              <button onclick="handleSelectSingle(${optNum})" class="w-full py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${isSelected ? 'bg-amber-600 text-white shadow-md shadow-amber-600/20' : 'bg-slate-900 hover:bg-slate-800 text-white'}">
                <i data-lucide="${isSelected ? 'check-check' : 'plus-circle'}" class="w-4 h-4"></i>
                <span>${isSelected ? 'Đang áp dụng món này' : `Chọn Lựa chọn ${optNum}`}</span>
              </button>
            </div>
          </div>`;
      }).join('');

      lucide.createIcons();
    }

    async function generateSingleSuggestions(forceRefresh = false) {
      if (singlePriceError) {
        showToast('Ngân sách không hợp lệ', singlePriceErrorMessage || 'Vui lòng kiểm tra lại số tiền nhập vào');
        const inputEl = document.getElementById('single-max-price-input');
        if (inputEl) inputEl.focus();
        return;
      }

      if (typeof MS_SINGLE_DISHES === 'undefined') {
        alert('Chưa tải được kho món lẻ (meal-suggest/single-dishes.js) — kiểm tra kết nối file.');
        return;
      }

      const btn = forceRefresh ? document.getElementById('btn-single-refresh') : document.getElementById('btn-single-generate');
      const origText = btn ? btn.innerHTML : '';
      if (btn) {
        btn.innerHTML = `<i data-lucide="loader" class="w-4 h-4 animate-spin"></i><span>${forceRefresh ? 'Đang đổi món...' : 'AI đang chọn món...'}</span>`;
        lucide.createIcons();
      }

      try {
        const pool = singlePool(singleMealMode);
        if (pool.length === 0) {
          singleCache[singleMealMode] = { options: [], selectedOption: null, status: 'pending' };
          renderSingleMode();
          alert(singleMaxPrice > 0
            ? `Không có món mua ngoài nào dưới ${singleFmtPrice(singleMaxPrice)}/phần cho bữa này. Vui lòng tăng ngân sách.`
            : 'Không có món mua ngoài nào khớp bộ lọc hiện tại.');
          return;
        }

        const key = localStorage.getItem('nutrifit_gemini_key') || '';
        const poolKey = `${pool.length}:${singleMaxPrice}:${pool.map((m) => m.title).join('|')}`;
        let order;

        if (!forceRefresh || !singleAiOrder[singleMealMode] || singleAiPoolKey[singleMealMode] !== poolKey) {
          const ranked = (typeof MS_AI_RANK !== 'undefined')
            ? await MS_AI_RANK.rank(pool.map((opt) => ({ opt })), singleMealMode, [], key, { dishMode: 'single', maxPrice: singleMaxPrice })
            : { order: pool.map((_, i) => i), reasons: [], source: 'expert' };
          order = ranked.order;
          singleAiOrder[singleMealMode] = order;
          singleAiReasons[singleMealMode] = ranked.reasons || [];
          singleAiPoolKey[singleMealMode] = poolKey;
          singleSuggestOffset[singleMealMode] = 0;
        } else {
          order = singleAiOrder[singleMealMode];
        }

        if (!Array.isArray(order) || order.length !== pool.length) {
          order = pool.map((_, i) => i);
          singleAiOrder[singleMealMode] = order;
          singleAiPoolKey[singleMealMode] = poolKey;
          singleSuggestOffset[singleMealMode] = 0;
        }

        let off = singleSuggestOffset[singleMealMode] || 0;
        off = pool.length > 0 ? off % pool.length : 0;
        const n = Math.min(3, pool.length);
        const three = [];
        for (let i = 0; i < n; i++) {
          const pos = order[(off + i) % order.length];
          const opt = Object.assign({}, pool[pos], { id: i + 1 });
          const reason = (singleAiReasons[singleMealMode] || [])[(off + i) % order.length] || '';
          if (reason) opt.aiReason = reason;
          three.push(opt);
        }
        singleSuggestOffset[singleMealMode] = pool.length > 0 ? (off + n) % pool.length : 0;
        singleCache[singleMealMode] = { options: three, selectedOption: null, status: 'pending' };
        renderSingleMode();
        showToast(pool.length <= 3
          ? `Hiển thị tất cả ${pool.length} món mua ngoài cho ${singleMealMode === 'lunch' ? 'trưa' : 'tối'}`
          : `Đã gợi ý 3 món mua ngoài (bấm tiếp "Đổi món khác" để xem tiếp)`,
          singleMaxPrice > 0 ? `Ngân sách ≤ ${singleFmtPrice(singleMaxPrice)}/phần` : 'Ưu tiên món cân bằng dinh dưỡng');
      } finally {
        if (btn) {
          btn.innerHTML = origText;
          lucide.createIcons();
        }
      }
    }

    function handleSelectSingle(optionNum) {
      const data = singleCache[singleMealMode];
      if (!data || !data.options || !data.options[optionNum - 1]) return;
      data.selectedOption = optionNum;
      data.status = 'decided';
      renderSingleMode();
      const title = data.options[optionNum - 1] ? data.options[optionNum - 1].title : '';
      showToast(`Đã chọn món mua ngoài Lựa chọn ${optionNum}`, title ? `${title} — đang mở Google Maps tìm quán gần nhất...` : '');
      openNearbyMap(title);
    }

    function handleSingleThinkLater() {
      const data = singleCache[singleMealMode];
      if (!data) return;
      data.selectedOption = null;
      data.status = 'pending';
      renderSingleMode();
      showToast('Đang suy nghĩ thêm', '3 món gợi ý mua ngoài vẫn được bảo toàn.');
    }

    // ========================================================================
    // GỢI Ý THỰC ĐƠN BỮA ĂN (KẾT NỐI BACKEND & CSDL SQL SERVER)
    // ========================================================================
    // GỌI AI GEMINI SINH MÓN
    async function generateMealSuggestions(forceRefresh = false) {
      const btn = forceRefresh ? document.getElementById('btn-refresh-meals') : document.getElementById('btn-generate-ai');
      const originalText = btn ? btn.innerHTML : '';
      if (btn) {
        btn.innerHTML = `<i data-lucide="loader" class="w-4 h-4 animate-spin"></i><span>${forceRefresh ? 'Đang đổi món...' : 'AI đang lên thực đơn...'}</span>`;
        lucide.createIcons();
      }

      const apiKey = localStorage.getItem('nutrifit_gemini_key') || '';

      const res = await NutriFitAPI.generateMeal(userProfile.id || 1, currentMealMode, apiKey, forceRefresh);
      if (btn) {
        btn.innerHTML = originalText;
        lucide.createIcons();
      }

      if (res.success && res.data) {
        todayMealsCache[currentMealMode] = res.data;
        renderCurrentMealMode();
        if (forceRefresh) {
          showToast("Đã đổi thực đơn mới!", "Đã cập nhật 3 gợi ý thực đơn mới cho bữa này.");
        }
      } else {
        alert("Lỗi: " + (res.message || "Không thể sinh thực đơn lúc này."));
      }
    }

    // CHỌN OPTION (1, 2 hoặc 3)
    async function handleSelectMeal(optionNum) {
      const res = await NutriFitAPI.selectMealOption(userProfile.id || 1, currentMealMode, optionNum);
      if (res.success) {
        if (!todayMealsCache[currentMealMode]) todayMealsCache[currentMealMode] = {};
        todayMealsCache[currentMealMode].selectedOption = optionNum;
        todayMealsCache[currentMealMode].status = 'decided';
        renderCurrentMealMode();
      }
    }

    // NÚT THỨ 4: ĐỂ TÔI SUY NGHĨ / QUYẾT ĐỊNH SAU
    async function handleThinkLater() {
      const btn = document.getElementById('btn-think-later');
      const originalHtml = btn.innerHTML;
      btn.innerHTML = `<i data-lucide="loader" class="w-4 h-4 animate-spin"></i><span>Đang lưu...</span>`;
      lucide.createIcons();

      const res = await NutriFitAPI.selectMealOption(userProfile.id || 1, currentMealMode, null);
      btn.innerHTML = originalHtml;
      lucide.createIcons();

      if (res.success) {
        if (!todayMealsCache[currentMealMode]) todayMealsCache[currentMealMode] = {};
        todayMealsCache[currentMealMode].selectedOption = null;
        todayMealsCache[currentMealMode].status = 'pending';
        renderCurrentMealMode();
        alert("Đã lưu trạng thái: 'Đang cân nhắc'. 3 lựa chọn ban đầu vẫn được giữ nguyên đầy đủ để bạn quay lại chọn sau nhé!");
      }
    }

    // CẤU HÌNH GEMINI API KEY
    function openApiKeyModal() {
      const currentKey = localStorage.getItem('nutrifit_gemini_key') || '';
      const input = prompt("Nhập Google Gemini API Key của bạn (bỏ trống nếu muốn dùng bộ đề xuất chuyên gia):", currentKey);
      if (input !== null) {
        localStorage.setItem('nutrifit_gemini_key', input.trim());
        checkSavedApiKey();
        alert(input.trim() ? "Đã lưu Gemini API Key!" : "Đã chuyển sang chế độ Chuyên gia Dinh dưỡng NutriFit.");
      }
    }

    function checkSavedApiKey() {
      const key = localStorage.getItem('nutrifit_gemini_key');
      const badge = document.getElementById('gemini-key-status');
      if (badge) {
        badge.innerText = key ? "Gemini Key (Active)" : "API Key";
      }
    }

    // MODAL LỊCH SỬ THỰC ĐƠN
    async function openMealHistoryModal() {
      const res = await NutriFitAPI.getMealHistory(userProfile.id || 1);
      const modal = document.getElementById('modal-history');
      const content = document.getElementById('modal-history-content');

      if (!res.success || !res.history || res.history.length === 0) {
        content.innerHTML = `<div class="py-8 text-center text-slate-400 text-xs">Chưa có lịch sử thực đơn nào được lưu lại.</div>`;
      } else {
        content.innerHTML = res.history.map(item => {
          const isDecided = item.status === 'decided' && item.chosenMeal;
          return `
            <div class="p-4 rounded-2xl border border-slate-200 bg-slate-50 space-y-2 text-xs">
              <div class="flex items-center justify-between">
                <span class="font-extrabold text-slate-800">📅 ${item.date} • ${item.mealType === 'lunch' ? '☀️ Bữa trưa' : '🌙 Bữa tối'}</span>
                <span class="px-2 py-0.5 rounded-full text-[10px] font-bold ${isDecided ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}">
                  ${isDecided ? `Đã chọn Option ${item.selectedOption}` : 'Chưa quyết định (Nghĩ sau)'}
                </span>
              </div>
              ${isDecided ? `
                <div class="bg-white p-3 rounded-xl border border-slate-100 space-y-1">
                  <p class="font-bold text-slate-800 text-sm">${item.chosenMeal.title} (${item.chosenMeal.calories} kcal)</p>
                  <p class="text-slate-500 text-[11px]">🍚 ${item.chosenMeal.carb} • 🥩 ${item.chosenMeal.protein} • 🥣 ${item.chosenMeal.soup} • 🥗 ${item.chosenMeal.veggie} • 🍌 ${item.chosenMeal.dessert}</p>
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
