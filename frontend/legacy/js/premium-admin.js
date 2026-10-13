/* Premium and Admin integration layer for the existing NutriFit UI. */
(function () {
  'use strict';
  const byId = id => document.getElementById(id);
  const money = value => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 }).format(Number(value) || 0);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[ch]));
  function sessionUser() {
    try { const raw = localStorage.getItem('nutrifit_session_user'); const s = raw ? JSON.parse(raw) : null; return s?.user || s || null; }
    catch (_) { return null; }
  }
  function isLoggedIn() { return Number(sessionUser()?.id) > 0; }
  function isAdmin() { return String(sessionUser()?.role || sessionUser()?.Role || '').toUpperCase() === 'ADMIN'; }
  function message(id, text, error = false) {
    const el = byId(id); if (!el) return;
    el.textContent = text || '';
    el.className = `mt-3 text-sm ${error ? 'text-rose-600' : 'text-emerald-700'}`;
  }
  window.closeNutriPanel = id => byId(id)?.classList.add('hidden');
  window.openPremiumPanel = async function () {
    if (!isLoggedIn()) { alert('Vui lòng đăng nhập để xem và mua gói Premium.'); return; }
    byId('nf-premium-panel')?.classList.remove('hidden');
    await loadPlans();
    await loadPaymentHistory();
  };
  window.openAdminPanel = async function () {
    if (!isLoggedIn()) { alert('Vui lòng đăng nhập.'); return; }
    if (!isAdmin()) { alert('Tài khoản hiện tại không có quyền Admin.'); return; }
    byId('nf-admin-panel')?.classList.remove('hidden');
    await loadAdminPanel();
  };
  async function loadPlans() {
    const list = byId('nf-plan-list');
    list.innerHTML = '<p class="text-sm text-slate-500">Đang tải các gói...</p>';
    try {
      const result = await NutriFitAPI.getSubscriptionPlans();
      if (!result.success || !Array.isArray(result.data)) throw new Error(result.message || 'Không tải được danh sách gói.');
      if (!result.data.length) { list.innerHTML = '<p class="rounded-xl bg-amber-50 p-4 text-sm text-amber-800">Chưa có gói dịch vụ trong database. Cần thêm SubscriptionPlans trước khi mua.</p>'; return; }
      list.innerHTML = result.data.map(plan => `<article class="flex flex-col rounded-2xl border border-slate-200 p-4 shadow-sm"><p class="text-xs font-extrabold uppercase tracking-wider text-amber-600">NutriFit Premium</p><h3 class="mt-2 text-lg font-black text-slate-900">${esc(plan.plan_name)}</h3><p class="mt-2 text-2xl font-black text-slate-900">${money(plan.price_vnd)}</p><p class="mt-1 text-xs text-slate-500">${Number(plan.duration_days) || 0} ngày</p><p class="my-3 flex-1 text-sm text-slate-600">${esc(plan.description || 'Mở rộng trải nghiệm NutriFit.')}</p><button type="button" data-plan-id="${Number(plan.plan_id)}" class="nf-buy-plan rounded-xl bg-slate-900 px-4 py-3 text-sm font-bold text-white hover:bg-slate-700">Tạo yêu cầu thanh toán</button></article>`).join('');
      list.querySelectorAll('.nf-buy-plan').forEach(btn => btn.addEventListener('click', () => checkout(Number(btn.dataset.planId), btn)));
    } catch (error) { list.innerHTML = `<p class="rounded-xl bg-rose-50 p-4 text-sm text-rose-700">${esc(error.message || 'Lỗi tải gói dịch vụ.')}</p>`; }
  }
  async function checkout(planId, button) {
    const out = byId('nf-checkout-result');
    button.disabled = true; button.textContent = 'Đang tạo yêu cầu...';
    out.innerHTML = '<p>Đang tạo đơn thanh toán...</p>';
    try {
      const result = await NutriFitAPI.createCheckout(planId);
      if (!result.success || !result.data) throw new Error(result.message || 'Không tạo được đơn thanh toán.');
      const d = result.data;
      out.innerHTML = `<div class="rounded-xl border border-amber-200 bg-amber-50 p-4"><p class="font-extrabold text-slate-900">${esc(d.plan_name || 'Đơn Premium')}</p><p class="mt-1 text-lg font-black">${money(d.amount_vnd)}</p><p class="mt-2 text-xs text-slate-600">Mã chuyển khoản</p><code class="mt-1 block break-all rounded-lg bg-white p-2 font-bold">${esc(d.transaction_code)}</code>${d.qr_code_url ? `<img class="mx-auto mt-4 w-full max-w-[240px] rounded-xl border border-slate-200 bg-white p-2" src="${esc(d.qr_code_url)}" alt="QR chuyển khoản" />` : ''}<p class="mt-3 text-xs text-amber-800">Đơn đang chờ xác nhận. Không đóng tiền vào tài khoản nếu thông tin người nhận chưa được xác nhận từ đơn vị vận hành. Premium chưa được kích hoạt khi trạng thái còn PENDING.</p></div>`;
      message('nf-premium-message', result.message || 'Đã tạo yêu cầu thanh toán.');
      await loadPaymentHistory();
    } catch (error) { out.innerHTML = `<p class="rounded-xl bg-rose-50 p-3 text-sm text-rose-700">${esc(error.message || 'Không tạo được đơn.')}</p>`; }
    finally { button.disabled = false; button.textContent = 'Tạo yêu cầu thanh toán'; }
  }
  window.loadPaymentHistory = async function () {
    const box = byId('nf-payment-history'); if (!box) return;
    box.innerHTML = '<p>Đang tải lịch sử...</p>';
    try {
      const result = await NutriFitAPI.getPaymentHistory();
      if (!result.success) throw new Error(result.message || 'Không tải được lịch sử.');
      const rows = result.data || [];
      box.innerHTML = rows.length ? rows.map(t => `<div class="rounded-lg border border-slate-200 bg-white p-3"><div class="flex justify-between gap-2"><strong>${esc(t.plan_name || 'Gói dịch vụ')}</strong><span class="font-bold">${money(t.amount)}</span></div><p class="mt-1 break-all text-slate-500">${esc(t.transaction_code)}</p><p class="mt-1 font-bold ${String(t.status).toUpperCase() === 'SUCCESS' ? 'text-emerald-700' : 'text-amber-700'}">${esc(t.status)}</p><p class="mt-1 text-slate-400">${esc(t.created_at || '')}</p></div>`).join('') : '<p>Chưa có giao dịch nào.</p>';
    } catch (error) { box.innerHTML = `<p class="text-rose-600">${esc(error.message)}</p>`; }
  };
  window.loadAdminPanel = async function () {
    if (!isAdmin()) { message('nf-admin-message', 'Backend không cho phép tài khoản này xem dữ liệu quản trị.', true); return; }
    message('nf-admin-message', 'Đang tải dữ liệu quản trị...');
    try {
      const [dash, users, txns] = await Promise.all([NutriFitAPI.getAdminDashboard(), NutriFitAPI.getAdminUsers(), NutriFitAPI.getAdminTransactions()]);
      if (!dash.success) throw new Error(dash.message || 'Không tải được thống kê Admin.');
      const d = dash.data || {};
      byId('nf-admin-users').textContent = d.users?.total ?? '—';
      byId('nf-admin-premium').textContent = d.users?.premium ?? '—';
      byId('nf-admin-revenue').textContent = money(d.financial?.total_revenue_vnd);
      if (!users.success) throw new Error(users.message || 'Không tải được danh sách người dùng.');
      const rows = users.data || [];
      byId('nf-admin-user-rows').innerHTML = rows.length ? rows.map(u => `<tr class="border-t border-slate-100"><td class="p-3">${esc(u.id ?? u.UserId)}</td><td class="p-3">${esc(u.email ?? u.Email)}</td><td class="p-3"><span class="rounded-full bg-slate-100 px-2 py-1 font-bold">${esc(u.role ?? u.Role ?? 'MEMBER')}</span></td><td class="p-3">${esc(u.subscription_status ?? u.SubscriptionStatus ?? 'FREE')}</td></tr>`).join('') : '<tr><td colspan="4" class="p-3 text-slate-500">Chưa có người dùng.</td></tr>';
      if (!txns.success) throw new Error(txns.message || 'Không tải được giao dịch.');
      const transactions = txns.data || [];
      byId('nf-admin-transactions').innerHTML = transactions.length ? transactions.map(t => `<article class="rounded-xl border border-slate-200 p-3"><div class="flex justify-between gap-3"><strong>${esc(t.user_email || t.user_name || 'Người dùng')}</strong><b>${money(t.amount)}</b></div><p class="mt-1 break-all text-slate-500">${esc(t.transaction_code)}</p><p class="mt-1">Trạng thái: <strong>${esc(t.status)}</strong></p><p class="mt-1 text-slate-400">${esc(t.created_at || '')}</p></article>`).join('') : '<p>Chưa có giao dịch.</p>';
      message('nf-admin-message', 'Đã tải dữ liệu từ API quản trị.');
    } catch (error) { message('nf-admin-message', error.message || 'Không tải được dữ liệu quản trị.', true); }
  };
  document.addEventListener('DOMContentLoaded', () => {
    const refreshRole = () => { const btn = byId('nav-admin-button'); if (btn) btn.classList.toggle('hidden', !isAdmin()); };
    refreshRole();
    document.addEventListener('nutrifit:session-expired', refreshRole);
    document.addEventListener('nutrifit:session-updated', refreshRole);
  });
})();
