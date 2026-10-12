(() => {
  'use strict';

  const $ = id => document.getElementById(id);
  let dishes = [];
  let currentMode = 'catalog';
  let requestVersion = 0;

  const format = (value, digits = 0) => Number.isFinite(Number(value))
    ? Number(value).toLocaleString('vi-VN', { maximumFractionDigits: digits }) : '—';
  const money = value => `${format(value, 0)} đ`;

  function status(message, kind = 'info') {
    const node = $('street-food-status');
    if (!node) return;
    node.textContent = message || '';
    node.dataset.kind = kind;
    node.classList.toggle('hidden', !message);
  }

  function apiError(result) {
    if (result?.isOffline) return 'Không kết nối được Backend. Hãy kiểm tra Flask đang chạy.';
    if (result?.httpStatus === 404) return 'Endpoint Street Food chưa được đăng ký hoặc kho món ăn chưa có dữ liệu. Hãy tích hợp module TV4 và kiểm tra bảng StreetFoodDish.';
    return result?.message || 'Chưa tải được danh sách món. Vui lòng thử lại.';
  }

  function makeTag(text, className = '') {
    const tag = document.createElement('span');
    tag.className = `nf-street-tag ${className}`.trim();
    tag.textContent = text;
    return tag;
  }

  function buildCard(dish, recommended = false) {
    const card = document.createElement('article');
    card.className = 'nf-street-card';
    const top = document.createElement('div');
    top.className = 'nf-street-card-top';
    const titleWrap = document.createElement('div');
    const title = document.createElement('h4');
    title.className = 'nf-street-title';
    title.textContent = dish.title || 'Món ăn';
    const meal = document.createElement('p');
    meal.className = 'nf-street-subtitle';
    const labels = { breakfast: 'Bữa sáng', lunch: 'Bữa trưa', dinner: 'Bữa tối', all: 'Nhiều bữa' };
    meal.textContent = labels[dish.meal_type] || 'Món Việt';
    titleWrap.append(title, meal);
    top.append(titleWrap);
    if (recommended && Number.isFinite(Number(dish.score))) top.append(makeTag(`Điểm ${format(dish.score, 1)}`, 'nf-street-tag-score'));
    card.append(top);

    const metrics = document.createElement('div');
    metrics.className = 'nf-street-metrics';
    [
      ['Giá', money(dish.price_vnd), 'price'],
      ['Năng lượng', `${format(dish.calories)} kcal`, 'kcal'],
      ['Protein', `${format(dish.protein_g, 1)} g`, 'macro']
    ].forEach(([labelText, valueText, variant]) => {
      const item = document.createElement('div');
      item.className = `nf-street-metric nf-street-metric-${variant}`;
      const label = document.createElement('span'); label.textContent = labelText;
      const value = document.createElement('strong'); value.textContent = valueText;
      item.append(label, value); metrics.append(item);
    });
    card.append(metrics);

    const macros = document.createElement('p');
    macros.className = 'nf-street-macros';
    macros.textContent = `Carbs ${format(dish.carbs_g, 1)} g · Chất béo ${format(dish.fat_g, 1)} g`;
    card.append(macros);

    const details = document.createElement('details');
    details.className = 'nf-street-details';
    const summary = document.createElement('summary'); summary.textContent = 'Xem thành phần món';
    details.append(summary);
    const ingredientRows = [
      ['Món đạm', dish.protein_desc],
      ['Tinh bột', dish.carb_desc],
      ['Canh / nước dùng', dish.soup_desc],
      ['Rau ăn kèm', dish.veggie_desc]
    ];
    ingredientRows.forEach(([labelText, valueText]) => {
      if (!valueText) return;
      const row = document.createElement('p');
      const label = document.createElement('b'); label.textContent = `${labelText}: `;
      const text = document.createElement('span'); text.textContent = valueText;
      row.append(label, text); details.append(row);
    });
    card.append(details);

    if (Array.isArray(dish.reasons) && dish.reasons.length) {
      const reasons = document.createElement('div');
      reasons.className = 'nf-street-reasons';
      dish.reasons.forEach(reason => reasons.append(makeTag(reason)));
      card.append(reasons);
    }
    const note = document.createElement('p');
    note.className = 'nf-street-card-note';
    note.textContent = 'Giá và dinh dưỡng theo dữ liệu catalog, có thể khác với khẩu phần tại quán thực tế.';
    card.append(note);
    return card;
  }

  function renderDishes(items, recommended = false) {
    const container = $('street-food-results');
    container.replaceChildren();
    $('street-food-count').textContent = `${items.length} món`;
    if (!items.length) {
      const empty = document.createElement('div');
      empty.className = 'nf-street-empty';
      const title = document.createElement('strong'); title.textContent = 'Chưa có món phù hợp';
      const desc = document.createElement('p'); desc.textContent = 'Thử nới ngân sách, mức calo hoặc đổi từ khóa tìm kiếm.';
      empty.append(title, desc); container.append(empty); return;
    }
    items.forEach(item => container.append(buildCard(item, recommended)));
  }

  function readFilters() {
    const priceText = $('street-food-max-price').value.trim();
    const kcalText = $('street-food-max-kcal').value.trim();
    return {
      q: $('street-food-query').value.trim(),
      meal_type: $('street-food-meal-type').value,
      max_price: priceText ? Number(priceText) : undefined,
      max_kcal: kcalText ? Number(kcalText) : undefined
    };
  }

  async function loadStreetFoodDishes() {
    const version = ++requestVersion;
    currentMode = 'catalog';
    status('Đang tải dữ liệu món ăn từ Backend…');
    $('street-food-filter-btn').disabled = true;
    $('street-food-recommend-btn').disabled = true;
    const filters = readFilters();
    const result = await NutriFitAPI.getStreetFood(filters);
    $('street-food-filter-btn').disabled = false;
    $('street-food-recommend-btn').disabled = false;
    if (version !== requestVersion) return;
    if (!result.success) {
      dishes = [];
      renderDishes([]);
      status(apiError(result), 'error');
      return;
    }
    dishes = Array.isArray(result.data?.items) ? result.data.items : [];
    renderDishes(dishes, false);
    status(`Đang hiển thị ${format(result.data?.count ?? dishes.length)} món theo bộ lọc.`, 'success');
  }

  async function recommendStreetFood() {
    const filters = readFilters();
    const budget = filters.max_price ?? 50000;
    const maxKcal = filters.max_kcal ?? 600;
    if (!Number.isFinite(budget) || budget <= 0 || !Number.isFinite(maxKcal) || maxKcal <= 0) {
      status('Ngân sách và calo tối đa phải lớn hơn 0.', 'error');
      return;
    }
    const version = ++requestVersion;
    currentMode = 'recommend';
    $('street-food-filter-btn').disabled = true;
    $('street-food-recommend-btn').disabled = true;
    status('Đang xếp hạng món theo ngân sách, calo và tỷ lệ đạm…');
    const result = await NutriFitAPI.recommendStreetFood({
      budget, max_kcal: maxKcal, meal_type: filters.meal_type, limit: 6
    });
    $('street-food-filter-btn').disabled = false;
    $('street-food-recommend-btn').disabled = false;
    if (version !== requestVersion) return;
    if (!result.success) {
      renderDishes([]);
      status(apiError(result), 'error');
      return;
    }
    dishes = Array.isArray(result.data?.items) ? result.data.items : [];
    renderDishes(dishes, true);
    status(`Đã gợi ý ${format(result.data?.count ?? dishes.length)} món trong ngân sách ${money(result.data?.budget ?? budget)} và tối đa ${format(result.data?.max_kcal ?? maxKcal)} kcal.`, 'success');
  }

  function resetFilters() {
    $('street-food-query').value = '';
    $('street-food-meal-type').value = 'all';
    $('street-food-max-price').value = '50000';
    $('street-food-max-kcal').value = '600';
    loadStreetFoodDishes();
  }

  document.addEventListener('DOMContentLoaded', () => {
    $('street-food-filter-form')?.addEventListener('submit', event => { event.preventDefault(); loadStreetFoodDishes(); });
    $('street-food-recommend-btn')?.addEventListener('click', recommendStreetFood);
    $('street-food-reset-btn')?.addEventListener('click', resetFilters);
  });

  window.loadStreetFoodDishes = loadStreetFoodDishes;
  window.recommendStreetFood = recommendStreetFood;
})();
