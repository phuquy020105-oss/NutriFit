(() => {
  'use strict';

  const $ = id => document.getElementById(id);
  const state = {
    results: [],
    selected: null,
    preview: null,
    pendingPayload: null,
    searching: false,
    previewing: false,
    confirming: false,
    priorFocus: null
  };

  function formatNumber(value, digits = 1) {
    const number = Number(value);
    return Number.isFinite(number)
      ? number.toLocaleString('vi-VN', { maximumFractionDigits: digits })
      : '—';
  }

  function showStatus(message, kind = 'info') {
    const status = $('quick-food-status');
    status.textContent = message || '';
    status.dataset.kind = kind;
    status.classList.toggle('hidden', !message);
  }

  function errorMessage(result, fallback = 'Chưa thể hoàn tất. Vui lòng thử lại.') {
    const code = result?.code;
    const known = {
      AUTH_REQUIRED: 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.',
      PREMIUM_REQUIRED: 'Quick Food yêu cầu gói Premium còn hiệu lực.',
      PREMIUM_UNAVAILABLE: 'Backend chưa có đủ schema quyền Premium. Chưa thể xác nhận món ăn.',
      FOOD_NOT_FOUND: 'Không tìm thấy món phù hợp. Hãy thử từ khóa khác.',
      INVALID_INPUT: 'Tên món hoặc định lượng không hợp lệ. Hãy kiểm tra lại.',
      CONFIRMATION_REQUIRED: 'Bạn cần xác nhận đã ăn món này trước khi ghi nhật ký.',
      DATABASE_ERROR: 'Database đang bận. Dữ liệu chưa được xác nhận; có thể thử lại an toàn.',
      FOOD_CATALOG_MIGRATION_REQUIRED: 'Kho món ăn chưa sẵn sàng. Hãy thử lại sau.',
      V4_MIGRATION_REQUIRED: 'Database chưa sẵn sàng cho Food Intake V4.'
    };
    if (known[code]) return known[code];
    if (result?.isOffline) return 'Không kết nối được Backend. Hãy kiểm tra Flask đang chạy.';
    return result?.message || fallback;
  }

  function setButton(button, busy, busyText, normalText) {
    if (!button.dataset.normalText) button.dataset.normalText = normalText || button.textContent;
    button.disabled = busy;
    button.textContent = busy ? busyText : (normalText || button.dataset.normalText);
  }

  function updateConfirmState() {
    const checked = $('quick-food-confirm-checkbox').checked;
    const grams = Number($('quick-food-grams').value);
    const previewMatches = state.preview && Number(state.preview.grams) === grams;
    $('quick-food-confirm-btn').disabled = state.confirming || !state.selected || !previewMatches || !checked;
    $('quick-food-confirm-btn').textContent = state.confirming
      ? 'Đang ghi nhận…'
      : state.pendingPayload ? 'Thử lại ghi nhận' : 'Xác nhận đã ăn';
  }

  function clearPreview() {
    state.preview = null;
    $('quick-food-preview').replaceChildren();
    $('quick-food-preview').classList.add('hidden');
    $('quick-food-confirm-checkbox').checked = false;
    updateConfirmState();
  }

  function resetQuickFood() {
    state.results = [];
    state.selected = null;
    state.preview = null;
    state.pendingPayload = null;
    state.searching = false;
    state.previewing = false;
    state.confirming = false;
    $('quick-food-query').value = '';
    $('quick-food-results').replaceChildren();
    $('quick-food-selected').classList.add('hidden');
    $('quick-food-selected-name').textContent = '';
    $('quick-food-grams').value = '';
    $('quick-food-confirm-checkbox').checked = false;
    $('quick-food-consumed-at').value = '';
    $('quick-food-preview').replaceChildren();
    $('quick-food-preview').classList.add('hidden');
    showStatus('Tìm món, chọn đúng kết quả, xem preview và chỉ xác nhận sau khi đã ăn.', 'info');
    setButton($('quick-food-search-btn'), false, '', 'Tìm món');
    setButton($('quick-food-preview-btn'), false, '', 'Xem dinh dưỡng');
    $('quick-food-confirm-btn').disabled = true;
    $('quick-food-confirm-btn').textContent = 'Xác nhận đã ăn';
  }

  function openQuickFoodModal() {
    state.priorFocus = document.activeElement;
    resetQuickFood();
    $('modal-quick-food').classList.remove('hidden');
    $('modal-quick-food').classList.add('flex');
    document.body.classList.add('nf-modal-open');
    $('quick-food-query').focus();
  }

  function closeQuickFoodModal() {
    if (state.confirming) return;
    $('modal-quick-food').classList.add('hidden');
    $('modal-quick-food').classList.remove('flex');
    if (!document.querySelector('.nf-modal:not(.hidden)')) document.body.classList.remove('nf-modal-open');
    if (state.priorFocus?.isConnected) state.priorFocus.focus();
  }

  async function searchQuickFood() {
    const query = $('quick-food-query').value.trim();
    if (query.length < 1) {
      showStatus('Nhập tên món ăn trước khi tìm.', 'error');
      $('quick-food-query').focus();
      return;
    }
    state.searching = true;
    setButton($('quick-food-search-btn'), true, 'Đang tìm…', 'Tìm món');
    showStatus('Đang tìm món trong Food Catalog…', 'info');
    $('quick-food-results').replaceChildren();
    $('quick-food-selected').classList.add('hidden');
    state.selected = null;
    state.pendingPayload = null;
    clearPreview();

    const result = await NutriFitAPI.searchQuickFood(query, 10);
    state.searching = false;
    setButton($('quick-food-search-btn'), false, '', 'Tìm món');

    if (!result.success) {
      showStatus(errorMessage(result, 'Không tìm thấy kết quả.'), 'error');
      return;
    }

    state.results = Array.isArray(result.data?.results) ? result.data.results : [];
    if (!state.results.length) {
      showStatus('Không có món phù hợp. Hãy thử từ khóa khác.', 'info');
      return;
    }

    showStatus(`Tìm thấy ${formatNumber(result.data.total, 0)} kết quả. Hãy chọn món chính xác trước khi xem dinh dưỡng.`, 'success');
    const container = $('quick-food-results');
    for (const dish of state.results) {
      const button = document.createElement('button');
      button.type = 'button';
      button.className = 'nf-quickfood-result';
      button.setAttribute('aria-pressed', 'false');

      const text = document.createElement('span');
      const name = document.createElement('span');
      name.className = 'nf-quickfood-result-name';
      name.textContent = dish.name || 'Món không tên';
      const meta = document.createElement('small');
      meta.className = 'nf-quickfood-result-meta';
      meta.textContent = `Khẩu phần tham khảo: ${formatNumber(dish.reference_grams, 0)} g · Chọn để xem preview`;
      text.append(name, meta);

      const match = document.createElement('span');
      match.className = 'nf-quickfood-match';
      match.textContent = dish.match === 'exact' ? 'Khớp tên' : 'Kết quả tìm';
      button.append(text, match);
      button.addEventListener('click', () => selectDish(dish, button));
      container.append(button);
    }
  }

  function selectDish(dish, button) {
    if (state.confirming || state.previewing) return;
    state.selected = dish;
    state.preview = null;
    state.pendingPayload = null;
    $('quick-food-results').querySelectorAll('.nf-quickfood-result').forEach(node => node.setAttribute('aria-pressed', 'false'));
    button.setAttribute('aria-pressed', 'true');
    $('quick-food-selected').classList.remove('hidden');
    $('quick-food-selected-name').textContent = dish.name;
    $('quick-food-grams').value = Number(dish.reference_grams) > 0 ? Number(dish.reference_grams) : 100;
    $('quick-food-meal-type').value = 'snack';
    $('quick-food-consumed-at').value = '';
    clearPreview();
    showStatus('Bạn đã chọn món. Nhập gram thực tế rồi bấm “Xem dinh dưỡng”; chưa có dữ liệu nào được ghi vào nhật ký.', 'info');
  }

  function renderPreview(data) {
    const preview = $('quick-food-preview');
    preview.replaceChildren();
    preview.classList.remove('hidden');
    const title = document.createElement('h5');
    title.className = 'font-extrabold text-sm text-slate-800';
    title.textContent = `${data.name} · ${formatNumber(data.grams, 2)} g`;
    const note = document.createElement('p');
    note.className = 'mt-1 text-xs text-slate-500';
    note.textContent = data.estimated ? 'Dinh dưỡng ước tính từ Food Catalog.' : 'Dinh dưỡng từ Food Catalog.';
    const grid = document.createElement('div');
    grid.className = 'nf-quickfood-preview-grid';
    const values = [
      ['Năng lượng', `${formatNumber(data.totals?.calories)} kcal`],
      ['Protein', `${formatNumber(data.totals?.protein)} g`],
      ['Carbs', `${formatNumber(data.totals?.carbs)} g`],
      ['Chất béo', `${formatNumber(data.totals?.fat)} g`],
      ['Chất xơ', `${formatNumber(data.totals?.fiber)} g`]
    ];
    for (const [labelText, valueText] of values) {
      const card = document.createElement('div');
      card.className = 'nf-quickfood-stat';
      const label = document.createElement('span');
      label.textContent = labelText;
      const value = document.createElement('strong');
      value.textContent = valueText;
      card.append(label, value);
      grid.append(card);
    }
    preview.append(title, note, grid);
    if (data.fiber_complete === false) {
      const fiberNote = document.createElement('p');
      fiberNote.className = 'mt-2 text-xs text-amber-700';
      fiberNote.textContent = 'Dữ liệu chất xơ của món này chưa đầy đủ.';
      preview.append(fiberNote);
    }
  }

  async function previewQuickFood() {
    if (!state.selected || state.previewing || state.confirming) return;
    const gramsText = $('quick-food-grams').value;
    const grams = gramsText === '' ? NaN : Number(gramsText);
    if (!Number.isFinite(grams) || grams < 1 || grams > 2000 || Math.round(grams * 100) !== grams * 100) {
      showStatus('Định lượng phải từ 1 đến 2.000 g, tối đa 2 chữ số thập phân.', 'error');
      return;
    }

    state.previewing = true;
    setButton($('quick-food-preview-btn'), true, 'Đang tính…', 'Xem dinh dưỡng');
    clearPreview();
    showStatus('Đang yêu cầu Backend xem trước dinh dưỡng…', 'info');
    const result = await NutriFitAPI.previewQuickFood(state.selected.dish_id, grams);
    state.previewing = false;
    setButton($('quick-food-preview-btn'), false, '', 'Xem dinh dưỡng');

    if (!result.success || !result.data) {
      showStatus(errorMessage(result, 'Không thể xem trước dinh dưỡng.'), 'error');
      return;
    }
    state.preview = result.data;
    state.pendingPayload = null;
    renderPreview(result.data);
    showStatus('Preview đã sẵn sàng. Chỉ nhấn xác nhận nếu bạn đã thực sự ăn khẩu phần này.', 'success');
    updateConfirmState();
  }

  function createRequestId() {
    if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID();
    return 'nf_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 18);
  }

  async function confirmQuickFood() {
    if (state.confirming || !state.selected) return;
    const grams = Number($('quick-food-grams').value);
    if (!state.preview || Number(state.preview.grams) !== grams) {
      showStatus('Hãy xem preview lại sau khi thay đổi định lượng.', 'error');
      return;
    }
    if (!$('quick-food-confirm-checkbox').checked) {
      showStatus('Vui lòng xác nhận bạn đã thực sự ăn món này.', 'error');
      return;
    }

    if (!state.pendingPayload) {
      const localDateTime = $('quick-food-consumed-at').value;
      let consumedAt;
      if (localDateTime) {
        const parsed = new Date(localDateTime);
        if (!Number.isFinite(parsed.getTime())) {
          showStatus('Thời gian ăn không hợp lệ.', 'error');
          return;
        }
        consumedAt = parsed.toISOString();
      }
      state.pendingPayload = {
        dish_id: state.selected.dish_id,
        grams,
        mealType: $('quick-food-meal-type').value,
        confirmed: true,
        requestId: createRequestId(),
        ...(consumedAt ? { consumedAt } : {})
      };
    }

    state.confirming = true;
    updateConfirmState();
    $('modal-quick-food').setAttribute('aria-busy', 'true');
    showStatus('Đang ghi nhận qua Backend… Không đóng khung trong lúc xử lý.', 'info');
    try {
      const result = await NutriFitAPI.confirmQuickFood(state.pendingPayload);
      if (!result.success || !result.data) {
        showStatus(errorMessage(result, 'Chưa nhận được xác nhận. Hãy kiểm tra nhật ký trước khi thử lại.'), 'error');
        // Giữ nguyên pendingPayload/requestId để retry không tạo bản ghi trùng.
        return;
      }

      const saved = result.data;
      state.pendingPayload = null;
      showStatus('Đã ghi nhận món ăn thành công.', 'success');
      if ($('v4-date') && saved.date) $('v4-date').value = saved.date;
      // Allow the success path to close the modal before finally resets the busy flag.
      state.confirming = false;
      $('modal-quick-food').removeAttribute('aria-busy');
      closeQuickFoodModal();
      if (typeof loadV4Daily === 'function') await loadV4Daily();
      if (typeof showMealToast === 'function') showMealToast('Đã ghi nhận món ăn nhanh và cập nhật lượng calo đã ăn!');
      resetQuickFood();
    } catch (error) {
      console.error('Quick Food confirm error:', error);
      showStatus('Chưa nhận được xác nhận từ Backend. Nhấn thử lại để gửi cùng mã request, tránh tạo bản ghi trùng.', 'error');
    } finally {
      state.confirming = false;
      $('modal-quick-food').removeAttribute('aria-busy');
      updateConfirmState();
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    $('btn-open-quick-food')?.addEventListener('click', openQuickFoodModal);
    $('quick-food-close')?.addEventListener('click', closeQuickFoodModal);
    $('quick-food-search-btn')?.addEventListener('click', searchQuickFood);
    $('quick-food-preview-btn')?.addEventListener('click', previewQuickFood);
    $('quick-food-confirm-btn')?.addEventListener('click', confirmQuickFood);
    $('quick-food-query')?.addEventListener('keydown', event => {
      if (event.key === 'Enter') { event.preventDefault(); searchQuickFood(); }
    });
    $('quick-food-grams')?.addEventListener('input', () => {
      state.preview = null;
      state.pendingPayload = null;
      clearPreview();
      showStatus('Đã thay đổi định lượng. Hãy xem preview lại trước khi xác nhận.', 'info');
    });
    $('quick-food-confirm-checkbox')?.addEventListener('change', updateConfirmState);
    $('modal-quick-food')?.addEventListener('click', event => {
      if (event.target === $('modal-quick-food')) closeQuickFoodModal();
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && !$('modal-quick-food')?.classList.contains('hidden')) closeQuickFoodModal();
    });
  });
})();
