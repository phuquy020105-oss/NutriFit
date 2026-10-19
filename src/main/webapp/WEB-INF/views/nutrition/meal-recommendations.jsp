<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.util.*,com.nutrifit.model.*,com.nutrifit.dto.*,com.nutrifit.util.Html" %>
<%
MealSuggestion suggestion = (MealSuggestion) request.getAttribute("suggestion");
String suggestionToken = (String) request.getAttribute("suggestionToken");
String[] factKeys = {"caloriesKcal", "proteinG", "carbsG", "fatG", "fiberG"};
String[] factLabels = {"Calories (kcal)", "Protein (g)", "Carbs (g)", "Fat (g)", "Fiber (g)"};
String ctx = request.getContextPath();
String csrf = (String) request.getAttribute("csrf");
%>
<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gợi ý món ăn - NutriFit</title><link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/dashboard.css">
<link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/nutrition.css"></head>
<body class="nf-page"><div class="app-shell">
<aside class="sidebar" id="sidebar">
<a class="logo" href="<%= Html.escape(ctx) %>/dashboard"><span class="logo-mark">✦</span> Nutri<span>Fit</span></a>
<p class="nav-caption">KHÔNG GIAN CỦA BẠN</p>
<nav class="side-nav" aria-label="Điều hướng chính">
<a href="<%= Html.escape(ctx) %>/dashboard"><span>▦</span> Tổng quan</a>
<a href="<%= Html.escape(ctx) %>/workout"><span>◈</span> Bài tập</a>
<a href="<%= Html.escape(ctx) %>/workout/plan"><span>▤</span> Lịch tập</a>
<a href="<%= Html.escape(ctx) %>/nutrition/meal-planner" class="active" aria-current="page"><span>◉</span> Dinh dưỡng</a>
<a href="<%= Html.escape(ctx) %>/chatbot"><span>✧</span> AI Chatbot</a>
<a href="<%= Html.escape(ctx) %>/payment"><span>♛</span> Premium</a>
<a href="<%= Html.escape(ctx) %>/profile"><span>◎</span> Hồ sơ</a>
<%@ include file="/WEB-INF/views/shared/admin-navigation.jspf" %>
</nav>
<div class="sidebar-bottom">
<div class="mini-promo"><strong>Mỗi ngày tốt hơn 1%</strong><p>Kiên trì từng bước nhỏ để đạt mục tiêu sức khỏe.</p></div>
<form method="post" action="<%= Html.escape(ctx) %>/logout"><input type="hidden" name="_csrf" value="${sessionScope.csrfToken}"><button class="logout" type="submit">↪ Đăng xuất</button></form>
</div>
</aside>
<div class="app-content">
<header class="topbar"><div class="topbar-left"><button class="menu-toggle" type="button" aria-label="Mở menu" aria-controls="sidebar" aria-expanded="false" onclick="toggleNutritionMenu(this)">☰</button><span>Không gian dinh dưỡng của bạn</span></div><div class="topbar-right"><span class="status">DINH DƯỠNG</span><a class="avatar" href="<%= Html.escape(ctx) %>/profile" aria-label="Hồ sơ cá nhân">☺</a></div></header>
<main class="nf-wrap">

<nav class="nf-nutrition-tabs" aria-label="Các chức năng dinh dưỡng">
<a href="<%= Html.escape(ctx) %>/nutrition/meal-planner">◉ Hôm nay</a>
<a href="<%= Html.escape(ctx) %>/nutrition/recommendations" class="active" aria-current="page">✧ Gợi ý món ăn</a>
<a href="<%= Html.escape(ctx) %>/nutrition/history">▤ Lịch sử</a>
<a href="<%= Html.escape(ctx) %>/nutrition/preferences">♡ Sở thích</a>
</nav>
<header class="nf-head"><div><h1>Gợi ý thực đơn hôm nay</h1><p>Ba món cho ba bữa, theo mục tiêu calories trong hồ sơ. Chỉ lưu sau khi bạn xác nhận.</p></div></header>
<p class="nf-muted" data-suggestion-mode><%= suggestion.personalized() ? "Đang áp dụng sở thích Premium: loại DISLIKE và ưu tiên LIKE." : "Gợi ý Free theo mục tiêu calories, không áp dụng LIKE/DISLIKE." %></p>
<form method="post" action="<%= Html.escape(ctx) %>/nutrition/recommendations" data-suggestion-form>
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>">
<input type="hidden" name="suggestionToken" value="<%= Html.escape(suggestionToken) %>">
<input type="hidden" name="action" value="save">
<div class="nf-suggestion-grid">
<% for (SuggestedMeal meal : suggestion.meals()) {
    NutritionFacts f = meal.nutrition();
    java.math.BigDecimal[] values = {f.caloriesKcal(), f.proteinG(), f.carbsG(), f.fatG(), f.fiberG()};
    String label = meal.mealType() == MealEntry.MealType.BREAKFAST ? "Bữa sáng" : meal.mealType() == MealEntry.MealType.LUNCH ? "Bữa trưa" : "Bữa tối";
%>
<section class="nf-card nf-suggested-meal" data-suggestion-meal="<%= meal.mealType().name() %>">
<h2><%= label %></h2><h3><%= Html.escape(meal.name()) %></h3>
<label>Khẩu phần<input type="number" name="servings_<%= meal.mealType().name() %>" min="0.01" max="999999.99" step="0.01" value="<%= Html.escape(meal.servings()) %>" required data-suggestion-servings></label>
<dl class="nf-suggestion-facts"><% for (int i=0; i<factKeys.length; i++) { %>
<div><dt><%= factLabels[i] %></dt><dd data-fact="<%= factKeys[i] %>"><%= Html.escape(values[i]) %></dd></div>
<% } %></dl></section><% } %></div>
<section class="nf-card"><h2>Tổng dinh dưỡng ba bữa</h2>
<% NutritionFacts total = suggestion.total();
   java.math.BigDecimal[] totals = {total.caloriesKcal(), total.proteinG(), total.carbsG(), total.fatG(), total.fiberG()}; %>
<dl class="nf-suggestion-facts nf-suggestion-totals"><% for (int i=0; i<factKeys.length; i++) { %>
<div><dt><%= factLabels[i] %></dt><dd data-total-fact="<%= factKeys[i] %>"><%= Html.escape(totals[i]) %></dd></div>
<% } %></dl>
<p>Mục tiêu: <strong data-suggestion-target><%= Html.escape(suggestion.targetKcal()) %></strong> kcal.
Chênh lệch so với mục tiêu: <strong data-suggestion-difference><%= Html.escape(suggestion.differenceKcal()) %></strong> kcal.</p>
<p class="nf-muted">Giá trị dương là vượt mục tiêu, âm là còn thiếu. Hãy chỉnh khẩu phần để phù hợp nhu cầu.</p>
<p data-suggestion-status role="status" aria-live="polite">Chưa lưu vào nhật ký.</p>
<div class="nf-suggestion-actions"><button type="button" data-refresh-suggestion>Tính lại khẩu phần</button><button type="submit" data-save-suggestion>Lưu vào nhật ký hôm nay</button></div>
<p class="nf-muted">Cả ba món được lưu cùng nhau. Món đã có trong cùng bữa được cộng khẩu phần theo snapshot đang lưu; các món khác được giữ nguyên.</p>
<p class="nf-muted">Dinh dưỡng là ước lượng; không thay thế tư vấn chuyên môn.</p></section></form>
<footer class="nf-footer">© NutriFit · Sống khỏe mỗi ngày</footer></main></div></div><script src="<%= Html.escape(ctx) %>/assets/js/nutrition.js" defer></script><script>
function toggleNutritionMenu(button){
  var sidebar=document.getElementById('sidebar');
  var expanded=sidebar.classList.toggle('open');
  button.setAttribute('aria-expanded',String(expanded));
}
</script></body></html>
