// NutriFit Frontend
// Extracted from the existing UI logic; behavior preserved.

    // ========================================================================
    // LOGIC GỢI Ý MÓN ĂN VIỆT NAM (GEMINI FLASH AI & NÚT THỨ 4 SUY NGHĨ)
    // ========================================================================
    let currentMealMode = 'lunch';
    let todayMealsCache = { breakfast: null, lunch: null, dinner: null };
    let mealPreferences = { breakfast: {}, lunch: {}, dinner: {} };
    let mealTargets = {};
    let mealLoadSequence = 0;
    const mealPending = { breakfast: null, lunch: null, dinner: null };
    const mealModes = {
      breakfast: { label: 'Bữa sáng', icon: '🌅', description: 'Nhanh gọn, món nước hoặc cân bằng.' },
      lunch: { label: 'Bữa trưa', icon: '☀️', description: 'Thực đơn đa dạng nguồn đạm và rau.' },
      dinner: { label: 'Bữa tối', icon: '🌙', description: 'Ưu tiên món hấp/luộc, ít dầu.' }
    };
    const mealFoodLabels = { fish: 'cá', seafood: 'hải sản', egg: 'trứng', milk: 'sữa', chicken: 'gà', beef: 'bò', pork: 'heo', soy: 'đậu phụ', wheat: 'bánh mì', oats: 'yến mạch', rice: 'cơm', noodles: 'bún', banana: 'chuối', sweet_potato: 'khoai lang' };
    Object.assign(mealFoodLabels, { peanut: 'đậu phộng', sesame: 'mè', garlic: 'tỏi', mushroom: 'nấm', tomato: 'cà chua', onion: 'hành tây', shallot: 'hành tím', scallion: 'hành lá', ginger: 'gừng', lemongrass: 'sả', fish_sauce: 'nước mắm', soy_sauce: 'nước tương', oyster_sauce: 'dầu hào', muong: 'rau muống', ngot: 'rau ngót', corn: 'ngô', crab: 'cua', oil: 'dầu ăn', turmeric: 'nghệ' });
    function escapeMealText(value) {
      return String(value ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
    }
    function mealDisplayText(value) {
      return String(value ?? '').replace(/\bV[34]\b/gi, 'đã lưu').replace(/catalog/gi, 'danh sách món').replace(/revision/gi, 'thông tin thực đơn').replace(/fallback/gi, 'dự phòng');
    }
    function mealUserMessage(result, defaultMessage = 'Chưa thể hoàn tất. Vui lòng thử lại.') {
      const messages = {
        DATABASE_ERROR: 'Không thể cập nhật thực đơn lúc này. Vui lòng thử lại.',
        V4_MIGRATION_REQUIRED: 'Chức năng này chưa sẵn sàng. Vui lòng thử lại sau.',
        V4_REFRESH_REQUIRED: 'Bạn đang có thực đơn đã lưu. Nhấn Đổi thực đơn để nhận gợi ý mới; nếu đã chốt, hãy chọn Nghĩ sau trước.',
        LEGACY_COMPONENT_NUTRITION_REQUIRED: 'Thực đơn đã lưu chưa hỗ trợ đổi từng món. Hãy tạo thực đơn mới.',
        STALE_INTAKE: 'Bữa ăn đã thay đổi. Hãy mở lại từ Lịch sử trước khi chỉnh sửa.',
        INTAKE_DELETED: 'Bữa ăn này đã được xóa. Hãy kiểm tra Lịch sử.',
        IDEMPOTENCY_CONFLICT: 'Lần ghi nhận này đã có nội dung khác. Hãy kiểm tra Lịch sử.',
        UNKNOWN_DISH: 'Món này chưa có dữ liệu dinh dưỡng. Hãy chọn món khác.',
        FOOD_CATALOG_MIGRATION_REQUIRED: 'Kho món ăn đang được cập nhật. Vui lòng thử lại sau.'
      };
      return messages[result.code] || mealDisplayText(result.isOffline ? 'Không thể kết nối. Hãy thử lại.' : result.message || defaultMessage);
    }
    function mealComponents(option) {
      if (Array.isArray(option.components) && option.components.length) return option.components;
      return ['carb', 'protein', 'soup', 'veggie', 'dessert'].filter(key => option[key]).map(key => ({ type: key.toUpperCase(), name: option[key] }));
    }
    function renderMealComponents(option) {
      const labels = { MAIN: '🍽️ Món chính', SIDE: '🥗 Ăn kèm', DRINK: '🥛 Đồ uống', CARB: '🍚 Tinh bột', PROTEIN: '🥩 Món mặn', SOUP: '🥣 Canh', VEGGIE: '🥗 Rau', DESSERT: '🍌 Tráng miệng' };
      return mealComponents(option).map(c => {
        const action = 'openV4ComponentPicker(' + Number(option.optionId) + ', ' + JSON.stringify(c.type) + ')';
        const swap = option.recipe ? '<button type="button" onclick="' + escapeMealText(action) + '" class="text-brand-600 text-xs font-bold shrink-0">Đổi món</button>' : '';
        return '<div class="flex items-start gap-2"><span class="text-emerald-700 font-bold shrink-0">' + (labels[c.type] || '🍽️ Thành phần') + ':</span><span class="font-semibold text-slate-800 flex-1">' + escapeMealText(c.name) + (c.grams ? ' · ' + escapeMealText(c.grams) + ' g' : '') + '</span>' + swap + '</div>';
      }).join('');
    }
    function supportedMealPreferences(value = {}) {
      return Object.fromEntries(['avoid', 'dislikes', 'prefer'].filter(key => Array.isArray(value[key])).map(key => [key, [...value[key]]]));
    }
    function readMealPreferences() {
      const terms = id => document.getElementById(id).value.split(',').map(v => v.trim()).filter(Boolean);
      // Form inputs are a draft; only a confirmed API response updates saved preferences.
      return { avoid: terms('meal-avoid'), dislikes: terms('meal-dislikes'), prefer: terms('meal-prefer') };
    }
    function renderMealPreferences() {
      const p = supportedMealPreferences(mealPreferences[currentMealMode]);
      const label = list => (list || []).map(v => mealFoodLabels[v] || v).join(', ');
      document.getElementById('meal-avoid').value = label(p.avoid);
      document.getElementById('meal-dislikes').value = label(p.dislikes);
      document.getElementById('meal-prefer').value = label(p.prefer);
    }

    // Tải thực đơn hôm nay khi mở Dashboard
    async function loadTodayMeals(allowPending = false) {
      const uid = userProfile.id, cache = todayMealsCache;
      if (!uid || (!allowPending && Object.values(mealPending).some(p => p?.uid === uid && p.cache === cache))) return;
      const sequence = ++mealLoadSequence;
      const res = await NutriFitAPI.getTodayMeals();
      if (uid !== userProfile.id || sequence !== mealLoadSequence || cache !== todayMealsCache) return;
      if (res.success && res.todayMeals) {
        todayMealsCache = res.todayMeals;
        if (typeof restoreV4Preferences === 'function') restoreV4Preferences();
        renderCurrentMealMode();
        return true;
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
      if (source) source.textContent = mealData?.catalog_refresh_required ? 'Danh sách món đã cập nhật. Chọn Nghĩ sau nếu đã chốt, rồi Đổi thực đơn; lịch sử cũ vẫn được giữ.' : mealData ? 'Dinh dưỡng ước tính theo khẩu phần' : '';
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
        updateMealLoading();
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
        statusText.innerHTML = `<b>Chưa chọn thực đơn.</b> Bạn có thể chọn một lựa chọn hoặc đổi bộ gợi ý.`;
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
                  <span>${escapeMealText(mealDisplayText(opt.reason || opt.digestibility || 'Thực đơn theo khẩu phần tham khảo.'))}</span>
                </div>
                <p class="text-[11px] text-slate-500 italic">
                  💡 ${escapeMealText(opt.nutritionNotes || 'Dinh dưỡng ước tính; đây là kế hoạch ăn.')}
                </p>
              </div>
            </div>

            <!-- Nút Chọn Thực Đơn -->
            <div class="pt-3 border-t border-slate-100">
              <button data-meal-select onclick="handleSelectMeal(${optNum})" class="w-full py-2.5 rounded-xl text-xs font-bold transition-all flex items-center justify-center gap-1.5 ${isSelected ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/20' : 'bg-slate-900 hover:bg-slate-800 text-white'}">
                <i data-lucide="${isSelected ? 'check-check' : 'plus-circle'}" class="w-4 h-4"></i>
                <span>${isSelected ? 'Đang áp dụng thực đơn này' : `Chọn Lựa chọn ${optNum}`}</span>
              </button>
              <button type="button" onclick="openV4IntakeForMeal(${Number(opt.optionId)})" class="w-full mt-2 py-2.5 rounded-xl text-xs font-semibold bg-emerald-50 text-emerald-700">Ghi nhận đã ăn</button>
            </div>
          </div>
        `;
      }).join('');

      updateMealLoading();
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
      if (icon) icon.textContent = kind === 'error' ? '!' : kind === 'info' ? 'ℹ' : '✓';
      toast.classList.remove('hidden');
      mealToastTimeout = setTimeout(hideMealToast, 4000);
    }

    async function handleMealError(result) {
      if (result.httpStatus === 401) return;
      if (result.code === 'STALE_MEAL') {
        if (!await loadTodayMeals(true)) return;
        const uid = userProfile.id, cache = todayMealsCache;
        await loadDashboardSummary();
        if (uid !== userProfile.id || cache !== todayMealsCache) return;
        showMealToast('Thực đơn đã thay đổi. Đã tải lại dữ liệu mới nhất; hãy chọn lại.', 'error');
      } else if (result.code === 'CATALOG_REFRESH_REQUIRED') {
        showMealToast('Danh sách món đã cập nhật. Chọn Nghĩ sau nếu đã chốt, rồi Đổi thực đơn. Lịch sử cũ vẫn được giữ.', 'error');
      } else if (result.code === 'PREFERENCES_REQUIRE_REFRESH') {
        showMealToast('Khẩu vị đã thay đổi. Nhấn Áp dụng khẩu vị để tạo gợi ý phù hợp.', 'error');
      } else if (result.code === 'MEAL_DECIDED') {
        showMealToast('Thực đơn đã chốt. Chọn Nghĩ sau trước khi làm mới.', 'error');
      } else {
        showMealToast(mealUserMessage(result, 'Không thể cập nhật thực đơn.'), 'error');
      }
    }

    function updateMealLoading() {
      const pending = mealPending[currentMealMode];
      const busy = !!pending && pending.uid === userProfile.id && pending.cache === todayMealsCache;
      for (const id of ['btn-generate-ai', 'btn-refresh-meals', 'btn-apply-meal-preferences',
                        'meal-avoid', 'meal-dislikes', 'meal-prefer', 'meal-planning-focus']) {
        const element = document.getElementById(id);
        if (element) element.disabled = busy;
      }
      document.querySelectorAll('[data-meal-select]').forEach(button => { button.disabled = busy || !!todayMealsCache[currentMealMode]?.catalog_refresh_required; });
      document.getElementById('meal-options-container')?.setAttribute('aria-busy', String(busy));
      const generate = document.getElementById('btn-generate-text');
      if (generate) generate.textContent = busy ? 'Đang tạo gợi ý phù hợp với khẩu vị của bạn…' : todayMealsCache[currentMealMode]?.options?.length ? 'Tải lại thực đơn đã lưu' : 'Gợi ý 3 thực đơn ngay';
      const refresh = document.getElementById('btn-refresh-text');
      if (refresh) refresh.textContent = busy ? 'Đang tạo gợi ý phù hợp với khẩu vị của bạn…' : 'Đổi bộ gợi ý';
    }

    function mealDishSignature(meal, portions = false) {
      const options = (meal?.options || []).map(option => mealComponents(option).map(part =>
        JSON.stringify([part.type, part.dish_id || String(part.name || '').trim().toLowerCase(),
                        ...(portions ? [Number(part.grams) || 0] : [])])).sort().join('|'));
      return JSON.stringify(options.sort());
    }

    function mealGenerationMessage(previous, result) {
      if (result.meta?.refresh_status === 'no_alternative') return 'Chưa tìm thấy bộ thực đơn khác đáp ứng các điều kiện hiện tại.';
      if (result.meta?.refresh_status === 'preferences_applied') return 'Đã áp dụng khẩu vị; chưa tìm thấy bộ món khác phù hợp hơn.';
      if (result.meta?.cached) return 'Đã tải lại thực đơn của bạn!';
      if (!previous?.options?.length) return 'Đã tạo 3 thực đơn cho bạn!';
      if (mealDishSignature(previous) === mealDishSignature(result.data)) {
        return mealDishSignature(previous, true) === mealDishSignature(result.data, true)
          ? 'Các món vẫn giống bộ trước; chưa có thực đơn khác.'
          : 'Đã cập nhật khẩu phần; các món vẫn giữ nguyên.';
      }
      return 'Đã tạo bộ gợi ý mới theo khẩu vị đã chọn.';
    }

    async function performMealRequest(mode, operation, onSuccess) {
      const uid = userProfile.id, cache = todayMealsCache, pending = mealPending[mode];
      if (!uid || (pending?.uid === uid && pending.cache === cache)) return;
      const token = { uid, cache };
      mealPending[mode] = token; mealLoadSequence++;
      hideMealToast(); updateMealLoading();
      const current = () => uid === userProfile.id && cache === todayMealsCache && mealPending[mode] === token;
      try {
        const result = await operation();
        if (!current()) return;
        if (!result.success) { await handleMealError(result); return; }
        if (!Array.isArray(result.data?.options) || !result.data?.revision) {
          showMealToast('Dữ liệu thực đơn chưa đầy đủ. Hãy tải lại.', 'error'); return;
        }
        mealLoadSequence++;
        todayMealsCache[mode] = result.data;
        const notice = onSuccess(result);
        const message = typeof notice === 'string' ? notice : notice.message;
        renderCurrentMealMode();
        await loadDashboardSummary();
        if (current()) {
          const unchanged = result.meta?.refresh_status === 'no_alternative' || result.meta?.refresh_status === 'preferences_applied' || (result.meta?.changed === false && !result.meta?.cached);
          showMealToast(currentMealMode === mode ? message : mealModes[mode].label + ': ' + message, typeof notice === 'object' ? notice.kind : unchanged ? 'info' : 'success');
        }
      } catch (_) {
        if (current()) showMealToast('Không thể cập nhật thực đơn lúc này. Vui lòng thử lại.', 'error');
      } finally {
        if (mealPending[mode] === token) mealPending[mode] = null;
        updateMealLoading();
      }
    }

    async function generateMealSuggestions(forceRefresh = false) {
      const mode = currentMealMode, previous = todayMealsCache[mode];
      const preferences = readMealPreferences();
      const settings = typeof readV4Settings === 'function' ? readV4Settings() : {};
      if (forceRefresh && previous && (previous.status === 'decided' || previous.selectedOption !== null && previous.selectedOption !== undefined)) {
        showMealToast('Thực đơn đã chốt. Chọn Nghĩ sau trước khi áp dụng khẩu vị hoặc làm mới.', 'error'); return;
      }
      return performMealRequest(mode,
        () => NutriFitAPI.generateMeal(mode, forceRefresh, forceRefresh ? previous?.revision : null, preferences, settings),
        result => {
          const saved = result.data.options[0]?.recipe?.preferences;
          if (saved) mealPreferences[mode] = supportedMealPreferences(saved);
          if (currentMealMode === mode) renderMealPreferences();
          const repeated = previous?.options?.length && mealDishSignature(previous) === mealDishSignature(result.data);
          let message = mealGenerationMessage(previous, result);
          if (result.meta?.preference_notices?.length) message += ' Điều kiện cần tránh và không thích được ưu tiên khi khẩu vị mâu thuẫn.';
          return { message, kind: repeated || result.meta?.changed === false ? 'info' : 'success' };
        });
    }

    async function applyMealPreferences() {
      return generateMealSuggestions(!!todayMealsCache[currentMealMode]);
    }

    async function selectMeal(selectedOption) {
      const mode = currentMealMode, meal = todayMealsCache[mode];
      if (!meal?.revision) { showMealToast('Hãy tạo hoặc tải thực đơn trước khi chọn.', 'error'); return; }
      return performMealRequest(mode,
        () => NutriFitAPI.selectMealOption(mode, selectedOption, meal.revision),
        () => selectedOption === null ? 'Đã lưu lựa chọn Nghĩ sau!' : 'Đã chọn thực đơn thành công!');
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
