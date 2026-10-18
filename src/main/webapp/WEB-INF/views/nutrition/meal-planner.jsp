<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.util.*,java.math.BigDecimal,com.nutrifit.dto.*,com.nutrifit.model.*,com.nutrifit.util.Html" %>
<%
DaySummary day = (DaySummary) request.getAttribute("today");
List<RecipeCandidate> recipes = (List<RecipeCandidate>) request.getAttribute("recipes");
String csrf = (String) request.getAttribute("csrf");
String ctx = request.getContextPath();
BigDecimal targetKcal = (BigDecimal) request.getAttribute("targetKcal");
String message = request.getParameter("message");
String notice = null;
if ("added".equals(message)) {
    notice = "Đã ghi nhận món ăn. Nếu món đã có trong cùng bữa, khẩu phần được cộng thêm.";
} else if ("updated".equals(message)) {
    notice = "Đã cập nhật món ăn.";
} else if ("deleted".equals(message)) {
    notice = "Đã xóa món ăn khỏi nhật ký hôm nay.";
} else if ("saved".equals(message)) {
    notice = "Đã lưu thay đổi.";
}
%>
<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Meal Planner - NutriFit</title><link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/dashboard.css">
<link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/nutrition.css?v=20261018-meal"></head>
<body class="nf-page nf-meal-today"><div class="app-shell">
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
<a href="<%= Html.escape(ctx) %>/nutrition/meal-planner" class="active" aria-current="page">◉ Hôm nay</a>
<a href="<%= Html.escape(ctx) %>/nutrition/recommendations">✧ Gợi ý món ăn</a>
<a href="<%= Html.escape(ctx) %>/nutrition/history">▤ Lịch sử</a>
<a href="<%= Html.escape(ctx) %>/nutrition/preferences">♡ Sở thích</a>
</nav>

<header class="nf-head nf-today-hero"><div><span class="nf-hero-eyebrow">NHẬT KÝ DINH DƯỠNG · HÔM NAY</span><h1>Ăn uống lành mạnh, mỗi ngày một chút</h1><p><%= Html.escape(day.date()) %> · Theo dõi các bữa ăn và tiến độ dinh dưỡng của bạn.</p></div><div class="nf-hero-symbol" aria-hidden="true">✦</div></header>
<% if (notice != null) { %><p class="nf-success" role="status"><%= Html.escape(notice) %></p><% } %>
<section class="nf-card nf-today-overview">
<div class="nf-section-heading"><div><span class="nf-section-kicker">TỔNG QUAN HÔM NAY</span><h2>Tiến độ dinh dưỡng</h2></div><span class="nf-section-icon" aria-hidden="true">◉</span></div>
<div class="nf-calorie-progress">
<div class="nf-calorie-heading"><div><span class="nf-calorie-caption">Năng lượng đã nạp</span><div class="nf-calorie-value"><strong><%= Html.escape(day.total().caloriesKcal()) %></strong><span>kcal</span></div></div><div class="nf-calorie-goal"><span>Mục tiêu mỗi ngày</span><strong><%= targetKcal != null ? Html.escape(targetKcal) + " kcal" : "Chưa thiết lập" %></strong></div></div>
<% if (targetKcal != null && targetKcal.signum() > 0) { java.math.BigDecimal progress = day.total().caloriesKcal().multiply(new java.math.BigDecimal("100")).divide(targetKcal, 1, java.math.RoundingMode.HALF_UP); java.math.BigDecimal capped = progress.max(java.math.BigDecimal.ZERO).min(new java.math.BigDecimal("100")); %>
<div class="nf-progress-track" role="progressbar" aria-label="Tiến độ năng lượng" aria-valuemin="0" aria-valuemax="100" aria-valuenow="<%= capped.intValue() %>"><div class="nf-progress-fill" style="width:<%= capped.toPlainString() %>%"></div></div><p class="nf-progress-note">Đã đạt <strong><%= Html.escape(progress) %>%</strong> mục tiêu năng lượng hôm nay.</p>
<% } else { %><p class="nf-progress-note">Bạn có thể thiết lập mục tiêu năng lượng trong hồ sơ.</p><% } %>
</div>
<div class="nf-macro-grid">
<div class="nf-macro"><span class="nf-macro-icon">P</span><span>Protein</span><strong><%= Html.escape(day.total().proteinG()) %> <small>g</small></strong></div>
<div class="nf-macro"><span class="nf-macro-icon">C</span><span>Carbs</span><strong><%= Html.escape(day.total().carbsG()) %> <small>g</small></strong></div>
<div class="nf-macro"><span class="nf-macro-icon">F</span><span>Fat</span><strong><%= Html.escape(day.total().fatG()) %> <small>g</small></strong></div>
<div class="nf-macro"><span class="nf-macro-icon">Fi</span><span>Fiber</span><strong><%= Html.escape(day.total().fiberG()) %> <small>g</small></strong></div>
</div></section>
<section class="nf-card nf-today-add"><div class="nf-section-heading"><div><span class="nf-section-kicker">THÊM VÀO NHẬT KÝ</span><h2>Ghi nhận món ăn</h2></div><span class="nf-section-icon" aria-hidden="true">＋</span></div>
<% if (recipes.isEmpty()) { %><p>Chưa có công thức hợp lệ. Hãy thêm dữ liệu Food/Recipe trước khi chọn món.</p><% } else { %>
<form method="post" action="<%= Html.escape(ctx) %>/nutrition/meal-planner" class="nf-form" id="add-meal" data-recipe-form>
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="action" value="add">
<label>Bữa ăn<select name="mealType" id="mealType" data-meal-select required><option value="BREAKFAST">Sáng</option><option value="LUNCH">Trưa</option><option value="DINNER">Tối</option></select></label>
<label>Công thức<select name="recipeId" id="recipeId" data-recipe-select required>
<% for (RecipeCandidate r : recipes) { %><option value="<%= r.recipeId() %>" data-meal="<%= r.mealType().name() %>">
<%= Html.escape(r.name()) %> — <%= Html.escape(r.perServing().caloriesKcal()) %> kcal / khẩu phần</option><% } %>
</select></label>
<label>Khẩu phần<input type="number" name="servings" value="1" min="0.01" max="999999.99" step="0.01" required></label>
<button type="submit">Thêm món</button><p class="nf-muted" data-empty-recipes hidden role="status">Chưa có công thức hợp lệ cho bữa đã chọn.</p></form>
<% } %></section>
<% for (MealEntry.MealType type : MealEntry.MealType.values()) {
String label = "";
switch (type) {
    case BREAKFAST: label = "Bữa sáng"; break;
    case LUNCH: label = "Bữa trưa"; break;
    case DINNER: label = "Bữa tối"; break;
}
%>
<section class="nf-card nf-today-meal"><div class="nf-section-heading"><div><span class="nf-section-kicker">NHẬT KÝ THEO BỮA</span><h2><%= label %></h2></div><span class="nf-section-icon" aria-hidden="true">◷</span></div>
<div class="nf-table-scroll"><table><thead><tr><th>Món</th><th>Khẩu phần</th><th>Kcal</th><th>Protein</th><th>Carbs</th><th>Fat</th><th>Fiber</th><th>Thao tác</th></tr></thead><tbody>
<% boolean found = false; for (MealEntry e : day.entries()) { if (e.getMealType()!=type) continue; found = true; %>
<tr><td><%= Html.escape(e.getRecipeNameSnapshot()) %></td>
<td><form method="post" action="<%= Html.escape(ctx) %>/nutrition/meal-planner" class="nf-inline">
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="action" value="update">
<input type="hidden" name="entryId" value="<%= e.getEntryId() %>"><input type="hidden" name="recipeId" value="<%= e.getRecipeId() %>">
<input type="hidden" name="mealType" value="<%= e.getMealType().name() %>">
<input type="number" class="nf-number" name="servings" min="0.01" max="999999.99" step="0.01" value="<%= Html.escape(e.getServings()) %>" required>
<button type="submit" class="nf-small">Sửa</button></form></td>
<td><%= Html.escape(e.getCaloriesKcal()) %></td><td><%= Html.escape(e.getProteinG()) %></td><td><%= Html.escape(e.getCarbsG()) %></td><td><%= Html.escape(e.getFatG()) %></td><td><%= Html.escape(e.getFiberG()) %></td>
<td><form method="post" action="<%= Html.escape(ctx) %>/nutrition/meal-planner" data-confirm="Xóa món này khỏi nhật ký hôm nay?">
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="action" value="delete">
<input type="hidden" name="entryId" value="<%= e.getEntryId() %>"><button type="submit" class="nf-danger nf-small">Xóa</button></form>
<% if (!recipes.isEmpty()) { %><details class="nf-edit"><summary>Đổi món hoặc bữa</summary>
<form method="post" action="<%= Html.escape(ctx) %>/nutrition/meal-planner" class="nf-edit-form" data-recipe-form>
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="action" value="update">
<input type="hidden" name="entryId" value="<%= e.getEntryId() %>">
<label>Bữa ăn<select name="mealType" data-meal-select required>
<% for (MealEntry.MealType t : MealEntry.MealType.values()) { %>
<option value="<%= t.name() %>" <%= t==e.getMealType()?"selected":"" %>><%= t==MealEntry.MealType.BREAKFAST?"Sáng":t==MealEntry.MealType.LUNCH?"Trưa":"Tối" %></option><% } %></select></label>
<label>Món thay thế<select name="recipeId" data-recipe-select required>
<% for (RecipeCandidate r : recipes) { %><option value="<%= r.recipeId() %>" data-meal="<%= r.mealType().name() %>" <%= e.getRecipeId().equals(r.recipeId())?"selected":"" %>><%= Html.escape(r.name()) %></option><% } %>
</select></label>
<label>Khẩu phần<input type="number" name="servings" min="0.01" max="999999.99" step="0.01" value="<%= Html.escape(e.getServings()) %>" required></label>
<p class="nf-muted">Đổi sang món khác sẽ tính lại dinh dưỡng. Hãy sửa khẩu phần ở dòng món đã có nếu muốn cộng thêm.</p>
<button type="submit" class="nf-small">Lưu thay đổi</button>
<p class="nf-muted" data-empty-recipes hidden role="status">Chưa có công thức hợp lệ cho bữa đã chọn.</p>
</form></details><% } %></td></tr>
<% } if(!found){ %><tr><td colspan="8">Chưa ghi nhận món nào.</td></tr><% } %>
</tbody></table></div></section>
<% } %>
<p class="nf-muted">Dữ liệu dinh dưỡng được lưu tại thời điểm ghi nhận (snapshot). Các ngày trước chỉ được xem.</p>
<footer class="nf-footer">© NutriFit · Sống khỏe mỗi ngày</footer></main></div></div>
<script src="<%= Html.escape(ctx) %>/assets/js/nutrition.js" defer></script><script>
function toggleNutritionMenu(button){
  var sidebar=document.getElementById('sidebar');
  var expanded=sidebar.classList.toggle('open');
  button.setAttribute('aria-expanded',String(expanded));
}
</script></body></html>
