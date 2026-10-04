// meal-suggest/app.js — Logic giao diện riêng của module gợi ý thực đơn.
// Đúng spec feature.txt: 3 options cố định + nút thứ 4 "suy nghĩ",
// 2 mode trưa/tối, lưu lịch sử theo ngày. Không sửa file cũ nào.

(() => {
  const $ = (id) => document.getElementById(id);

  const state = {
    userId: 1,
    mealMode: 'lunch',
    dishMode: 'combo', // 'combo' = mâm cơm 5 món | 'single' = món lẻ 1 món
    cache: { lunch: null, dinner: null },
    singleCache: { lunch: null, dinner: null },
    pantry: [],
    maxKcal: 0,
    maxPrice: 0, // món mua ngoài: ngân sách tối đa VND/phần
    sortBy: 'match',
    onlyMatch: true,
    matchMode: 'any',
    favorites: [],
    tab: 'today',
    fullFilter: 'all',
    targetKcal: 1500,
    suggestOffset: { lunch: 0, dinner: 0 },
    aiOrder: { lunch: null, dinner: null },
    aiReasons: { lunch: [], dinner: [] },
    aiSource: { lunch: '', dinner: '' },
    aiDishes: [] // mâm cơm do AI sáng tạo (localStorage ms_ai_dishes)
  };

  // Lấy userId từ session mà app chính đã lưu (nếu có), fallback = 1.
  function resolveUserId() {
    try {
      const raw = localStorage.getItem('nutrifit_session_user');
      if (raw) {
        const parsed = JSON.parse(raw);
        const id = parsed?.user?.id || parsed?.user?.UserId || parsed?.userId;
        if (id) state.userId = Number(id);
      }
    } catch (e) { /* giữ mặc định */ }
    $('ms-user-id').value = state.userId;
  }

  function apiKey() {
    return localStorage.getItem('nutrifit_gemini_key') || '';
  }

  function setStatus(msg, isError = false) {
    const el = $('ms-status');
    el.classList.remove('hidden');
    el.className = 'p-3 rounded-xl text-xs font-semibold flex items-center gap-2 border ' +
      (isError
        ? 'bg-rose-50 text-rose-700 border-rose-200'
        : 'bg-emerald-50 text-emerald-800 border-emerald-200');
    $('ms-status-text').innerText = msg;
  }

  function hideStatus() {
    $('ms-status').classList.add('hidden');
  }

  function cardBadge(n) {
    const colors = [
      'bg-emerald-50 text-emerald-700 border-emerald-200',
      'bg-blue-50 text-blue-700 border-blue-200',
      'bg-purple-50 text-purple-700 border-purple-200'
    ];
    return colors[(n - 1) % 3];
  }

  function escapeHtml(s) {
    return String(s ?? '').replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
  }

  // --- Yêu cầu người dùng: nguyên liệu sẵn có, lọc, yêu thích.
  // Lưu localStorage, chấm khớp hoàn toàn phía client — không sửa backend/file cũ.
  const LS_PANTRY = 'ms_pantry';
  const LS_FAVS = 'ms_favorites';
  const LS_AI_DISHES = 'ms_ai_dishes';

  // Món AI tự sáng tạo (localStorage, gộp vào thực đơn tổng khi lọc/gợi ý).
  // Cùng cấu trúc trường với MS_FULL_MENUS nên tái dùng enrich + lọc + fav.
  function fullMenuAll() {
    const base = typeof MS_FULL_MENUS !== 'undefined' ? MS_FULL_MENUS : [];
    return base.concat(state.aiDishes || []);
  }

  function loadAiDishes() {
    try {
      const raw = JSON.parse(localStorage.getItem(LS_AI_DISHES) || '[]');
      state.aiDishes = Array.isArray(raw)
        ? raw.filter((d) => d && d.title && (d.mealType === 'lunch' || d.mealType === 'dinner'))
        : [];
    } catch (e) { state.aiDishes = []; }
  }

  function saveAiDishes() {
    try { localStorage.setItem(LS_AI_DISHES, JSON.stringify(state.aiDishes || [])); } catch (e) {}
  }

  function aiBadge(opt) {
    return opt && opt.ai
      ? '<span class="text-[11px] font-extrabold px-2 py-0.5 rounded-lg border bg-violet-50 text-violet-700 border-violet-200">✨ AI tạo</span>'
      : '';
  }

  function loadPantry() {
    try {
      const raw = localStorage.getItem(LS_PANTRY) || '';
      state.pantry = raw.split(/[,\n]/).map((s) => s.trim().toLowerCase()).filter(Boolean);
      const box = $('ms-pantry');
      if (box && !box.value) box.value = raw;
    } catch (e) { state.pantry = []; }
  }

  function savePantry() {
    const raw = $('ms-pantry').value || '';
    try { localStorage.setItem(LS_PANTRY, raw); } catch (e) {}
    state.pantry = raw.split(/[,\n]/).map((s) => s.trim().toLowerCase()).filter(Boolean);
    renderOptions();
    if (state.tab === 'full') renderFullMenus();
    setStatus(state.pantry.length
      ? `Đã lưu ${state.pantry.length} nguyên liệu — gợi ý đã xếp lại theo độ khớp.`
      : 'Đã xóa nguyên liệu sẵn có.');
  }

  function optionText(opt) {
    return [opt.title, opt.carb, opt.protein, opt.soup, opt.veggie, opt.dessert, opt.parts]
      .join(' ').toLowerCase();
  }

  // Chuẩn hóa tiếng Việt: bỏ dấu, đ→d để "ga" khớp "gà".
  function normVi(s) {
    return String(s ?? '').toLowerCase()
      .normalize('NFD').replace(/[̀-ͯ]/g, '')
      .replace(/đ/g, 'd');
  }

  function optionTokens(opt) {
    return new Set(normVi(optionText(opt)).split(/[^a-z0-9]+/).filter((w) => w.length >= 2));
  }

  // Một nguyên liệu được tính là khớp khi MỌI từ của nó xuất hiện nguyên từ
  // trong món ăn. Ưu tiên khớp chính xác có dấu trước: "cá" chỉ khớp "cá"
  // chứ không khớp nhầm "canh"/"cua" như kiểu includes() chuỗi thô.
  // Chỉ khi người dùng gõ không dấu ("ga", "rau muong") mới fallback
  // sang so sánh không dấu — nên "nấm" không bao giờ khớp nhầm "nam bộ".
  function ingredientMatches(ingRaw, opt, tokenSet) {
    const ing = String(ingRaw ?? '').trim().toLowerCase();
    if (!ing) return false;
    const words = ing.split(/[^a-zà-ỹđ0-9]+/).filter((w) => w.length >= 2);
    if (words.length === 0) return false;
    const textTokens = optionText(opt).split(/[^a-zà-ỹđ0-9]+/);
    if (words.every((w) => textTokens.includes(w))) return true;
    if (normVi(ing) !== ing) return false;
    return words.every((w) => tokenSet.has(w));
  }

  function scoreOption(opt) {
    const tokens = optionTokens(opt);
    const matched = state.pantry.filter((ing) => ing && ingredientMatches(ing, opt, tokens));
    return { score: matched.length, matched };
  }

  // --- Giá tiền món mua ngoài (VND/phần).
  function fmtPrice(v) {
    const n = Number(v || 0);
    return n > 0 ? `${n.toLocaleString('vi-VN')}đ` : '—';
  }

  function priceBadge(opt) {
    if (state.dishMode !== 'single') return '';
    if (!opt.price) return '';
    return `<div class="text-[11px] font-bold text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-2 py-1">💰 Giá tham khảo: ${fmtPrice(opt.price)}/phần</div>`;
  }

  function matchBadge(matched) {
    if (state.dishMode === 'single') return '';
    if (state.pantry.length === 0) return '';
    if (matched && matched.length > 0) {
      return `<div class="text-[11px] font-bold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-2 py-1">✓ Khớp ${matched.length}/${state.pantry.length} nguyên liệu: ${escapeHtml(matched.join(', '))}</div>`;
    }
    return '<div class="text-[11px] font-semibold text-slate-400 bg-slate-50 border border-slate-200 rounded-lg px-2 py-1">Không khớp nguyên liệu đã nhập</div>';
  }

  function getVisibleOptions(data) {
    let list = data.options.map((opt, i) => {
      const { score, matched } = scoreOption(opt);
      return { opt, n: i + 1, score, matched };
    });
    if (state.maxKcal > 0) list = list.filter((x) => Number(x.opt.calories) <= state.maxKcal);
    if (state.dishMode === 'single') {
      // Món mua ngoài: lọc theo ngân sách, xếp giá rẻ trước.
      if (state.maxPrice > 0) list = list.filter((x) => Number(x.opt.price || 0) > 0 && Number(x.opt.price) <= state.maxPrice);
      if (state.sortBy === 'price-asc') list.sort((a, b) => (a.opt.price || 0) - (b.opt.price || 0));
      else if (state.sortBy === 'kcal-asc') list.sort((a, b) => a.opt.calories - b.opt.calories);
      else if (state.sortBy === 'protein-desc') list.sort((a, b) => (b.opt.macros?.protein || 0) - (a.opt.macros?.protein || 0));
      else list.sort((a, b) => (a.opt.price || 0) - (b.opt.price || 0) || a.opt.calories - b.opt.calories);
      return list;
    }
    if (state.pantry.length > 0 && state.onlyMatch) {
      list = list.filter((x) => state.matchMode === 'all'
        ? x.score === state.pantry.length && x.score > 0
        : x.score > 0);
    }
    if (state.sortBy === 'kcal-asc') list.sort((a, b) => a.opt.calories - b.opt.calories);
    else if (state.sortBy === 'protein-desc') list.sort((a, b) => (b.opt.macros?.protein || 0) - (a.opt.macros?.protein || 0));
    else list.sort((a, b) => b.score - a.score || a.opt.calories - b.opt.calories);
    return list;
  }

  // --- Lọc trên THỰC ĐƠN TỔNG 42 món (MS_FULL_MENUS).
  // Cùng công thức calo backend: cal = targetKcal * cal_pct, C50/P25/F25.
  function inferTargetKcal() {
    const lun = state.cache.lunch && state.cache.lunch.options;
    if (lun && lun.length > 0) {
      const avg = lun.reduce((s, o) => s + Number(o.calories || 0), 0) / lun.length;
      if (avg > 0) state.targetKcal = Math.round(avg / 0.40);
      return;
    }
    const din = state.cache.dinner && state.cache.dinner.options;
    if (din && din.length > 0) {
      const avg = din.reduce((s, o) => s + Number(o.calories || 0), 0) / din.length;
      if (avg > 0) state.targetKcal = Math.round(avg / 0.29);
    }
  }

  function enrichFull(m) {
    const cal = Math.round(state.targetKcal * (m.cal_pct || 0.40));
    return Object.assign({}, m, {
      calories: cal,
      macros: {
        carbs: Math.round((cal * 0.50) / 4),
        protein: Math.round((cal * 0.25) / 4),
        fat: Math.round((cal * 0.25) / 9)
      }
    });
  }

  function isFavIn(mealType, title) {
    return state.favorites.some((f) => f.title === title && f.mealType === mealType);
  }

  function toggleFavFull(idx) {
    const m = fullMenuAll()[idx];
    if (!m) return;
    const at = state.favorites.findIndex((f) => f.title === m.title && f.mealType === m.mealType);
    if (at >= 0) state.favorites.splice(at, 1);
    else state.favorites.push({ title: m.title, mealType: m.mealType, calories: Math.round(state.targetKcal * (m.cal_pct || 0.40)), date: new Date().toISOString().slice(0, 10) });
    try { localStorage.setItem(LS_FAVS, JSON.stringify(state.favorites)); } catch (e) {}
    renderFullMenus();
    renderFavorites();
    if (state.tab === 'today') renderOptions();
  }

  function copyFull(idx) {
    const m = fullMenuAll()[idx];
    if (!m) return;
    const cal = Math.round(state.targetKcal * (m.cal_pct || 0.40));
    const text = `${m.title} (${cal} kcal)\n- Món chính: ${m.carb}\n- Món mặn: ${m.protein}\n- Món canh: ${m.soup}\n- Món rau: ${m.veggie}\n- Tráng miệng: ${m.dessert}`;
    const done = () => setStatus('Đã sao chép thực đơn vào clipboard.');
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, () => setStatus('Không sao chép được.', true));
    } else {
      setStatus('Trình duyệt không hỗ trợ sao chép nhanh.', true);
    }
  }

  // --- Gợi ý CHỈ từ thực đơn tổng đã lọc (MS_FULL_MENUS).
  // Dùng chung bộ lọc pantry / kcal tối đa / chế độ khớp / sắp xếp,
  // ép mealType = bữa đang xem (trưa/tối), bỏ qua tab lọc fullFilter.
  function getSuggestPool(mode) {
    const mm = mode || state.mealMode;
    let pool = fullMenuAll().map((m, idx) => ({ m: enrichFull(m), idx }))
      .filter((x) => x.m.mealType === mm);
    let list = pool.map((x) => {
      const { score, matched } = scoreOption(x.m);
      return { opt: x.m, idx: x.idx, score, matched };
    });
    if (state.maxKcal > 0) list = list.filter((x) => Number(x.opt.calories) <= state.maxKcal);
    if (state.pantry.length > 0 && state.onlyMatch) {
      list = list.filter((x) => state.matchMode === 'all'
        ? x.score === state.pantry.length && x.score > 0
        : x.score > 0);
    }
    if (state.sortBy === 'kcal-asc') list.sort((a, b) => a.opt.calories - b.opt.calories);
    else if (state.sortBy === 'protein-desc') list.sort((a, b) => (b.opt.macros?.protein || 0) - (a.opt.macros?.protein || 0));
    else list.sort((a, b) => b.score - a.score || a.opt.calories - b.opt.calories);
    return list;
  }

  // --- MÓN MUA NGOÀI: pool từ MS_SINGLE_DISHES, lọc theo bữa / kcal / giá.
  // mealType "all" hợp cả bữa trưa lẫn bữa tối. KHÔNG lọc pantry
  // (mua ngoài quán nên nguyên liệu ở nhà không còn ý nghĩa).
  function getSinglePool(mode) {
    const mm = mode || state.mealMode;
    if (typeof MS_SINGLE_DISHES === 'undefined') return [];
    const pool = MS_SINGLE_DISHES.map((m, idx) => ({ m: enrichFull(m), idx }))
      .filter((x) => x.m.mealType === mm || x.m.mealType === 'all');
    let list = pool.map((x) => {
      const { score, matched } = scoreOption(x.m);
      return { opt: x.m, idx: x.idx, score, matched };
    });
    if (state.maxKcal > 0) list = list.filter((x) => Number(x.opt.calories) <= state.maxKcal);
    if (state.maxPrice > 0) list = list.filter((x) => Number(x.opt.price || 0) > 0 && Number(x.opt.price) <= state.maxPrice);
    if (state.sortBy === 'price-asc') list.sort((a, b) => (a.opt.price || 0) - (b.opt.price || 0));
    else if (state.sortBy === 'kcal-asc') list.sort((a, b) => a.opt.calories - b.opt.calories);
    else if (state.sortBy === 'protein-desc') list.sort((a, b) => (b.opt.macros?.protein || 0) - (a.opt.macros?.protein || 0));
    else list.sort((a, b) => (a.opt.price || 0) - (b.opt.price || 0) || a.opt.calories - b.opt.calories);
    return list;
  }

  function setDishMode(mode) {
    state.dishMode = mode;
    state.aiOrder[state.mealMode] = null;
    state.suggestOffset[state.mealMode] = 0;
    const isSingle = mode === 'single';
    $('btn-dish-combo').className = 'px-4 py-1.5 text-xs font-bold rounded-lg ' +
      (!isSingle ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900');
    $('btn-dish-single').className = 'px-4 py-1.5 text-xs font-bold rounded-lg ' +
      (isSingle ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900');
    $('btn-ms-generate').innerText = isSingle ? 'Gợi ý 3 món mua ngoài' : 'Gợi ý 3 thực đơn';
    syncSingleFilters();
    renderOptions();
  }

  // Ẩn/hiện bộ lọc theo chế độ: món mua ngoài lọc theo GIÁ + kcal,
  // ẩn ô nguyên liệu / khớp nguyên liệu vì mua ngoài quán.
  function syncSingleFilters() {
    const isSingle = state.dishMode === 'single';
    const pantryBox = $('ms-pantry') && $('ms-pantry').closest('div');
    if (pantryBox) pantryBox.style.display = isSingle ? 'none' : '';
    const hint = $('ms-single-hint');
    if (hint) hint.classList.toggle('hidden', !isSingle);
    const priceInput = $('ms-max-price');
    if (priceInput) priceInput.classList.toggle('hidden', !isSingle);
    const onlyMatchLabel = $('ms-only-match') && $('ms-only-match').closest('label');
    if (onlyMatchLabel) onlyMatchLabel.style.display = isSingle ? 'none' : '';
    const matchMode = $('ms-match-mode');
    if (matchMode) matchMode.style.display = isSingle ? 'none' : '';
    const sort = $('ms-sort');
    if (sort) {
      if (isSingle) {
        sort.innerHTML = '<option value="price-asc">Giá rẻ → đắt</option><option value="kcal-asc">Calo thấp → cao</option><option value="protein-desc">Nhiều đạm nhất</option>';
        if (state.sortBy === 'match') state.sortBy = 'price-asc';
      } else {
        sort.innerHTML = '<option value="match">Ưu tiên khớp nguyên liệu</option><option value="kcal-asc">Calo thấp → cao</option><option value="protein-desc">Nhiều đạm nhất</option>';
        if (state.sortBy === 'price-asc') state.sortBy = 'match';
      }
      sort.value = state.sortBy;
    }
  }

  // Cache riêng theo chế độ: mâm cơm dùng state.cache (đồng bộ backend cũ),
  // món lẻ dùng state.singleCache (chỉ local, không gọi select backend cũ
  // vì backend expect option 1-3 của mâm cơm).
  function curStore() { return state.dishMode === 'single' ? state.singleCache : state.cache; }
  function curData() { return curStore()[state.mealMode]; }

  function resetSuggestOffset() {
    state.suggestOffset.lunch = 0;
    state.suggestOffset.dinner = 0;
    state.aiOrder.lunch = null;
    state.aiOrder.dinner = null;
    state.aiReasons.lunch = [];
    state.aiReasons.dinner = [];
    state.aiSource.lunch = '';
    state.aiSource.dinner = '';
  }

  function getVisibleFull() {
    let pool = fullMenuAll().map((m, idx) => ({ m: enrichFull(m), idx }));
    if (state.fullFilter !== 'all') pool = pool.filter((x) => x.m.mealType === state.fullFilter);
    let list = pool.map((x) => {
      const { score, matched } = scoreOption(x.m);
      return { opt: x.m, idx: x.idx, score, matched };
    });
    if (state.maxKcal > 0) list = list.filter((x) => Number(x.opt.calories) <= state.maxKcal);
    if (state.pantry.length > 0 && state.onlyMatch) {
      list = list.filter((x) => state.matchMode === 'all'
        ? x.score === state.pantry.length && x.score > 0
        : x.score > 0);
    }
    if (state.sortBy === 'kcal-asc') list.sort((a, b) => a.opt.calories - b.opt.calories);
    else if (state.sortBy === 'protein-desc') list.sort((a, b) => (b.opt.macros?.protein || 0) - (a.opt.macros?.protein || 0));
    else list.sort((a, b) => b.score - a.score || a.opt.calories - b.opt.calories);
    return list;
  }

  function renderFullMenus() {
    const box = $('ms-full-options');
    const count = $('ms-full-count');
    if (!box) return;
    const list = getVisibleFull();
    if (count) count.innerText = `${list.length} món`;
    if (list.length === 0) {
      box.innerHTML = `
        <div class="col-span-full py-12 text-center bg-amber-50 border border-dashed border-amber-300 rounded-3xl space-y-2">
          <p class="font-bold text-sm text-amber-800">Không món nào trong thực đơn tổng khớp "${escapeHtml(state.pantry.join(', '))}"</p>
          <p class="text-xs text-amber-600">Thử tắt "Chỉ hiện món khớp", chuyển sang "Khớp ≥1 nguyên liệu", hoặc xóa bớt nguyên liệu.</p>
        </div>`;
      return;
    }
    box.innerHTML = list.map(({ opt, idx, matched }) => `
      <div class="border-2 border-slate-200 rounded-3xl p-5 bg-white flex flex-col justify-between gap-4">
        <div class="space-y-3">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-extrabold uppercase px-2.5 py-0.5 rounded-lg border bg-slate-100 text-slate-600 border-slate-200">${opt.day != null && typeof MS_DAY_NAMES !== 'undefined' ? MS_DAY_NAMES[opt.day] + ' · ' : ''}${opt.mealType === 'lunch' ? 'Trưa' : 'Tối'}</span>
            <span class="text-base font-black text-slate-800">${escapeHtml(opt.calories)} <span class="text-[11px] font-normal text-slate-400">kcal</span></span>
          </div>
          <h4 class="font-extrabold text-sm text-slate-800">${escapeHtml(opt.title)} ${aiBadge(opt)}</h4>
          ${matchBadge(matched)}
          <div class="flex flex-wrap gap-1.5 text-[11px]">
            <span class="px-2 py-0.5 rounded-lg bg-amber-50 border border-amber-200 font-semibold">🌾 C: <b>${opt.macros?.carbs || 0}g</b></span>
            <span class="px-2 py-0.5 rounded-lg bg-rose-50 border border-rose-200 font-semibold">🥩 P: <b>${opt.macros?.protein || 0}g</b></span>
            <span class="px-2 py-0.5 rounded-lg bg-emerald-50 border border-emerald-200 font-semibold">🥑 F: <b>${opt.macros?.fat || 0}g</b></span>
          </div>
          <div class="p-3.5 bg-slate-50/80 rounded-2xl border border-slate-100 space-y-2 text-xs">
            <div><span class="font-bold text-amber-600">🍚 Món chính:</span> <span class="font-semibold">${escapeHtml(opt.carb)}</span></div>
            <div><span class="font-bold text-rose-600">🥩 Món mặn:</span> <span class="font-semibold">${escapeHtml(opt.protein)}</span></div>
            <div><span class="font-bold text-blue-600">🥣 Món canh:</span> <span class="font-semibold">${escapeHtml(opt.soup)}</span></div>
            <div><span class="font-bold text-emerald-600">🥗 Món rau:</span> <span class="font-semibold">${escapeHtml(opt.veggie)}</span></div>
            <div><span class="font-bold text-yellow-600">🍌 Tráng miệng:</span> <span class="font-semibold">${escapeHtml(opt.dessert)}</span></div>
          </div>
          <p class="text-[11px] text-slate-500 italic">💡 ${escapeHtml(opt.nutritionNotes || '')}</p>
        </div>
        <div class="flex gap-2">
          <button data-full-fav="${idx}" class="ms-full-fav flex-1 py-2 rounded-xl text-xs font-bold border ${isFavIn(opt.mealType, opt.title) ? 'bg-rose-500 text-white border-rose-500' : 'bg-white border-slate-200 hover:bg-rose-50'}">${isFavIn(opt.mealType, opt.title) ? '❤️ Đã thích' : '🤍 Thích'}</button>
          <button data-full-copy="${idx}" class="ms-full-copy flex-1 py-2 rounded-xl text-xs font-bold bg-white border border-slate-200 hover:bg-slate-50">📋 Sao chép</button>
        </div>
      </div>`).join('');
    box.querySelectorAll('.ms-full-fav').forEach((btn) => {
      btn.addEventListener('click', () => toggleFavFull(Number(btn.dataset.fullFav)));
    });
    box.querySelectorAll('.ms-full-copy').forEach((btn) => {
      btn.addEventListener('click', () => copyFull(Number(btn.dataset.fullCopy)));
    });
  }

  function switchTab(tab) {
    state.tab = tab;
    const today = tab === 'today';
    $('ms-today-box').classList.toggle('hidden', !today);
    $('ms-full-box').classList.toggle('hidden', today);
    $('btn-tab-today').className = 'px-4 py-2 font-bold rounded-xl ' + (today ? 'bg-slate-900 text-white' : 'text-slate-500 hover:text-slate-900');
    $('btn-tab-full').className = 'px-4 py-2 font-bold rounded-xl ' + (!today ? 'bg-slate-900 text-white' : 'text-slate-500 hover:text-slate-900');
    if (!today) renderFullMenus();
  }

  function setFullFilter(f) {
    state.fullFilter = f;
    const on = 'px-3 py-1.5 font-bold rounded-lg bg-white shadow-sm';
    const off = 'px-3 py-1.5 font-bold rounded-lg text-slate-500';
    $('btn-full-all').className = f === 'all' ? on : off;
    $('btn-full-lunch').className = f === 'lunch' ? on : off;
    $('btn-full-dinner').className = f === 'dinner' ? on : off;
    renderFullMenus();
  }

  // AI tự sáng tạo mâm cơm mới cho thực đơn tổng (cần Gemini API Key,
  // nhập bằng nút "API Key" trên header). Món mới lưu localStorage,
  // tự tham gia lọc tổng + "Gợi ý 3 thực đơn", có badge ✨ AI.
  async function aiGenerateDishes() {
    const key = apiKey();
    if (!key) {
      setStatus('Cần Gemini API Key để AI tạo món mới — bấm nút "API Key" trên header để nhập.', true);
      return;
    }
    if (typeof MS_AI_RANK === 'undefined' || !MS_AI_RANK.generateDishes) {
      setStatus('Chưa tải được module AI (ai-rank.js).', true);
      return;
    }
    await setLoading('btn-ai-generate', true, 'AI đang sáng tạo món...');
    try {
      const mealFilter = state.fullFilter === 'all' ? 'all' : state.fullFilter;
      const count = mealFilter === 'all' ? 6 : 3;
      const existing = fullMenuAll().map((m) => m.title);
      const dishes = await MS_AI_RANK.generateDishes(count, mealFilter, existing, state.pantry, key);
      if (!dishes || dishes.length === 0) {
        setStatus('AI không trả về món mới hợp lệ — thử lại sau.', true);
        return;
      }
      state.aiDishes = (state.aiDishes || []).concat(dishes);
      saveAiDishes();
      resetSuggestOffset();
      syncAiClearBtn();
      renderFullMenus();
      const nLunch = dishes.filter((d) => d.mealType === 'lunch').length;
      const nDinner = dishes.length - nLunch;
      setStatus(`✨ AI đã tạo ${dishes.length} món mới (${nLunch} trưa · ${nDinner} tối) — đã thêm vào thực đơn tổng, bấm "Gợi ý 3 thực đơn" để thử.`);
    } finally {
      await setLoading('btn-ai-generate', false);
    }
  }

  function aiClearDishes() {
    if (!state.aiDishes || state.aiDishes.length === 0) return;
    state.aiDishes = [];
    saveAiDishes();
    resetSuggestOffset();
    syncAiClearBtn();
    renderFullMenus();
    setStatus('Đã xóa toàn bộ món do AI tạo — thực đơn tổng về lại bản gốc.');
  }

  function syncAiClearBtn() {
    const btn = $('btn-ai-clear');
    if (btn) btn.classList.toggle('hidden', !(state.aiDishes && state.aiDishes.length > 0));
  }

  function loadFavorites() {
    try { state.favorites = JSON.parse(localStorage.getItem(LS_FAVS) || '[]'); }
    catch (e) { state.favorites = []; }
  }

  function isFav(title) {
    return state.favorites.some((f) => f.title === title && f.mealType === state.mealMode);
  }

  function toggleFav(n) {
    const data = curData();
    if (!data) return;
    const opt = data.options[n - 1];
    if (!opt) return;
    const idx = state.favorites.findIndex((f) => f.title === opt.title && f.mealType === state.mealMode);
    if (idx >= 0) state.favorites.splice(idx, 1);
    else state.favorites.push({ title: opt.title, mealType: state.mealMode, calories: opt.calories, price: opt.price, date: new Date().toISOString().slice(0, 10) });
    try { localStorage.setItem(LS_FAVS, JSON.stringify(state.favorites)); } catch (e) {}
    renderOptions();
    renderFavorites();
  }

  function removeFav(i) {
    state.favorites.splice(i, 1);
    try { localStorage.setItem(LS_FAVS, JSON.stringify(state.favorites)); } catch (e) {}
    renderOptions();
    renderFavorites();
  }

  function renderFavorites() {
    const box = $('ms-favorites');
    if (!box) return;
    if (state.favorites.length === 0) {
      box.innerHTML = '<p class="text-xs text-slate-400">Nhấn 🤍 Thích trên món ăn để lưu lại tại đây.</p>';
      return;
    }
    box.innerHTML = state.favorites.map((f, i) => `
      <div class="p-3 bg-rose-50/60 rounded-xl border border-rose-100 text-xs space-y-1">
        <div class="flex items-center justify-between gap-2">
          <b>${escapeHtml(f.title)}</b>
          <button data-unfav="${i}" class="ms-unfav px-2 py-1 bg-white border border-rose-200 rounded-lg font-bold text-rose-600">Xóa</button>
        </div>
        <p class="text-slate-500">Bữa ${f.mealType === 'lunch' ? 'trưa' : 'tối'} · ${escapeHtml(f.calories)} kcal${f.price ? ' · ' + escapeHtml(fmtPrice(f.price)) + '/phần' : ''}${f.date ? ' · lưu ' + escapeHtml(f.date) : ''}</p>
      </div>`).join('');
    box.querySelectorAll('.ms-unfav').forEach((btn) => {
      btn.addEventListener('click', () => removeFav(Number(btn.dataset.unfav)));
    });
  }

  function copyOption(n) {
    const data = curData();
    const opt = data && data.options[n - 1];
    if (!opt) return;
    const detail = state.dishMode === 'single'
      ? `- Giá tham khảo: ${fmtPrice(opt.price)}/phần\n- Có gì: ${opt.protein}\n- Tinh bột: ${opt.carb}\n- Nước chấm/nước dùng: ${opt.soup}\n- Ăn kèm: ${opt.veggie}`
      : `- Món chính: ${opt.carb}\n- Món mặn: ${opt.protein}\n- Món canh: ${opt.soup}\n- Món rau: ${opt.veggie}\n- Tráng miệng: ${opt.dessert}`;
    const text = `${opt.title} (${opt.calories} kcal)\n${detail}`;
    const done = () => setStatus('Đã sao chép thực đơn vào clipboard.');
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(done, () => setStatus('Không sao chép được.', true));
    } else {
      setStatus('Trình duyệt không hỗ trợ sao chép nhanh.', true);
    }
  }

  // Chi tiết card: mâm cơm hiện 5 món; món lẻ hiện thành phần + mô tả gọn.
  function detailBlock(opt) {
    if (state.dishMode === 'single') {
      const rows = [];
      if (opt.price) rows.push(`<div><span class="font-bold text-amber-600">💰 Giá tham khảo:</span> <span class="font-semibold">${fmtPrice(opt.price)}/phần</span></div>`);
      if (opt.protein && opt.protein !== '—') rows.push(`<div><span class="font-bold text-rose-600">🍖 Có gì:</span> <span class="font-semibold">${escapeHtml(opt.protein)}</span></div>`);
      if (opt.carb && opt.carb !== '—') rows.push(`<div><span class="font-bold text-amber-600">🍚 Tinh bột:</span> <span class="font-semibold">${escapeHtml(opt.carb)}</span></div>`);
      if (opt.soup && opt.soup !== '—') rows.push(`<div><span class="font-bold text-blue-600">🥣 Nước chấm/nước dùng:</span> <span class="font-semibold">${escapeHtml(opt.soup)}</span></div>`);
      if (opt.veggie && opt.veggie !== '—') rows.push(`<div><span class="font-bold text-emerald-600">🥗 Rau ăn kèm:</span> <span class="font-semibold">${escapeHtml(opt.veggie)}</span></div>`);
      if (opt.parts) rows.push(`<div><span class="font-bold text-slate-500">🧺 Thành phần:</span> <span class="font-semibold">${escapeHtml(opt.parts)}</span></div>`);
      return `<div class="p-3.5 bg-slate-50/80 rounded-2xl border border-slate-100 space-y-2 text-xs">${rows.join('')}</div>`;
    }
    return `
            <div class="p-3.5 bg-slate-50/80 rounded-2xl border border-slate-100 space-y-2 text-xs">
              <div><span class="font-bold text-amber-600">🍚 Món chính:</span> <span class="font-semibold">${escapeHtml(opt.carb)}</span></div>
              <div><span class="font-bold text-rose-600">🥩 Món mặn:</span> <span class="font-semibold">${escapeHtml(opt.protein)}</span></div>
              <div><span class="font-bold text-blue-600">🥣 Món canh:</span> <span class="font-semibold">${escapeHtml(opt.soup)}</span></div>
              <div><span class="font-bold text-emerald-600">🥗 Món rau:</span> <span class="font-semibold">${escapeHtml(opt.veggie)}</span></div>
              <div><span class="font-bold text-yellow-600">🍌 Tráng miệng:</span> <span class="font-semibold">${escapeHtml(opt.dessert)}</span></div>
            </div>`;
  }

  // Vẽ 3 option cards cho mode hiện tại.
  function renderOptions() {
    const data = curData();
    const box = $('ms-options');
    const isSingle = state.dishMode === 'single';
    const kindLabel = isSingle ? 'món mua ngoài' : 'thực đơn';

    if (!data || !data.options || data.options.length === 0) {
      box.innerHTML = `
        <div class="col-span-full py-12 text-center bg-slate-50 border border-dashed border-slate-200 rounded-3xl space-y-3">
          <p class="font-bold text-sm text-slate-700">Chưa có gợi ý ${kindLabel} cho ${state.mealMode === 'lunch' ? 'Bữa trưa' : 'Bữa tối'} hôm nay</p>
          <p class="text-xs text-slate-400">Nhấn <b>"${isSingle ? 'Gợi ý 3 món mua ngoài' : 'Gợi ý 3 thực đơn'}"</b> để ${isSingle ? 'lọc theo giá tiền và bữa ăn' : 'lọc theo nguyên liệu bạn có'}.</p>
        </div>`;
      $('ms-think-box').classList.add('hidden');
      updateBanner();
      return;
    }

    $('ms-think-box').classList.remove('hidden');

    const visible = getVisibleOptions(data);
    if (visible.length === 0) {
      const emptyMsg = isSingle
        ? (state.maxPrice > 0 ? `Không món mua ngoài nào dưới ${fmtPrice(state.maxPrice)}/phần` : 'Không món mua ngoài nào khớp bộ lọc hiện tại')
        : `Không món nào khớp nguyên liệu "${escapeHtml(state.pantry.join(', '))}"`;
      const emptyHint = isSingle
        ? 'Thử tăng ngân sách, xóa kcal tối đa, hoặc bấm "🔄 Đổi thực đơn khác".'
        : 'Thử tắt "Chỉ hiện món khớp", chuyển sang "Khớp ≥1 nguyên liệu", hoặc bấm "🔄 Đổi thực đơn khác".';
      box.innerHTML = `
        <div class="col-span-full py-12 text-center bg-amber-50 border border-dashed border-amber-300 rounded-3xl space-y-2">
          <p class="font-bold text-sm text-amber-800">${emptyMsg}</p>
          <p class="text-xs text-amber-600">${emptyHint}</p>
        </div>`;
      if (data.selectedOption) {
        const chosen = data.options[data.selectedOption - 1];
        setStatus(`Đã chốt Lựa chọn ${data.selectedOption}${chosen ? ': ' + chosen.title : ''}.`);
      } else {
        setStatus('Trạng thái: Đang suy nghĩ / cân nhắc — 3 lựa chọn ban đầu được giữ nguyên.');
      }
      updateBanner();
      return;
    }

    if (data.selectedOption) {
      const chosen = data.options[data.selectedOption - 1];
      setStatus(`Đã chốt Lựa chọn ${data.selectedOption}${chosen ? ': ' + chosen.title : ''}.`);
    } else {
      setStatus('Trạng thái: Đang suy nghĩ / cân nhắc — 3 lựa chọn ban đầu được giữ nguyên.');
    }

    box.innerHTML = visible.map(({ opt, n, matched }) => {
      const selected = data.selectedOption === n;
      return `
        <div class="border-2 ${selected ? 'border-emerald-500 ring-4 ring-emerald-500/10' : 'border-slate-200'} rounded-3xl p-5 bg-white flex flex-col justify-between gap-4 relative">
          ${selected ? '<span class="absolute -top-3 right-4 bg-emerald-500 text-white text-[10px] font-black px-3 py-0.5 rounded-full">ĐÃ CHỌN</span>' : ''}
          <div class="space-y-3">
            <div class="flex items-center justify-between">
              <span class="text-[11px] font-extrabold uppercase px-2.5 py-0.5 rounded-lg border ${cardBadge(n)}">Lựa chọn ${n}</span>
              <span class="text-base font-black text-slate-800">${escapeHtml(opt.calories)} <span class="text-[11px] font-normal text-slate-400">kcal</span></span>
            </div>
            <h4 class="font-extrabold text-sm text-slate-800">${escapeHtml(opt.title)}</h4>
            ${priceBadge(opt)}
            ${matchBadge(matched)}
            <div class="flex flex-wrap gap-1.5 text-[11px]">
              <span class="px-2 py-0.5 rounded-lg bg-amber-50 border border-amber-200 font-semibold">🌾 C: <b>${opt.macros?.carbs || 0}g</b></span>
              <span class="px-2 py-0.5 rounded-lg bg-rose-50 border border-rose-200 font-semibold">🥩 P: <b>${opt.macros?.protein || 0}g</b></span>
              <span class="px-2 py-0.5 rounded-lg bg-emerald-50 border border-emerald-200 font-semibold">🥑 F: <b>${opt.macros?.fat || 0}g</b></span>
            </div>
            ${detailBlock(opt)}
            <p class="text-[11px] text-slate-500 italic">💡 ${escapeHtml(opt.nutritionNotes || '')}</p>
            ${opt.aiReason ? `<p class="text-[11px] font-semibold text-violet-700 bg-violet-50 border border-violet-200 rounded-lg px-2 py-1">✨ AI chọn vì: ${escapeHtml(opt.aiReason)}</p>` : ''}
          </div>
          <div class="flex gap-2">
            <button data-fav="${n}" class="ms-fav flex-1 py-2 rounded-xl text-xs font-bold border ${isFav(opt.title) ? 'bg-rose-500 text-white border-rose-500' : 'bg-white border-slate-200 hover:bg-rose-50'}">${isFav(opt.title) ? '❤️ Đã thích' : '🤍 Thích'}</button>
            <button data-copy="${n}" class="ms-copy flex-1 py-2 rounded-xl text-xs font-bold bg-white border border-slate-200 hover:bg-slate-50">📋 Sao chép</button>
            ${isSingle ? `<button data-map="${n}" class="ms-map flex-1 py-2 rounded-xl text-xs font-bold bg-blue-50 border border-blue-200 text-blue-700 hover:bg-blue-100">📍 Quán gần nhất</button>` : ''}
          </div>
          <button data-opt="${n}" ${selected ? 'disabled' : ''}
            class="ms-pick w-full py-2.5 rounded-xl text-xs font-bold ${selected ? 'bg-emerald-600 text-white' : 'bg-slate-900 hover:bg-slate-700 text-white'}">
            ${selected ? 'Đang áp dụng' : 'Chọn Lựa chọn ' + n}
          </button>
        </div>`;
    }).join('');

    box.querySelectorAll('.ms-pick:not([disabled])').forEach((btn) => {
      btn.addEventListener('click', () => handleSelect(Number(btn.dataset.opt)));
    });
    box.querySelectorAll('.ms-fav').forEach((btn) => {
      btn.addEventListener('click', () => toggleFav(Number(btn.dataset.fav)));
    });
    box.querySelectorAll('.ms-copy').forEach((btn) => {
      btn.addEventListener('click', () => copyOption(Number(btn.dataset.copy)));
    });
    box.querySelectorAll('.ms-map').forEach((btn) => {
      btn.addEventListener('click', () => {
        const data = curData();
        const opt = data && data.options[Number(btn.dataset.map) - 1];
        if (opt) openNearbyMap(opt.title);
      });
    });

    updateBanner();
  }

  function updateBanner() {
    const isLunch = state.mealMode === 'lunch';
    $('ms-banner-icon').innerText = isLunch ? '☀️' : '🌙';
    $('ms-banner-title').innerText = isLunch
      ? 'Bữa Trưa — Ăn no, năng lượng bền bỉ'
      : 'Bữa Tối — Thanh đạm, dễ tiêu, ngủ ngon';
    $('btn-mode-lunch').className = 'px-4 py-1.5 text-xs font-bold rounded-lg flex items-center gap-1.5 ' +
      (isLunch ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900');
    $('btn-mode-dinner').className = 'px-4 py-1.5 text-xs font-bold rounded-lg flex items-center gap-1.5 ' +
      (!isLunch ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-900');
  }

  async function setLoading(btnId, loading, text) {
    const btn = $(btnId);
    if (!btn) return;
    if (loading) {
      btn.dataset.orig = btn.innerHTML;
      btn.disabled = true;
      btn.innerHTML = `<span>${text || 'Đang xử lý...'}</span>`;
    } else {
      btn.innerHTML = btn.dataset.orig || btn.innerHTML;
      btn.disabled = false;
    }
  }

  async function loadToday() {
    hideStatus();
    const res = await MealSuggestAPI.getTodayMeals(state.userId);
    if (res.success && res.todayMeals) {
      state.cache = res.todayMeals;
      inferTargetKcal();
      renderOptions();
      if (state.tab === 'full') renderFullMenus();
    } else {
      setStatus(res.message || 'Không tải được thực đơn hôm nay.', true);
    }
  }

  async function generate(forceRefresh) {
    const btnId = forceRefresh ? 'btn-ms-refresh' : 'btn-ms-generate';
    const isSingle = state.dishMode === 'single';
    const poolName = isSingle ? 'MS_SINGLE_DISHES' : 'MS_FULL_MENUS';
    const kindLabel = isSingle ? 'món mua ngoài' : 'món';
    const srcCheck = isSingle ? (typeof MS_SINGLE_DISHES !== 'undefined') : (typeof MS_FULL_MENUS !== 'undefined');
    // Gợi ý CHỈ từ thực đơn đã lọc + AI xếp hạng (Gemini Flash).
    // AI không sáng tạo món mới — chỉ xếp hạng các món đã lọc;
    // không có key thì dùng thứ hạng chuyên gia (điểm khớp nguyên liệu).
    if (!srcCheck) {
      setStatus(`Chưa tải được kho ${kindLabel} (${poolName}.js). Kiểm tra lại file.`, true);
      return;
    }
    await setLoading(btnId, true,
      forceRefresh ? 'Đang đổi món...' : (isSingle ? 'AI đang chọn món mua ngoài...' : 'AI đang chọn từ thực đơn đã lọc...'));
    const pool = isSingle ? getSinglePool(state.mealMode) : getSuggestPool(state.mealMode);
    if (pool.length === 0) {
      await setLoading(btnId, false);
      const keys = state.pantry.length ? `"${state.pantry.join(', ')}"` : 'bộ lọc hiện tại';
      const poolWord = isSingle ? 'kho món mua ngoài' : 'thực đơn tổng';
      if (isSingle) {
        setStatus(`Không món mua ngoài nào ${state.maxPrice > 0 ? `dưới ${fmtPrice(state.maxPrice)}/phần ` : ''}cho bữa ${state.mealMode === 'lunch' ? 'trưa' : 'tối'}. Thử tăng ngân sách hoặc xóa kcal tối đa.`, true);
      } else {
        setStatus(`Không món nào trong ${poolWord} khớp ${keys} cho bữa ${state.mealMode === 'lunch' ? 'trưa' : 'tối'}. Thử tắt "Chỉ hiện món khớp" hoặc xóa bớt nguyên liệu.`, true);
      }
      curStore()[state.mealMode] = {
        suggestionId: null, mealType: state.mealMode,
        date: new Date().toISOString().slice(0, 10),
        options: [], selectedOption: null, status: 'pending'
      };
      renderOptions();
      return;
    }
    let order, reasons, source;
    if (!forceRefresh || !state.aiOrder[state.mealMode]) {
      // Nút "Gợi ý": gọi AI xếp hạng toàn bộ pool đã lọc một lần.
      const ranked = (typeof MS_AI_RANK !== 'undefined')
        ? await MS_AI_RANK.rank(pool, state.mealMode, state.pantry, apiKey(), { dishMode: state.dishMode, maxPrice: state.maxPrice })
        : { order: pool.map((_, i) => i), reasons: [], source: 'expert' };
      order = ranked.order;
      reasons = ranked.reasons || [];
      source = ranked.source;
      state.aiOrder[state.mealMode] = order;
      state.aiReasons[state.mealMode] = reasons;
      state.aiSource[state.mealMode] = source;
      state.suggestOffset[state.mealMode] = 0;
    } else {
      // Nút "Đổi món khác": xoay vòng qua thứ hạng AI đã có, không gọi AI lại.
      order = state.aiOrder[state.mealMode];
      reasons = state.aiReasons[state.mealMode] || [];
      source = state.aiSource[state.mealMode];
    }
    let off = state.suggestOffset[state.mealMode] || 0;
    off = pool.length > 0 ? off % pool.length : 0;
    const n = Math.min(3, pool.length);
    const three = [];
    const threeReasons = [];
    for (let i = 0; i < n; i++) {
      const pos = order[(off + i) % order.length];
      three.push(pool[pos]);
      threeReasons.push(reasons[(off + i) % order.length] || '');
    }
    state.suggestOffset[state.mealMode] = pool.length > 0 ? (off + n) % pool.length : 0;
    const store = curStore();
    if (!store[state.mealMode]) {
      store[state.mealMode] = {
        suggestionId: null, mealType: state.mealMode,
        date: new Date().toISOString().slice(0, 10)
      };
    }
    store[state.mealMode].options = three.map((x, i) => Object.assign({}, x.opt, {
      id: i + 1,
      aiReason: threeReasons[i] || ''
    }));
    store[state.mealMode].selectedOption = null;
    store[state.mealMode].status = 'pending';
    await setLoading(btnId, false);
    if (state.tab !== 'today') switchTab('today');
    renderOptions();
    const mealName = state.mealMode === 'lunch' ? 'trưa' : 'tối';
    const srcLabel = source === 'ai' ? 'AI Gemini' : 'chuyên gia';
    const kindWord = isSingle ? 'món mua ngoài' : 'món';
    setStatus(pool.length <= 3
      ? `Kho đã lọc chỉ còn ${pool.length} ${kindWord} bữa ${mealName} — hiển thị tất cả (${srcLabel} chọn).`
      : `Đã gợi ý ${n} ${kindWord} bữa ${mealName} từ ${pool.length} món đã lọc (${srcLabel} chọn).${forceRefresh ? ' (Bấm tiếp "Đổi thực đơn khác" để xem 3 món kế tiếp.)' : ''}`);
  }

  // Món mua ngoài: mở Google Maps tìm quán bán món này gần vị trí người dùng.
  function openNearbyMap(title) {
    if (!title) return;
    const q = encodeURIComponent(`${title} gần đây`);
    window.open(`https://www.google.com/maps/search/?api=1&query=${q}`, '_blank', 'noopener');
  }

  async function handleSelect(n) {
    const data = curData();
    if (!data || !data.options || !data.options[n - 1]) return;
    data.selectedOption = n;
    data.status = 'decided';
    renderOptions();
    const title = data.options[n - 1] ? data.options[n - 1].title : '';
    if (state.dishMode === 'single') {
      // Món lẻ chỉ chốt local — không gọi backend cũ (backend expect mâm cơm 1-3).
      setStatus(`Đã chốt món mua ngoài Lựa chọn ${n}${title ? ': ' + title : ''}. Đang mở Google Maps tìm quán gần nhất...`);
      openNearbyMap(title);
      return;
    }
    const res = await MealSuggestAPI.selectMealOption(state.userId, state.mealMode, n);
    if (res.success) {
      setStatus(`Đã chốt Lựa chọn ${n}${title ? ': ' + title : ''} (từ thực đơn đã lọc).`);
    } else {
      setStatus(`Đã chốt Lựa chọn ${n} trên màn hình, nhưng chưa đồng bộ máy chủ: ${res.message || ''}`, true);
    }
  }

  // Nút thứ 4: suy nghĩ sau — giữ nguyên 3 options, chỉ đổi status.
  async function handleThinkLater() {
    await setLoading('btn-ms-think', true, 'Đang lưu...');
    const data = curData();
    if (data) {
      data.selectedOption = null;
      data.status = 'pending';
      renderOptions();
    }
    if (state.dishMode === 'single') {
      await setLoading('btn-ms-think', false);
      setStatus('Đã lưu trạng thái: Đang cân nhắc — 3 món mua ngoài được giữ nguyên.');
      return;
    }
    const res = await MealSuggestAPI.selectMealOption(state.userId, state.mealMode, null);
    await setLoading('btn-ms-think', false);
    if (res.success) {
      setStatus('Đã lưu trạng thái: Đang cân nhắc — 3 gợi ý từ thực đơn đã lọc được giữ nguyên.');
    } else {
      setStatus(`Đã chuyển "Đang cân nhắc" trên màn hình, chưa đồng bộ máy chủ: ${res.message || ''}`, true);
    }
  }

  async function loadHistory() {
    const box = $('ms-history');
    box.innerHTML = '<p class="text-xs text-slate-400">Đang tải lịch sử...</p>';
    const res = await MealSuggestAPI.getMealHistory(state.userId);
    if (!res.success) {
      box.innerHTML = `<p class="text-xs text-rose-500">${escapeHtml(res.message || 'Lỗi tải lịch sử.')}</p>`;
      return;
    }
    if (res.history.length === 0) {
      box.innerHTML = '<p class="text-xs text-slate-400">Chưa có lịch sử lựa chọn nào.</p>';
      return;
    }
    box.innerHTML = res.history.slice(0, 20).map((h) => {
      const mealName = h.mealType === 'lunch' ? 'Trưa' : 'Tối';
      const chosen = h.chosenMeal ? escapeHtml(h.chosenMeal.title) : 'Đang suy nghĩ';
      const badge = h.status === 'decided'
        ? '<span class="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 text-[10px] font-bold">Đã chốt</span>'
        : '<span class="px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 text-[10px] font-bold">Đang chờ</span>';
      return `
        <div class="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs space-y-1">
          <div class="flex items-center justify-between">
            <b>${escapeHtml(h.date)} — Bữa ${mealName}</b>${badge}
          </div>
          <p class="text-slate-600">${h.selectedOption ? `Option ${h.selectedOption}: ${chosen}` : chosen}</p>
        </div>`;
    }).join('');
  }

  function bindEvents() {
    $('btn-mode-lunch').addEventListener('click', () => { state.mealMode = 'lunch'; renderOptions(); });
    $('btn-mode-dinner').addEventListener('click', () => { state.mealMode = 'dinner'; renderOptions(); });
    $('btn-ms-generate').addEventListener('click', () => generate(false));
    $('btn-ms-refresh').addEventListener('click', () => generate(true));
    $('btn-dish-combo').addEventListener('click', () => setDishMode('combo'));
    $('btn-dish-single').addEventListener('click', () => setDishMode('single'));
    $('btn-ms-think').addEventListener('click', handleThinkLater);
    $('btn-ms-history').addEventListener('click', loadHistory);
    $('btn-ms-key').addEventListener('click', () => {
      const cur = localStorage.getItem('nutrifit_gemini_key') || '';
      const input = prompt('Nhập Gemini API Key (bỏ trống = dùng chế độ chuyên gia):', cur);
      if (input !== null) {
        localStorage.setItem('nutrifit_gemini_key', input.trim());
        setStatus(input.trim() ? 'Đã lưu Gemini API Key.' : 'Đã chuyển sang chế độ chuyên gia.');
      }
    });
    $('ms-user-id').addEventListener('change', (e) => {
      state.userId = Number(e.target.value) || 1;
      loadToday();
    });
    $('btn-ms-pantry').addEventListener('click', () => { resetSuggestOffset(); savePantry(); });
    $('ms-max-kcal').addEventListener('input', (e) => {
      state.maxKcal = Number(e.target.value) || 0;
      state.aiOrder[state.mealMode] = null;
      state.suggestOffset[state.mealMode] = 0;
      renderOptions();
      if (state.tab === 'full') renderFullMenus();
    });
    $('ms-sort').addEventListener('change', (e) => {
      state.sortBy = e.target.value;
      state.aiOrder[state.mealMode] = null;
      state.suggestOffset[state.mealMode] = 0;
      renderOptions();
      if (state.tab === 'full') renderFullMenus();
    });
    $('ms-only-match').addEventListener('change', (e) => {
      state.onlyMatch = e.target.checked;
      state.aiOrder[state.mealMode] = null;
      state.suggestOffset[state.mealMode] = 0;
      renderOptions();
      if (state.tab === 'full') renderFullMenus();
    });
    $('ms-match-mode').addEventListener('change', (e) => {
      state.matchMode = e.target.value;
      state.aiOrder[state.mealMode] = null;
      state.suggestOffset[state.mealMode] = 0;
      renderOptions();
      if (state.tab === 'full') renderFullMenus();
    });
    const priceInput = $('ms-max-price');
    if (priceInput) priceInput.addEventListener('input', (e) => {
      state.maxPrice = Number(e.target.value) || 0;
      state.aiOrder[state.mealMode] = null;
      state.suggestOffset[state.mealMode] = 0;
      renderOptions();
    });
    $('btn-ms-clear-filter').addEventListener('click', () => {
      state.maxKcal = 0; state.maxPrice = 0;
      state.sortBy = state.dishMode === 'single' ? 'price-asc' : 'match';
      state.onlyMatch = false; state.matchMode = 'any';
      state.aiOrder[state.mealMode] = null;
      state.suggestOffset[state.mealMode] = 0;
      $('ms-max-kcal').value = ''; $('ms-sort').value = state.sortBy;
      $('ms-only-match').checked = false; $('ms-match-mode').value = 'any';
      if ($('ms-max-price')) $('ms-max-price').value = '';
      renderOptions();
      if (state.tab === 'full') renderFullMenus();
    });
    $('btn-tab-today').addEventListener('click', () => switchTab('today'));
    $('btn-tab-full').addEventListener('click', () => switchTab('full'));
    $('btn-full-all').addEventListener('click', () => setFullFilter('all'));
    $('btn-full-lunch').addEventListener('click', () => setFullFilter('lunch'));
    $('btn-full-dinner').addEventListener('click', () => setFullFilter('dinner'));
    $('btn-ai-generate').addEventListener('click', aiGenerateDishes);
    $('btn-ai-clear').addEventListener('click', aiClearDishes);
  }

  document.addEventListener('DOMContentLoaded', () => {
    resolveUserId();
    loadPantry();
    loadFavorites();
    loadAiDishes();
    bindEvents();
    syncSingleFilters();
    syncAiClearBtn();
    renderFavorites();
    loadToday();
  });
})();
