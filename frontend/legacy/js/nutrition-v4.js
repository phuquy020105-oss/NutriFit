let v4ActualGramLimits = null;
// Personal nutrition UI. API/session, recipe revisions and saved snapshots remain authoritative.
let v4Catalog = [];
let v4Daily = null;
let v4IntakeContext = null;
let v4ComponentContext = null;
let v4DeleteContext = null;
let v4DailyRequest = 0;
const v4ModalFocus = new Map();

function v4Today() {
  const parts = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Ho_Chi_Minh', year: 'numeric', month: '2-digit', day: '2-digit' }).formatToParts(new Date());
  const value = key => parts.find(p => p.type === key).value;
  return value('year') + '-' + value('month') + '-' + value('day');
}
function v4LocalTime(date = new Date()) {
  return new Date(date.getTime() - date.getTimezoneOffset() * 60000).toISOString().slice(0, 16);
}
function v4Number(value, digits = 0) {
  return Number.isFinite(Number(value)) ? Number(value).toLocaleString('vi-VN', { maximumFractionDigits: digits }) : '—';
}
function readV4Settings() {
  return { plannerVersion: 'v4', planningFocus: document.getElementById('meal-planning-focus').value || null };
}
function restoreV4Preferences() {
  for (const [mode, meal] of Object.entries(todayMealsCache)) {
    const recipe = meal?.options?.[0]?.recipe;
    if (recipe) mealPreferences[mode] = supportedMealPreferences(recipe.preferences);
  }
  const recipe = todayMealsCache[currentMealMode]?.options?.[0]?.recipe;
  if (recipe) document.getElementById('meal-planning-focus').value = recipe.focus;
  renderMealPreferences();
}
function closeV4Modal(id) {
  if ((id === 'modal-v4-intake' && v4IntakeContext?.submitting) || (id === 'modal-v4-delete' && v4DeleteContext?.submitting) || (id === 'modal-v4-component' && v4ComponentContext?.submitting)) return;
  const el = document.getElementById(id);
  el.classList.add('hidden'); el.classList.remove('flex');
  if (id === 'modal-v4-intake' && !v4IntakeContext?.pendingPayload) v4IntakeContext = null;
  if (id === 'modal-v4-component') v4ComponentContext = null;
  if (!document.querySelector('[id^="modal-v4-"]:not(.hidden)')) document.body.classList.remove('nf-modal-open');
  const previous = v4ModalFocus.get(id);
  if (previous?.isConnected && !previous.closest('.hidden')) previous.focus();
  v4ModalFocus.delete(id);
}
function openV4Modal(id) {
  const el = document.getElementById(id);
  if (el.classList.contains('hidden')) v4ModalFocus.set(id, document.activeElement);
  el.classList.remove('hidden'); el.classList.add('flex');
  document.body.classList.add('nf-modal-open');
  el.querySelector('button:not(:disabled), input:not(:disabled), select:not(:disabled)')?.focus();
}
document.addEventListener('keydown', event => {
  const modal = Array.from(document.querySelectorAll('[id^="modal-v4-"]:not(.hidden)')).at(-1);
  if (!modal) return;
  if (event.key === 'Escape') { event.preventDefault(); closeV4Modal(modal.id); }
  if (event.key !== 'Tab') return;
  const controls = Array.from(modal.querySelectorAll('button, input, select, summary, [tabindex="0"]'))
    .filter(el => !el.matches(':disabled') && el.getClientRects().length);
  const first = controls[0], last = controls.at(-1);
  if (!first) return;
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
});
function clearV4State() {
  v4DailyRequest++;
  v4ActualGramLimits = null;
  v4Catalog = []; v4Daily = null; v4IntakeContext = null; v4ComponentContext = null; v4DeleteContext = null;
  ['modal-v4-component', 'modal-v4-intake', 'modal-v4-delete', 'modal-v4-history'].forEach(closeV4Modal);
  for (const id of ['v4-log-list', 'v4-recommendations', 'v4-macros', 'v4-status', 'v4-history-status']) document.getElementById(id).textContent = '';
  for (const id of ['v4-target-kcal', 'v4-consumed-kcal', 'v4-remaining-kcal']) document.getElementById(id).textContent = '—';
  document.getElementById('v4-energy-fill').style.width = '0%';
  document.getElementById('v4-energy-progress').removeAttribute('aria-valuenow');
  document.getElementById('v4-energy-progress').removeAttribute('data-over');
  document.getElementById('v4-progress-label').textContent = 'Chưa có dữ liệu';
  document.getElementById('v4-over-message').classList.add('hidden');
  document.getElementById('v4-target-warning').textContent = '';
  document.getElementById('v4-target-warning').classList.add('hidden');
  document.getElementById('v4-status').classList.add('hidden');
  document.getElementById('v4-macro-details').open = false;
  document.getElementById('meal-planning-focus').value = '';
  document.getElementById('v4-date').value = '';
  document.getElementById('v4-tracking-date').textContent = 'Hôm nay';
  document.getElementById('v4-intake-fields').disabled = false;
  document.getElementById('section-intake').removeAttribute('aria-busy');
}
function resetV4Metrics() {
  document.getElementById('v4-progress-label').textContent = 'Chưa có dữ liệu';
  document.getElementById('v4-energy-progress').removeAttribute('data-over');
  for (const id of ['v4-target-kcal', 'v4-consumed-kcal', 'v4-remaining-kcal']) document.getElementById(id).textContent = '—';
  document.getElementById('v4-energy-fill').style.width = '0%';
  document.getElementById('v4-energy-progress').removeAttribute('aria-valuenow');
  document.getElementById('v4-over-message').classList.add('hidden');
  document.getElementById('v4-target-warning').textContent = '';
  document.getElementById('v4-target-warning').classList.add('hidden');
}
async function loadV4Daily() {
  const uid = userProfile.id;
  if (!uid) return;
  const input = document.getElementById('v4-date');
  if (!input.value) input.value = v4Today();
  const day = input.value;
  const sequence = ++v4DailyRequest;
  const status = document.getElementById('v4-status');
  status.textContent = 'Đang tải dinh dưỡng…'; status.classList.remove('hidden');
  document.getElementById('section-intake').setAttribute('aria-busy', 'true');
  document.getElementById('v4-history-status').textContent = 'Đang tải bữa ăn…';
  if (v4Daily?.date !== day) { resetV4Metrics(); document.getElementById('v4-log-list').replaceChildren(); }
  const result = await NutriFitAPI.getDailyIntake(day);
  if (userProfile.id !== uid || input.value !== day || sequence !== v4DailyRequest) return;
  document.getElementById('section-intake').removeAttribute('aria-busy');
  if (!result.success) {
    v4Daily = null; resetV4Metrics();
    status.textContent = mealUserMessage(result, 'Chưa tải được dinh dưỡng.');
    const retry = document.createElement('button'); retry.type = 'button'; retry.className = 'nf-btn nf-btn-text'; retry.textContent = 'Thử lại'; retry.onclick = loadV4Daily; status.append(' ', retry);
    document.getElementById('v4-history-status').textContent = mealUserMessage(result, 'Chưa tải được lịch sử.');
    for (const id of ['v4-log-list', 'v4-recommendations', 'v4-macros']) document.getElementById(id).replaceChildren();
    document.getElementById('v4-progress-label').textContent = 'Chưa có dữ liệu';
    return;
  }
  v4Daily = result.data;
  status.textContent = ''; status.classList.add('hidden');
  const target = v4Daily.targets?.target_kcal;
  if (!v4ValidTarget(target) || !Number.isFinite(v4Daily.consumed?.calories)) {
    resetV4Metrics();
    document.getElementById('v4-progress-label').textContent = 'Chưa có mục tiêu dinh dưỡng';
    status.textContent = 'Chưa đủ dữ liệu mục tiêu. Hãy lưu Hồ sơ trước khi theo dõi mức vượt.';
    status.classList.remove('hidden');
    document.getElementById('v4-macros').replaceChildren();
    document.getElementById('v4-recommendations').replaceChildren();
    renderV4IntakeHistory(); return;
  }
  const consumed = v4Daily.consumed.calories;
  const percent = target > 0 ? consumed / target * 100 : 0;
  const over = v4Daily.consumed.calories > target ? (v4Daily.over_target?.calories ?? v4Daily.consumed.calories - target) : 0;
  renderV4TargetWarning(v4Daily);
  document.getElementById('v4-tracking-date').textContent = day === v4Today() ? 'Hôm nay' : new Date(day + 'T12:00:00').toLocaleDateString('vi-VN');
  document.getElementById('v4-target-kcal').textContent = v4Number(target);
  document.getElementById('v4-consumed-kcal').textContent = v4Number(consumed);
  document.getElementById('v4-remaining-kcal').textContent = v4Number(Math.max(0, v4Daily.remaining?.calories ?? target - consumed));
  document.getElementById('v4-over-kcal').textContent = v4Number(over, 1);
  document.getElementById('v4-over-message').classList.toggle('hidden', over <= 0);
  document.getElementById('v4-energy-fill').style.width = Math.min(100, Math.max(0, percent)) + '%';
  const progress = document.getElementById('v4-energy-progress');
  progress.dataset.over = String(over > 0);
  progress.setAttribute('aria-valuenow', Math.min(100, Math.max(0, percent)).toFixed(1));
  progress.setAttribute('aria-valuetext', v4Number(percent) + '% mục tiêu' + (over > 0 ? ', vượt ' + v4Number(over, 1) + ' kcal' : ''));
  document.getElementById('v4-progress-label').textContent = v4Number(percent) + '% mục tiêu ngày';
  const macros = document.getElementById('v4-macros'); macros.replaceChildren();
  for (const [key, name] of [['protein', 'Protein'], ['carbs', 'Carbs'], ['fat', 'Chất béo']]) {
    const p = document.createElement('p'), label = document.createElement('span'), value = document.createElement('b'), rest = document.createElement('span');
    const goal = v4Daily.targets.macros?.[key], actual = v4Daily.consumed[key];
    const known = v4ValidTarget(goal) && Number.isFinite(actual);
    const remaining = known ? (v4Daily.remaining?.[key] ?? goal - actual) : null;
    label.textContent = name; value.textContent = v4Number(actual, 1) + ' / ' + (known ? v4Number(goal, 1) : '—') + ' g';
    rest.textContent = !known ? 'Chưa có mục tiêu' : remaining < 0 ? 'Vượt ' + v4Number(-remaining, 1) + ' g' : 'Còn ' + v4Number(remaining, 1) + ' g';
    p.append(label, value, rest); macros.append(p);
  }
  renderV4Recommendations(day);
  renderV4IntakeHistory();
}
function v4ValidTarget(value) { return typeof value === 'number' && Number.isFinite(value) && value > 0; }
function renderV4TargetWarning(daily) {
  const warning = document.getElementById('v4-target-warning');
  const exceeded = [], missing = [];
  for (const [key, label, unit] of [['calories', 'Năng lượng', 'kcal'], ['protein', 'Protein', 'g'], ['carbs', 'Carbs', 'g'], ['fat', 'Chất béo', 'g']]) {
    const target = key === 'calories' ? daily.targets?.target_kcal : daily.targets?.macros?.[key];
    const actual = daily.consumed?.[key];
    if (!v4ValidTarget(target) || !Number.isFinite(actual)) { missing.push(label); continue; }
    // Only actual intake can trigger a warning; a selected plan is not intake.
    if (actual > target) {
      const over = daily.over_target?.[key] ?? actual - target;
      exceeded.push(label + ' +' + v4Number(over, 1) + ' ' + unit);
    }
  }
  warning.textContent = exceeded.length ? 'Vượt mục tiêu tham khảo: ' + exceeded.join(' · ') + '.' : '';
  warning.classList.toggle('hidden', !exceeded.length);
  if (missing.length) {
    const status = document.getElementById('v4-status');
    status.textContent = 'Chưa đủ dữ liệu mục tiêu: ' + missing.join(', ') + '. Hãy kiểm tra Hồ sơ.';
    status.classList.remove('hidden');
  }
}
function normalizeV4FoodName(value) {
  return String(value || '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').trim().replace(/\s+/g, ' ');
}
function rankV4FoodSearch(dishes, query, mealType) {
  const rank = dish => {
    const name = normalizeV4FoodName(dish.name);
    return [query && name === query ? 0 : query && name.startsWith(query) ? 1 : 2,
      mealType && dish.meal_types?.includes(mealType) ? 0 : 1];
  };
  return dishes.filter(d => normalizeV4FoodName(d.name).includes(query)).sort((a, b) => {
    const x = rank(a), y = rank(b);
    return x[0] - y[0] || x[1] - y[1] || a.name.localeCompare(b.name, 'vi');
  });
}
function renderV4Recommendations(day) {
  const list = document.getElementById('v4-recommendations'); list.replaceChildren();
  if (day !== v4Today()) return;
  for (const [mode, kcal] of Object.entries(v4Daily.suggested_meal_targets || {})) {
    if (mode === 'snack') {
      const label = document.createElement('span'); label.textContent = 'Bữa phụ ~' + v4Number(kcal) + ' kcal'; list.append(label); continue;
    }
    const button = document.createElement('button'); button.type = 'button';
    button.textContent = mealModes[mode].label + ' ~' + v4Number(kcal) + ' kcal';
    button.onclick = () => { switchMealMode(mode); document.getElementById('section-meals').scrollIntoView({ behavior: 'smooth' }); };
    list.append(button);
  }
}
function renderV4IntakeHistory() {
  const list = document.getElementById('v4-log-list'); list.replaceChildren();
  document.getElementById('v4-history-status').textContent = v4Daily.logs.length ? v4Daily.logs.length + ' bữa đã ghi nhận' : '';
  if (!v4Daily.logs.length) {
    const empty = document.createElement('p'); empty.className = 'nf-food-empty'; empty.textContent = 'Chưa có bữa ăn nào trong ngày này.'; list.append(empty); return;
  }
  for (const row of v4Daily.logs) {
    const box = document.createElement('div'); box.className = 'nf-log-row';
    const heading = document.createElement('div'); heading.className = 'nf-log-heading';
    const name = document.createElement('b'); name.textContent = mealModes[row.mealType]?.label || 'Bữa phụ';
    const energy = document.createElement('span'); energy.textContent = v4Number(row.totals.calories, 1) + ' kcal'; heading.append(name, energy);
    const foods = document.createElement('p');
    foods.textContent = row.source === 'legacy_meal_total' ? row.title + ' · ' + v4Number(row.servings, 1) + ' phần' : row.items.map(i => i.name + ' · ' + v4Number(i.grams, 1) + ' g').join(', ');
    const time = document.createElement('p'); time.textContent = new Date(row.consumedAtUtc.replace(' ', 'T') + 'Z').toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    const actions = document.createElement('div'); actions.className = 'nf-log-actions';
    const edit = document.createElement('button'); edit.type = 'button'; edit.textContent = 'Sửa'; edit.onclick = () => openV4IntakeEdit(row.id);
    const remove = document.createElement('button'); remove.type = 'button'; remove.textContent = 'Xóa'; remove.onclick = () => { v4DeleteContext = { id: row.id, version: row.version }; openV4Modal('modal-v4-delete'); };
    actions.append(edit, remove); box.append(heading, foods, time, actions); list.append(box);
  }
}
async function openV4IntakeHistory() {
  openV4Modal('modal-v4-history'); await loadV4Daily();
}
async function ensureV4Catalog() {
  // Refresh activity/status before opening a new intake; history uses frozen values.
  const uid = userProfile.id;
  const status = document.getElementById('v4-food-count');
  status.textContent = 'Đang tải danh sách món…';
  const result = await NutriFitAPI.getFoodCatalog();
  if (uid !== userProfile.id) return false;
  if (!result.success || !Array.isArray(result.data)) {
    v4Catalog = []; document.getElementById('v4-food-results').replaceChildren();
    status.textContent = mealUserMessage(result, 'Chưa tải được danh sách món. Hãy thử lại.');
    await handleMealError(result); return false;
  }
  v4Catalog = result.data; v4ActualGramLimits = result.intake_gram_limits || null;
  status.textContent = v4Catalog.length ? v4Catalog.length + ' món ăn có thể lựa chọn.' : 'Danh sách món ăn hiện đang trống.';
  return true;
}
function v4ComponentCurrent(context) {
  return context === v4ComponentContext && context.uid === userProfile.id && context.cache === todayMealsCache;
}
async function openV4ComponentPicker(optionId, componentType) {
  if (v4ComponentContext?.submitting) return;
  const mode = currentMealMode, meal = todayMealsCache[mode];
  if (!userProfile.id || !meal || mealPending[mode]) return;
  if (meal.catalog_refresh_required) { showMealToast('Danh sách món đã cập nhật. Hãy đổi cả bộ gợi ý trước khi thay món.', 'error'); return; }
  if (meal.status === 'decided' || meal.selectedOption != null) {
    showMealToast('Thực đơn đã chốt. Chọn Nghĩ sau trước khi đổi món.', 'error'); return;
  }
  if (v4ComponentCurrent(v4ComponentContext || {}) && v4ComponentContext.loading && v4ComponentContext.optionId === optionId && v4ComponentContext.componentType === componentType && v4ComponentContext.mealType === mode) return;
  const option = meal.options.find(o => o.optionId === optionId);
  if (!option?.recipe?.components.some(c => c.type === componentType)) {
    showMealToast('Món này chưa có dữ liệu để thay từng thành phần. Hãy tạo bộ gợi ý mới.', 'error'); return;
  }
  const context = { uid: userProfile.id, cache: todayMealsCache, mealType: mode, optionId,
    componentType, revision: meal.revision, choices: [], loading: true, submitting: false };
  v4ComponentContext = context;
  document.getElementById('v4-component-query').value = '';
  document.getElementById('v4-component-source').textContent = 'Tìm món cùng nhóm, phù hợp bữa ăn. Khẩu vị đã lưu vẫn được kiểm tra khi thay.';
  document.getElementById('v4-component-status').textContent = 'Đang tải món ăn…';
  document.getElementById('v4-component-query').disabled = true;
  document.getElementById('v4-component-dish').replaceChildren();
  updateV4ReplacementPortion(); openV4Modal('modal-v4-component');
  try {
    // Catalog lookup is available to FREE accounts and does not call Gemini.
    const result = await NutriFitAPI.getFoodCatalog();
    if (!v4ComponentCurrent(context)) return;
    if (todayMealsCache[mode]?.revision !== context.revision) {
      closeV4Modal('modal-v4-component'); showMealToast('Thực đơn đã thay đổi. Hãy mở lại Đổi món.', 'error'); return;
    }
    if (!result.success || !Array.isArray(result.data)) {
      document.getElementById('v4-component-status').textContent = mealUserMessage(result, 'Chưa tải được món. Đóng và mở lại để thử lại.'); return;
    }
    context.choices = result.data.filter(d => d.type === componentType && d.meal_types?.includes(mode) && d.preparation_state !== 'raw');
    context.loading = false;
    renderV4ComponentSearch();
  } catch (_) {
    if (v4ComponentCurrent(context)) document.getElementById('v4-component-status').textContent = 'Chưa tải được món. Đóng và mở lại để thử lại.';
  } finally {
    if (v4ComponentCurrent(context)) {
      context.loading = false;
      document.getElementById('v4-component-query').disabled = false;
      updateV4ComponentPreview();
    }
  }
}
function renderV4ComponentSearch() {
  const context = v4ComponentContext;
  if (!context || context.loading || context.submitting) return;
  const select = document.getElementById('v4-component-dish'), previous = select.value;
  const query = normalizeV4FoodName(document.getElementById('v4-component-query').value);
  const matches = rankV4FoodSearch(context.choices, query, context.mealType);
  select.replaceChildren();
  const placeholder = document.createElement('option'); placeholder.value = ''; placeholder.textContent = 'Chọn món thay thế'; select.append(placeholder);
  for (const dish of matches) {
    const item = document.createElement('option'); item.value = dish.dish_id;
    const factor = dish.reference_grams / 100, macro = dish.macros_per_100g;
    item.textContent = dish.name + ' · ' + v4Number(dish.reference_grams) + ' g · ~' + v4Number(dish.calories_per_100g * factor, 1) + ' kcal · P/C/F ' + ['protein', 'carbs', 'fat'].map(k => v4Number(macro[k] * factor, 1)).join('/') + ' g';
    select.append(item);
  }
  select.value = matches.some(d => d.dish_id === previous) ? previous : '';
  select.disabled = !matches.length;
  document.getElementById('v4-component-status').textContent = !context.choices.length ? 'Chưa có món đủ điều kiện cho nhóm và bữa ăn này.' : query ? 'Tìm thấy ' + matches.length + '/' + context.choices.length + ' món đủ điều kiện cho nhóm và bữa ăn này.' : context.choices.length + ' món đủ điều kiện cho nhóm và bữa ăn này.';
  if (context.choices.length && !matches.length) document.getElementById('v4-component-status').textContent += ' Không tìm thấy món với từ khóa này. Thử tên khác nhé.';
  if (select.value && select.value === previous) updateV4ComponentPreview();
  else updateV4ReplacementPortion();
}
function updateV4ReplacementPortion() {
  const dish = v4ComponentContext?.choices.find(d => d.dish_id === document.getElementById('v4-component-dish').value);
  const input = document.getElementById('v4-component-grams');
  if (dish) { input.min = dish.min_grams; input.max = dish.max_grams; input.value = dish.reference_grams; }
  else input.value = '';
  updateV4ComponentPreview();
}
function updateV4ComponentPreview() {
  const context = v4ComponentContext;
  const dish = context?.choices.find(d => d.dish_id === document.getElementById('v4-component-dish').value);
  const grams = Number(document.getElementById('v4-component-grams').value);
  const valid = !!dish && Number.isFinite(grams) && grams >= dish.min_grams && grams <= dish.max_grams;
  document.getElementById('v4-component-grams').disabled = !dish || !!context?.submitting;
  document.getElementById('v4-component-save').disabled = !valid || !!context?.loading || !!context?.submitting;
  document.getElementById('v4-component-reason').textContent = !dish ? 'Chọn một món để xem khẩu phần và dinh dưỡng.' : !valid ? 'Khẩu phần cần từ ' + dish.min_grams + ' đến ' + dish.max_grams + ' g.' : '~' + v4Number(dish.calories_per_100g * grams / 100, 1) + ' kcal · ' + [['protein', 'Protein'], ['carbs', 'Carbs'], ['fat', 'Chất béo']].map(([k, label]) => label + ' ' + v4Number(dish.macros_per_100g[k] * grams / 100, 1) + ' g').join(' · ') + ' (ước tính).';
  return valid;
}
async function applyV4Component() {
  const context = v4ComponentContext;
  if (!context || !v4ComponentCurrent(context) || context.loading || context.submitting || !updateV4ComponentPreview()) return;
  if (mealPending[context.mealType]) return;
  const button = document.getElementById('v4-component-save'); context.submitting = true; button.disabled = true;
  const current = () => v4ComponentCurrent(context);
  document.getElementById('v4-component-query').disabled = true;
  document.getElementById('v4-component-dish').disabled = true;
  document.getElementById('v4-component-grams').disabled = true;
  // Share the per-meal mutation lock with refresh/select; retain server revision protection.
  const token = { uid: context.uid, cache: context.cache };
  mealPending[context.mealType] = token; mealLoadSequence++; updateMealLoading();
  try {
    const result = await NutriFitAPI.replaceComponent({ mealType: context.mealType, optionId: context.optionId,
      componentType: context.componentType, revision: context.revision,
      dishId: document.getElementById('v4-component-dish').value, grams: Number(document.getElementById('v4-component-grams').value) });
    if (!current()) return;
    if (!result.success) {
      if (result.httpStatus === 409) { context.submitting = false; closeV4Modal('modal-v4-component'); }
      else document.getElementById('v4-component-status').textContent = mealUserMessage(result, 'Chưa đổi được món.');
      await handleMealError(result); return;
    }
    if (!Array.isArray(result.data?.options) || !result.data?.revision) {
      document.getElementById('v4-component-status').textContent = 'Dữ liệu thực đơn chưa đầy đủ. Hãy tải lại.'; return;
    }
    mealLoadSequence++; todayMealsCache[context.mealType] = result.data; renderCurrentMealMode();
    context.submitting = false; closeV4Modal('modal-v4-component');
    await loadDashboardSummary();
    if (context.uid === userProfile.id && context.cache === todayMealsCache) showMealToast('Đã đổi món và cập nhật kế hoạch!');
  } catch (_) {
    if (current()) document.getElementById('v4-component-status').textContent = 'Chưa đổi được món. Thử lại hoặc tải lại thực đơn.';
  } finally {
    context.submitting = false;
    if (mealPending[context.mealType] === token) mealPending[context.mealType] = null;
    updateMealLoading();
    if (current()) {
      document.getElementById('v4-component-query').disabled = false;
      document.getElementById('v4-component-dish').disabled = false;
      updateV4ComponentPreview();
    }
  }
}
function v4IntakeError(message = '') {
  const error = document.getElementById('v4-intake-error'); error.textContent = message; error.classList.toggle('hidden', !message);
}
function setV4IntakeForm(context, mealType, when = new Date()) {
  closeV4Modal('modal-v4-history');
  v4IntakeContext = { ...context, submitting: false, pendingPayload: null };
  document.getElementById('v4-intake-fields').disabled = false;
  document.getElementById('v4-intake-meal').value = mealType;
  document.getElementById('v4-intake-meal').disabled = !!context.meal;
  document.getElementById('v4-intake-time').value = v4LocalTime(when);
  document.getElementById('v4-intake-title').textContent = context.id ? 'Chỉnh sửa bữa ăn' : 'Ghi nhận bữa ăn';
  v4IntakeError(); closeV4FoodSearch(); renderV4IntakeItems(); openV4Modal('modal-v4-intake');
}
function resumeV4Intake() {
  if (!v4IntakeContext?.pendingPayload) return false;
  openV4Modal('modal-v4-intake'); return true;
}
async function openV4IntakeForMeal(optionId) {
  if (resumeV4Intake()) return;
  const uid = userProfile.id, meal = todayMealsCache[currentMealMode];
  const option = meal?.options.find(o => o.optionId === optionId);
  if (!option) return;
  if (meal.catalog_refresh_required) { showMealToast('Bộ gợi ý đã cũ. Hãy đổi bộ hoặc dùng Thêm bữa ăn để chọn món hiện tại.', 'error'); return; }
  if (option.recipe && !await ensureV4Catalog()) return;
  if (uid !== userProfile.id) return;
  setV4IntakeForm({ requestId: crypto.randomUUID(), meal: { optionId, revision: meal.revision },
    items: option.recipe ? option.recipe.components.map(c => ({ dish_id: c.dish_id, grams: Math.round(c.grams) })) : [],
    legacy: !option.recipe, title: option.title, servings: 1,
    baseTotals: { calories: option.calories, ...option.macros } }, meal.mealType);
}
async function openV4IntakeOutside() {
  if (resumeV4Intake()) return;
  if (!await ensureV4Catalog()) return;
  setV4IntakeForm({ requestId: crypto.randomUUID(), items: [] }, currentMealMode);
  addV4IntakeItem();
}
async function openV4IntakeEdit(id) {
  if (resumeV4Intake()) return;
  const uid = userProfile.id, row = v4Daily?.logs.find(r => r.id === id);
  if (!row) return;
  if (row.source !== 'legacy_meal_total' && !await ensureV4Catalog()) return;
  if (uid !== userProfile.id) return;
  const perServing = Object.fromEntries(Object.entries(row.totals).map(([k, v]) => [k, v / (row.servings || 1)]));
  const frozenCatalog = row.items.map(part => {
    const nutrition = part.nutrition_per_100g || { calories: part.calories / part.grams * 100,
      ...Object.fromEntries(Object.entries(part.macros).map(([k, v]) => [k, v / part.grams * 100])) };
    const { calories, ...macros } = nutrition;
    return { dish_id: part.dish_id, name: part.name, calories_per_100g: calories, macros_per_100g: macros,
      min_grams: part.portion_limits?.min, max_grams: part.portion_limits?.max };
  });
  setV4IntakeForm({ id: row.id, version: row.version, items: row.items.map(i => ({ dish_id: i.dish_id, grams: i.grams })),
    frozenCatalog, legacy: row.source === 'legacy_meal_total', title: row.title, servings: row.servings, baseTotals: perServing },
    row.mealType, new Date(row.consumedAtUtc.replace(' ', 'T') + 'Z'));
}
function v4ItemPreview(item) {
  const dish = v4IntakeDish(item.dish_id);
  const bounds = v4IntakeBounds(item.dish_id);
  if (!dish || !bounds || !Number.isFinite(item.grams) || item.grams < bounds.min || item.grams > bounds.max) return null;
  // Display estimate from the existing backend catalog; saved response remains authoritative.
  const round4 = n => Number(n.toFixed(4));
  const macros = Object.fromEntries(Object.entries(dish.macros_per_100g).map(([k, v]) => [k, round4(v * item.grams / 100)]));
  return { calories: round4(dish.calories_per_100g * item.grams / 100), ...macros };
}
function v4IntakeDish(id) {
  const live = v4Catalog.find(d => d.dish_id === id);
  const frozen = v4IntakeContext?.frozenCatalog?.find(d => d.dish_id === id);
  if (!frozen) return live;
  return { ...live, ...frozen,
    min_grams: frozen.min_grams ?? live?.min_grams ?? v4ActualGramLimits?.min,
    max_grams: frozen.max_grams ?? live?.max_grams ?? v4ActualGramLimits?.max };
}
function v4IntakeBounds(id) {
  const dish = v4IntakeDish(id);
  const min = dish?.min_grams, max = dish?.max_grams;
  return typeof min === 'number' && typeof max === 'number' && Number.isFinite(min) && Number.isFinite(max) && min > 0 && max >= min ? { min, max } : null;
}
function v4IntakePreview() {
  const context = v4IntakeContext;
  if (!context) return null;
  const keys = ['calories', 'carbs', 'protein', 'fat', 'fiber'];
  if (context.legacy) {
    if (!Number.isFinite(context.servings) || context.servings < 0.1 || context.servings > 4) return null;
    return Object.fromEntries(keys.map(k => [k, Number((context.baseTotals[k] * context.servings).toFixed(1))]));
  }
  if (!context.items.length || context.items.length > 20) return null;
  const parts = context.items.map(v4ItemPreview);
  if (parts.some(p => !p)) return null;
  return Object.fromEntries(keys.map(k => [k, Number(parts.reduce((sum, p) => sum + p[k], 0).toFixed(1))]));
}
function updateV4IntakeTotal() {
  const context = v4IntakeContext;
  if (!context) return;
  const total = v4IntakePreview();
  document.getElementById('v4-intake-kcal').textContent = total ? v4Number(total.calories, 1) : (context.items.length || context.legacy ? '—' : '0');
  document.getElementById('v4-intake-macros').textContent = total ? 'Protein ' + v4Number(total.protein, 1) + ' g · Carbs ' + v4Number(total.carbs, 1) + ' g · Chất béo ' + v4Number(total.fat, 1) + ' g' : 'Thêm món và nhập khẩu phần hợp lệ.';
  const button = document.getElementById('v4-intake-save');
  button.disabled = context.submitting || (!total && !context.pendingPayload);
  button.textContent = context.submitting ? 'Đang ghi nhận…' : context.pendingPayload ? 'Thử ghi nhận lại' : context.id ? 'Lưu thay đổi' : 'Ghi nhận bữa ăn';
}
function renderV4IntakeItems() {
  const context = v4IntakeContext;
  if (!context) return;
  const list = document.getElementById('v4-intake-items'); list.replaceChildren();
  document.getElementById('v4-add-item').classList.toggle('hidden', !!context.legacy);
  if (!context.legacy && !context.items.length) {
    const empty = document.createElement('p'); empty.className = 'nf-food-empty'; empty.textContent = 'Thêm món bạn đã ăn để bắt đầu.'; list.append(empty);
  }
  const rows = context.legacy ? [{ legacy: true }] : context.items;
  rows.forEach((item, index) => {
    const dish = item.legacy ? null : v4IntakeDish(item.dish_id);
    const row = document.createElement('div'); row.className = 'nf-food-row';
    const info = document.createElement('div'), name = document.createElement('h4'), portion = document.createElement('p');
    name.textContent = item.legacy ? context.title : dish?.name || 'Món chưa có thông tin';
    portion.textContent = item.legacy ? 'Tổng dinh dưỡng của bữa ăn đã lưu, ước tính theo phần.' : 'Khẩu phần thực tế'; info.append(name, portion);
    const controls = document.createElement('div'); controls.className = 'nf-food-controls';
    const calories = document.createElement('span'); calories.className = 'nf-food-kcal';
    const quantity = document.createElement('div'); quantity.className = 'nf-portion';
    const bounds = item.legacy ? { min: 0.1, max: 4 } : v4IntakeBounds(item.dish_id);
    const input = document.createElement('input'); input.type = 'number';
    if (bounds) { input.min = String(bounds.min); input.max = String(bounds.max); } input.step = item.legacy ? '0.1' : '1'; input.value = item.legacy ? context.servings : Number(item.grams.toFixed(1)); input.setAttribute('aria-label', item.legacy ? 'Số phần thực tế' : 'Gram thực tế của ' + name.textContent);
    if (item.legacy) input.id = 'v4-intake-servings';
    const field = document.createElement('div'); field.className = 'nf-portion-field';
    const error = document.createElement('p'); error.id = 'v4-portion-error-' + index; error.className = 'nf-portion-error'; error.setAttribute('aria-live', 'polite');
    input.setAttribute('aria-describedby', error.id);
    const refresh = () => {
      const value = item.legacy ? v4IntakePreview() : v4ItemPreview(item);
      calories.textContent = (value ? v4Number(value.calories, 1) : '—') + ' kcal';
      input.setAttribute('aria-invalid', String(!value));
      error.textContent = value ? '' : !bounds ? 'Chưa có giới hạn khẩu phần. Hãy tải lại dữ liệu món ăn.' : 'Khẩu phần không hợp lệ. Vui lòng nhập từ ' + bounds.min + ' đến ' + bounds.max + (item.legacy ? ' phần.' : ' g.');
      error.classList.toggle('hidden', !!value);
      updateV4IntakeTotal();
    };
    input.oninput = () => {
      if (context.submitting || context.pendingPayload) return;
      const value = input.value === '' ? NaN : Number(input.value);
      if (item.legacy) context.servings = value; else item.grams = value;
      v4IntakeError(); refresh();
    };
    const change = delta => {
      if (context.submitting || context.pendingPayload || !bounds) return;
      const current = item.legacy ? context.servings : item.grams;
      const next = Number(Math.min(Number(input.max), Math.max(Number(input.min), (Number.isFinite(current) ? current : Number(input.min)) + delta)).toFixed(1));
      if (item.legacy) context.servings = next; else item.grams = next;
      input.value = next; v4IntakeError(); refresh();
    };
    const minus = document.createElement('button'); minus.type = 'button'; minus.className = 'nf-icon-btn'; minus.textContent = '−'; minus.setAttribute('aria-label', 'Giảm khẩu phần của ' + name.textContent); minus.onclick = () => change(item.legacy ? -0.1 : -10);
    const plus = document.createElement('button'); plus.type = 'button'; plus.className = 'nf-icon-btn'; plus.textContent = '+'; plus.setAttribute('aria-label', 'Tăng khẩu phần của ' + name.textContent); plus.onclick = () => change(item.legacy ? 0.1 : 10);
    const unit = document.createElement('span'); unit.className = 'nf-muted'; unit.textContent = item.legacy ? 'phần' : 'g';
    const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'nf-icon-btn'; remove.textContent = '×'; remove.setAttribute('aria-label', 'Bỏ ' + name.textContent + ' khỏi lần ghi nhận'); remove.onclick = () => {
      if (context.submitting || context.pendingPayload) return;
      if (item.legacy) { context.legacy = false; context.items = []; } else context.items.splice(index, 1);
      v4IntakeError(); renderV4IntakeItems();
    };
    quantity.append(minus, input, unit, plus); field.append(quantity, error); controls.append(calories, field, remove); row.append(info, controls); list.append(row); refresh();
  });
  updateV4IntakeTotal();
}
async function addV4IntakeItem() {
  if (!v4IntakeContext || v4IntakeContext.submitting || v4IntakeContext.pendingPayload) return;
  if (v4IntakeContext.items.length >= 20) { v4IntakeError('Mỗi bữa ăn có tối đa 20 món.'); return; }
  if (!await ensureV4Catalog() || !v4IntakeContext) return;
  document.getElementById('v4-food-search').classList.remove('hidden');
  document.getElementById('v4-food-query').value = '';
  renderV4FoodSearch(); document.getElementById('v4-food-query').focus();
}
function closeV4FoodSearch() { document.getElementById('v4-food-search').classList.add('hidden'); }
function renderV4FoodSearch() {
  const query = normalizeV4FoodName(document.getElementById('v4-food-query').value);
  const list = document.getElementById('v4-food-results'); list.replaceChildren();
  const matches = rankV4FoodSearch(v4Catalog, query, document.getElementById("v4-intake-meal").value);
  const count = document.getElementById('v4-food-count');
  count.textContent = !v4Catalog.length ? 'Danh sách món ăn hiện đang trống.' : query ? 'Tìm thấy ' + matches.length + '/' + v4Catalog.length + ' món.' : v4Catalog.length + ' món ăn có thể lựa chọn.';
  if (!matches.length) { const p = document.createElement('p'); p.className = 'nf-muted'; p.textContent = v4Catalog.length ? 'Không tìm thấy món. Thử tên khác nhé.' : 'Chưa có món ăn để lựa chọn.'; list.append(p); }
  for (const dish of matches) {
    const button = document.createElement('button'); button.type = 'button';
    const name = document.createElement('span'); name.textContent = dish.name;
    const estimate = document.createElement('small'); estimate.textContent = v4Number(dish.reference_grams) + ' g · ~' + v4Number(dish.calories_per_100g * dish.reference_grams / 100) + ' kcal';
    button.append(name, estimate); button.onclick = () => {
      const context = v4IntakeContext;
      if (!context || context.submitting || context.pendingPayload || context.items.length >= 20) return;
      context.items.push({ dish_id: dish.dish_id, grams: Math.round(dish.reference_grams) });
      closeV4FoodSearch(); v4IntakeError(); renderV4IntakeItems();
      document.querySelector('#v4-intake-items .nf-food-row:last-child input')?.focus();
    };
    list.append(button);
  }
}
async function saveV4Intake() {
  const context = v4IntakeContext;
  if (!context || context.submitting) return;
  const uid = userProfile.id;
  if (!uid) return;
  let payload = context.pendingPayload;
  if (!payload) {
    if (!v4IntakePreview()) { v4IntakeError(context.items.length || context.legacy ? 'Hãy kiểm tra khẩu phần được báo lỗi bên dưới từng món.' : 'Hãy thêm ít nhất một món bạn đã ăn.'); return; }
    const when = new Date(document.getElementById('v4-intake-time').value);
    if (!Number.isFinite(when.getTime())) { v4IntakeError('Hãy nhập thời gian ăn hợp lệ.'); return; }
    payload = { confirmed: true, mealType: document.getElementById('v4-intake-meal').value, consumedAt: when.toISOString(),
      ...(context.meal ? { meal: context.meal } : {}),
      ...(context.legacy ? { servings: context.servings } : { items: structuredClone(context.items) }),
      ...(context.id ? { version: context.version } : { requestId: context.requestId }) };
  }
  // Keep the exact payload/UUID while retrying an uncertain response, without a second write.
  context.pendingPayload = payload; context.submitting = true;
  document.getElementById('v4-intake-fields').disabled = true;
  v4IntakeError(); updateV4IntakeTotal();
  try {
    const result = context.id ? await NutriFitAPI.updateIntake(context.id, payload) : await NutriFitAPI.addIntake(payload);
    if (uid !== userProfile.id || context !== v4IntakeContext) return;
    if (!result.success) {
      if (result.httpStatus >= 400 && result.httpStatus < 500) { context.pendingPayload = null; document.getElementById('v4-intake-fields').disabled = false; }
      v4IntakeError(mealUserMessage(result, 'Chưa nhận được xác nhận. Thử lại hoặc kiểm tra Lịch sử trước khi nhập lại.'));
      return;
    }
    context.pendingPayload = null; context.submitting = false;
    closeV4Modal('modal-v4-intake');
    document.getElementById('v4-date').value = result.data.date;
    await loadDashboardSummary(false); await loadV4Daily(); showMealToast(context.id ? 'Đã cập nhật bữa ăn!' : 'Đã ghi nhận bữa ăn!');
  } catch (_) {
    if (uid === userProfile.id && context === v4IntakeContext) v4IntakeError('Chưa nhận được xác nhận. Thử lại để tránh ghi trùng.');
  } finally {
    context.submitting = false;
    if (context === v4IntakeContext) updateV4IntakeTotal();
  }
}
async function confirmV4Delete() {
  const context = v4DeleteContext;
  if (!context || context.submitting) return;
  const uid = userProfile.id, button = document.getElementById('v4-delete-save');
  button.disabled = true; context.submitting = true;
  try {
    const result = await NutriFitAPI.deleteIntake(context.id, context.version);
    if (uid !== userProfile.id) return;
    if (!result.success) { await handleMealError(result); return; }
    context.submitting = false; closeV4Modal('modal-v4-delete'); v4DeleteContext = null;
    await loadDashboardSummary(false); await loadV4Daily(); showMealToast('Đã xóa bữa ăn và cập nhật dinh dưỡng!');
  } finally { context.submitting = false; button.disabled = false; }
}
