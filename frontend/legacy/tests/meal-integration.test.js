/* Focused JS regression with a fake DOM and mocked API. No HTTP or database calls.
 * Run: node frontend/tests/meal-integration.test.js
 */
async function runMealIntegrationTests(sources) {
  const results = [];
  const assert = (value, message) => { if (!value) throw new Error(message); };
  const copy = value => JSON.parse(JSON.stringify(value));
  const deferred = () => { let resolve; const promise = new Promise(done => { resolve = done; }); return { promise, resolve }; };
  async function test(name, check) {
    try { await check(); results.push({ name, pass: true }); }
    catch (error) { results.push({ name, pass: false, error: error.message }); }
  }
  function dom() {
    const elements = new Map();
    const element = () => {
      const classes = new Set(['hidden']);
      return { value: '', checked: false, disabled: false, textContent: '', innerHTML: '', innerText: '',
        children: [], style: {}, dataset: {}, attributes: {}, isConnected: true,
        classList: { add(...names) { names.forEach(n => classes.add(n)); }, remove(...names) { names.forEach(n => classes.delete(n)); },
          contains: n => classes.has(n), toggle(n, force) { const add = force ?? !classes.has(n); if (add) classes.add(n); else classes.delete(n); } },
        setAttribute(k, v) { this.attributes[k] = v; }, removeAttribute(k) { delete this.attributes[k]; },
        querySelector() { return element(); }, closest() { return null; }, focus() {},
        replaceChildren(...nodes) { this.children = nodes; }, append(...nodes) { this.children.push(...nodes); } };
    };
    return { elements, body: element(), activeElement: null, addEventListener() {}, dispatchEvent() {}, querySelectorAll() { return []; }, querySelector() { return null; },
      getElementById(id) { if (!elements.has(id)) elements.set(id, element()); return elements.get(id); }, createElement: element };
  }
  function meal(label = 'old', revision = 'a'.repeat(24), grams = 100) {
    return { mealType: 'lunch', status: 'pending', selectedOption: null, revision,
      options: [1, 2, 3].map(id => ({ id, optionId: id, title: label + id, calories: 500, macros: { protein: 30, carbs: 60, fat: 15 },
        components: [{ type: 'PROTEIN', dish_id: label + id, name: label + id, grams }],
        recipe: { focus: 'maintain', preferences: {}, components: [{ type: 'PROTEIN', dish_id: label + id, name: label + id, grams }] } })) };
  }
  const success = data => ({ success: true, data, meta: { cached: false } });
  function harness(api = {}) {
    const document = dom(), profile = { id: 7 }, toasts = [];
    const mockApi = { getTodayMeals: async () => ({ success: true, todayMeals: { breakfast: null, lunch: meal('server'), dinner: null } }), ...api };
    const create = new Function('document', 'window', 'userProfile', 'NutriFitAPI', 'lucide', 'loadDashboardSummary', 'structuredClone', 'toasts',
      sources.meals + '\n' + sources.nutrition + `
      showMealToast = (message, kind = 'success') => toasts.push({ message, kind });
      hideMealToast = () => {};
      v4Today = () => '2026-10-12';
      return { generate: generateMealSuggestions, apply: applyMealPreferences, select: selectMeal, load: loadTodayMeals,
        openComponent: openV4ComponentPicker, searchComponent: renderV4ComponentSearch,
        chooseComponent: updateV4ReplacementPortion, componentPreview: updateV4ComponentPreview,
        replaceComponent: applyV4Component, closeModal: closeV4Modal, loadDaily: loadV4Daily,
        foodSearch: renderV4FoodSearch, saveIntake: saveV4Intake, deleteIntake: confirmV4Delete,
        renderIntake: renderV4IntakeItems, previewIntake: v4IntakePreview, loadCatalog: ensureV4Catalog,
        setActualLimits: value => { v4ActualGramLimits = value; },
        setDelete: value => { v4DeleteContext = value; },
        setCatalog: value => { v4Catalog = value; },
        setIntake: value => { v4IntakeContext = value; },
        setMeal: (mode, value) => { todayMealsCache[mode] = value; },
        setMode: mode => { currentMealMode = mode; },
        reset: id => { userProfile.id = id; todayMealsCache = { breakfast: null, lunch: null, dinner: null }; },
        state: () => ({ cache: todayMealsCache, preferences: mealPreferences, component: v4ComponentContext, daily: v4Daily }) };
      `);
    const actions = create(document, {}, profile, mockApi, { createIcons() {} }, async () => {}, copy, toasts);
    return { ...actions, document, profile, toasts };
  }
  await test('API uses cookie for Nutrition/Auth/Profile and retains Core headers', async () => {
    const calls = [], window = {}, document = dom();
    const fetch = async (url, options) => { calls.push({ url, options }); return { ok: true, status: 200, json: async () => ({ success: true }) }; };
    const SearchParams = globalThis.URLSearchParams || class {
      constructor() { this.values = new Map(); }
      set(key, value) { this.values.set(key, value); }
      toString() { return [...this.values].map(([k, v]) => encodeURIComponent(k) + '=' + encodeURIComponent(v)).join('&'); }
    };
    const api = new Function('window', 'document', 'localStorage', 'fetch', 'console', 'URLSearchParams', sources.api + '\nreturn { api: NutriFitAPI, request };')(
      window, document, { getItem: () => '{"user":{"id":7}}' }, fetch, { error() {} }, SearchParams);
    await api.api.getNutrition(); await api.api.generateMeal('lunch', true, 'a'.repeat(24));
    await api.api.getFoodCatalog(); await api.api.searchQuickFood('thit kho'); await api.api.getProfile(7);
    await api.api.login('demo@example.invalid', 'mock-input');
    for (const call of calls) {
      assert(!('X-User-Id' in call.options.headers), 'Unexpected legacy header');
      assert(call.options.credentials === 'include', 'Cookie missing');
    }
    await api.api.createCheckout(1); await api.api.getPaymentHistory(); await api.api.getAdminUsers();
    assert(calls.slice(-3).every(c => c.options.headers['X-User-Id'] === '7'), 'Core compatibility broken');
    await api.request('/api/payment-other'); assert(!('X-User-Id' in calls.at(-1).options.headers), 'Header prefix too broad');
  });
  await test('Refresh waits for API, sends revision, updates cache and rendered DOM', async () => {
    const wait = deferred(); let payload;
    const h = harness({ generateMeal: (...args) => { payload = args; return wait.promise; } }); h.setMeal('lunch', meal());
    const pending = h.generate(true);
    assert(h.document.getElementById('btn-refresh-meals').disabled, 'Missing loading guard');
    assert(!h.toasts.length, 'Premature success');
    wait.resolve(success(meal('new', 'b'.repeat(24)))); await pending;
    assert(payload[1] === true && payload[2] === 'a'.repeat(24), 'Wrong refresh/revision');
    assert(h.state().cache.lunch.revision === 'b'.repeat(24), 'Cache stale');
    assert(h.document.getElementById('meal-options-container').innerHTML.includes('new1'), 'DOM stale');
    assert(!h.document.getElementById('btn-refresh-meals').disabled, 'Loading not cleared');
  });
  await test('Repeated/reordered dishes do not claim different food', async () => {
    const next = meal(); next.revision = 'b'.repeat(24); next.options.reverse();
    const h = harness({ generateMeal: async () => success(next) }); h.setMeal('lunch', meal()); await h.generate(true);
    assert(h.toasts.at(-1).message.includes('vẫn giống'), 'Misleading refresh success');
  });
  await test('Only changed grams are reported as portion updates', async () => {
    const h = harness({ generateMeal: async () => success(meal('old', 'b'.repeat(24), 130)) }); h.setMeal('lunch', meal()); await h.generate(true);
    assert(h.toasts.at(-1).message.includes('khẩu phần'), 'Portion change mislabeled');
  });
  await test('Cached response is reported as a reload', async () => {
    const h = harness({ generateMeal: async () => ({ ...success(meal()), meta: { cached: true } }) }); h.setMeal('lunch', meal()); await h.generate(false);
    assert(h.toasts.at(-1).message === 'Đã tải lại thực đơn của bạn!', 'Cache mislabeled');
  });
  await test('Selecting an option calls select only, not generation or intake', async () => {
    let args; const picked = meal(); picked.selectedOption = 2; picked.status = 'decided';
    const h = harness({ selectMealOption: async (...values) => { args = values; return success(picked); } }); h.setMeal('lunch', meal()); await h.select(2);
    assert(args[1] === 2 && args[2] === 'a'.repeat(24), 'Wrong selection');
    assert(h.state().cache.lunch.selectedOption === 2, 'Selection not updated');
    assert(h.document.getElementById('meal-options-container').innerHTML.includes('Đã chọn thực đơn này'), 'Selection not rendered');
  });
  await test('Think later sends null and retains the returned plan', async () => {
    let selected; const h = harness({ selectMealOption: async (_, value) => { selected = value; return success(meal()); } }); h.setMeal('lunch', meal()); await h.select(null);
    assert(selected === null && h.toasts.at(-1).message.includes('Nghĩ sau'), 'Think later broken');
  });
  await test('Apply preferences refreshes existing plan and sends distinct preference fields', async () => {
    let args; const next = meal('new'); next.options[0].recipe.preferences = { avoid: ['fish'], dislikes: ['beef'], prefer: ['chicken'] };
    const h = harness({ generateMeal: async (...values) => { args = values; return success(next); } }); h.setMeal('lunch', meal());
    for (const [id, value] of [['meal-avoid', 'cá'], ['meal-dislikes', 'bò'], ['meal-prefer', 'gà']]) h.document.getElementById(id).value = value;
    await h.apply();
    assert(args[1] === true && args[2] === 'a'.repeat(24), 'Preferences did not refresh');
    assert(args[3].avoid[0] === 'cá' && args[3].dislikes[0] === 'bò' && args[3].prefer[0] === 'gà', 'Preference fields mixed');
    assert(h.state().preferences.lunch.avoid[0] === 'fish', 'Backend preferences not restored');
  });
  await test('Apply preferences generates first plan without a stale revision', async () => {
    let args; const h = harness({ generateMeal: async (...values) => { args = values; return success(meal('new')); } }); await h.apply();
    assert(args[1] === false && args[2] === null, 'First generation incorrectly refreshed');
  });
  await test('Decided plan is not silently unselected or refreshed', async () => {
    let called = false; const h = harness({ generateMeal: async () => { called = true; return success(meal()); } }); const picked = meal(); picked.selectedOption = 1; picked.status = 'decided'; h.setMeal('lunch', picked); await h.apply();
    assert(!called && h.toasts.at(-1).kind === 'error', 'Decided guard bypassed');
  });
  await test('STALE_MEAL reloads authoritative data and does not show success', async () => {
    const h = harness({ generateMeal: async () => ({ success: false, httpStatus: 409, code: 'STALE_MEAL' }) }); h.setMeal('lunch', meal()); await h.generate(true);
    assert(h.state().cache.lunch.options[0].title === 'server1', 'Stale recovery failed');
    assert(h.toasts.at(-1).kind === 'error', '409 reported as success');
  });
  await test('Changed cached preferences show an explicit apply instruction', async () => {
    const h = harness({ generateMeal: async () => ({ success: false, httpStatus: 409, code: 'PREFERENCES_REQUIRE_REFRESH' }) }); h.setMeal('lunch', meal()); await h.generate(false);
    assert(h.toasts.at(-1).message.includes('Áp dụng khẩu vị'), 'Missing preference action');
  });
  await test('Server error keeps the old plan and clears loading', async () => {
    const h = harness({ generateMeal: async () => ({ success: false, httpStatus: 500, message: 'mock failure' }) }); h.setMeal('lunch', meal()); await h.generate(true);
    assert(h.state().cache.lunch.options[0].title === 'old1', 'Failed request replaced plan');
    assert(h.toasts.at(-1).kind === 'error' && !h.document.getElementById('btn-refresh-meals').disabled, 'Error/loading broken');
  });
  await test('Double click and select during refresh send only one mutation', async () => {
    const wait = deferred(); let count = 0; const h = harness({ generateMeal: () => { count++; return wait.promise; } }); h.setMeal('lunch', meal());
    const first = h.generate(true); await h.generate(true); await h.select(2); assert(count === 1, 'Duplicate mutation'); wait.resolve(success(meal('new'))); await first;
  });
  await test('Late response after session reset is discarded', async () => {
    const wait = deferred(); const h = harness({ generateMeal: () => wait.promise }); h.setMeal('lunch', meal());
    const pending = h.generate(true); h.reset(8); wait.resolve(success(meal('old-user'))); await pending;
    assert(h.state().cache.lunch === null && !h.toasts.length, 'Old session data leaked into UI');
  });
  await test('An older GET cannot overwrite a completed refresh', async () => {
    const wait = deferred(); const h = harness({ getTodayMeals: () => wait.promise, generateMeal: async () => success(meal('new', 'b'.repeat(24))) }); h.setMeal('lunch', meal());
    const oldLoad = h.load(); await h.generate(true); wait.resolve({ success: true, todayMeals: { lunch: meal('old'), dinner: null, breakfast: null } }); await oldLoad;
    assert(h.state().cache.lunch.options[0].title === 'new1', 'Outdated GET overwrote refresh');
  });
  await test('Switching meal tabs while loading does not render the wrong meal', async () => {
    const wait = deferred(); const h = harness({ generateMeal: () => wait.promise }); h.setMeal('lunch', meal()); h.setMeal('dinner', { ...meal('dinner'), mealType: 'dinner' });
    const pending = h.generate(true); h.setMode('dinner'); wait.resolve(success(meal('new-lunch'))); await pending;
    assert(h.document.getElementById('meal-options-container').innerHTML.includes('dinner1'), 'Wrong tab rendered');
    assert(h.toasts.at(-1).message.startsWith('Bữa trưa:'), 'Completion meal ambiguous');
  });
  const dish = (id = 'vn_thit_kho_trung', extra = {}) => ({ dish_id: id, name: 'Thịt kho trứng', type: 'PROTEIN',
    meal_types: ['lunch', 'dinner'], preparation_state: 'cooked', reference_grams: 120, min_grams: 50, max_grams: 200,
    calories_per_100g: 200, macros_per_100g: { protein: 20, carbs: 5, fat: 10, fiber: 0 }, ...extra });
  async function picker(api = {}, catalog = [dish()]) {
    const h = harness({ getFoodCatalog: async () => success(catalog), ...api });
    h.setMeal('lunch', meal()); await h.openComponent(1, 'PROTEIN'); return h;
  }
  function choose(h, id = 'vn_thit_kho_trung', grams) {
    h.document.getElementById('v4-component-dish').value = id; h.chooseComponent();
    if (grams !== undefined) h.document.getElementById('v4-component-grams').value = grams;
  }
  const daily = (consumed = {}, extra = {}) => ({ date: '2026-10-12',
    targets: { target_kcal: 2000, macros: { protein: 100, carbs: 250, fat: 60 } },
    consumed: { calories: 1000, protein: 50, carbs: 100, fat: 30, ...consumed },
    logs: [], suggested_meal_targets: {}, ...extra });
  await test('Component catalog search matches accented/unaccented names and whitespace', async () => {
    const h = await picker({}, [dish(), dish('tofu', { name: 'Đậu phụ sốt cà chua' })]);
    for (const query of ['Thịt kho trứng', ' THIT  KHO   TRUNG ']) {
      h.document.getElementById('v4-component-query').value = query; h.searchComponent();
      const rows = h.document.getElementById('v4-component-dish').children;
      assert(rows.length === 2 && rows[1].value === 'vn_thit_kho_trung', 'Wrong search match');
      assert(rows[1].textContent.includes('240') && rows[1].textContent.includes('P/C/F'), 'Missing catalog nutrients');
    }
    h.document.getElementById('v4-component-query').value = ' DAU  PHU '; h.searchComponent();
    assert(h.document.getElementById('v4-component-dish').children[1].value === 'tofu', 'Vietnamese đ normalization broken');
  });
  await test('Catalog search filters role, meal type and raw food without Premium calls', async () => {
    const h = await picker({}, [dish(), dish('carb', { type: 'CARB' }), dish('morning', { meal_types: ['breakfast'] }), dish('raw', { preparation_state: 'raw' })]);
    assert(h.state().component.choices.length === 1, 'Invalid role/meal/raw candidate');
    assert(h.document.getElementById('v4-component-save').disabled, 'Unselected food may submit');
  });
  await test('Component search empty results, loading and API failures are explicit', async () => {
    const wait = deferred(); const h = harness({ getFoodCatalog: () => wait.promise }); h.setMeal('lunch', meal());
    const pending = h.openComponent(1, 'PROTEIN');
    assert(h.document.getElementById('v4-component-query').disabled && h.document.getElementById('v4-component-save').disabled, 'No loading guard');
    wait.resolve({ success: false, httpStatus: 500, message: 'Không tải được món' }); await pending;
    assert(h.document.getElementById('v4-component-status').textContent.includes('Không tải'), 'Error not visible');
    const empty = await picker(); empty.document.getElementById('v4-component-query').value = 'khong co mon nay'; empty.searchComponent();
    assert(empty.document.getElementById('v4-component-status').textContent.includes('Không tìm thấy') && empty.document.getElementById('v4-component-save').disabled, 'Empty results not guarded');
  });
  await test('Replacing sends ID/grams/current revision and updates planned without intake', async () => {
    let payload, intakeWrites = 0; const next = meal('replacement', 'b'.repeat(24)); next.options[0].recipe.change = 2;
    const h = await picker({ replaceComponent: async value => { payload = value; return success(next); }, addIntake: async () => { intakeWrites++; } });
    choose(h, undefined, 150); await h.replaceComponent();
    assert(payload.dishId === 'vn_thit_kho_trung' && payload.grams === 150 && payload.revision === 'a'.repeat(24) && payload.componentType === 'PROTEIN' && payload.optionId === 1, 'Incorrect replace payload');
    assert(Object.keys(payload).length === 6, 'Internal context leaked into API');
    assert(h.state().cache.lunch.options[0].recipe.change === 2 && h.document.getElementById('meal-options-container').innerHTML.includes('replacement1'), 'Recipe/DOM stale');
    assert(intakeWrites === 0 && h.state().daily === null, 'Planned became consumed');
  });
  await test('Component gram validation and search retain valid custom portion', async () => {
    let calls = 0; const h = await picker({ replaceComponent: async () => { calls++; return success(meal('new')); } });
    choose(h, undefined, 150); h.document.getElementById('v4-component-query').value = 'thit'; h.searchComponent();
    assert(Number(h.document.getElementById('v4-component-grams').value) === 150, 'Search reset grams');
    assert(h.document.getElementById('v4-component-reason').textContent.includes('300'), 'Wrong calorie preview');
    for (const grams of ['', -1, 0, 201, 'abc']) { h.document.getElementById('v4-component-grams').value = grams; await h.replaceComponent(); }
    assert(calls === 0, 'Invalid grams submitted');
  });
  await test('Component STALE_MEAL 409 reloads and closes the obsolete picker', async () => {
    const h = await picker({ replaceComponent: async () => ({ success: false, httpStatus: 409, code: 'STALE_MEAL' }) }); choose(h); await h.replaceComponent();
    assert(h.state().cache.lunch.options[0].title === 'server1' && h.state().component === null, 'Stale picker/cache retained');
    assert(h.toasts.at(-1).kind === 'error', '409 marked success');
  });
  await test('Component MEAL_DECIDED 409 closes picker without unselecting plan', async () => {
    const h = await picker({ replaceComponent: async () => ({ success: false, httpStatus: 409, code: 'MEAL_DECIDED' }) }); choose(h); await h.replaceComponent();
    assert(h.state().component === null && h.state().cache.lunch.revision === 'a'.repeat(24) && h.toasts.at(-1).kind === 'error', 'Decided handling broken');
  });
  await test('Avoid rejection keeps original meal and no success notification', async () => {
    const h = await picker({ replaceComponent: async () => ({ success: false, httpStatus: 422, code: 'AVOID_CONFLICT', message: 'Món vi phạm tránh món.' }) }); choose(h); await h.replaceComponent();
    assert(h.state().cache.lunch.options[0].title === 'old1' && h.toasts.at(-1).kind === 'error', 'Avoid failure accepted');
    assert(!h.document.getElementById('v4-component-save').disabled, 'Cannot retry after rejection');
  });
  await test('Replacement double-click and concurrent refresh/select send one mutation', async () => {
    const wait = deferred(); let calls = 0; const h = await picker({ replaceComponent: () => { calls++; return wait.promise; } }); choose(h);
    const pending = h.replaceComponent(); await h.replaceComponent(); await h.generate(true); await h.select(2);
    assert(calls === 1, 'Repeated component mutation'); wait.resolve(success(meal('new'))); await pending;
  });
  await test('Closing picker discards a late catalog response; repeat open is guarded', async () => {
    const wait = deferred(); let calls = 0; const h = harness({ getFoodCatalog: () => { calls++; return wait.promise; } }); h.setMeal('lunch', meal());
    const pending = h.openComponent(1, 'PROTEIN'); await h.openComponent(1, 'PROTEIN'); h.closeModal('modal-v4-component');
    wait.resolve(success([dish()])); await pending; assert(h.state().component === null && calls === 1, 'Closed picker reopened or duplicate read');
  });
  await test('Replacement response after session reset cannot update another session', async () => {
    const wait = deferred(); const h = await picker({ replaceComponent: () => wait.promise }); choose(h); const pending = h.replaceComponent(); h.reset(8);
    wait.resolve(success(meal('old-user'))); await pending; assert(h.state().cache.lunch === null && !h.toasts.length, 'Session response leaked');
  });
  await test('Inline warnings show actual kcal and each exceeded macro', async () => {
    const h = harness({ getDailyIntake: async () => success(daily({ calories: 2300, protein: 125, carbs: 270, fat: 72 }, { over_target: { calories: 300, protein: 25, carbs: 20, fat: 12 } })) }); await h.loadDaily();
    const warning = h.document.getElementById('v4-target-warning');
    assert(!warning.classList.contains('hidden') && warning.textContent.includes('Vượt mục tiêu tham khảo'), 'Warning invisible');
    for (const value of ['300 kcal', 'Protein +25 g', 'Carbs +20 g', 'Chất béo +12 g']) assert(warning.textContent.includes(value), 'Missing excess: ' + value);
    assert(h.document.getElementById('v4-remaining-kcal').textContent === '0', 'Negative allowance');
  });
  await test('A single exceeded macro warns even when actual calories remain below target', async () => {
    const h = harness({ getDailyIntake: async () => success(daily({ protein: 125 })) }); await h.loadDaily();
    const text = h.document.getElementById('v4-target-warning').textContent;
    assert(text.includes('Protein +25 g') && !text.includes('Năng lượng'), 'Macro-only warning incorrect');
  });
  await test('Planned food does not trigger an actual-intake warning', async () => {
    const h = harness({ getDailyIntake: async () => success(daily({}, { planned: { calories: 9000, protein: 900, carbs: 900, fat: 900 } })) }); await h.loadDaily();
    assert(h.document.getElementById('v4-target-warning').classList.contains('hidden'), 'Planned counted as consumed');
  });
  await test('Missing/null targets are explicit and never replaced with fake targets', async () => {
    for (const targets of [null, {}, { target_kcal: null }, { target_kcal: 2000, macros: {} }]) {
      const h = harness({ getDailyIntake: async () => success(daily({}, { targets })) }); await h.loadDaily();
      assert(!h.document.getElementById('v4-status').classList.contains('hidden') && h.document.getElementById('v4-status').textContent.includes('dữ liệu mục tiêu'), 'Missing target silently substituted');
      assert(h.document.getElementById('v4-target-warning').classList.contains('hidden'), 'Unknown target warns');
    }
  });
  await test('Warning is removed after updating consumed intake and switching dates', async () => {
    let response = daily({ calories: 2300 }); const h = harness({ getDailyIntake: async () => success(response) }); await h.loadDaily();
    response = daily(); await h.loadDaily(); assert(h.document.getElementById('v4-target-warning').classList.contains('hidden'), 'Warning retained after intake update');
    response = daily({ calories: 2300 }); await h.loadDaily(); h.document.getElementById('v4-date').value = '2026-10-11';
    response = daily({}, { date: '2026-10-11' }); await h.loadDaily(); assert(h.document.getElementById('v4-target-warning').classList.contains('hidden'), 'Other date warning retained');
  });
  await test('Outdated daily response cannot restore warnings after date change', async () => {
    const wait = deferred(); let count = 0; const h = harness({ getDailyIntake: () => ++count === 1 ? wait.promise : Promise.resolve(success(daily({}, { date: '2026-10-11' }))) });
    const pending = h.loadDaily(); h.document.getElementById('v4-date').value = '2026-10-11'; await h.loadDaily(); wait.resolve(success(daily({ calories: 2300 }))); await pending;
    assert(h.state().daily.date === '2026-10-11' && h.document.getElementById('v4-target-warning').classList.contains('hidden'), 'Late warning leaked');
  });
  await test('Failed daily lookup clears previous warning and shows error', async () => {
    let response = success(daily({ calories: 2300 })); const h = harness({ getDailyIntake: async () => response }); await h.loadDaily();
    response = { success: false, httpStatus: 500, message: 'Không tải được' }; await h.loadDaily();
    assert(h.document.getElementById('v4-target-warning').classList.contains('hidden') && h.document.getElementById('v4-status').textContent.includes('Không tải'), 'Error kept stale warning');
  });
  await test('Intake add/update/delete reload actual warnings independently of planned summary', async () => {
    for (const operation of ['add', 'update', 'delete']) {
      let writes = 0, reads = 0;
      const h = harness({ addIntake: async () => { writes++; return success({ date: '2026-10-12' }); }, updateIntake: async () => { writes++; return success({ date: '2026-10-12' }); },
        deleteIntake: async () => { writes++; return success({}); }, getDailyIntake: async () => { reads++; return success(daily({ protein: 125 })); } });
      if (operation === 'delete') { h.setDelete({ id: 1, version: 2 }); await h.deleteIntake(); }
      else { h.setIntake({ ...(operation === 'update' ? { id: 1 } : {}), items: [], pendingPayload: { confirmed: true }, submitting: false }); await h.saveIntake(); }
      assert(writes === 1 && reads === 1 && h.document.getElementById('v4-target-warning').textContent.includes('Protein'), 'No actual daily reload for ' + operation);
    }
  });
  await test('Intake Add another food searches all 141 API dishes, not a fixed legacy count', async () => {
    const h = harness(); const catalog = Array.from({ length: 140 }, (_, n) => dish('id' + n, { name: 'Món ' + n })); catalog.push(dish()); h.setCatalog(catalog);
    for (const query of ['Thịt kho trứng', ' thit  kho TRUNG ']) {
      h.document.getElementById('v4-food-query').value = query; h.foodSearch();
      const rows = h.document.getElementById('v4-food-results').children;
      assert(rows.length === 1 && rows[0].children[0].textContent === 'Thịt kho trứng', 'Intake search truncated or accent mismatch');
    }
  });
  await test('Removed free-text controls have no dangling frontend handlers', async () => {
    for (const text of [sources.meals, sources.app, sources.html]) assert(!/meal-replace-request|btn-replace-meal|replaceMealSuggestions/.test(text), 'Removed control still referenced');
    assert(sources.html.includes('btn-apply-meal-preferences') && sources.html.includes('v4-component-query'), 'Required controls removed');
    assert(sources.api.includes('/api/meals/replace'), 'Existing API accidentally removed');
  });
  await test('Snack UI uses Bữa phụ without changing internal contract', async () => {
    assert(!/Ăn nhẹ/.test(sources.nutrition + sources.html), 'Old snack label still visible');
    assert(sources.html.includes('value="snack"') && sources.html.includes('Bữa phụ'), 'Internal snack contract changed');
  });
  await test('Catalog exact and prefix matches rank first without hiding remaining results', async () => {
    const h = harness();
    h.setCatalog([
      {dish_id:'third',name:'Canh cà chua trứng',reference_grams:200,calories_per_100g:40},
      {dish_id:'second',name:'Trứng chiên hành',reference_grams:100,calories_per_100g:150},
      {dish_id:'first',name:'Trứng',reference_grams:100,calories_per_100g:150}
    ]);
    h.document.getElementById('v4-food-query').value = 'TRUNG'; h.foodSearch();
    const rows = h.document.getElementById('v4-food-results').children;
    assert(rows.length === 3 && rows[0].children[0].textContent === 'Trứng' && rows[1].children[0].textContent === 'Trứng chiên hành', 'Relevance or result completeness changed');
  });
  await test('Retired cached recipe cannot open component picker for a new selection', async () => {
    let calls = 0;
    const h = harness({ getFoodCatalog: async () => { calls++; return success([]); } });
    const old = meal(); old.catalog_refresh_required = true; h.setMeal('lunch',old);
    await h.openComponent(1,'PROTEIN');
    assert(calls === 0 && h.toasts.some(t => t.kind === 'error'), 'Retired plan offered as current selection');
  });
  await test('Invalid grams explain each dish bounds, hide kcal and block requests', async () => {
    for (const value of ['49', '2345', '', 'không phải số']) {
      let writes = 0;
      const h = harness({ addIntake: async () => { writes++; return success({}); } });
      h.setCatalog([dish('portion', { name:'Đậu phụ chiên', min_grams:50, max_grams:220, reference_grams:100 })]);
      h.setIntake({ items:[{dish_id:'portion',grams:100}], requestId:'safe-validation-request' }); h.renderIntake();
      const controls = h.document.getElementById('v4-intake-items').children[0].children[1];
      const field = controls.children[1], input = field.children[0].children[1], error = field.children[1];
      input.value = value; input.oninput();
      assert(error.textContent.includes('50 đến 220 g') && !error.classList.contains('hidden'), 'Missing specific range for '+value);
      assert(input.attributes['aria-invalid'] === 'true' && h.document.getElementById('v4-intake-save').disabled, 'Invalid input enabled submit');
      assert(h.document.getElementById('v4-intake-kcal').textContent === '—' && h.previewIntake() === null, 'Invalid kcal estimate');
      await h.saveIntake(); assert(writes === 0, 'Invalid request sent');
      input.value = '120'; input.oninput();
      assert(error.textContent === '' && error.classList.contains('hidden') && !h.document.getElementById('v4-intake-save').disabled, 'Error did not clear');
    }
  });
  await test('Different foods and edited frozen logs use their own limits and nutrient snapshots', async () => {
    const h = harness();
    h.setCatalog([dish('first',{ min_grams:50,max_grams:220 }),dish('second',{ min_grams:150,max_grams:500,calories_per_100g:999 })]);
    h.setIntake({ id:1,items:[{dish_id:'second',grams:100}],frozenCatalog:[dish('second',{ min_grams:150,max_grams:500,calories_per_100g:100 })] });h.renderIntake();
    const field=h.document.getElementById('v4-intake-items').children[0].children[1].children[1];
    const input=field.children[0].children[1], error=field.children[1];
    assert(error.textContent.includes('150 đến 500 g'), 'Generic portion range used');
    input.value='200';input.oninput();assert(h.previewIntake().calories===200,'Current catalog overwrote frozen nutrients');
    assert(input.min==='150' && input.max==='500','Wrong edit limits');
  });
  await test('Old retired intake uses backend actual limits without inventing reference bounds', async () => {
    const h=harness();h.setCatalog([]);h.setActualLimits({min:1,max:2000});
    h.setIntake({id:1,items:[{dish_id:'retired',grams:100}],frozenCatalog:[{dish_id:'retired',name:'Món lịch sử',calories_per_100g:100,macros_per_100g:{protein:10,carbs:10,fat:2,fiber:null}}]});h.renderIntake();
    assert(h.previewIntake().calories===100,'Historical intake no longer editable');
    const field=h.document.getElementById('v4-intake-items').children[0].children[1].children[1];
    const input=field.children[0].children[1];input.value='2345';input.oninput();
    assert(field.children[1].textContent.includes('1 đến 2000 g'),'Missing authoritative historical bounds');
  });
  await test('Catalog counters use actual API result length and accented filtered counts', async () => {
    for (const total of [158,173]) {
      const catalog=Array.from({length:total-1},(_,n)=>dish('new'+n,{name:'Món khác '+n}));catalog.push(dish('match',{name:'Rau muống xào tỏi'}));
      const h=harness({getFoodCatalog:async()=>({...success(catalog),intake_gram_limits:{min:1,max:2000}})});
      await h.loadCatalog();h.foodSearch();
      assert(h.document.getElementById('v4-food-count').textContent===total+' món ăn có thể lựa chọn.','Counter hardcoded');
      assert(h.document.getElementById('v4-food-results').children.length===total,'Result list truncated');
      for (const query of ['Rau muống xào tỏi','  RAU  MUONG XAO TOI ']) {
        h.document.getElementById('v4-food-query').value=query;h.foodSearch();
        assert(h.document.getElementById('v4-food-count').textContent==='Tìm thấy 1/'+total+' món.','Filter count wrong');
      }
      h.document.getElementById('v4-food-query').value='Không tồn tại';h.foodSearch();
      assert(h.document.getElementById('v4-food-count').textContent==='Tìm thấy 0/'+total+' món.','No-match counter wrong');
    }
  });
  await test('Empty catalog and failed load have different states', async () => {
    const empty=harness({getFoodCatalog:async()=>success([])});await empty.loadCatalog();empty.foodSearch();
    assert(empty.document.getElementById('v4-food-count').textContent.includes('trống'),'Missing empty state');
    const failed=harness({getFoodCatalog:async()=>({success:false,httpStatus:500,message:'Không tải được danh sách'})});
    assert(await failed.loadCatalog()===false,'Failed load accepted');
    assert(failed.document.getElementById('v4-food-count').textContent.includes('Không tải'),'Error mistaken for empty');
  });
  await test('Replacement counter counts only eligible role and meal-type choices', async () => {
    const h=harness({getFoodCatalog:async()=>success([dish('ok1'),dish('ok2',{name:'Món mặn mới'}),dish('wrong-role',{type:'SOUP'}),dish('wrong-meal',{meal_types:['breakfast']})])});
    h.setMeal('lunch',meal());await h.openComponent(1,'PROTEIN');
    assert(h.document.getElementById('v4-component-status').textContent.startsWith('2 món đủ điều kiện'),'Global count used for replacement');
    h.document.getElementById('v4-component-query').value='mon man';h.searchComponent();
    assert(h.document.getElementById('v4-component-status').textContent.startsWith('Tìm thấy 1/2'),'Filtered eligible count wrong');
  });
  await test('Preference UI contains only three ingredient fields and no time controls', async () => {
    for (const id of ['meal-avoid', 'meal-dislikes', 'meal-prefer', 'btn-apply-meal-preferences']) assert(sources.html.includes('id="' + id + '"'), id);
    for (const id of ['meal-prefer-easy', 'meal-prep-minutes', 'meal-breakfast-prep']) {
      assert(!sources.html.includes(id) && !sources.meals.includes(id), 'Retired time binding: ' + id);
    }
    assert(!sources.meals.includes('Hệ thống giữ nguyên 3 lựa chọn ban đầu'), 'Misleading saved status');
  });
  await test('Breakfast old time preferences do not leak into refreshed payload', async () => {
    let args;const old=meal();old.mealType='breakfast';old.options[0].recipe.preferences={avoid:['chicken'],preferEasy:true,maxPrepMinutes:1};
    const h=harness({ getTodayMeals:async()=>({success:true,todayMeals:{breakfast:old,lunch:null,dinner:null}}),generateMeal:async(...values)=>{args=values;return success({...meal('new'),mealType:'breakfast'});} });
    h.setMode('breakfast');await h.load();await h.apply();
    assert(args[3].avoid[0]==='gà' && !('preferEasy' in args[3]) && !('maxPrepMinutes' in args[3]),'Hidden time preference');
    assert(!('maxPrepMinutes' in h.state().preferences.breakfast),'Retired saved UI setting');
  });
  await test('Comma-separated accents duplicates and all three preferences reach backend', async () => {
    let args;const h=harness({generateMeal:async(...values)=>{args=values;return success(meal('new'));}});
    for(const [id,value] of [['meal-avoid','  gà, ga, heo  '],['meal-dislikes','heo'],['meal-prefer','bò']]) h.document.getElementById(id).value=value;
    await h.apply();assert(args[3].avoid.join('|')==='gà|ga|heo' && args[3].dislikes[0]==='heo' && args[3].prefer[0]==='bò','Incorrect terms');
  });
  await test('No alternative preserves revision, uses info and clears loading', async () => {
    const old=meal();const h=harness({generateMeal:async()=>({success:true,data:old,meta:{cached:true,changed:false,refresh_status:'no_alternative'}})});
    h.setMeal('lunch',old);await h.generate(true);
    assert(h.state().cache.lunch.revision===old.revision,'No-op changed revision');
    assert(h.toasts.at(-1).kind==='info' && h.toasts.at(-1).message.includes('Chưa tìm thấy'),'False success');
    assert(!h.document.getElementById('btn-refresh-meals').disabled,'Loading stuck');
  });
  await test('Unchanged or reordered dishes never show successful food change', async () => {
    const next=meal();next.options.reverse();const h=harness({generateMeal:async()=>success(next)});h.setMeal('lunch',meal());await h.generate(true);
    assert(h.toasts.at(-1).kind==='info','Unchanged response got success style');
  });
  await test('Rejected preferences never replace confirmed state and show unknown term', async () => {
    const h=harness({generateMeal:async()=>({success:false,httpStatus:400,code:'UNSUPPORTED_PREFERENCE',message:'Không nhận diện được nguyên liệu: abcxyz123. Vui lòng kiểm tra lại.'})});h.setMeal('lunch',meal());
    h.document.getElementById('meal-avoid').value='abcxyz123';await h.apply();
    assert(!h.state().preferences.lunch.avoid?.includes('abcxyz123'),'Rejected preference persisted');
    assert(h.toasts.at(-1).kind==='error' && h.toasts.at(-1).message.includes('abcxyz123'),'Error hidden');
  });
  await test('Reload restores saved ingredient preferences and server recipe', async () => {
    const saved=meal('saved');saved.options[0].recipe.preferences={avoid:['chicken'],dislikes:['pork'],prefer:['beef']};
    const h=harness({getTodayMeals:async()=>({success:true,todayMeals:{lunch:saved,breakfast:null,dinner:null}})});await h.load();
    assert(h.document.getElementById('meal-avoid').value==='gà' && h.document.getElementById('meal-dislikes').value==='heo' && h.document.getElementById('meal-prefer').value==='bò','Reload prefs');
    assert(h.document.getElementById('meal-options-container').innerHTML.includes('saved1'),'Reload meals');
  });
  await test('System failure shows API error instead of invented candidate shortage', async () => {
    const h=harness({generateMeal:async()=>({success:false,httpStatus:503,code:'DATABASE_ERROR'})});h.setMeal('lunch',meal());await h.generate(true);
    assert(h.toasts.at(-1).kind==='error' && h.toasts.at(-1).message.includes('Không thể cập nhật'),'System failure hidden');
    assert(!h.toasts.at(-1).message.includes('thiếu món'),'Invented shortage');
  });
  return { passed: results.filter(r => r.pass).length, total: results.length, results };
}
if (typeof module !== 'undefined') {
  module.exports = runMealIntegrationTests;
  if (require.main === module) {
    const fs = require('node:fs'), path = require('node:path'), dir = path.resolve(__dirname, '..', 'js');
    runMealIntegrationTests({ api: fs.readFileSync(path.join(dir, 'api.js'), 'utf8'), meals: fs.readFileSync(path.join(dir, 'meals.js'), 'utf8'), nutrition: fs.readFileSync(path.join(dir, 'nutrition-v4.js'), 'utf8'), app: fs.readFileSync(path.join(dir, 'app.js'), 'utf8'), html: fs.readFileSync(path.join(dir, '..', 'index.html'), 'utf8') })
      .then(result => { console.log(JSON.stringify(result, null, 2)); process.exitCode = result.passed === result.total ? 0 : 1; })
      .catch(error => { console.error(error.message); process.exitCode = 1; });
  }
}
