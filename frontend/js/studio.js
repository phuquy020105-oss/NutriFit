/* NutriFit Studio – dependency-free UI for the integrated Flask application.
 * Demo figures are visibly illustrative; all writes require a real signed-in account.
 */
(() => {
  'use strict';
  const API = String(window.NUTRIFIT_API_BASE_URL || 'http://127.0.0.1:5000').replace(/\/+$/, '');
  const $ = selector => document.querySelector(selector);
  const E = value => String(value ?? '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  const fmt = value => Math.round(Number(value) || 0).toLocaleString('vi-VN');
  const money = value => `${fmt(value)}đ`;
  // Old internal QR codes may start with DEMO_; keep the storage key untouched.
  const displayTransactionCode = value => String(value || '').replace(/^DEMO_/i,'NF_');
  // BMI = cân nặng (kg) / [chiều cao (m)]².
  // Ưu tiên kết quả Backend; tương thích hồ sơ cũ chưa có trường bmi.
  const displayBmi = (providedBmi, weightKg, heightCm) => {
    let bmi = Number(providedBmi);
    if (providedBmi == null || providedBmi === '' || !Number.isFinite(bmi) || bmi <= 0) {
      const weight = Number(weightKg);
      const height = Number(heightCm) / 100;
      bmi = Number.isFinite(weight) && Number.isFinite(height) && weight > 0 && height > 0
        ? weight / (height * height) : NaN;
    }
    return Number.isFinite(bmi) && bmi > 0
      ? bmi.toLocaleString('vi-VN', {minimumFractionDigits: 1, maximumFractionDigits: 1})
      : '—';
  };
  const today = () => { const d = new Date(); return [d.getFullYear(), String(d.getMonth()+1).padStart(2,'0'), String(d.getDate()).padStart(2,'0')].join('-'); };
  const initials = value => String(value || 'N').trim().split(/\s+/).slice(-2).map(x => x[0]).join('').toUpperCase();
  const storage = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } };
  const save = (key, value) => localStorage.setItem(key, JSON.stringify(value));
  const paths = {
    grid:'<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>',
    leaf:'<path d="M20 4c-8.5 0-15 3-15 11a5 5 0 0 0 5 5c8 0 11-6.5 10-16Z"/><path d="M5 20c3-6 7-9 12-12"/>',
    utensils:'<path d="M4 3v7a3 3 0 0 0 6 0V3M7 3v18M19 3v18M19 3c-4 2-4 8 0 10"/>',
    dumbbell:'<path d="M6.5 6.5l11 11m-15-8 7-7m-5 11 9-9m0 15 7-7m-5 11 9-9"/>',
    store:'<path d="m3 9 2-5h14l2 5v2a3 3 0 0 1-4 2.8 3 3 0 0 1-5 0 3 3 0 0 1-5 0A3 3 0 0 1 3 11V9ZM5 14v7h14v-7M10 21v-6h4v6"/>',
    spark:'<path d="m12 3 1.8 6.2L20 11l-6.2 1.8L12 19l-1.8-6.2L4 11l6.2-1.8L12 3ZM19 18l.6 1.4L21 20l-1.4.6L19 22l-.6-1.4L17 20l1.4-.6L19 18Z"/>',
    user:'<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.4-7 8-7s8 3 8 7"/>',
    crown:'<path d="m3 7 5 4 4-7 4 7 5-4-2 12H5L3 7Z"/><path d="M5 19h14"/>',
    chart:'<path d="M4 20V10M10 20V4M16 20v-8M22 20v-5"/>',
    fire:'<path d="M12 22c4 0 7-3.1 7-7 0-3.3-2-5.2-3-6-.3 2-1.5 3-2 3 0-5-2-7-4-9 0 4-5 6.4-5 12a7 7 0 0 0 7 7Z"/>',
    droplet:'<path d="M12 22a8 8 0 0 0 8-8C20 9 12 2 12 2S4 9 4 14a8 8 0 0 0 8 8Z"/>',
    heart:'<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8L12 21l8.8-8.6a5.5 5.5 0 0 0 0-7.8Z"/>',
    plus:'<path d="M12 5v14M5 12h14"/>',
    arrow:'<path d="M5 12h14M13 6l6 6-6 6"/>',
    check:'<path d="m4 12 5 5L20 6"/>',
    clock:'<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    bell:'<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9ZM10 21h4"/>',
    search:'<circle cx="11" cy="11" r="7"/><path d="m16 16 5 5"/>',
    shield:'<path d="m12 2 9 4v6c0 6-3.5 9-9 10-5.5-1-9-4-9-10V6l9-4Z"/><path d="m8 12 3 3 5-5"/>',
    arrowup:'<path d="M12 19V5m-6 6 6-6 6 6"/>',
    calendar:'<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 10h18"/>',
    lightbulb:'<path d="M9 18h6M10 21h4M9 15a7 7 0 1 1 6 0l-1 3h-4l-1-3Z"/>',
    zap:'<path d="m13 2-9 12h7l-1 8 10-13h-7l0-7Z"/>',
    logout:'<path d="M10 4H5a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h5M14 7l5 5-5 5M19 12H8"/>',
    info:'<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 7h.01"/>',
    eye:'<path d="M2 12s3.6-6.5 10-6.5S22 12 22 12s-3.6 6.5-10 6.5S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
    eyeoff:'<path d="M3 3l18 18M10.6 5.6A11 11 0 0 1 12 5.5c6.4 0 10 6.5 10 6.5a14.3 14.3 0 0 1-4.2 4.8M6.4 6.6A15 15 0 0 0 2 12s3.6 6.5 10 6.5c1.7 0 3.2-.4 4.4-1.1M10 10a3 3 0 0 0 4 4"/>'

  };
  const icon = (name, size=20) => `<svg viewBox="0 0 24 24" width="${size}" height="${size}" aria-hidden="true">${paths[name] || paths.spark}</svg>`;
  const routes = [
    ['dashboard','Tổng quan','grid'], ['nutrition','Dinh dưỡng','leaf'], ['meals','Thực đơn AI','utensils'],
    ['workouts','Luyện tập','dumbbell'], ['chat','Trợ lý AI','spark'],
    ['profile','Hồ sơ của tôi','user'], ['premium','Gói Premium','crown'], ['admin','Quản trị','chart']
  ];
  const exampleMeals = {
    breakfast:[{id:1,title:'Yến mạch, chuối và sữa chua',calories:385,macros:{protein:19,carbs:55,fat:10},reason:'Giàu chất xơ, dễ chuẩn bị.'},{id:2,title:'Bánh mì trứng và rau xanh',calories:410,macros:{protein:23,carbs:41,fat:16},reason:'Đủ năng lượng để bắt đầu ngày mới.'},{id:3,title:'Phở gà ít bánh phở',calories:430,macros:{protein:29,carbs:49,fat:12},reason:'Hương vị Việt, giàu đạm.'}],
    lunch:[{id:1,title:'Cơm gạo lứt, ức gà và rau củ',calories:620,macros:{protein:42,carbs:70,fat:16},reason:'Cân bằng các nhóm chất.'},{id:2,title:'Cá hồi áp chảo, khoai và salad',calories:590,macros:{protein:38,carbs:54,fat:24},reason:'Bổ sung chất béo tốt.'},{id:3,title:'Bún thịt nướng và rau sống',calories:565,macros:{protein:31,carbs:67,fat:18},reason:'Hợp khẩu vị Việt Nam.'}],
    dinner:[{id:1,title:'Cá hấp gừng, cơm và rau luộc',calories:475,macros:{protein:35,carbs:49,fat:14},reason:'Nhẹ bụng, ít dầu mỡ.'},{id:2,title:'Bún gà rau củ',calories:450,macros:{protein:29,carbs:55,fat:12},reason:'Đạm nạc và nhiều rau.'},{id:3,title:'Đậu hũ sốt cà, cơm gạo lứt',calories:490,macros:{protein:23,carbs:69,fat:13},reason:'Phù hợp bữa tối thanh đạm.'}]
  };
  const demoWorkouts = [
    {id:1,name:'Đi bộ nhanh',category:'Cardio',durationMinutes:30,caloriesBurned:150,emoji:'🚶'},
    {id:2,name:'Chạy bộ',category:'Cardio',durationMinutes:30,caloriesBurned:310,emoji:'🏃'},
    {id:3,name:'Đạp xe',category:'Cardio',durationMinutes:45,caloriesBurned:325,emoji:'🚴'},
    {id:4,name:'Yoga thư giãn',category:'Linh hoạt',durationMinutes:30,caloriesBurned:100,emoji:'🧘'},
    {id:5,name:'Squat cơ bản',category:'Sức mạnh',durationMinutes:20,caloriesBurned:115,emoji:'🏋️'},
    {id:6,name:'Nhảy dây',category:'Cardio',durationMinutes:20,caloriesBurned:220,emoji:'🪢'}
  ];
  const activityDemo = [42,70,55,85,62,92,72];
  const state = {
    page:'dashboard', online:false, user:storage('nutrifit_session_user',null),
    profile:null,calc:null,daily:null,summary:null,mealData:{},dailyPlan:null,planMealType:"breakfast",planDraft:{breakfast:"",lunch:"",dinner:"",snack:""},premiumAccess:false,workouts:[],workoutLogs:[],progress:null,
    mealPrefOwner:null,mealPrefOpen:true,mealPrefDraft:{avoid:"",dislikes:"",prefer:"",ingredientMode:"strict"},mealPrefApplied:{avoid:[],dislikes:[],prefer:[]},
    street:[],streetSearch:'',mealType:'lunch',workoutCategory:'Tất cả',streetType:'all',streetBudget:'all',
    chat:storage('nutrifit_studio_chat',[]),chatPending:false,plans:[],adminStats:null,adminUsers:[],adminTransactions:[],adminTab:'overview',adminPeriod:'day',adminSearch:'',adminFilter:'all',adminPageIndex:1,adminLoading:false,adminError:'',
    water:storage('nutrifit_studio_water',{}), mealBusy:false,planBusy:false,loadingData:false,recommendation:null
  };
  let toastTimer;
  let pendingOtpEmail = "";
  let demoPaymentPoll = null;
  function stopDemoPaymentPoll(){ if (demoPaymentPoll) { clearTimeout(demoPaymentPoll); demoPaymentPoll=null; } }
  async function pollDemoPayment(transactionId){
    if (!$('#modal-root .demo-payment-modal')) return;
    const result = await req('/api/payment/demo-status/'+Number(transactionId), undefined, 'GET', 7000);
    if (!$('#modal-root .demo-payment-modal')) return;
    const status = String(result.data?.status || '');
    if(result.httpStatus === 401 || result.httpStatus === 403){
      stopDemoPaymentPoll();
      toast(result.message || 'Vui lòng đăng nhập lại trước khi tiếp tục.',true);
      return;
    }
    if(result.success && result.data?.user_id && Number(result.data.user_id) !== id()){
      stopDemoPaymentPoll();
      toast('Phiên đăng nhập không khớp tài khoản. Hãy đăng nhập lại.',true);
      return;
    }
    if(result.success && ['DEMO_SUCCESS','DEMO_MAIL_ERROR'].includes(status)){
      stopDemoPaymentPoll();
      // Reload entitlement from server after QR confirmation, not from stale login data.
      const access = await req('/api/meals/premium-access', undefined, 'GET', 7000);
      const granted = access.success && Number(access.user_id) === id()
        ? access.premium === true : result.data?.premium_active === true;
      state.premiumAccess = granted;
      render();
      if(adminRole() && state.adminStats) await loadAdminData();
      if(!granted){
        openModal('Đang cập nhật tài khoản',`<div class="demo-payment-result">${icon('clock',44)}<h3>Giao dịch đã được xác nhận</h3><p>Quyền Premium chưa được cập nhật. Vui lòng tải lại trang Hồ sơ; nếu vẫn là Free, hãy liên hệ quản trị viên và cung cấp mã giao dịch.</p><button class="btn btn-primary" data-action="close-modal">Đóng</button></div>`);
        toast('Giao dịch đã xác nhận nhưng quyền Premium chưa được cập nhật.',true);
        return;
      }
      const mailNote = status === 'DEMO_MAIL_ERROR'
        ? '<p>Email xác nhận chưa gửi được, nhưng quyền Premium đã được kích hoạt.</p>'
        : '<p>Email thông báo đã gửi đến địa chỉ đăng ký.</p>';
      openModal('Nâng cấp thành công',`<div class="demo-payment-result">${icon('check',44)}<h3>Chào mừng bạn đến với Premium!</h3><p>Gói Premium đã được kích hoạt cho tài khoản của bạn.</p>${mailNote}<button class="btn btn-primary" data-action="premium-activated">Xem hồ sơ Premium</button></div>`);
      toast('Tài khoản đã được nâng cấp lên Premium!');
      return;
    }
    demoPaymentPoll=setTimeout(()=>pollDemoPayment(transactionId), 2500);
  }

  const id = () => Number(state.user?.user?.id ?? state.user?.id ?? 0);
  const realUser = () => Boolean(id() && state.online);
  const noDemo = () => realUser();
  const premiumUser = () => realUser() && state.premiumAccess === true;
  const userName = () => state.user?.user?.full_name || state.user?.full_name || 'Bạn của NutriFit';
  const pageName = () => routes.find(r=>r[0]===state.page)?.[1] || 'Tổng quan';
  const demoBanner = () => !realUser() ? `<div class="demo-banner">${icon('info')}<span><b>Chế độ xem trước.</b> Các chỉ số sức khỏe và nhật ký bên dưới chỉ là dữ liệu minh họa; chưa ghi lên hệ thống. <a href="#profile">Đăng nhập</a> và kết nối Backend để sử dụng dữ liệu thật.</span></div>` : '';
  const signedPrompt = () => realUser() ? '' : `<div class="auth-prompt">${icon('shield')}<span><b>Bạn đang khám phá NutriFit Studio.</b> Đăng nhập để lưu nhật ký và đồng bộ dữ liệu của riêng bạn.</span><button class="btn btn-primary btn-small" data-action="login-modal">Đăng nhập</button></div>`;
  const heading = (eyebrow, title, desc, actions='') => `<div class="page-head"><div><div class="eyebrow">${eyebrow}</div><h1>${title}</h1><p>${desc}</p></div>${actions ? `<div class="button-row">${actions}</div>` : ''}</div>`;
  const titleCard = (title, extra='', text='') => `<div class="card-title"><div><h3>${title}</h3>${text ? `<p>${text}</p>` : ''}</div>${extra}</div>`;
  const btn = (label, action, type='btn-primary', attrs='') => `<button type="button" class="btn ${type}" data-action="${action}" ${attrs}>${label}</button>`;
  const clamp = (value,min=0,max=100) => Math.min(max,Math.max(min,Number(value)||0));
  const percent = (value,target) => target > 0 ? clamp(100*value/target) : 0;
  const macro = (name, val, total, tone='') => `<div class="macro"><div class="macro-heading"><span><i class="macro-dot ${tone}"></i>${name}</span><span>${Math.round(percent(val,total))}%</span></div><strong>${fmt(val)}<small> / ${fmt(total)} g</small></strong><div class="meter ${tone}"><span style="width:${percent(val,total)}%"></span></div></div>`;
  const input = (label,name,defaultValue='',type='text',other='') => `<div class="form-group"><label class="form-label" for="${E(name)}">${label}</label><input class="field" id="${E(name)}" name="${E(name)}" type="${type}" value="${E(defaultValue)}" ${other} required /></div>`;
  // Each password input owns an independent visibility button. No password is stored.
  const passwordField = (label, name, autocomplete, register=false) => `<div class="form-group auth-password-field">
    <label class="form-label" for="${name}">${E(label)}</label>
    <div class="auth-password-wrap">
      <input class="field" id="${name}" name="${name}" type="password" autocomplete="${autocomplete}" maxlength="128" ${register?'minlength="8"':''} aria-describedby="${name}-hint" required>
      <button type="button" class="auth-password-toggle" data-action="toggle-password" data-password-target="${name}" aria-label="Hiện ${E(label.toLowerCase())}" aria-pressed="false" title="Hiện mật khẩu">${icon('eye',19)}</button>
    </div>
    ${register?`<p class="auth-password-hint" id="${name}-hint" aria-live="polite">${name==='password'?'Mật khẩu từ 8–128 ký tự bất kỳ; không bắt buộc chữ hoa, số hoặc ký tự đặc biệt.':'Nhập lại mật khẩu để xác nhận trùng khớp.'}</p>`:`<span class="screen-only" id="${name}-hint">Nhấn nút con mắt để hiện hoặc ẩn mật khẩu.</span>`}
  </div>`;
  function updateRegistrationPasswordFeedback(form){
    if(form?.dataset.mode!=='register')return true;
    const pw=form.elements.namedItem('password');
    const confirm=form.elements.namedItem('confirm_password');
    const hint=form.querySelector('#password-hint');
    const confirmHint=form.querySelector('#confirm_password-hint');
    if(!pw||!confirm||!hint||!confirmHint)return false;
    const length=pw.value.length;
    const hasPassword=length>0;
    const lengthValid=length>=8&&length<=128;
    hint.textContent=!hasPassword
      ? 'Mật khẩu từ 8–128 ký tự bất kỳ; không bắt buộc chữ hoa, số hoặc ký tự đặc biệt.'
      : !lengthValid ? `Mật khẩu cần ít nhất 8 ký tự (hiện có ${length}).`
      : '✓ Mật khẩu đạt yêu cầu độ dài.';
    hint.classList.toggle('is-success',hasPassword&&lengthValid);
    hint.classList.toggle('is-error',hasPassword&&!lengthValid);
    const filled=confirm.value.length>0;
    const matches=filled&&pw.value===confirm.value;
    confirmHint.textContent=!filled ? 'Nhập lại mật khẩu để xác nhận trùng khớp.'
      : matches ? '✓ Hai mật khẩu đã trùng khớp.' : 'Mật khẩu nhập lại chưa trùng khớp.';
    confirmHint.classList.toggle('is-success',matches);
    confirmHint.classList.toggle('is-error',filled&&!matches);
    confirm.classList.toggle('is-invalid',filled&&!matches);
    confirm.classList.toggle('is-valid',matches);
    // Native form constraint stops mismatches even if submit is triggered with Enter.
    confirm.setCustomValidity(filled&&!matches?'Mật khẩu nhập lại không trùng khớp.':'');
    return lengthValid&&matches;
  }
  const selectField = (label,name,options,value) => `<div class="form-group"><label class="form-label" for="${E(name)}">${label}</label><select class="field" name="${E(name)}" id="${E(name)}">${options.map(o=>`<option value="${E(o[0])}" ${String(o[0])===String(value)?'selected':''}>${E(o[1])}</option>`).join('')}</select></div>`;
  const genderOptions = [['male','Nam'],['female','Nữ']];
  // Ba mức vận động được chọn để tính TDEE (BMR x hệ số hoạt động).
  const activityOptions = [
    [1.2, 'Ít vận động (0–2 buổi/tuần)'],
    [1.55, 'Vận động vừa (3–5 buổi/tuần)'],
    [1.725, 'Vận động nhiều (6–7 buổi/tuần)']
  ];
  // Hiển thị hồ sơ cũ có hệ số 1.375 hoặc 1.9 bằng mức gần nhất.
  // Không thay đổi dữ liệu MySQL cho đến khi người dùng nhấn Lưu.
  const activityForSelect = value => {
    const n = Number(value);
    if (n === 1.375) return 1.2;
    if (n === 1.9) return 1.725;
    return [1.2, 1.55, 1.725].includes(n) ? n : 1.55;
  };
  const goalOptions = [['maintain','Duy trì cân nặng'],['lose','Giảm cân'],['gain','Tăng cân']];
  const mealNames = {breakfast:'Bữa sáng',lunch:'Bữa trưa',dinner:'Bữa tối'};
  const makeProfilePayload = data => ({gender:data.gender,age:Number(data.age),weight:Number(data.weight),height:Number(data.height),activity_level:Number(data.activity_level),goal:data.goal});
  const demoValues = () => ({target_kcal:2100,target_fiber:29,macros:{protein:131,carbs:236,fat:70},bmi:22.4,bmr:1580,tdee:2300,target_water_ml:2300});
  const getValues = () => state.calc || state.daily?.data?.targets || state.summary?.data?.targets || (realUser()?{target_kcal:0,macros:{protein:0,carbs:0,fat:0},bmi:0,bmr:0,tdee:0,target_water_ml:0}:demoValues());
  const consumed = () => state.daily?.data?.consumed || (!realUser()?{calories:1480,protein:92,carbs:156,fat:47,fiber:18}: {calories:0,protein:0,carbs:0,fat:0,fiber:0});
  const getTargetMacro = (target,kind) => Number(target?.macros?.[kind] ?? target?.[`target_${kind}`] ?? 0);
  const mealObj = type => state.mealData[type] || null;
  const mealGroupLabels = {MAIN:'Món chính',CARB:'Tinh bột',PROTEIN:'Chất đạm',VEGGIE:'Rau củ · chất xơ',SOUP:'Canh',DESSERT:'Tráng miệng',SIDE:'Món ăn kèm',DRINK:'Đồ uống'};
  const eatenMealLogs = () => state.daily?.data?.logs || [];
  const wasMealEaten = (type, option) => eatenMealLogs().some(log => log.mealType === type && Number(log.meal_reference?.optionId) === Number(option?.optionId));

  const mealOptions = type => realUser() ? mealObj(type)?.options || [] : exampleMeals[type] || [];
  const matchedEmoji = food => { const t = String(food||'').toLowerCase();if (/phở|hủ tiếu|bún|mì|miến|bánh canh/.test(t))return '🍜';if (/cơm/.test(t))return '🍛';if (/cháo|súp/.test(t))return '🥣';if (/bánh mì|bánh cuốn|bánh hỏi/.test(t))return '🥖';if (/salad|rau/.test(t))return '🥗';if (/gà/.test(t))return '🍗';if (/cá|ghẹ|cua/.test(t))return '🐟';return '🥘'; };
  // One error per message rather than a pile of identical 30-second timeout toasts.
  function toast(msg,isError=false) {
    const root=$('#toast-root');
    if(!root)return;
    const message=String(msg||'');
    if([...root.querySelectorAll('.toast')].some(el=>el.textContent===message))return;
    while(root.querySelectorAll('.toast').length>=3)root.querySelector('.toast')?.remove();
    const el=document.createElement('div');
    el.className='toast'+(isError?' error':'');
    el.textContent=message;
    root.append(el);
    setTimeout(()=>el.remove(),4400);
  }
  async function req(endpoint, data, method, timeout=15000) {
    const controller=new AbortController();const timeoutId=setTimeout(()=>controller.abort(),timeout);
    try {
      const user = state.user?.user || state.user;
      const headers={'Content-Type':'application/json'};
      if (/^\/api\/(payment|admin)\//.test(endpoint) && user?.id) headers['X-User-Id']=String(user.id);
      const response=await fetch(API+endpoint,{method:method||(data===undefined?'GET':'POST'),credentials:'include',headers,body:data===undefined?undefined:JSON.stringify(data),signal:controller.signal});
      const json=await response.json().catch(()=>({}));
      if (!response.ok && response.status===401 && !endpoint.includes('/api/auth/')) { /* session is not valid in browser */ }
      return {...json,ok:response.ok,httpStatus:response.status,
        message:json.message||(!response.ok?`Backend trả HTTP ${response.status}. Kiểm tra Terminal Flask cổng 5000.`:json.message)};
    } catch (error) {
      const timedOut=error.name==='AbortError';
      return {success:false,ok:false,
        message:timedOut?`Backend không phản hồi trong ${Math.ceil(timeout/1000)} giây. Kiểm tra Terminal Flask cổng 5000.`:'Không gọi được API Backend cổng 5000. Kiểm tra Flask, CORS và Network.',
        offline:!timedOut,timedOut};
    }
    finally { clearTimeout(timeoutId); }
  }
  async function checkConnection() {
    const result=await req('/api/health',undefined,'GET',4000);
    state.online=Boolean(result.ok && result.status==='connected');
    const el=$('#connection-status');if(el){el.className='status-pill '+(state.online?'connected':'offline');el.innerHTML=`<span class="status-dot"></span><span>${state.online?'Backend online':'Chế độ xem trước'}</span>`;}
    return state.online;
  }
  function setNavigation() {
    $('#main-nav').innerHTML=routes.filter(r=>r[0]!=='admin'||(state.user?.user?.role||state.user?.role)==='ADMIN').map(([key,label,ico])=>`<button type="button" class="nav-link ${state.page===key?'active':''}" data-page="${key}">${icon(ico)}<span>${E(label)}</span>${key==='chat'?'<span class="nav-tag">AI</span>':''}</button>`).join('');
    $('#page-crumb').textContent=pageName();
    $('#sidebar-user').textContent=userName();
    $('#sidebar-user-plan').textContent=state.user?(premiumUser()?'Thành viên Premium':'Thành viên NutriFit'):'Khách tham quan';
    $('#sidebar-avatar').textContent=initials(userName());$('.top-avatar').textContent=initials(userName());
  }
  async function loadData(page=state.page) {
    if (!state.online) return;
    if (page==='street') {
      const query = new URLSearchParams({meal_type:state.streetType,q:state.streetSearch});
      if(state.streetBudget!=='all')query.set('max_price',state.streetBudget);
      const response=await req('/api/street-food?'+query);
      if(response.success)state.street=response.data?.items || [];
    }
    if (page==='premium') {const response=await req('/api/payment/plans');if(response.success)state.plans=response.data||[];}
    if (page==='admin' && id()) await loadAdminData();
    if (!id()) return;
    if (['workouts','meals','profile','premium'].includes(page)) {
      const access = await req('/api/meals/premium-access');
      state.premiumAccess = access.success === true && Number(access.user_id) === id() && access.premium === true;
      if (!state.premiumAccess) state.dailyPlan=null;
    }
    if(page==='meals' && state.premiumAccess){
      const dailyPlan = await req('/api/meals/daily-plan');
      if(dailyPlan.success){
        state.dailyPlan=dailyPlan.data||null;
        if(state.dailyPlan?.meals?.length){
          for (const meal of state.dailyPlan.meals){
            if(!state.planDraft[meal.key])state.planDraft[meal.key]=meal.title||'';
          }
        }
      }
    }
    if(['dashboard','nutrition'].includes(page)) {
      const [daily, summary, profile]=await Promise.all([req('/api/nutrition/daily'),req('/api/nutrition/summary'),req('/'+id())]);
      if(daily.httpStatus===401 || summary.httpStatus===401){state.user=null;state.daily=null;state.summary=null;state.profile=null;localStorage.removeItem('nutrifit_session_user');toast('Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại.',true);return;}
      if(daily.success)state.daily=daily;if(summary.success)state.summary=summary;if(profile.success)state.profile=profile.data;
    }
    if(page==='meals'){const eaten=await req('/api/nutrition/daily');if(eaten.success)state.daily=eaten;}
    if(['dashboard','meals'].includes(page)) {
      const result=await req('/api/meals/today');if(result.httpStatus===401){state.user=null;state.mealData={};localStorage.removeItem('nutrifit_session_user');toast('Hãy đăng nhập lại để tiếp tục.',true);return;}
      if(result.success)state.mealData=result.todayMeals||{};
    }
    if(['workouts','dashboard'].includes(page)) {
      const [catalog, logs, progress] = await Promise.all([req('/api/workouts/catalog?user_id='+id()),req('/api/workouts/logs?user_id='+id()),req('/api/progress/weekly/'+id())]);
      if(catalog.success)state.workouts=(catalog.data||[]).flatMap(group=>(group.workouts||[]).map(w=>({...w,category:group.name||'Vận động',durationMinutes:w.duration_minutes,caloriesBurned:w.calories_burned})));
      if(logs.success)state.workoutLogs=logs.data||[];
      if(progress.success)state.progress=progress.data;
    }
    if(page==='profile') { const result=await req('/'+id());if(result.success)state.profile=result.data; }
  }
  let navigationSeq=0;
  async function navigate(page, refresh=false) {
    if(!routes.some(r=>r[0]===page))page='dashboard';
    state.page=page;state.recommendation=null;
    if(location.hash!=='#'+page)history.replaceState(null,'','#'+page);
    const sequence=++navigationSeq;
    setNavigation();render();
    if(state.online){state.loadingData=true;try{await loadData(page);}finally{state.loadingData=false;}}
    if(sequence===navigationSeq)render();
    if(!refresh){window.scrollTo({top:0,behavior:'smooth'});$('#shell').classList.remove('menu-open');}
  }
  function render() { setNavigation();const root=$('#page-content');root.innerHTML=({dashboard:dashboardPage,nutrition:nutritionPage,meals:mealsPage,workouts:workoutsPage,street:streetPage,chat:chatPage,profile:profilePage,premium:premiumPage,admin:adminPage}[state.page]||dashboardPage)(); }
  function dashboardPage() {
    const tgt=getValues(), eat=consumed();const first=userName().split(' ').slice(-1)[0];
    const sessions=realUser()?Number(state.progress?.totals?.sessions||0):4;
    const burned=realUser()?Number(state.progress?.totals?.calories||0):1250;
    const bars=realUser() ? (state.progress?.days||[]).map(d=>Number(d.calories)||0) : activityDemo;
    const max=Math.max(...bars,1);
    return `${heading('CÙNG NUTRIFIT BẮT ĐẦU NÀO',`Xin chào, ${E(first)}! <span style="font-size:28px">👋</span>`,'Đây là không gian chăm sóc sức khỏe dành riêng cho bạn.',btn(`${icon('calendar')} ${new Date().toLocaleDateString('vi-VN',{weekday:'long',day:'numeric',month:'long'})}`,'refresh','btn-light'))}
      ${demoBanner()}
      <div class="dash-grid">
        <section class="hero-card"><div class="hero-text"><div class="hero-kicker">✦ MỖI NGÀY MỘT CHÚT TỐT HƠN</div><h2>Chăm cơ thể tốt,<br> yêu bản thân hơn.</h2><p>Khám phá thực đơn phù hợp và xây dựng những thói quen tích cực mỗi ngày.</p>${btn(`Khám phá thực đơn ${icon('arrow')}`,'go-meals')}</div><div class="hero-orbit"><span class="orb-food">🥗</span><span class="orb-small">🥑</span></div></section>
        <section class="card insight-card"><div class="insight-top"><span class="insight-chip">✦ GÓC NHỎ SỨC KHỎE</span><span class="insight-icon">☘</span></div><h3>Hành trình ngàn dặm bắt đầu từ một bước nhỏ.</h3><p>Một bữa ăn cân bằng, một buổi vận động nhẹ. Chỉ cần bạn bắt đầu.</p><button type="button" data-page="nutrition">Xem mục tiêu của tôi ↗</button></section>
      </div>
      <section class="stats-row" aria-label="Chỉ số tổng quan">
        ${stat('Calo đã nạp',fmt(eat.calories)+' <small>kcal</small>','Mục tiêu '+fmt(tgt.target_kcal)+' kcal','fire','orange')}
        ${stat('Protein',fmt(eat.protein)+' <small>g</small>',`${Math.round(percent(eat.protein,getTargetMacro(tgt,'protein')))}% mục tiêu hôm nay`,'leaf','')}
        ${stat('Bài tập tuần này',fmt(sessions)+' <small>bài</small>',realUser()?`${state.progress?.totals?.active_days||0} ngày vận động`:'Đếm các bài tập đã ghi nhận','dumbbell','blue','7 ngày')}
        ${stat('Calo vận động',fmt(burned)+' <small>kcal</small>','Tổng trong 7 ngày','heart','pink','7 ngày')}
      </section>
      <div class="content-grid">
        <section class="card">${titleCard('Tổng quan dinh dưỡng',`<button class="btn-link" data-page="nutrition">Chi tiết ${icon('arrow',14)}</button>`,'Theo dõi năng lượng và các nhóm chất hôm nay')}
          <div class="nutri-progress"><div class="meter-top"><b>Năng lượng tiêu thụ</b><span><b>${fmt(eat.calories)}</b> <small>/ ${fmt(tgt.target_kcal)} kcal</small></span></div><div class="meter"><span style="width:${percent(eat.calories,tgt.target_kcal)}%"></span></div></div>
          <div class="macro-grid">${macro('Protein',eat.protein,getTargetMacro(tgt,'protein'))}${macro('Carbs',eat.carbs,getTargetMacro(tgt,'carbs'),'orange')}${macro('Fat',eat.fat,getTargetMacro(tgt,'fat'),'blue')}${macro('Chất xơ',eat.fiber,tgt.target_fiber,'fiber')}</div>
          <p class="dashboard-explain mt-16">${realUser()?'Chỉ số nạp được tính từ nhật ký ăn uống đã ghi nhận.':'Các số liệu trong phần này là ví dụ minh họa giao diện.'}</p>
        </section>
        <section class="card">${titleCard('Hoạt động trong tuần',`<button class="btn-link" data-page="workouts">Xem thêm ${icon('arrow',14)}</button>`,'Năng lượng đốt cháy từng ngày')}
          <div class="week-bars">${(bars.length?bars:[0,0,0,0,0,0,0]).slice(-7).map((v,i)=>`<div class="week-col"><div class="bar-pair"><span style="height:${Math.max(3,v/max*72)}%"></span><span class="second" style="height:${Math.max(3,v/max*95)}%"></span></div><em>${['T2','T3','T4','T5','T6','T7','CN'][i]}</em></div>`).join('')}</div><div class="chart-legend"><span>Mục tiêu tham khảo</span><span>Hoạt động</span></div>
        </section>
      </div>
      <div class="content-grid">
        <section class="card">${titleCard('Bữa ăn hôm nay',`<button class="btn-link" data-page="meals">Xem tất cả ${icon('arrow',14)}</button>`,'Những gợi ý giúp bạn ăn ngon và cân bằng')}
          <div class="meals-list">${Object.keys(mealNames).map((type,i)=>{const m=mealObj(type);const chosen=m?.options?.find(o=>o.id===m.selectedOption);const item=realUser()?(chosen||m?.options?.[0]):exampleMeals[type][0];return `<div class="meal-line"><div class="meal-thumb">${['🥣','🥗','🍲'][i]}</div><div class="meal-info"><strong>${item?E(item.title):'Chưa lên thực đơn'}</strong><small>${mealNames[type]} · ${m?.selectedOption?'Đã chốt':realUser()?'Gợi ý chưa chốt':'Minh họa'}</small></div><span class="cal">${item?fmt(item.calories)+' kcal':'—'}</span></div>`;}).join('')}</div>
        </section>
        <section class="card">${titleCard('Mẹo nhỏ mỗi ngày','','Sống khỏe không cần quá phức tạp')}<div class="tips-card"><span class="emoji">💧</span><h3>Đừng quên uống đủ nước nhé!</h3><p>Uống nước đều đặn trong ngày giúp bạn duy trì năng lượng và tập trung tốt hơn. Mục tiêu có thể tùy chỉnh theo nhu cầu.</p><button class="btn btn-mint btn-small mt-16" data-page="nutrition">Theo dõi nước uống ${icon('arrow')}</button></div><div class="tips-card mt-16" style="background:#fff8ef;border-color:#f5eadb"><span class="emoji">🚶</span><h3>Chỉ 20 phút vận động</h3><p>Đi bộ, đạp xe hoặc kéo giãn cơ đều là cách tuyệt vời để bắt đầu thói quen tốt.</p></div></section>
      </div>
      <div class="quick-actions"><button class="quick-action" data-page="meals"><span class="qa-icon">${icon('utensils')}</span><span><strong>Lên thực đơn</strong><small>Chọn món phù hợp</small></span></button><button class="quick-action" data-page="workouts"><span class="qa-icon">${icon('dumbbell')}</span><span><strong>Ghi nhận tập luyện</strong><small>Theo dõi vận động</small></span></button><button class="quick-action" data-page="chat"><span class="qa-icon">${icon('spark')}</span><span><strong>Hỏi NutriFit AI</strong><small>Trợ lý sức khỏe</small></span></button></div>`;
  }
  function stat(label,value,foot,ico,tone,period='Hôm nay') {return `<div class="card stat"><div class="stat-top"><span class="stat-icon ${tone}">${icon(ico)}</span><span class="stat-delta">● ${E(period)}</span></div><div class="stat-label">${label}</div><div class="stat-number">${value}</div><div class="stat-foot">${foot}</div></div>`;}
  function nutritionPage() {
    const target=getValues(), eat=consumed();
    const amt=Number(state.water[today()]||0);const waterTarget=Number(target.target_water_ml||2300);
    const fields=state.profile||{};
    const p={gender:String(fields.gender||'male').toLowerCase(),age:fields.age||25,height:fields.height||170,weight:fields.weight||65,goal:String(fields.goal||'maintain').toLowerCase(),activity_level:fields.activity_level||1.55};
    return `${heading('HIỂU CƠ THỂ CỦA BẠN','Dinh dưỡng & chỉ số','Theo dõi lượng calo, macro và nhu cầu năng lượng của riêng bạn.',btn(`${icon('plus')} Tính nhu cầu calo`,'scroll-calculator'))}${demoBanner()}
      <div class="three-col mb-20">
        <section class="card card-pad text-center"><div class="eyebrow">TIẾN ĐỘ HÔM NAY</div><div class="progress-wheel" style="--progress:${percent(eat.calories,target.target_kcal)}%"><div class="wheel-inner"><strong>${Math.round(percent(eat.calories,target.target_kcal))}%</strong><small>năng lượng đã nạp</small></div></div><div class="cal-big">${fmt(eat.calories)} <small>kcal</small></div><div class="muted text-sm mt-16">Mục tiêu ${fmt(target.target_kcal)} kcal/ngày</div></section>
        <section class="card card-pad">${titleCard('Phân bổ dinh dưỡng','','Mức tiêu thụ trong hôm nay')}<div class="nutri-progress"><div class="meter-top"><span>Protein</span><b>${fmt(eat.protein)} / ${fmt(getTargetMacro(target,'protein'))} g</b></div><div class="meter"><span style="width:${percent(eat.protein,getTargetMacro(target,'protein'))}%"></span></div></div><div class="nutri-progress"><div class="meter-top"><span>Carbohydrate</span><b>${fmt(eat.carbs)} / ${fmt(getTargetMacro(target,'carbs'))} g</b></div><div class="meter orange"><span style="width:${percent(eat.carbs,getTargetMacro(target,'carbs'))}%"></span></div></div><div class="nutri-progress"><div class="meter-top"><span>Chất béo</span><b>${fmt(eat.fat)} / ${fmt(getTargetMacro(target,'fat'))} g</b></div><div class="meter blue"><span style="width:${percent(eat.fat,getTargetMacro(target,'fat'))}%"></span></div></div><div class="nutri-progress"><div class="meter-top"><span>Chất xơ</span><b>${fmt(eat.fiber)} / ${fmt(target.target_fiber)} g</b></div><div class="meter fiber"><span style="width:${percent(eat.fiber,target.target_fiber)}%"></span></div><small class="fiber-info">${state.daily?.data?.fiber_complete===false?'Một số món thiếu dữ liệu chất xơ; đây là mức tối thiểu đã biết.':'Lượng chất xơ là ước tính theo món đã ghi nhận.'}</small></div></section>
        <section class="card card-pad"><div class="card-title"><div><h3>Uống nước mỗi ngày 💧</h3><p>Chỉ lưu trong trình duyệt của bạn</p></div></div><div class="cal-big" style="font-size:38px">${fmt(amt)} <small>ml</small></div><p class="section-intro">Mục tiêu tham khảo ${fmt(waterTarget)} ml/ngày</p><div class="meter blue"><span style="width:${percent(amt,waterTarget)}%"></span></div><div class="button-row mt-20">${btn('+ 250 ml','add-water','btn-primary btn-small')}${btn('Đặt lại','reset-water','btn-light btn-small')}</div></section>
      </div>
      <div class="two-col">
        <section class="card card-pad" id="nutrition-calculator">${titleCard('Máy tính dinh dưỡng','','Áp dụng công thức Mifflin–St Jeor và phân bổ macro cơ bản')}<form id="nutrition-form"><div class="form-grid">${selectField('Giới tính','gender',genderOptions,p.gender)}${input('Tuổi','age',p.age,'number','min="12" max="95"')}${input('Chiều cao (cm)','height',p.height,'number','min="100" max="250" step="0.1"')}${input('Cân nặng (kg)','weight',p.weight,'number','min="30" max="250" step="0.1"')}${selectField('Mức độ vận động','activity_level',activityOptions,activityForSelect(p.activity_level))}${selectField('Mục tiêu','goal',goalOptions,p.goal)}</div><button type="submit" class="btn btn-primary full">${icon('chart')} Tính chỉ số của tôi</button></form></section>
        <section class="card card-pad">${titleCard('Kết quả phân tích','<span class="pill green">Ước tính</span>')}<div class="split-stat"><div class="soft-box"><small>BMI</small><strong>${displayBmi(target.bmi, target.weight ?? state.profile?.weight, target.height ?? state.profile?.height)}</strong></div><div class="soft-box"><small>BMR</small><strong>${fmt(target.bmr)} <span class="text-sm">kcal</span></strong></div><div class="soft-box"><small>TDEE</small><strong>${fmt(target.tdee)} <span class="text-sm">kcal</span></strong></div><div class="soft-box"><small>Calo mục tiêu</small><strong>${fmt(target.target_kcal)} <span class="text-sm">kcal</span></strong></div></div><div class="mini-note mt-20">${icon('info')} Đây là mức năng lượng tham khảo, không thay thế tư vấn y tế. Chỉ số thực tế cần được điều chỉnh theo thể trạng và hoạt động của bạn.</div>${state.calc ? `<p class="form-hint">Kết quả vừa tính được cập nhật trong trang này. Để lưu vào hồ sơ, chuyển sang mục Hồ sơ của tôi.</p>`:''}</section>
      </div>
      <section class="card card-pad mt-20">${titleCard('Nhật ký dinh dưỡng','','Bữa ăn đã thực sự ghi nhận trong hệ thống')}${!realUser()?`<div class="empty"><div class="empty-icon">📝</div><h3>Nhật ký sẵn sàng cho bạn</h3><p>Đăng nhập để ghi nhận những gì bạn đã ăn, chỉnh khẩu phần và theo dõi tiến độ hằng ngày.</p>${btn('Đăng nhập để bắt đầu','login-modal')}</div>`:renderFoodLogs()}</section>`;
  }
  function renderFoodLogs(){const logs=state.daily?.data?.logs||[];return !logs.length?`<div class="empty"><div class="empty-icon">🥣</div><h3>Chưa có bữa ăn được ghi nhận</h3><p>Bạn có thể ghi bữa ăn trong giao diện gốc với các tính năng chọn món và thay khẩu phần đầy đủ.</p><a class="btn btn-light" href="legacy/index.html">Mở nhật ký chi tiết ↗</a></div>`:`<div class="table-wrap"><table class="data-table"><thead><tr><th>Bữa ăn</th><th>Năng lượng</th><th>Protein</th><th>Chất xơ</th><th>Thời gian</th></tr></thead><tbody>${logs.map(l=>`<tr><td><strong>${E(mealNames[l.mealType]||l.mealType||'Bữa ăn')}</strong></td><td>${fmt(l.totals?.calories)} kcal</td><td>${fmt(l.totals?.protein)} g</td><td>${fmt(l.totals?.fiber)} g</td><td>${E(l.consumedAtUtc||l.date||today())}</td></tr>`).join('')}</tbody></table></div><a class="btn btn-light btn-small mt-16" href="legacy/index.html">Chỉnh sửa nhật ký chi tiết ↗</a>`;}
  // Preferences are kept per signed-in account in this browser; the Flask API
  // validates and applies them when the user requests suggestions. No medical
  // allergy guarantees are implied by ingredient filtering.
  function ensureMealPreferences(){
    const owner=id() || 0;
    if(state.mealPrefOwner===owner)return;
    const saved=storage('nutrifit_meal_pref_'+owner,{});
    const clean=value=>Array.isArray(value)?value.filter(x=>typeof x==='string'):[];
    const ingredientMode=saved.ingredientMode==='reference'?'reference':'strict';
    state.mealPrefApplied={avoid:clean(saved.avoid),dislikes:clean(saved.dislikes),prefer:clean(saved.prefer),...(ingredientMode==='reference'?{ingredientMode}:{})};
    state.mealPrefDraft={...Object.fromEntries(['avoid','dislikes','prefer'].map(k=>[k, (saved[k]||[]).join(', ')])),ingredientMode};
    state.mealPrefOwner=owner;
  }
  const preferenceList = text => String(text||'').split(',').map(x=>x.trim()).filter(Boolean);
  const getDraftPreferences = () => ({...Object.fromEntries(['avoid','dislikes','prefer'].map(k=>[k,preferenceList(state.mealPrefDraft[k])])),
    ...(state.mealPrefDraft.ingredientMode==='reference'?{ingredientMode:'reference'}:{})});
  function preferencePanel(){
    const fields=[['avoid','Thực phẩm cần tránh (bắt buộc nếu có)','Ví dụ: cá, trứng'],['dislikes','Thực phẩm không thích (ưu tiên hạn chế)','Ví dụ: heo, bò'],['prefer','Thực phẩm muốn ưu tiên (tùy chọn)','Ví dụ: gà']];
    const applied=Object.values(state.mealPrefApplied).some(a=>a.length);
    return `<section class="meal-preferences card mb-20">
       <button class="meal-preference-toggle" type="button" data-action="toggle-meal-prefs" aria-expanded="${state.mealPrefOpen}">${state.mealPrefOpen?'▾':'▸'} Khẩu vị và đổi món theo ý bạn <span>${applied?'✓ Đã áp dụng':''}</span></button>
       ${state.mealPrefOpen?`<div class="meal-preference-body"><div class="meal-pref-grid">${fields.map(([name,label,hint])=>`<div class="form-group"><label class="form-label" for="meal-pref-${name}">${label}</label><input id="meal-pref-${name}" class="field" data-meal-pref="${name}" value="${E(state.mealPrefDraft[name]||'')}" placeholder="${hint}" autocomplete="off" maxlength="600" /></div>`).join('')}</div>
       <p class="meal-pref-note">Nhập nhiều nguyên liệu, ngăn cách bằng dấu phẩy. Nguyên liệu chưa được nhận diện sẽ báo lỗi. Không dùng bộ lọc để đảm bảo an toàn dị ứng.</p>
       <label class="meal-ingredient-mode"><input type="checkbox" id="meal-pref-reference-mode" ${state.mealPrefDraft.ingredientMode==='reference'?'checked':''}> Mở rộng gợi ý theo nguyên liệu được khai báo (chỉ dùng khi không thích / tránh theo sở thích, KHÔNG dùng khi dị ứng)</label>
       <p class="meal-pref-note">Mặc định hệ thống chỉ dùng món có danh sách nguyên liệu đã được xác nhận đầy đủ. Chế độ mở rộng có nhiều món hơn nhưng công thức tham khảo có thể thiếu thành phần.</p>
       <button type="button" class="btn btn-primary" data-action="apply-meal-prefs" ${state.mealBusy?'disabled':''}>${icon('check',16)} Áp dụng khẩu vị</button>
       </div>`:''}
     </section>`;
  }
  function mealOptionCard(option,index,selected){
    const parts=Array.isArray(option.components)?option.components:[];
    const isChosen=selected===option.id;
    const macros=option.macros||{};
    // A NULL fiber value means no reference data, NOT zero grams of fiber.
    const fiberKnown=Boolean(option.recipe?.fiber_complete===true || (option.recipe==null && macros.fiber!=null));
    const fiberText=fiberKnown?`${Number(macros.fiber||0).toFixed(1)}g`:'Chưa đủ dữ liệu';
    return `<article class="meal-option meal-option-v2 ${isChosen?'selected':''}">
      <div class="meal-option-head"><span class="meal-choice-badge meal-choice-${index+1}">LỰA CHỌN ${index+1}</span><strong>${Number(option.calories||0).toLocaleString('vi-VN',{maximumFractionDigits:1})} <small>kcal</small></strong></div>
      <h3>${E(option.title)}</h3>
      <div class="meal-macro-badges"><span class="carb">🌾 C: ${Number(macros.carbs||0).toFixed(1)}g</span><span class="protein">🥩 P: ${Number(macros.protein||0).toFixed(1)}g</span><span class="fat">🥑 F: ${Number(macros.fat||0).toFixed(1)}g</span><span class="fiber">🌿 Chất xơ: ${fiberText}</span></div>
      ${parts.length?`<div class="meal-component-list">${parts.map(part=>`<div class="meal-component-row"><span class="meal-component-name">${E(part.name)} <small class="meal-group-pill">${E(mealGroupLabels[part.type]||part.type||'')}</small></span><span class="meal-component-grams">${fmt(part.grams)} g</span>${realUser() && !selected && option.recipe && option.optionId?`<button type="button" ${state.mealBusy?'disabled':''} data-component-swap data-option-id="${Number(option.optionId)}" data-component-type="${E(part.type)}" class="meal-swap-link">Đổi món</button>`:''}</div>`).join('')}</div>`:`<p class="meal-legacy-info">Bộ gợi ý cũ chưa có danh sách từng món; chọn “Đổi bộ gợi ý” để tạo thực đơn mới có thể thay món.</p>`}
      <p class="meal-option-reason">${E(option.reason||option.digestibility||'Dinh dưỡng ước tính theo khẩu phần hiển thị.')}</p>
      <p class="meal-estimated-note">Giá trị dinh dưỡng chỉ mang tính ước tính.</p>
      <div class="meal-card-actions">${realUser()?`<button type="button" class="btn ${isChosen?'btn-mint':'btn-primary'} full" data-select-meal="${option.id}" ${isChosen||state.mealBusy?'disabled':''}>${isChosen?'✓ Đã chọn làm kế hoạch':`⊕ Chọn Lựa chọn ${index+1}`}</button>${isChosen?`<button type="button" class="btn ${wasMealEaten(state.mealType,option)?'btn-mint':'btn-light'} full" data-action="confirm-selected-meal" ${wasMealEaten(state.mealType,option)?'disabled':''}>${wasMealEaten(state.mealType,option)?'✓ Đã ghi nhật ký dinh dưỡng':'✓ Xác nhận đã ăn · Ghi vào Dinh dưỡng'}</button>`:''}`:`<button type="button" class="btn btn-light full" data-action="login-modal">Đăng nhập để chọn</button>`}</div>
     </article>`;
  }
  function mealsPage() {
    ensureMealPreferences();
    const type=state.mealType,meal=mealObj(type),options=mealOptions(type);
    const tabs=Object.entries(mealNames).map(([k,label])=>`<button type="button" class="tab ${type===k?'active':''}" data-meal="${k}">${({breakfast:'🌅',lunch:'☀️',dinner:'🌙'})[k]} ${label}</button>`).join('');
    return `${heading('ĂN NGON MỖI NGÀY','Gợi ý món ăn sức khỏe','Ba lựa chọn cho mỗi bữa với khẩu phần và dinh dưỡng ước tính.')}${demoBanner()}${signedPrompt()}
       ${dailyPlanPanel()}
       <div class="meal-toolbar"><div class="tabs">${tabs}</div><div class="meal-toolbar-actions">${btn(`${icon('spark',16)} Gợi ý món mới`,'generate-meal','btn-light',state.mealBusy?'disabled':'')}${options.length?btn(`${icon('arrow',16)} Đổi bộ gợi ý`,'refresh-meal','btn-primary',state.mealBusy?'disabled':''):''}${btn(`${icon('clock',16)} Lịch sử`,'meal-history','btn-light')}</div></div>
       ${preferencePanel()}
       <div class="meal-mode-bar"><div><span class="eyebrow">THỰC ĐƠN ${E(mealNames[type].toUpperCase())}</span><h3>${meal?'Thực đơn được đề xuất cho bạn':'Hôm nay ăn gì cho khỏe?'}</h3><p>${meal?'Bạn có thể đổi riêng từng món, chọn một phương án hoặc đổi cả bộ.':'Chọn một bữa và nhấn Gợi ý món mới để bắt đầu.'}</p></div><span class="pill green">${meal?.selectedOption?'✓ Đã chọn':options.length?'3 phương án':'Chưa gợi ý'}</span></div>
       <div class="meal-macro-legend"><strong>Chú thích dinh dưỡng:</strong><span>🌾 C: Carbs (Tinh bột)</span><span>🥩 P: Protein (Chất đạm)</span><span>🥑 F: Fat (Chất béo)</span><span>🌿 Chất xơ: Fiber (g)</span></div>
       ${options.length?`<div class="three-col meal-options-grid">${options.map((o,i)=>mealOptionCard(o,i,meal?.selectedOption)).join('')}</div>`:`<div class="empty meal-empty"><div class="empty-icon">🥗</div><h3>Chưa có gợi ý cho bữa này</h3><p>Nhấn Gợi ý món mới để nhận 3 phương án phù hợp hồ sơ và khẩu vị.</p>${btn('Gợi ý món mới','generate-meal')}</div>`}
       ${meal?.selectedOption?`<div class="meal-selected-toolbar">${icon('check',18)} Đây là thực đơn bạn dự định ăn. Chỉ cộng dinh dưỡng sau khi bạn nhấn “Xác nhận đã ăn”. ${btn('Bỏ chọn để đổi thực đơn','defer-meal','btn-light')}</div>`:''}`;
  }

  function dailyPlanPanel(){
    const access = premiumUser();
    const plan = state.dailyPlan;
    const mealSlots = [['breakfast','Bữa sáng','Ví dụ: 1 tô phở bò'],['lunch','Bữa trưa','Ví dụ: 1 chén cơm, 150g thịt gà, rau luộc'],['dinner','Bữa tối','Ví dụ: 1 tô bún riêu'],['snack','Bữa phụ','Ví dụ: 1 hộp sữa chua và 1 quả chuối']];
    const selected=mealSlots.find(m=>m[0]===state.planMealType)||mealSlots[0];
    return `<section class="card card-pad mb-20 daily-plan-shell">
      <div class="card-title"><div><span class="eyebrow">ƯỚC TÍNH BỮA ĂN · PREMIUM</span><h3>Chọn bữa ăn bất kỳ</h3><p>Chọn một trong bốn bữa, nhập món bạn muốn ăn và khẩu phần. AI sẽ ước tính dinh dưỡng cho riêng bữa đó; không cần nhập tất cả các bữa.</p></div><span class="pill gold">${icon('crown',14)} Premium</span></div>
      ${access ? `<form id="manual-daily-plan-form" class="daily-plan-input-form"><div class="daily-plan-input-grid">
        <div class="form-group"><label class="form-label" for="plan-meal-type">Chọn bữa ăn</label><select class="field" id="plan-meal-type" name="meal_type">${mealSlots.map(([key,label])=>`<option value="${key}" ${selected[0]===key?'selected':''}>${label}</option>`).join('')}</select></div>
        <div class="form-group"><label class="form-label" for="plan-dish">Món ăn và khẩu phần</label><input class="field" id="plan-dish" name="dish" value="${E(state.planDraft[selected[0]]||'')}" placeholder="${E(selected[2])}" maxlength="160" minlength="3" required></div>
        </div><div class="daily-plan-actions"><button type="submit" class="btn btn-primary" ${state.planBusy?'disabled':''}>${icon('spark')} ${state.planBusy?'AI đang tính dinh dưỡng...':'AI ước tính và lưu bữa ăn'}</button><p class="mini-note">Chỉ cần nhập một bữa mỗi lần. Bạn có thể quay lại chọn bữa khác; các bữa đã lưu hôm nay sẽ được giữ nguyên.</p></div></form>`
      : `<div class="premium-upsell-inline"><p>Tính năng chọn bữa ăn và ước tính dinh dưỡng bằng AI dành cho thành viên Premium.</p>${btn(`${icon('crown')} Nâng cấp Premium`,'upgrade-premium','btn-primary')}</div>`}
      ${access && plan?.meals?.length ? `<div class="daily-plan-result"><h4 class="mb-16">Các bữa đã lưu hôm nay · ${plan.meals.length} bữa</h4><div class="daily-plan-totals"><span>Tổng các bữa đã nhập: <strong>~${fmt(plan.total_kcal)} kcal</strong></span><span>Protein: <strong>${fmt(plan.totals?.protein)} g</strong></span><span>Carb: <strong>${fmt(plan.totals?.carbs)} g</strong></span><span>Chất béo: <strong>${fmt(plan.totals?.fat)} g</strong></span><span>Chất xơ: <strong>${plan.fiber_complete===true?`${fmt(plan.totals?.fiber)} g`:'Chưa đủ dữ liệu'}</strong></span></div>
      <div class="daily-plan-grid">${plan.meals.map(m=>`<article class="daily-plan-meal"><span class="pill green">${E(m.label)}</span><h4>${E(m.title)}</h4><strong>~${fmt(m.calories)} kcal</strong><small>Đạm ${fmt(m.macros?.protein)}g · Carb ${fmt(m.macros?.carbs)}g · Béo ${fmt(m.macros?.fat)}g · Xơ ${m.macros?.fiber==null?'—':`${fmt(m.macros.fiber)}g`}</small><p>${E(m.portion||'')}</p><p>${E(m.note||'Năng lượng ước tính')}</p></article>`).join('')}</div>
      <p class="mini-note mt-16">${E(plan.note||'Các chỉ số là ước tính; không bao gồm bữa bạn chưa nhập.')}</p></div>` : ''}
    </section>`;
  }
  async function estimateManualDailyPlan(form){
    if(!realUser())return authModal('login');
    if(!premiumUser())return upgradePremium();
    if(state.planBusy)return;
    const data=new FormData(form);
    const slot=String(data.get('meal_type')||'');
    const dish=String(data.get('dish')||'').trim();
    if(!['breakfast','lunch','dinner','snack'].includes(slot))return toast('Vui lòng chọn một bữa ăn.',true);
    if(dish.length<3 || dish.length>160)return toast('Nhập tên món và khẩu phần từ 3 đến 160 ký tự.',true);
    state.planMealType=slot;
    state.planDraft[slot]=dish;
    state.planBusy=true;render();
    try {
      const result=await req('/api/meals/daily-plan',{user_id:id(),meals:{[slot]:dish}},'POST',70000);
      if(result.httpStatus===403 && result.code==='PREMIUM_REQUIRED'){
        state.premiumAccess=false;state.dailyPlan=null;return upgradePremium();
      }
      if(result.success && result.data?.meals?.some(m=>m.key===slot)){
        state.dailyPlan=result.data;toast('Đã ước tính và lưu bữa ăn bạn chọn.');
      }else toast(result.message||'Chưa thể ước tính bữa ăn. Hãy kiểm tra kết nối Gemini.',true);
    }finally{state.planBusy=false;render();}
  }
  function upgradePremium(){
    if(!realUser())return authModal('login');
    openModal('Mở khóa cùng NutriFit Premium',`<p class="modal-intro">Tính năng này dành cho thành viên Premium. Nâng cấp để tạo bài tập bằng AI và chọn bữa ăn bất kỳ để ước tính dinh dưỡng.</p><div class="premium-upsell-inline"><div class="button-row"><button class="btn btn-primary full" data-action="go-premium">${icon('crown')} Xem các gói Premium</button></div></div>`);
  }

  // Thống kê dựa trên số dòng WorkoutLogs: mỗi lần ghi nhật ký là một bài tập.
  function workoutMetric(label,value,unit,note,ico){
    return `<div class="workout-metric"><span class="workout-metric-icon">${icon(ico,18)}</span><div class="workout-metric-label">${label}</div><div class="workout-metric-value">${fmt(value)} <small>${unit}</small></div><p>${note}</p></div>`;
  }
  function workoutCard(w,i){
    return `<article class="card exercise-card workout-compact">
      <div class="workout-card-head"><span class="pill green">${E(w.category||'Vận động')}</span>${w.is_custom?'<span class="pill gray">Bài tập của bạn</span>':''}</div>
      <h3>${E(w.name)}</h3>
      <p>Thời lượng và calo mang tính tham khảo, có thể thay đổi theo cường độ và thể trạng.</p>
      <div class="exercise-meta"><span>${icon('clock',14)} <b>${fmt(w.durationMinutes??w.duration_minutes)} phút</b></span><span>${icon('fire',14)} <b>~${fmt(w.caloriesBurned??w.calories_burned)} kcal</b></span></div>
      <button class="btn btn-light full" data-workout="${Number(w.id)||0}">${realUser()?'Ghi nhận bài tập':'Xem bài tập'} ${icon('arrow')}</button>
    </article>`;
  }
  function workoutsPage() {
    const workouts=realUser()?state.workouts:demoWorkouts;
    const categories=['Tất cả',...new Set(workouts.map(w=>w.category||'Khác'))];
    const filtered=state.workoutCategory==='Tất cả'?workouts:workouts.filter(w=>w.category===state.workoutCategory);
    const week=realUser()?(state.progress?.totals||{}):{sessions:4,minutes:150,calories:1250,active_days:3};
    const lastDay=realUser()?(state.progress?.days||[]).find(d=>d.date===today()):null;
    const day=realUser()?(lastDay||{sessions:0,minutes:0,calories:0}):{sessions:1,minutes:30,calories:250};
    const share=Number(week.calories)>0?Math.round(100*Number(day.calories||0)/Number(week.calories)):0;
    return `${heading('CƠ THỂ NĂNG ĐỘNG','Luyện tập & tiến độ','Theo dõi từng bài tập đã hoàn thành trong ngày và trong 7 ngày gần nhất.',btn(`${icon('plus')} ${premiumUser()?'Tạo bài tập với AI':'Tạo bài tập với AI · Premium'}`,'custom-workout-modal'))}${demoBanner()}${signedPrompt()}
      <div class="workout-comparison">
        <section class="workout-summary-panel"><div class="workout-summary-head"><div><span class="eyebrow">HOẠT ĐỘNG HÔM NAY</span><h2>Trong ngày</h2><p>${new Date().toLocaleDateString('vi-VN',{day:'2-digit',month:'2-digit',year:'numeric'})}</p></div><span class="workout-summary-badge">${icon('calendar',16)} Hôm nay</span></div>
          <div class="workout-metric-grid">${workoutMetric('Bài tập',day.sessions,'bài','Số bài đã ghi nhận','dumbbell')}${workoutMetric('Thời gian',day.minutes,'phút','Tổng thời gian hôm nay','clock')}${workoutMetric('Calo đốt cháy',day.calories,'kcal','Ước lượng từ nhật ký','fire')}</div></section>
        <section class="workout-summary-panel"><div class="workout-summary-head"><div><span class="eyebrow">TỔNG KẾT 7 NGÀY</span><h2>Trong tuần</h2><p>7 ngày gần nhất, bao gồm hôm nay</p></div><span class="workout-summary-badge">${icon('chart',16)} 7 ngày</span></div>
          <div class="workout-metric-grid">${workoutMetric('Bài tập',week.sessions,'bài',`${fmt(week.active_days)} ngày có vận động`,'dumbbell')}${workoutMetric('Thời gian',week.minutes,'phút','Tổng cộng 7 ngày','clock')}${workoutMetric('Calo đốt cháy',week.calories,'kcal','Ước lượng từ nhật ký','fire')}</div></section>
      </div>
      <div class="workout-comparison-foot">${icon('info',16)} Hôm nay đóng góp <b>${share}%</b> số calo vận động của 7 ngày gần nhất. Mỗi lần ghi nhận được tính là một bài tập; calo là ước lượng.</div>
      <div class="page-head"><div><div class="eyebrow">THƯ VIỆN BÀI TẬP</div><h1 style="font-size:22px">Chọn cách vận động bạn thích</h1></div><div class="filters">${categories.slice(0,5).map(c=>`<button class="tab ${state.workoutCategory===c?'active':''}" data-workout-filter="${E(c)}">${E(c)}</button>`).join('')}</div></div>
      ${filtered.length?`<div class="three-col">${filtered.map(workoutCard).join('')}</div>`:`<div class="empty"><h3>Chưa có bài tập</h3><p>Danh mục chưa có bài phù hợp với bộ lọc của bạn.</p></div>`}
      <section class="card card-pad mt-20">${titleCard('Nhật ký luyện tập',btn('Ghi nhận bài tập','log-workout-modal','btn-light btn-small'),'Các bài tập đã lưu vào tài khoản')}${realUser()?(state.workoutLogs?.length?`<div class="timeline">${state.workoutLogs.slice(0,8).map(l=>`<div class="timeline-item"><div><strong>${E(l.workout_name||'Vận động')}</strong><small>${E(l.date||today())} · ${fmt(l.duration_minutes)} phút · ~${fmt(l.calories_burned)} kcal</small></div><button class="btn btn-danger btn-small" data-delete-log="${Number(l.log_id)}">Xóa</button></div>`).join('')}</div>`:`<div class="empty"><h3>Chưa có bài tập được ghi nhận</h3><p>Chọn bài tập trong thư viện và ghi nhận để theo dõi tiến độ.</p></div>`):`<div class="mini-note">Đăng nhập để tạo bài tập với AI và lưu nhật ký luyện tập.</div>`}</section>`;
  }
  function streetPage(){
    const all=state.street.length?state.street:streetSeed;
    const list=all.filter(d=>{
      const match=(state.streetType==='all'||d.meal_type===state.streetType||d.meal_type==='all') && (state.streetBudget==='all'||Number(d.price_vnd)<=Number(state.streetBudget));
      const search=!state.streetSearch||String(d.title).toLocaleLowerCase('vi').includes(state.streetSearch.toLocaleLowerCase('vi'));
      return match&&search;
    });
    return `${heading('HƯƠNG VỊ QUEN THUỘC','Món ngon Việt Nam','Khám phá những món ăn gần gũi theo lượng calo và ngân sách.',btn(`${icon('spark')} Gợi ý theo ngân sách`,'street-recommend'))}${!realUser()?`<div class="demo-banner">${icon('info')}<span>Danh sách tham khảo từ bộ dữ liệu 36 món của dự án. Giá và dinh dưỡng đều là ước tính, không phải bảng giá thực tế.</span></div>`:''}
      <section class="card card-pad mb-20"><div class="tool-strip"><div class="form-group search-group"><label class="form-label" for="food-search">Tìm tên món ăn</label><input class="field" id="food-search" placeholder="Ví dụ: phở bò, cơm gà..." value="${E(state.streetSearch)}" /></div><div class="form-group">${selectField('Bữa ăn','street-type',[['all','Tất cả các bữa'],['breakfast','Bữa sáng'],['lunch','Bữa trưa'],['dinner','Bữa tối']],state.streetType).replace('class="form-group"','class="form-group" style="margin:0"')}</div><div class="form-group">${selectField('Ngân sách tối đa','street-budget',[['all','Không giới hạn'],['35000','35.000đ'],['45000','45.000đ'],['50000','50.000đ'],['60000','60.000đ']],state.streetBudget).replace('class="form-group"','class="form-group" style="margin:0"')}</div></div><span class="pill green">${list.length} món được tìm thấy</span></section>
      ${state.recommendation?`<div class="card card-pad mb-20" style="border-color:#bcdbbe;background:#f7fbf5"><div class="card-title"><h3>✦ Các món phù hợp được gợi ý</h3><button class="btn btn-light btn-small" data-action="clear-recommend">Hiển thị tất cả</button></div><p class="section-intro">Chọn lọc theo ngân sách và năng lượng cho một bữa ăn.</p><div class="button-row">${state.recommendation.map(d=>`<span class="pill green">${E(d.title)} · ${fmt(d.calories)} kcal</span>`).join('')}</div></div>`:''}
      ${list.length?`<div class="three-col">${list.map((d,i)=>`<article class="card food-card"><div class="food-content"><span class="pill green food-price-inline">${money(d.price_vnd)}</span><h3 class="food-title">${E(d.title)}</h3><div class="food-stats"><span>🔥 <b>${fmt(d.calories)} kcal</b></span><span>Đạm <b>${fmt(d.protein_g)}g</b></span><span>Carbs <b>${fmt(d.carbs_g)}g</b></span></div><p class="food-note">${E(d.protein_desc||d.veggie_desc||'Dữ liệu món Việt từ dự án.')}</p><button class="btn btn-light full btn-small" data-food-detail="${Number(d.id)||0}">Xem thông tin món ${icon('arrow')}</button></div></article>`).join('')}</div>`:`<div class="empty"><div class="empty-icon">🔎</div><h3>Chưa tìm thấy món phù hợp</h3><p>Thử tăng ngân sách hoặc đổi từ khóa để xem thêm món ngon.</p>${btn('Xóa bộ lọc','clear-street','btn-light')}</div>`}
      <div class="mini-note mt-20">Thông tin calo, thành phần và giá của danh mục đường phố chỉ mang tính tham khảo. Không đồng nhất với bữa ăn đã ghi nhận trong nhật ký.</div>`;
  }
  function chatPage(){
    const greetings=`Xin chào! Mình là NutriFit AI. Bạn có thể hỏi về thực đơn, công thức, calo, chỉ số cơ thể hay lịch tập luyện. 🌿`;
    const chats=[{role:'assistant',content:greetings},...state.chat];
    return `${heading('TRỢ LÝ CỦA BẠN','NutriFit AI Assistant','Một người bạn đồng hành để bạn hiểu hơn về ăn uống và vận động.',btn(`${icon('plus')} Cuộc trò chuyện mới`,'new-chat','btn-light'))}
      ${!state.online?`<div class="demo-banner">${icon('info')}<span>Backend đang offline. Bạn có thể xem trước giao diện chat; để nhận câu trả lời AI thật, hãy chạy Flask và cấu hình <b>GEMINI_API_KEY</b> trong file .env.</span></div>`:''}
      <div class="chat-shell"><section class="card chat-panel"><div class="chat-head"><div class="bot-avatar">✳</div><div style="flex:1"><strong>NutriFit AI</strong><small>${state.online?'Kết nối qua Gemini API':'Chờ kết nối Backend'} · Trợ lý dinh dưỡng</small></div><span class="pill green">✦ AI</span></div><div class="chat-messages" id="chat-messages">${chats.map(m=>`<div class="chat-bubble ${m.role==='user'?'you':'bot'}"><span class="chat-name">${m.role==='user'?'Bạn':'✳ NutriFit AI'}</span>${E(m.content)}</div>`).join('')}${state.chatPending?`<div class="chat-bubble bot"><span class="chat-name">✳ NutriFit AI</span>Đang tìm câu trả lời…</div>`:''}</div><form id="chat-form" class="chat-compose"><textarea class="field" name="message" placeholder="Hỏi NutriFit điều gì đó..." rows="1" maxlength="2000" required></textarea><button class="btn btn-primary" type="submit" ${state.chatPending?'disabled':''} aria-label="Gửi tin nhắn">${icon('arrowup')}</button></form></section>
      <aside class="chat-side"><div class="card">${titleCard('Bạn có thể hỏi gì?','','Chạm vào một câu hỏi để bắt đầu')}<div class="prompt-list">${[['🥗','Gợi ý thực đơn 1 ngày 2.000 kcal'],['🍳','Cách làm ức gà áp chảo mềm ngon'],['🏃','Lịch tập cho người mới 3 buổi/tuần'],['📊','BMI và TDEE khác nhau thế nào?']].map(([ico,text])=>`<button class="prompt-btn" data-prompt="${E(text)}"><span>${ico}</span>${E(text)}</button>`).join('')}</div></div><div class="tips-card mt-16"><span class="emoji">✨</span><h3>Được thiết kế cho sức khỏe</h3><p>AI tư vấn thông tin chung; không thay thế bác sĩ hoặc chuyên gia dinh dưỡng.</p></div></aside></div>`;
  }
  function profilePage(){const p=state.profile||{};const member=state.user?.user||state.user;
    return `${heading('KHÔNG GIAN CỦA RIÊNG BẠN','Hồ sơ cá nhân','Hoàn thiện thông tin để nhận những gợi ý sát hơn với nhu cầu.')}${demoBanner()}
      <div class="two-col"><section class="card card-pad"><div style="display:flex;align-items:center;gap:17px;margin-bottom:24px"><div class="user-avatar" style="width:65px;height:65px;font-size:23px;border-radius:17px">${E(initials(userName()))}</div><div><div class="eyebrow">HỒ SƠ NUTRIFIT</div><h2 style="font-size:20px;margin:0 0 5px">${E(userName())}</h2><p class="muted text-sm" style="margin:0">${member?E(member.email||'Thành viên NutriFit'):'Khách tham quan'}</p></div></div><div class="button-row mb-20"><span class="pill ${member?'green':'gray'}">${member?'✓ Đã đăng nhập':'Chưa đăng nhập'}</span><span class="pill gold">${premiumUser()?'Premium':'Free'}</span></div>${member?`${btn(icon('logout')+' Đăng xuất','logout','btn-light')}`:`${btn('Đăng nhập','login-modal')}${btn('Đăng ký tài khoản','register-modal','btn-light')}`}<div class="mini-note mt-20">Tài khoản, hồ sơ và thông tin dinh dưỡng được xử lý bởi Backend Flask. Không lưu mật khẩu trong trình duyệt.</div></section>
      <section class="card card-pad">${titleCard('Thông tin thể trạng','','Lưu thay đổi để cập nhật mục tiêu dinh dưỡng trên hệ thống')}<form id="profile-form"><div class="form-grid">${selectField('Giới tính','gender',[['MALE','Nam'],['FEMALE','Nữ']],String(p.gender||'MALE').toUpperCase())}${input('Tuổi','age',p.age||25,'number','min="12" max="95"')}${input('Chiều cao (cm)','height',p.height||170,'number','min="100" max="250" step="0.1"')}${input('Cân nặng (kg)','weight',p.weight||65,'number','min="30" max="250" step="0.1"')}${selectField('Mức độ vận động','activity_level',activityOptions,activityForSelect(p.activity_level))}${selectField('Mục tiêu','goal',[['MAINTAIN','Duy trì'],['LOSE','Giảm cân'],['GAIN','Tăng cân']],String(p.goal||'MAINTAIN').toUpperCase())}</div><button class="btn btn-primary full" type="submit">${icon('check')} Lưu hồ sơ sức khỏe</button></form></section></div>
      <div class="two-col mt-20"><section class="card card-pad">${titleCard('Chỉ số cơ thể')}${[['BMI',displayBmi(p.bmi,p.weight,p.height)],['BMR',fmt(p.bmr)+' kcal'],['TDEE',fmt(p.tdee)+' kcal'],['Năng lượng mục tiêu',fmt(p.target_kcal)+' kcal'],['Nước uống gợi ý',fmt(p.target_water_ml)+' ml']].map(([label,value])=>`<div class="timeline-item" style="margin-bottom:10px"><strong>${label}</strong><span>${value}</span></div>`).join('')}</section><section class="tips-card"><span class="emoji">🌿</span><h3>Hồ sơ khỏe, đề xuất sát hơn</h3><p>Khi bạn điền cân nặng, chiều cao, độ tuổi và mục tiêu, NutriFit dùng các thông tin này để tính BMR, TDEE, phân bổ macro và tạo thực đơn phù hợp. Bạn có thể cập nhật bất kỳ lúc nào.</p><button class="btn btn-mint mt-20" data-page="nutrition">Xem chỉ số dinh dưỡng ${icon('arrow')}</button></section></div>`;
  }
  function premiumPage(){
    const plans=state.plans.length?state.plans:[{plan_id:null,plan_name:'Khám phá',price_vnd:0,duration_days:0,description:'Bắt đầu hành trình wellness.'},{plan_id:null,plan_name:'Premium tháng',price_vnd:null,duration_days:30,description:'Mở khóa những tính năng chuyên sâu.'},{plan_id:null,plan_name:'Premium dài hạn',price_vnd:null,duration_days:365,description:'Đồng hành lâu hơn với sức khỏe.'}];
    return `${heading('NÂNG TẦM TRẢI NGHIỆM','NutriFit Premium','Chọn gói phù hợp với nhu cầu luyện tập và chăm sóc dinh dưỡng.')}${!state.online?'<div class="demo-banner">Các gói và giá trong hệ thống chỉ được hiển thị chính xác khi Backend và database đã được kết nối. Không thể tạo thanh toán trong chế độ xem trước.</div>':''}
      <div class="pricing-grid">${plans.map((p,i)=>`<div class="card price-card ${i===1?'featured':''}"><span class="pill ${i===1?'gold':'green'}" style="width:max-content;margin-bottom:17px">${i===1?'✦ Đề xuất':'NutriFit'}</span><h3>${E(p.plan_name)}</h3><p>${E(p.description||'Trải nghiệm phù hợp với lộ trình của bạn.')}</p><div class="price-amount">${p.price_vnd===null?'Liên hệ':fmt(p.price_vnd)+'đ'} <small>${p.duration_days?' / '+p.duration_days+' ngày':''}</small></div><div class="price-benefits"><span>Giao diện theo dõi cá nhân</span><span>Tạo bài tập AI & thực đơn cả ngày</span><span>Thống kê hoạt động và nhật ký</span><span>Hỗ trợ gợi ý thực đơn thông minh</span></div><button type="button" class="btn ${i===1?'btn-mint':'btn-primary'}" data-checkout="${p.plan_id ?? ''}" ${p.plan_id===null?'disabled':''}>${i===0?'Chọn gói':'Chọn gói này'} ${icon('arrow')}</button></div>`).join('')}</div>
      <div class="card card-pad mt-20">${titleCard('Vì sao nên chọn NutriFit?','','Mọi hành trình lành mạnh đều cần sự kiên trì')}<div class="three-col"><div class="soft-box">${icon('leaf')}<h3>Ăn uống cân bằng</h3><p class="text-sm muted">Thực đơn món Việt đi kèm ước tính dinh dưỡng.</p></div><div class="soft-box">${icon('chart')}<h3>Theo dõi mỗi ngày</h3><p class="text-sm muted">Lưu hoạt động và xem tiến độ của bạn.</p></div><div class="soft-box">${icon('spark')}<h3>Trợ lý AI</h3><p class="text-sm muted">Giải đáp kiến thức dinh dưỡng và luyện tập.</p></div></div></div><div class="mini-note mt-16">Sau khi hoàn tất xác nhận đăng ký, gói Premium được kích hoạt trực tiếp trên tài khoản của bạn.</div>`;
  }
  const adminRole = () => String(state.user?.user?.role || state.user?.role || '').toUpperCase()==='ADMIN';
  const adminDate = (value, short=false) => {
    const match = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
    if (!match) return '—';
    return short ? `${match[3]}/${match[2]}` : `${match[3]}/${match[2]}/${match[1]}`;
  };
  const adminStatus = value => {
    const key = String(value || '').toUpperCase();
    const statuses = {SUCCESS:['Thành công','success'],PENDING:['Chờ xử lý','pending'],FAILED:['Thất bại','failed'],CANCELLED:['Đã hủy','neutral'],CANCELED:['Đã hủy','neutral'],DEMO_PENDING:['Chờ xác nhận QR','pending'],DEMO_CONFIRMING:['Đang xử lý','pending'],DEMO_SUCCESS:['Thành công','success'],DEMO_MAIL_ERROR:['Thành công · lỗi email','success']};
    const [label,tone] = statuses[key] || [key || 'Không rõ','neutral'];
    return `<span class="admin-status ${tone}"><span class="admin-status-dot"></span>${E(label)}</span>`;
  };
  const adminMethod = value => ({BANK_TRANSFER:'Chuyển khoản',DEMO:'Chuyển trạng thái',DEMO_QR:'QR NutriFit',CASH:'Tiền mặt'}[String(value||'').toUpperCase()] || value || '—');
  const adminBlank = (title, detail='Không có dữ liệu phù hợp với bộ lọc hiện tại.') => `<div class="admin-blank">${icon('info',26)}<strong>${E(title)}</strong><span>${E(detail)}</span></div>`;
  const adminTxnRow = item => `<tr><td><div class="admin-code">${E(displayTransactionCode(item.transaction_code || '#'+(item.transaction_id||'')))}</div><small class="admin-table-meta">#${E(item.transaction_id ?? '—')} · ${E(adminMethod(item.payment_method))}</small></td><td><strong>${E(item.user_name || 'Chưa có tên')}</strong><small class="admin-table-meta">${E(item.user_email || '—')}</small></td><td>${E(item.plan_name || '—')}</td><td class="admin-number">${money(item.amount)}</td><td>${adminStatus(item.status)}</td><td>${E(adminDate(item.created_at))}</td></tr>`;
  const adminUserRow = item => `<tr><td><div class="admin-user-cell"><span class="admin-user-avatar">${E(initials(item.full_name||item.email))}</span><div><strong>${E(item.full_name||'Chưa cập nhật')}</strong><small class="admin-table-meta">#${E(item.id)}</small></div></div></td><td>${E(item.email||'—')}</td><td><span class="admin-role ${String(item.role).toUpperCase()==='ADMIN'?'role-admin':''}">${E(String(item.role).toUpperCase()==='ADMIN'?'Quản trị viên':'Thành viên')}</span></td><td><span class="admin-status ${item.subscription_status==='PREMIUM'?'success':'neutral'}"><span class="admin-status-dot"></span>${E(item.subscription_status==='PREMIUM'?'Premium':'Free')}</span></td><td>${E(adminDate(item.created_at))}</td></tr>`;
  const adminTable = (kind, items) => {
    if (!items.length) return adminBlank(kind==='users'?'Không tìm thấy người dùng':'Không có giao dịch');
    if (kind==='users') return `<div class="admin-table-scroll"><table class="admin-table"><thead><tr><th>Người dùng</th><th>Email</th><th>Vai trò</th><th>Gói hiện tại</th><th>Ngày tham gia</th></tr></thead><tbody>${items.map(adminUserRow).join('')}</tbody></table></div><div class="admin-swipe-hint">← Vuốt ngang để xem đầy đủ các cột →</div>`;
    return `<div class="admin-table-scroll"><table class="admin-table"><thead><tr><th>Mã giao dịch</th><th>Khách hàng</th><th>Gói Premium</th><th>Số tiền</th><th>Trạng thái</th><th>Ngày tạo</th></tr></thead><tbody>${items.map(adminTxnRow).join('')}</tbody></table></div><div class="admin-swipe-hint">← Vuốt ngang để xem đầy đủ các cột →</div>`;
  };
  const adminFiltered = () => {
    const kind=state.adminTab;
    const list=kind==='users'?state.adminUsers:state.adminTransactions;
    const search=state.adminSearch.toLocaleLowerCase('vi').trim();
    return list.filter(item=>{
      const match=kind==='users' ? (state.adminFilter==='all'|| (state.adminFilter==='ADMIN' ? String(item.role).toUpperCase()==='ADMIN' : String(item.subscription_status).toUpperCase()===state.adminFilter))
        : (state.adminFilter==='all'||String(item.status).toUpperCase()===state.adminFilter);
      if(!match)return false;
      const fields=kind==='users'?[item.id,item.full_name,item.email]:[item.transaction_id,item.transaction_code,item.user_name,item.user_email,item.plan_name,item.payment_method];
      return !search||fields.some(field=>String(field??'').toLocaleLowerCase('vi').includes(search));
    });
  };
  const adminResults = () => {
    const rows=adminFiltered();const pageSize=10;const pages=Math.max(1,Math.ceil(rows.length/pageSize));
    state.adminPageIndex=Math.min(Math.max(1,state.adminPageIndex),pages);
    const from=(state.adminPageIndex-1)*pageSize;
    return `${adminTable(state.adminTab,rows.slice(from,from+pageSize))}<div class="admin-table-footer"><span>Hiển thị <b>${rows.length?from+1:0}–${Math.min(from+pageSize,rows.length)}</b> trong tổng số <b>${fmt(rows.length)}</b> mục</span><div class="admin-pager"><button type="button" data-action="admin-prev" ${state.adminPageIndex===1?'disabled':''} aria-label="Trang trước">‹</button><span>Trang ${state.adminPageIndex}/${pages}</span><button type="button" data-action="admin-next" ${state.adminPageIndex>=pages?'disabled':''} aria-label="Trang sau">›</button></div></div>`;
  };
  const adminOverview = () => {
    const data=state.adminStats;
    if (!data) return adminBlank('Chưa tải được thống kê','Hãy kiểm tra kết nối Flask, MySQL và quyền ADMIN rồi chọn “Làm mới”.');
    const users=data.users||{},moneyData=data.financial||{},transactions=Array.isArray(data.recent_transactions)?data.recent_transactions:[];
    const chart=Array.isArray(data.revenue_chart)?data.revenue_chart.slice(-9):[];
    const premium=Math.max(0,Number(users.premium)||0),free=Math.max(0,Number(users.free)||0),total=Math.max(0,Number(users.total)||0);
    const premiumPercent=total?Math.round(premium/total*100):0;
    const maxRevenue=Math.max(1,...chart.map(p=>Math.max(0,Number(p.revenue)||0)));
    return `<div class="admin-kpi-grid">
        <article class="admin-kpi"><div class="admin-kpi-label">Tổng thành viên<span class="admin-kpi-icon green">${icon('user')}</span></div><strong>${fmt(total)}</strong><p>${fmt(free)} Free · ${fmt(premium)} Premium</p></article>
        <article class="admin-kpi"><div class="admin-kpi-label">Thành viên Premium<span class="admin-kpi-icon gold">${icon('crown')}</span></div><strong>${fmt(premium)}</strong><p>${premiumPercent}% tổng số thành viên</p></article>
        <article class="admin-kpi"><div class="admin-kpi-label">Giá trị giao dịch đã xác nhận<span class="admin-kpi-icon teal">${icon('chart')}</span></div><strong>${money(moneyData.total_confirmed_value_vnd ?? moneyData.total_revenue_vnd)}</strong><p>Thực thu: ${money(moneyData.real_revenue_vnd ?? moneyData.total_revenue_vnd)} · Thử nghiệm: ${money(moneyData.simulated_revenue_vnd || 0)}</p></article>
        <article class="admin-kpi"><div class="admin-kpi-label">Tổng giao dịch<span class="admin-kpi-icon orange">${icon('grid')}</span></div><strong>${fmt(moneyData.total_transactions)}</strong><p>Bao gồm mọi trạng thái</p></article>
      </div>
      <div class="admin-analytics-grid">
        <section class="card admin-panel"><div class="admin-panel-heading"><div><span class="admin-section-kicker">PHÂN TÍCH GIAO DỊCH</span><h3>Giá trị giao dịch theo thời gian</h3><p>Tổng giá trị các giao dịch đã được xác nhận trên NutriFit</p></div><div class="admin-period"><button type="button" data-admin-period="day" class="${state.adminPeriod==='day'?'selected':''}">Theo ngày</button><button type="button" data-admin-period="month" class="${state.adminPeriod==='month'?'selected':''}">Theo tháng</button></div></div>
          ${chart.length?`<div class="admin-revenue-chart" role="img" aria-label="Biểu đồ giá trị giao dịch ${state.adminPeriod==='month'?'theo tháng':'theo ngày'}">${chart.map((p)=>{const rev=Math.max(0,Number(p.revenue)||0);const height=rev?Math.max(6,100*rev/maxRevenue):0;return `<div class="admin-bar-item"><div class="admin-bar-value">${rev?`${fmt(Math.round(rev/1000))}k`:'0'}</div><div class="admin-bar-track"><span style="height:${height}%" title="${E(String(p.timeline||''))}: tổng ${money(rev)} · thực thu ${money(p.real_revenue||0)} · giá trị QR ${money(p.simulated_value||0)}"></span></div><small>${E(state.adminPeriod==='month'?String(p.timeline||'').slice(5,7)+'/'+String(p.timeline||'').slice(2,4):adminDate(p.timeline,true))}</small></div>`;}).join('')}</div><div class="admin-chart-caption"><span class="admin-chart-key"></span>Giá trị giao dịch xác nhận (VNĐ) <span class="admin-chart-note">${fmt(chart.length)} mốc thời gian gần nhất</span></div>`:adminBlank('Chưa có giao dịch xác nhận','Biểu đồ sẽ hiển thị khi giao dịch được xác nhận thành công.')}
        </section>
        <section class="card admin-panel admin-membership"><div class="admin-panel-heading"><div><span class="admin-section-kicker">THÀNH VIÊN</span><h3>Cơ cấu tài khoản</h3><p>Phân bổ theo gói đang sử dụng</p></div></div>
          <div class="admin-donut-wrap"><div class="admin-donut" role="img" aria-label="${premiumPercent}% tài khoản Premium" style="--premium-pct:${premiumPercent}%"><div class="admin-donut-inner"><strong>${premiumPercent}%</strong><span>Premium</span></div></div></div>
          <div class="admin-membership-list"><div><span><i class="admin-legend-dot premium"></i>Premium</span><strong>${fmt(premium)}</strong></div><div><span><i class="admin-legend-dot free"></i>Miễn phí</span><strong>${fmt(free)}</strong></div></div>
        </section>
      </div>
      <section class="card admin-panel admin-recent"><div class="admin-panel-heading"><div><span class="admin-section-kicker">GIAO DỊCH MỚI</span><h3>Thanh toán gần đây</h3><p>5 giao dịch mới nhất từ hệ thống</p></div><button class="btn btn-light btn-small" data-admin-tab="transactions">Xem tất cả ${icon('arrow',16)}</button></div>${adminTable('transactions',transactions)}</section>`;
  };
  const adminListPage = () => {
    const users=state.adminTab==='users';
    const list=users?state.adminUsers:state.adminTransactions;
    return `<section class="card admin-panel admin-list-panel"><div class="admin-panel-heading"><div><span class="admin-section-kicker">${users?'DANH SÁCH NGƯỜI DÙNG':'LỊCH SỬ THANH TOÁN'}</span><h3>${users?'Quản lý tài khoản':'Quản lý giao dịch'}</h3><p>${users?'Tra cứu tài khoản và hạng thành viên':'Theo dõi giao dịch và trạng thái thanh toán'} · ${fmt(list.length)} bản ghi</p></div></div>
    <div class="admin-toolbar"><div class="admin-search">${icon('search',18)}<input id="admin-search" type="search" placeholder="${users?'Tìm tên, email, ID...':'Tìm mã, tên, email, gói...'}" value="${E(state.adminSearch)}" aria-label="Tìm kiếm" /></div><select id="admin-filter" class="admin-filter" aria-label="Lọc kết quả">${(users?[['all','Tất cả tài khoản'],['PREMIUM','Premium'],['FREE','Miễn phí'],['ADMIN','Quản trị viên']]:[['all','Mọi trạng thái'],['SUCCESS','Thành công'],['PENDING','Chờ xử lý'],['FAILED','Thất bại'],['CANCELLED','Đã hủy'],['DEMO_SUCCESS','Thành công (QR)'],['DEMO_MAIL_ERROR','Thành công · lỗi email'],['DEMO_PENDING','Chờ xác nhận QR']]).map(([value,label])=>`<option value="${value}" ${state.adminFilter===value?'selected':''}>${E(label)}</option>`).join('')}</select></div>
    <div id="admin-results">${adminResults()}</div></section>`;
  };
  function adminPage(){
    if (!adminRole()) return `${heading('QUẢN TRỊ','Quản trị hệ thống','Khu vực dành riêng cho quản trị viên NutriFit.')}${signedPrompt()}`;
    const tabs=[['overview','Tổng quan','grid'],['users','Người dùng','user'],['transactions','Giao dịch','chart']];
    return `${heading('KHÔNG GIAN QUẢN TRỊ','Bảng điều khiển hệ thống','Quản lý tài khoản, doanh thu và thanh toán của NutriFit.',btn(`${icon('arrow')} Làm mới dữ liệu`,'admin-refresh','btn-light'))}
      <section class="admin-hero"><div class="admin-hero-content"><span class="admin-hero-overline">✦ NUTRIFIT · CONTROL CENTER</span><h2>Mọi thông tin quản trị,<br>trong một không gian.</h2><p>Dữ liệu được lấy trực tiếp từ hệ thống. Theo dõi rõ ràng, xử lý thuận tiện.</p><span class="admin-live"><i></i> ${state.online?'Backend đang kết nối':'Backend chưa kết nối'}</span></div><div class="admin-hero-symbol" aria-hidden="true">✳</div></section>
      <div class="admin-tabs" role="tablist" aria-label="Các mục quản trị">${tabs.map(([key,label,ico])=>`<button type="button" role="tab" aria-selected="${state.adminTab===key}" class="${state.adminTab===key?'active':''}" data-admin-tab="${key}">${icon(ico,17)}${label}</button>`).join('')}</div>
      ${state.adminError?`<div class="admin-alert" role="alert">${icon('info',18)}<span>${E(state.adminError)}</span></div>`:''}
      ${state.adminLoading?`<div class="admin-loading"><span class="admin-loading-spinner"></span>Đang tải dữ liệu quản trị...</div>`:(state.adminTab==='overview'?adminOverview():adminListPage())}
      <p class="admin-endnote">${icon('shield',15)} Dữ liệu lấy từ API quản trị. Trang này chỉ hiển thị và tra cứu; không tự ý thay đổi tài khoản hoặc trạng thái thanh toán.</p>`;
  }
  async function loadAdminData(){
    if (!adminRole() || !state.online) {state.adminError='Vui lòng kết nối Backend và đăng nhập bằng tài khoản có quyền ADMIN.';return;}
    state.adminError='';
    const endpoint=state.adminTab==='users'?'/api/admin/users':state.adminTab==='transactions'?'/api/admin/transactions':'/api/admin/dashboard?period='+state.adminPeriod;
    const response=await req(endpoint,undefined,'GET',20000);
    if (!response.success){state.adminError=response.message || (response.httpStatus===403?'Tài khoản hiện tại không có quyền ADMIN.':'Không tải được dữ liệu quản trị. Kiểm tra Backend và MySQL.');return;}
    if (state.adminTab==='users') state.adminUsers=Array.isArray(response.data)?response.data:[];
    else if (state.adminTab==='transactions') state.adminTransactions=Array.isArray(response.data)?response.data:[];
    else state.adminStats=response.data||null;
  }
  async function changeAdminTab(tab){
    if(!['overview','users','transactions'].includes(tab)||!adminRole())return;
    state.adminTab=tab;state.adminFilter='all';state.adminSearch='';state.adminPageIndex=1;
    state.adminLoading=true;render();await loadAdminData();state.adminLoading=false;render();
  }
  let streetSeed=[];
  function openModal(title,body){stopDemoPaymentPoll();$('#modal-root').innerHTML=`<div class="modal-backdrop" data-action="close-backdrop"><div class="modal-card" role="dialog" aria-modal="true" aria-label="${E(title)}"><div class="modal-head"><h2>${E(title)}</h2><button class="close-modal" data-action="close-modal" aria-label="Đóng">×</button></div>${body}</div></div>`;}
  function closeModal(){stopDemoPaymentPoll();$('#modal-root').innerHTML='';}
  function authModal(mode){
    const register=mode==='register';
    pendingOtpEmail='';
    openModal(register?'Tạo tài khoản NutriFit':'Chào mừng trở lại',`<p class="modal-intro">${register?'Bắt đầu bằng Gmail thật. Hệ thống sẽ gửi OTP để xác minh trước khi tạo tài khoản.':'Đăng nhập để đồng bộ thực đơn, chỉ số cơ thể và nhật ký hoạt động.'}</p>
      <form id="auth-form" data-mode="${mode}">
        ${register?input('Họ và tên','full_name','','text','autocomplete="name" maxlength="100"'):''}
        ${input(register?'Gmail':'Email','email','','email','autocomplete="email"')}
        ${passwordField('Mật khẩu','password',register?'new-password':'current-password',register)}
        ${register?passwordField('Nhập lại mật khẩu','confirm_password','new-password',true):''}
        <button type="submit" class="btn btn-primary full">${register?'Gửi mã OTP đến Gmail':'Đăng nhập'}</button>
      </form>
      <p class="text-center text-sm mt-20 muted">${register?'Đã có tài khoản?':'Chưa có tài khoản?'} <button class="btn-link" data-action="${register?'login-modal':'register-modal'}">${register?'Đăng nhập':'Đăng ký ngay'}</button></p>`);
  }
  function otpModal(email){
    pendingOtpEmail=email;
    openModal('Xác minh Gmail',`<p class="modal-intro">Mã gồm <b>6 chữ số</b> vừa được gửi đến <b>${E(email)}</b>. Mã có hiệu lực trong <b>10 phút</b>. Kiểm tra cả thư Spam nếu chưa nhận được.</p><form id="otp-form">${input('Nhập mã OTP','otp','','text','inputmode="numeric" autocomplete="one-time-code" pattern="[0-9]{6}" maxlength="6" placeholder="000000"')}<button type="submit" class="btn btn-primary full">Xác minh và tạo tài khoản</button></form><div class="text-center text-sm mt-20 muted"><button type="button" class="btn-link" data-action="resend-otp">Gửi lại mã OTP</button><span> · </span><button type="button" class="btn-link" data-action="register-modal">Đổi Gmail</button></div><p class="text-center text-sm muted mt-20">Có thể gửi lại sau 60 giây. Mỗi Gmail được gửi tối đa 5 mã/giờ.</p>`);
  }
  function finishLogin(user,message){
    state.user=user;save('nutrifit_session_user',user);state.profile=null;state.daily=null;state.mealData={};state.dailyPlan=null;state.planDraft={breakfast:'',lunch:'',dinner:'',snack:''};state.premiumAccess=false;pendingOtpEmail='';closeModal();toast(message);return navigate('profile',true);
  }

  function workoutModal(w){if(!realUser()){authModal('login');return;}const list=w?[w]:state.workouts;if(!list.length){toast('Danh sách bài tập đang trống.',true);return;}
    openModal('Ghi nhận bài tập',`<p class="modal-intro">Lưu bài tập đã thực hiện vào nhật ký của bạn.</p><form id="workout-log-form">${selectField('Bài tập','workout_id',list.map(a=>[a.id,a.name]),w?.id||list[0].id)}${input('Thời lượng (phút)','duration_minutes',w?.durationMinutes||30,'number','min="1" max="600"')}${input('Ngày tập','date',today(),'date')}<button type="submit" class="btn btn-primary full">${icon('check')} Ghi nhận</button></form>`);
  }
  function customWorkoutModal(){
    if(!realUser()){authModal('login');return;}
    if(!premiumUser()){upgradePremium();return;}
    openModal('Tạo bài tập với AI',`<p class="modal-intro">Nhập tên hoạt động và thời gian. Tên bài phổ biến được đối chiếu với danh mục; bài mới sẽ được AI xác minh. Calo được ước tính dựa trên cân nặng trong hồ sơ. Bạn không cần tự nhập calo.</p>
      <form id="custom-workout-form">${input('Tên bài tập','name','','text','maxlength="100" placeholder="Ví dụ: Chạy bộ, tập squat..."')}${input('Thời lượng (phút)','duration_minutes','30','number','min="1" max="600"')}
      <div class="mini-note">Các bài ngoài danh mục cần kết nối AI. Nếu chưa có hồ sơ cân nặng, hệ thống tạm dùng 60 kg khi ước lượng.</div>
      <button type="submit" class="btn btn-primary full">${icon('spark')} Kiểm tra & ước tính calo</button></form>`);
  }
  function customWorkoutReview(result){
    const fromCatalog = result.source === 'catalog';
    const verificationLabel = fromCatalog ? 'Có trong danh mục chuẩn' : 'AI đã xác minh';
    openModal('Xác nhận bài tập',`<p class="modal-intro">Bài tập đã được kiểm tra. Bạn hãy xem lượng calo ước tính trước khi lưu.</p>
      <div class="ai-workout-preview"><span class="pill green">${icon('check',14)} ${verificationLabel}</span><h3>${E(result.name)}</h3>
      <div class="workout-review-grid"><div><small>Thời lượng</small><strong>${fmt(result.duration_minutes)} phút</strong></div><div><small>Cân nặng tham chiếu</small><strong>${fmt(result.weight_kg_used)} kg</strong></div><div><small>Calo ước tính</small><strong>~${fmt(result.calories_burned)} kcal</strong></div></div>
      <p>${E(result.note||'Ước lượng dựa trên chỉ số MET của bài tập.')}</p></div>
      <form id="custom-workout-save-form"><input type="hidden" name="name" value="${E(result.name)}"><input type="hidden" name="duration_minutes" value="${Number(result.duration_minutes)}"><input type="hidden" name="estimate_token" value="${E(result.estimate_token)}">
      <button type="submit" class="btn btn-primary full">${icon('check')} Lưu bài tập đã xác minh</button></form>
      <button class="btn btn-light full mt-16" data-action="custom-workout-modal">Nhập lại bài tập</button>
      <p class="workout-ai-note">Calo là số ước tính, không phải số đo trực tiếp. Kết quả xác minh có hiệu lực trong 10 phút.</p>`);
  }
  function foodModal(d){openModal(d.title,`<div class="split-stat"><div class="soft-box"><small>Năng lượng ước tính</small><strong>${fmt(d.calories)} kcal</strong></div><div class="soft-box"><small>Giá tham khảo</small><strong>${money(d.price_vnd)}</strong></div><div class="soft-box"><small>Protein</small><strong>${fmt(d.protein_g)} g</strong></div><div class="soft-box"><small>Carbs / Fat</small><strong>${fmt(d.carbs_g)} / ${fmt(d.fat_g)} g</strong></div></div><div class="mini-note mt-20">${E([d.protein_desc,d.carb_desc,d.soup_desc,d.veggie_desc].filter(Boolean).join(' · '))}</div><button class="btn btn-primary mt-20" data-action="close-modal">Đóng</button>`);}
  async function doAction(action,node){
    switch(action){
      case 'toggle-menu': $('#shell').classList.toggle('menu-open');return;
      case 'refresh': await checkConnection();await navigate(state.page,true);toast('Đã cập nhật trạng thái kết nối.');return;
      case 'admin-refresh':state.adminLoading=true;render();await checkConnection();await loadAdminData();state.adminLoading=false;render();if(!state.adminError)toast('Đã cập nhật dữ liệu quản trị.');return;
      case 'admin-prev':state.adminPageIndex=Math.max(1,state.adminPageIndex-1);$('#admin-results').innerHTML=adminResults();return;
      case 'admin-next':state.adminPageIndex+=1;$('#admin-results').innerHTML=adminResults();return;
      case 'profile':return navigate('profile');
      case 'go-meals':return navigate('meals');
      case 'go-premium':closeModal();return navigate('premium');
      case 'premium-activated':closeModal();return navigate('profile',true);
      case 'upgrade-premium':return upgradePremium();
      case 'close-backdrop':if(node.classList.contains('modal-backdrop'))closeModal();return;
      case 'close-modal':return closeModal();
      case 'toggle-password':{
        const inputField=$('#modal-root')?.querySelector(`[name="${node.dataset.passwordTarget}"]`);
        if(!inputField||inputField.type!=='password'&&inputField.type!=='text')return;
        const visible=inputField.type==='password';
        inputField.type=visible?'text':'password';
        node.setAttribute('aria-pressed',String(visible));
        node.setAttribute('aria-label',visible?'Ẩn mật khẩu':'Hiện mật khẩu');
        node.title=visible?'Ẩn mật khẩu':'Hiện mật khẩu';
        node.innerHTML=icon(visible?'eyeoff':'eye',19);
        return;
      }
      case 'custom-workout-modal':return customWorkoutModal();
      case 'login-modal':return authModal('login');
      case 'register-modal':return authModal('register');
      case 'resend-otp':{
        if(!pendingOtpEmail)return toast('Vui lòng bắt đầu đăng ký lại.',true);
        node.disabled=true;
        const response=await req('/api/auth/resend-otp',{email:pendingOtpEmail},'POST',35000);
        node.disabled=false;
        toast(response.message||(response.success?'Đã gửi OTP mới.':'Không gửi được OTP.'),!response.success);
        return;
      }
      case 'logout':{
        if(state.online)await req('/api/nutrition/logout',{});
        state.user=null;state.profile=null;state.daily=null;state.summary=null;state.mealData={};state.premiumAccess=false;state.dailyPlan=null;state.planDraft={breakfast:"",lunch:"",dinner:"",snack:""};state.workoutLogs=[];state.progress=null;
        localStorage.removeItem('nutrifit_session_user');closeModal();toast('Bạn đã đăng xuất.');return navigate('dashboard');
      }
      case 'scroll-calculator':return $('#nutrition-calculator')?.scrollIntoView({behavior:'smooth'});
      case 'add-water':state.water[today()]=Math.min(12000,Number(state.water[today()]||0)+250);save('nutrifit_studio_water',state.water);render();return;
      case 'reset-water':state.water[today()]=0;save('nutrifit_studio_water',state.water);render();return;
      // Fast database-backed suggestions by default; Premium manual AI remains Gemini-based.
      case 'generate-meal':return generateMeal(false,undefined,true);
      case 'refresh-meal':return generateMeal(true,undefined,true);
      case 'toggle-meal-prefs':state.mealPrefOpen=!state.mealPrefOpen;render();return;
      case 'apply-meal-prefs':return applyMealPreferences();
      case 'defer-meal':return deferMeal();
      case 'meal-history':return showMealHistory();
      case 'confirm-selected-meal':return openMealConfirmation();
      case 'confirm-meal-intake':return confirmMealIntake(node);
      case 'confirm-component-swap':return replaceComponent(node);
      case 'log-workout-modal':return workoutModal();
      case 'custom-workout-modal':return customWorkoutModal();
      case 'new-chat':state.chat=[];save('nutrifit_studio_chat',[]);render();return;
      case 'clear-street':state.streetSearch='';state.streetType='all';state.streetBudget='all';state.recommendation=null;return navigate('street',true);
      case 'clear-recommend':state.recommendation=null;render();return;
      case 'street-recommend':return streetRecommend();
      case 'open-legacy':location.href='legacy/index.html';return;
    }
  }
  async function applyMealPreferences(){
    if(!realUser())return authModal('login');
    if(state.mealBusy)return false;
    const next=getDraftPreferences();
    if(['avoid','dislikes','prefer'].some(k=>next[k].length>15 || next[k].some(x=>x.length>40))){
      toast('Mỗi nhóm tối đa 15 nguyên liệu; mỗi tên tối đa 40 ký tự.',true);return false;
    }
    // Serialize menu actions. AbortController only cancels the browser wait;
    // the Flask request may continue even after a timeout.
    state.mealBusy=true;
    render();
    try {
      const validated=await req('/api/meals/validate-preferences',{
        mealType:state.mealType,preferences:next},'POST',10000);
      if(!validated.success){
        toast(validated.message||'Không thể xác minh khẩu vị. Hãy kiểm tra kết nối Flask.',true);
        return false;
      }
      state.mealPrefApplied=next;
      save('nutrifit_meal_pref_'+id(),next);
      const meal=mealObj(state.mealType);
      if(meal?.selectedOption){
        toast('Đã lưu khẩu vị. Bỏ chọn thực đơn, rồi nhấn “Đổi bộ gợi ý” để áp dụng.');
      } else {
        toast('Đã lưu khẩu vị. Nhấn “Đổi bộ gợi ý” để cập nhật bộ món và các lựa chọn thay thế.');
      }
      return true;
    } finally {
      state.mealBusy=false;
      if(state.page==='meals')render();
    }
  }
  // Read the canonical MySQL revision after another tab/request has changed a menu.
  // Never blindly reuse the stale revision or overwrite a confirmed meal.
  async function syncMealRevision(type){
    const latest=await req('/api/meals/today',undefined,'GET',15000);
    if(!latest.success)return false;
    state.mealData=latest.todayMeals||{};
    return true;
  }
  async function generateMeal(force=false, overrides, catalogOnly=false){
    if(!realUser()){authModal('login');return false;}
    if(state.mealBusy)return false;
    const type=state.mealType;
    if(mealObj(type)?.selectedOption){toast('Bạn đã chốt thực đơn. Hãy bấm “Bỏ chọn” trước khi đổi.',true);return false;}
    state.mealBusy=true;render();
    try {
      let result;
      // Only one automatic re-sync/retry; a live concurrent writer should not
      // trigger an endless client loop or accidentally overwrite a meal choice.
      for(let attempt=0;attempt<2;attempt++){
        const current=mealObj(type);
        if(current?.selectedOption){
          toast('Thực đơn vừa được chốt ở phiên khác. Hãy bỏ chọn trước khi đổi.',true);
          return false;
        }
        const body={mealType:type,forceRefresh:Boolean(current),plannerVersion:'v4',
          catalogOnly:Boolean(catalogOnly),preferences:overrides||state.mealPrefApplied};
        if(current)body.revision=current.revision;
        result=await req('/api/meals/generate',body,'POST',catalogOnly?30000:60000);
        if(result.httpStatus!==409 || result.code!=='STALE_MEAL' || attempt===1)break;
        if(!await syncMealRevision(type))break;
      }
      if(result?.success){
        state.mealData[type]=result.data;
        if(result.meta?.changed===false){
          toast('Chưa tìm thấy tổ hợp khác phù hợp khẩu vị và mục tiêu. Bạn có thể đổi món riêng hoặc điều chỉnh khẩu vị.',true);
        } else {
          toast('Đã tạo bộ gợi ý mới. Bạn có thể tiếp tục nhấn “Đổi bộ gợi ý”.');
        }
        return result.meta?.changed!==false;
      }
      if(result?.httpStatus===409 && (result.code==='STALE_MEAL'||result.code==='PREFERENCES_REQUIRE_REFRESH')){
        await syncMealRevision(type);
        toast('Dữ liệu thực đơn đã đồng bộ. Hãy nhấn “Đổi bộ gợi ý” một lần nữa.',true);
      } else {
        toast(result?.message||'Chưa thể gợi ý món ăn. Kiểm tra kết nối Backend.',true);
      }
      return false;
    } finally {
      state.mealBusy=false;
      render();
    }
  }
  async function openComponentAlternatives(optionId, componentType){
    if(!realUser())return authModal('login');
    if(state.mealBusy)return false;
    const m=mealObj(state.mealType);
    if(!m?.revision)return toast('Vui lòng tạo thực đơn trước khi thay món.',true);
    const option=m.options?.find(o=>Number(o.optionId)===Number(optionId));
    if(!option?.recipe)return toast('Bộ cũ chưa có thông tin từng món. Hãy đổi bộ gợi ý.',true);
    state.mealBusy=true;
    if(state.page==='meals')render();
    try {
    const result=await req('/api/meals/component-suggestions',{
      mealType:state.mealType,optionId,componentType,revision:m.revision
    },'POST',30000);
    if(!result.success)return toast(result.message||'Chưa tìm được món thay thế.',true);
    const choices=(result.data?.catalog_choices?.length ? result.data.catalog_choices : result.data?.choices || []).slice(0,15);
    if(!choices.length)return toast('Chưa có món thay thế cùng nhóm phù hợp khẩu vị.',true);
    const limit=15;
    const available=Number(result.data?.available_count ?? choices.length);
    const limitedNote=choices.length < limit
      ? `<p class="mini-note">Có ${available} món cùng nhóm đáp ứng bộ lọc hiện tại (${choices.length}/${limit} đang hiển thị). Nếu dùng thực phẩm cần tránh và muốn xem thêm món có thành phần tham khảo, hãy bật chế độ mở rộng trong mục Khẩu vị — chỉ khi không có dị ứng.</p>`
      : '';
    const current=option.recipe.components.find(c=>c.type===componentType);
    // Only server-approved candidates are displayed; the Backend rechecks type and preferences.
    const opts=choices.map(c=>`<option value="${E(c.dish_id)}" data-grams="${Number(c.reference_grams)}" data-min="${Number(c.min_grams)}" data-max="${Number(c.max_grams)}">${E(c.name)} · ${Number(c.calories_per_100g||0).toFixed(0)} kcal/100g</option>`).join('');
    openModal('Đổi món trong thực đơn',`<div class="meal-swap-form" data-meal-swap-form data-option-id="${Number(optionId)}" data-component-type="${E(componentType)}">
      <div class="meal-swap-group"><span class="pill green">${E(mealGroupLabels[componentType]||componentType)}</span><p>Đang thay: <strong>${E(current?.name||'Món ăn')}</strong>. Chỉ các món cùng nhóm và phù hợp khẩu vị đã lưu mới được chọn.</p></div>
      <label class="form-label" for="meal-swap-search">Tìm tên món</label><input id="meal-swap-search" class="field" placeholder="Nhập tên món, có dấu hoặc không dấu…" autocomplete="off">
      <label class="form-label" for="meal-swap-select">Món thay thế (${choices.length}/${limit} lựa chọn)</label><select id="meal-swap-select" class="field" required>${opts}</select>
      ${limitedNote}
      <div class="meal-swap-detail" id="meal-swap-detail"></div>
      <label class="form-label" for="meal-swap-grams">Khẩu phần (g)</label><input id="meal-swap-grams" class="field" type="number" step="1" min="1" max="2000" value="${Number(choices[0].reference_grams)}" required>
      <p class="mini-note">Sau khi thay món, calo, carb, đạm, chất béo và chất xơ được Backend tính lại.</p>
      <button type="button" class="btn btn-primary full" data-action="confirm-component-swap">Xác nhận thay món</button>
    </div>`);
    updateMealSwapDetail();
    } finally {
      state.mealBusy=false;
      if(state.page==='meals')render();
    }
  }
  function updateMealSwapDetail(){
    const select=$('#meal-swap-select'),grams=$('#meal-swap-grams'),detail=$('#meal-swap-detail');
    if(!select||!select.selectedOptions.length)return;
    const option=select.selectedOptions[0];
    if(grams){grams.min=option.dataset.min||'1';grams.max=option.dataset.max||'2000';grams.value=option.dataset.grams||'100';}
    if(detail)detail.textContent=`Khẩu phần mẫu: ${option.dataset.grams} g · Hợp nhóm ${mealGroupLabels[$('[data-meal-swap-form]')?.dataset.componentType]||'thực phẩm'}.`;
  }
  async function replaceComponent(node){
    const m=mealObj(state.mealType),form=$('[data-meal-swap-form]'),choice=$('#meal-swap-select'),gramsField=$('#meal-swap-grams');
    if(!m||!form||!choice?.value)return;
    const grams=Number(gramsField?.value),option=choice.selectedOptions[0];
    if(!Number.isFinite(grams)||grams<Number(option.dataset.min)||grams>Number(option.dataset.max)){
      toast('Khẩu phần không nằm trong giới hạn của món đã chọn.',true);return;
    }
    node.disabled=true;
    const result=await req('/api/meals/replace-component',{
      mealType:state.mealType,optionId:Number(form.dataset.optionId),componentType:form.dataset.componentType,
      revision:m.revision,dishId:choice.value,grams
    },'POST',35000);
    node.disabled=false;
    if(result.success){state.mealData[state.mealType]=result.data;closeModal();toast('Đã thay món và tính lại dinh dưỡng.');render();}
    else{toast(result.message||'Không thể thay món.',true);if(result.httpStatus===409){closeModal();await navigate('meals',true);}}
  }
  async function selectMeal(option){
    if(state.mealBusy)return;
    if(!realUser()){authModal('login');return;}
    const type=state.mealType,m=mealObj(type);if(!m)return;
    const res=await req('/api/meals/select',{mealType:type,selectedOption:option,revision:m.revision});
    if(res.success){state.mealData[type]=res.data;render();openMealConfirmation();}
    else toast(res.message||'Không thể chọn thực đơn.',true);
  }
  function openMealConfirmation(){
    const m=mealObj(state.mealType),o=m?.options?.find(opt=>opt.id===m.selectedOption);
    if(!o)return toast('Hãy chọn một thực đơn trước.',true);
    if(wasMealEaten(state.mealType,o))return toast('Bữa này đã được ghi nhận vào nhật ký dinh dưỡng.');
    openModal('Xác nhận bữa ăn',`<div class="meal-confirmation"><span class="pill green">${E(mealNames[state.mealType])}</span><h3>${E(o.title)}</h3>
      <div class="meal-confirm-totals"><strong>${fmt(o.calories)} kcal</strong><span>Đạm ${Number(o.macros?.protein||0).toFixed(1)}g</span><span>Carb ${Number(o.macros?.carbs||0).toFixed(1)}g</span><span>Chất béo ${Number(o.macros?.fat||0).toFixed(1)}g</span><span>Chất xơ ${o.recipe?.fiber_complete===true?`${Number(o.macros?.fiber||0).toFixed(1)}g`:'Chưa đủ dữ liệu'}</span></div>
      <p class="modal-intro">Bạn đã chọn thực đơn làm kế hoạch. <strong>Chỉ nhấn “Đã ăn” nếu bạn đã thực sự ăn</strong> đủ khẩu phần được gợi ý. Khi đó các chỉ số sẽ được cộng vào Dinh dưỡng hôm nay.</p>
      <button type="button" class="btn btn-primary full" data-action="confirm-meal-intake">✓ Tôi đã ăn · Lưu vào Dinh dưỡng</button><button type="button" class="btn btn-light full" data-action="close-modal">Để sau, chỉ lưu kế hoạch</button></div>`);
  }
  async function confirmMealIntake(node){
    const m=mealObj(state.mealType),option=m?.options?.find(o=>o.id===m.selectedOption);
    if(!m||!option)return toast('Không tìm thấy thực đơn đã chọn.',true);
    if(wasMealEaten(state.mealType,option))return toast('Bữa ăn này đã ghi vào Dinh dưỡng.');
    const parts=option.recipe?.components;
    if(!Array.isArray(parts)||!parts.length){toast('Bộ thực đơn cũ chưa có khẩu phần riêng. Vui lòng đổi sang bộ V4 để ghi nhận.',true);return;}
    node.disabled=true;
    const payload={requestId:`nfmeal_${id()}_${m.date||today()}_${state.mealType}`,confirmed:true,mealType:state.mealType,
      meal:{optionId:option.optionId,revision:m.revision},items:parts.map(part=>({dish_id:part.dish_id,grams:part.grams}))};
    const res=await req('/api/nutrition/intake',payload,'POST',30000);
    node.disabled=false;
    if(!res.success){toast(res.message||'Chưa thể ghi bữa ăn vào Dinh dưỡng.',true);return;}
    const daily=await req('/api/nutrition/daily');
    if(daily.success)state.daily=daily;
    closeModal();render();toast(res.created===false?'Bữa ăn đã được ghi nhận trước đó.':'Đã ghi bữa ăn và cập nhật Dinh dưỡng hôm nay.');
    openModal('Ghi nhận thành công',`<div class="meal-confirmation"><span class="pill green">✓ Nhật ký đã cập nhật</span><h3>${E(option.title)}</h3><p>Đã cộng <strong>${fmt(option.calories)} kcal</strong> và các chỉ số dinh dưỡng, bao gồm chất xơ.</p><button class="btn btn-primary full" data-page="nutrition">Xem Dinh dưỡng hôm nay ${icon('arrow')}</button><button class="btn btn-light full" data-action="close-modal">Tiếp tục xem thực đơn</button></div>`);
  }
  async function deferMeal(){
    if(!realUser()){authModal('login');return;}
    const m=mealObj(state.mealType);if(!m){toast('Chưa có thực đơn để điều chỉnh.');return;}
    const res=await req('/api/meals/select',{mealType:state.mealType,selectedOption:null,revision:m.revision});
    if(res.success){state.mealData[state.mealType]=res.data;toast('Đã đặt lại lựa chọn.');render();}
    else toast(res.message||'Không thể cập nhật.',true);
  }
  async function showMealHistory(){if(!realUser()){authModal('login');return;}
    const res=await req('/api/meals/history?page=1&limit=10');if(!res.success){toast(res.message||'Không thể tải lịch sử.',true);return;}
    const items=res.history||[];openModal('Lịch sử thực đơn',items.length?`<div class="timeline">${items.map(item=>`<div class="timeline-item"><div><strong>${E(mealNames[item.mealType]||item.mealType||'Bữa ăn')}</strong><small>${E(item.date||item.suggestionDate||'')}</small></div><span class="pill ${item.status==='decided'?'green':'gray'}">${E(item.status||'Đã lưu')}</span></div>`).join('')}</div>`:'<div class="empty"><h3>Chưa có lịch sử</h3><p>Thực đơn bạn tạo sẽ xuất hiện tại đây.</p></div>');
  }
  async function streetRecommend(){
    const budget=state.streetBudget==='all'?50000:Number(state.streetBudget);
    if(state.online){const result=await req('/api/street-food/recommend',{budget,max_kcal:650,meal_type:state.streetType,limit:5});
      if(result.success){const obj=result.data||{};const list=Array.isArray(obj)?obj:obj.items||obj.recommendations||obj.dishes||[];if(list.length){state.recommendation=list;render();return;}}
    }
    const list=streetSeed.filter(d=>(state.streetType==='all'||d.meal_type===state.streetType||d.meal_type==='all')&&d.price_vnd<=budget&&d.calories<=650).sort((a,b)=>(b.protein_g/b.calories)-(a.protein_g/a.calories)).slice(0,5);
    if(!list.length){toast('Không tìm thấy món phù hợp, hãy thử ngân sách cao hơn.',true);return;}
    state.recommendation=list;render();toast('Đã gợi ý món từ dữ liệu tham khảo.');
  }
  async function sendChat(message){
    message=String(message||'').trim();if(!message||state.chatPending)return;
    if(message.length>2000){toast('Câu hỏi không được quá 2000 ký tự.',true);return;}
    const history=state.chat.slice(-12);
    state.chat.push({role:'user',content:message});state.chatPending=true;save('nutrifit_studio_chat',state.chat);render();
    const scroller=$('#chat-messages');if(scroller)scroller.scrollTop=scroller.scrollHeight;
    const p=state.profile;const profile=p?{sex:String(p.gender||'').toLowerCase(),age:p.age,weight_kg:p.weight,height_cm:p.height,activity:p.activity_level,goal:String(p.goal||'').toLowerCase()}:undefined;
    const res=await req('/api/chatbot/chat',{message,history,stream:false,...(profile?{profile}:{})},'POST',60000);
    if(res.success&&res.reply)state.chat.push({role:'assistant',content:String(res.reply)});
    else state.chat.push({role:'assistant',content:res.message||'Chưa kết nối được AI. Hãy chạy Backend và cấu hình GEMINI_API_KEY trong .env.'});
    state.chatPending=false;save('nutrifit_studio_chat',state.chat);if(state.page==='chat'){render();const div=$('#chat-messages');if(div)div.scrollTop=div.scrollHeight;}
  }
  document.addEventListener('click',async event=>{
    const node=event.target.closest('[data-component-swap],[data-meal-replacement],[data-admin-tab],[data-admin-period],[data-page],[data-action],[data-meal],[data-select-meal],[data-workout],[data-workout-filter],[data-food-detail],[data-prompt],[data-checkout],[data-delete-log]');if(!node)return;
    if(node.hasAttribute('data-component-swap')){event.preventDefault();return openComponentAlternatives(Number(node.dataset.optionId),node.dataset.componentType);}
    if(node.hasAttribute('data-meal-replacement')){event.preventDefault();return replaceComponent(node);}
    if(node.dataset.page){event.preventDefault();if(node.closest('.modal-backdrop'))closeModal();return navigate(node.dataset.page);}
    if(node.dataset.adminTab){event.preventDefault();return changeAdminTab(node.dataset.adminTab);}
    if(node.dataset.adminPeriod){event.preventDefault();if(state.adminPeriod===node.dataset.adminPeriod)return;state.adminPeriod=node.dataset.adminPeriod;state.adminLoading=true;render();await loadAdminData();state.adminLoading=false;render();return;}
    // The backdrop is an ancestor of every modal field. Only a direct click on
    // the backdrop itself should close the modal, not a click inside its card.
    if(node.dataset.action==='close-backdrop' && event.target!==node)return;
    if(node.dataset.action){event.preventDefault();return doAction(node.dataset.action,node);}
    if(node.dataset.meal){state.mealType=node.dataset.meal;render();return;}
    if(node.dataset.selectMeal){return selectMeal(Number(node.dataset.selectMeal));}
    if(node.dataset.workoutFilter){state.workoutCategory=node.dataset.workoutFilter;render();return;}
    if(node.dataset.workout){const w=(realUser()?state.workouts:demoWorkouts).find(w=>Number(w.id)===Number(node.dataset.workout));if(w)workoutModal(w);return;}
    if(node.dataset.foodDetail){const d=streetSeed.concat(state.street).find(w=>Number(w.id)===Number(node.dataset.foodDetail));if(d)foodModal(d);return;}
    if(node.dataset.prompt){return sendChat(node.dataset.prompt);}
    if(node.hasAttribute('data-checkout')){
      if(!realUser()){authModal('login');return;}
      if(!node.dataset.checkout)return toast('Chưa có gói thanh toán từ Backend.',true);
      const res=await req('/api/payment/demo-checkout',{plan_id:Number(node.dataset.checkout)});
      if(res.success){
        const d=res.data||{};
        openModal('Thanh toán Premium',`<div class="demo-payment-modal nf-gateway-modal">
          <span class="demo-payment-tag">NUTRIFIT PREMIUM</span>
          <h3 class="nf-gateway-modal-title">Đơn hàng của bạn đã sẵn sàng</h3>
          <p class="modal-intro">Chọn phương thức thanh toán trên cổng NutriFit Pay, hoặc quét QR để mở trang xác nhận bằng điện thoại.</p>
          <div class="demo-payment-info">
            <div><span>Gói đăng ký</span><strong>${E(d.plan_name)}</strong></div>
            <div><span>Người nhận</span><strong>${E(d.recipient_name)}</strong></div>
            <div><span>Mã đơn hàng</span><strong class="demo-payment-code">${E(displayTransactionCode(d.transaction_code))}</strong></div>
            <div class="nf-gateway-modal-total"><span>Tổng thanh toán</span><strong class="demo-payment-money">${money(d.amount_vnd)}</strong></div>
          </div>
          <div class="nf-gateway-method-preview" aria-label="Phương thức trên cổng thanh toán">
            <span>▦ Quét QR</span><span>▤ Ngân hàng</span><span>▰ Thẻ quốc tế</span><span>◈ Ví điện tử</span>
          </div>
          <a class="btn btn-primary full nf-gateway-launch" href="${E(d.confirm_url)}" target="_blank" rel="noopener noreferrer">Đến cổng thanh toán <span aria-hidden="true">↗</span></a>
          <details class="nf-gateway-qr-toggle"><summary>Quét QR để mở trên điện thoại</summary><div class="demo-payment-qr"><img src="${E(d.qr_data_url)}" alt="QR mở cổng thanh toán NutriFit"></div></details>
          <div class="demo-payment-wait">${icon('clock',16)} Đang chờ xác nhận đăng ký…</div>
          <div class="mini-note">Khi hoàn tất, hệ thống tự kích hoạt gói Premium trên tài khoản của bạn.</div>
        </div>`);
        demoPaymentPoll=setTimeout(()=>pollDemoPayment(d.transaction_id), 1500);
      } else toast(res.message||'Chưa thể tạo yêu cầu thanh toán.',true);
      return;
    }
    if(node.dataset.deleteLog){if(!realUser())return;if(!confirm('Xóa bài tập này khỏi nhật ký?'))return;
      const res=await req('/api/workouts/log/'+Number(node.dataset.deleteLog)+'?user_id='+id(),undefined,'DELETE');if(res.success){toast('Đã xóa bài tập.');return navigate('workouts',true);}toast(res.message||'Không thể xóa.',true);return;
    }
  });
  document.addEventListener('change',event=>{
    if(event.target.id==='meal-swap-select'){updateMealSwapDetail();return;}
    if(event.target.id==='meal-pref-reference-mode'){
      state.mealPrefDraft.ingredientMode=event.target.checked?'reference':'strict';
      return;
    }

    if(event.target.id==='plan-meal-type' && ['breakfast','lunch','dinner','snack'].includes(event.target.value)){
      state.planMealType=event.target.value;render();return;
    }
    if(event.target.id==='street-type'){state.streetType=event.target.value;state.recommendation=null;navigate('street',true);}
    if(event.target.id==='street-budget'){state.streetBudget=event.target.value;state.recommendation=null;navigate('street',true);}
    if(event.target.id==='food-search'){state.streetSearch=event.target.value.trim();state.recommendation=null;navigate('street',true);}
  });
  document.addEventListener('input',event=>{
    if(event.target.id==='meal-swap-search'){
      const query=event.target.value.toLocaleLowerCase('vi-VN').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d');
      const selector=$('#meal-swap-select');if(!selector)return;
      for(const option of selector.options){
        const name=option.text.toLocaleLowerCase('vi-VN').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d');
        option.hidden=!name.includes(query);
      }
      const first=[...selector.options].find(o=>!o.hidden);
      if(first){selector.value=first.value;updateMealSwapDetail();}
      return;
    }

    if(event.target.hasAttribute('data-meal-pref')){
      ensureMealPreferences();
      state.mealPrefDraft[event.target.dataset.mealPref]=event.target.value;
    }
    if(event.target.closest('#auth-form') && ['password','confirm_password'].includes(event.target.name)){
      updateRegistrationPasswordFeedback(event.target.form);
    }
    if(event.target.id==='admin-search'){
      state.adminSearch=event.target.value;state.adminPageIndex=1;
      const results=$('#admin-results');if(results)results.innerHTML=adminResults();
    }
  });
  document.addEventListener('change',event=>{
    if(event.target.id==='admin-filter'){
      state.adminFilter=event.target.value;state.adminPageIndex=1;
      const results=$('#admin-results');if(results)results.innerHTML=adminResults();
    }
  });
  document.addEventListener('keydown',event=>{
    if(event.key==='Escape')closeModal();
    if(event.target.id==='food-search'&&event.key==='Enter'){event.preventDefault();state.streetSearch=event.target.value.trim();navigate('street',true);}
    if(event.target.closest('#chat-form textarea')&&event.key==='Enter'&&!event.shiftKey){event.preventDefault();event.target.form?.requestSubmit();}
  });
  document.addEventListener('input',event=>{
    if(event.target.id==='plan-dish' && event.target.closest('#manual-daily-plan-form')){
      state.planDraft[state.planMealType]=event.target.value;
    }
  });
  document.addEventListener('submit',async event=>{
    const form=event.target;event.preventDefault();
    const data=Object.fromEntries(new FormData(form).entries());
    if(form.id==='auth-form'){
      const mode=form.dataset.mode;
      if(mode==='register'&&!updateRegistrationPasswordFeedback(form)){
        const pw=form.elements.namedItem('password');
        const confirm=form.elements.namedItem('confirm_password');
        if(pw.value.length<8 || pw.value.length>128){
          toast('Mật khẩu cần từ 8 đến 128 ký tự.',true);pw.focus();
        }else{
          toast('Mật khẩu nhập lại chưa trùng khớp.',true);confirm.focus();confirm.reportValidity();
        }
        return;
      }
      const result=await req('/api/auth/'+(mode==='register'?'register':'login'),{email:data.email,password:data.password,...(mode==='register'?{full_name:data.full_name}:{})},'POST',mode==='register'?35000:15000);
      if(mode==='register'&&result.success&&result.requires_otp){otpModal(result.email||data.email);toast('Mã OTP đã được gửi. Kiểm tra hộp thư Gmail.');return;}
      if(mode==='login'&&result.success&&result.user)return finishLogin(result.user,'Đăng nhập thành công!');
      toast(result.message||'Không thể hoàn tất yêu cầu. Kiểm tra Backend và Gmail.',true);return;
    }
    if(form.id==='otp-form'){
      if(!pendingOtpEmail){authModal('register');return;}
      const button=form.querySelector('button[type="submit"]');if(button)button.disabled=true;
      const result=await req('/api/auth/verify-otp',{email:pendingOtpEmail,otp:String(data.otp||'').trim()});
      if(button)button.disabled=false;
      if(result.success&&result.user)return finishLogin(result.user,'Xác minh Gmail thành công! Tài khoản đã được tạo.');
      toast(result.message||'Mã OTP không hợp lệ.',true);return;
    }
    if(form.id==='nutrition-form'){
      const payload=makeProfilePayload(data);let response=await req('/api/nutrition/calculate',payload);
      if(response.success)state.calc=response.data;
      else {
        // Clearly local, illustrative fallback if the live calculator is unavailable.
        const bmr=10*payload.weight+6.25*payload.height-5*payload.age+(payload.gender==='male'?5:-161);
        const tdee=bmr*payload.activity_level;const kcal=Math.round(tdee+(payload.goal==='lose'?-500:payload.goal==='gain'?500:0));
        state.calc={...payload,bmr:Math.round(bmr),tdee:Math.round(tdee),bmi:Math.round(payload.weight/((payload.height/100)**2)*10)/10,target_kcal:kcal,target_water_ml:Math.round(payload.weight*35),macros:{protein:kcal*.25/4,carbs:kcal*.45/4,fat:kcal*.3/9}};
        toast('Đã tính trên trình duyệt (ước tính, chưa lưu).');
      }
      render();return;
    }
    if(form.id==='profile-form'){
      if(!realUser()){authModal('login');return;}
      const payload={user_id:id(),gender:data.gender,age:Number(data.age),height:Number(data.height),weight:Number(data.weight),activity_level:Number(data.activity_level),goal:data.goal};
      const res=await req('/save',payload);
      if(res.success){toast('Đã cập nhật hồ sơ.');return navigate('profile',true);}toast(res.message||'Lưu hồ sơ chưa thành công.',true);return;
    }
    if(form.id==='workout-log-form'){
      const res=await req('/api/workouts/log',{user_id:id(),workout_id:Number(data.workout_id),duration_minutes:Number(data.duration_minutes),date:data.date});
      if(res.success){closeModal();toast('Đã ghi nhận bài tập!');return navigate('workouts',true);}toast(res.message||'Không thể lưu bài tập.',true);return;
    }
    if(form.id==='custom-workout-form'){
      const button=form.querySelector('button[type="submit"]');
      if(button)button.disabled=true;
      const res=await req('/api/workouts/estimate',{user_id:id(),name:String(data.name||'').trim(),duration_minutes:Number(data.duration_minutes)},'POST',35000);
      if(button)button.disabled=false;
      if(res.success && res.data?.estimate_token){customWorkoutReview(res.data);return;}
      if(res.httpStatus===403&&res.code==='PREMIUM_REQUIRED'){state.premiumAccess=false;return upgradePremium();}
      toast(res.message||'AI chưa thể xác minh bài tập này.',true);return;
    }
    if(form.id==='custom-workout-save-form'){
      const button=form.querySelector('button[type="submit"]');
      if(button)button.disabled=true;
      const res=await req('/api/workouts/custom',{user_id:id(),name:data.name,duration_minutes:Number(data.duration_minutes),estimate_token:data.estimate_token},'POST',20000);
      if(button)button.disabled=false;
      if(res.success){closeModal();toast('Đã tạo bài tập được AI xác minh.');return navigate('workouts',true);}
      if(res.httpStatus===403&&res.code==='PREMIUM_REQUIRED'){state.premiumAccess=false;return upgradePremium();}
      toast(res.message||'Không thể lưu bài tập, vui lòng kiểm tra lại với AI.',true);return;
    }
    if(form.id==='manual-daily-plan-form')return estimateManualDailyPlan(form);
    if(form.id==='chat-form'){const msg=data.message;return sendChat(msg);}
  });
  window.addEventListener('hashchange',()=>{const next=location.hash.slice(1);if(next!==state.page)navigate(next);});
  async function boot(){
    try {const response=await fetch('data/street-food.json',{cache:'no-cache'});if(response.ok){streetSeed=await response.json();}}
    catch {streetSeed=[];}
    await checkConnection();
    navigate(location.hash.replace('#','')||'dashboard',true);
  }
  boot();
  // Cập nhật số liệu Admin tự động khi đang ở tab Tổng quan.
  // Không làm mới bảng danh sách khi người quản trị đang tìm kiếm/nhập bộ lọc.
  setInterval(async () => {
    if (state.page !== 'admin' || state.adminTab !== 'overview' || !state.online ||
        !adminRole() || state.adminLoading || document.hidden) return;
    const previous = JSON.stringify(state.adminStats);
    await loadAdminData();
    if (state.page === 'admin' && state.adminTab === 'overview' &&
        JSON.stringify(state.adminStats) !== previous) render();
  }, 15000);
})();
