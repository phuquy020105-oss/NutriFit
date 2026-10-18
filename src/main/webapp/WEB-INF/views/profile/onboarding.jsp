<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<!doctype html><html lang="vi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thiết lập hồ sơ | NutriFit</title><link rel="stylesheet" href="${pageContext.request.contextPath}/assets/css/onboarding.css"></head>
<body><main class="shell"><header><div class="brand">✳ NutriFit</div><p>Chỉ mất khoảng 2 phút để cá nhân hóa hành trình của bạn.</p></header>
<section class="panel"><div class="top"><h1>Thiết lập hồ sơ thể chất</h1><span id="count">Bước 1/4</span></div>
<div class="progress"><span id="bar"></span></div>
<% if (request.getAttribute("error") != null) { %><p class="error" role="alert">Dữ liệu chưa hợp lệ. Vui lòng kiểm tra các trường và thử lại.</p><% } %>
<form id="setup" method="post" action="${pageContext.request.contextPath}/onboarding">
<input type="hidden" name="_csrf" value="${sessionScope.csrfToken}">
<fieldset class="step active"><legend>1. Mục tiêu tập luyện</legend><p class="sub">Bạn muốn NutriFit giúp đạt được điều gì?</p>
<label class="option"><input type="radio" name="goal" value="lose" required><span><b>Giảm cân</b><small>Giảm mỡ, cải thiện vóc dáng</small></span></label>
<label class="option"><input type="radio" name="goal" value="maintain" checked><span><b>Duy trì cân nặng</b><small>Giữ cân nặng và sức khỏe</small></span></label>
<label class="option"><input type="radio" name="goal" value="gain"><span><b>Tăng cân</b><small>Tăng cân và hỗ trợ phát triển cơ</small></span></label></fieldset>
<fieldset class="step"><legend>2. Thông tin cá nhân</legend><p class="sub">Dùng để ước tính nhu cầu năng lượng.</p>
<label>Giới tính sinh học dùng cho công thức BMR<select name="gender" required><option value="">Chọn giới tính</option><option value="male">Nam</option><option value="female">Nữ</option></select></label>
<label>Tuổi<input type="number" name="age" min="18" max="100" placeholder="Ví dụ: 21" required></label><small>Phiên bản này dành cho người từ 18 tuổi trở lên.</small></fieldset>
<fieldset class="step"><legend>3. Chỉ số cơ thể</legend><p class="sub">Nhập số đo hiện tại của bạn.</p>
<label>Chiều cao (cm)<input type="number" name="heightCm" min="100" max="250" step="0.1" placeholder="175" required></label>
<label>Cân nặng (kg)<input type="number" name="weightKg" min="25" max="350" step="0.1" placeholder="65" required></label></fieldset>
<fieldset class="step"><legend>4. Mức độ vận động</legend><p class="sub">Chọn mức phù hợp với sinh hoạt thường ngày.</p>
<label class="option"><input type="radio" name="activityLevel" value="sedentary" required><span><b>Ít vận động</b><small>Ít hoặc không tập luyện</small></span></label>
<label class="option"><input type="radio" name="activityLevel" value="light"><span><b>Nhẹ</b><small>1–3 buổi/tuần</small></span></label>
<label class="option"><input type="radio" name="activityLevel" value="moderate" checked><span><b>Trung bình</b><small>3–5 buổi/tuần</small></span></label>
<label class="option"><input type="radio" name="activityLevel" value="high"><span><b>Cao</b><small>6–7 buổi/tuần</small></span></label>
<label class="option"><input type="radio" name="activityLevel" value="very_high"><span><b>Rất cao</b><small>Công việc thể lực nặng hoặc tập nhiều lần/ngày</small></span></label></fieldset>
<p class="note">Các mục tiêu calo và nước uống là ước tính tham khảo, có thể điều chỉnh sau.</p>
<div class="actions"><button type="button" id="back" class="secondary">Quay lại</button><button type="button" id="next">Tiếp tục →</button><button type="submit" id="submit" hidden>Hoàn tất thiết lập ✓</button></div>
</form></section></main><script>
(()=>{const steps=[...document.querySelectorAll('.step')],form=document.getElementById('setup');let i=0;
const back=document.getElementById('back'),next=document.getElementById('next'),submit=document.getElementById('submit');
function show(){steps.forEach((s,j)=>s.classList.toggle('active',j===i));document.getElementById('count').textContent=`Bước ${i+1}/4`;document.getElementById('bar').style.width=`${(i+1)*25}%`;back.hidden=i===0;next.hidden=i===3;submit.hidden=i!==3;}
next.addEventListener('click',()=>{const fields=[...steps[i].querySelectorAll('input,select')];for (const f of fields){if(!f.checkValidity()){f.reportValidity();return;}}i=Math.min(3,i+1);show();});
back.addEventListener('click',()=>{i=Math.max(0,i-1);show();});
form.addEventListener('submit',e=>{if(!form.checkValidity()){e.preventDefault();const invalid=form.querySelector(':invalid');if(invalid){i=steps.findIndex(s=>s.contains(invalid));show();invalid.reportValidity();}}});show();})();
</script></body></html>
