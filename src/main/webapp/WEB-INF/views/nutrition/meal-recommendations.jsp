<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.util.*,com.nutrifit.model.*,com.nutrifit.dto.*,com.nutrifit.util.Html,com.nutrifit.util.NutritionDisplay,com.nutrifit.util.RecipeImage" %>
<%
MealSuggestion suggestion = (MealSuggestion) request.getAttribute("suggestion");
String suggestionToken = (String) request.getAttribute("suggestionToken");
String[] factKeys = {"caloriesKcal", "proteinG", "carbsG", "fatG", "fiberG"};
String[] factLabels = {"Calories (kcal)", "Protein (g)", "Carbs (g)", "Fat (g)", "Fiber (g)"};
String ctx = request.getContextPath();
String csrf = (String) request.getAttribute("csrf");
DaySummary today = (DaySummary) request.getAttribute("today");
List<RecipeCandidate> recipes = (List<RecipeCandidate>) request.getAttribute("recipes");
boolean saved = Boolean.TRUE.equals(request.getAttribute("suggestionSaved"));
boolean blocked = Boolean.TRUE.equals(request.getAttribute("saveBlocked"));
String notice = (String) request.getAttribute("notice");
%>
<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Thực đơn hôm nay - NutriFit</title><link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/dashboard.css">
<link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/nutrition.css"></head>
<body class="nf-page"><div class="app-shell">
<aside class="sidebar" id="sidebar">
<a class="logo" href="<%= Html.escape(ctx) %>/dashboard"><span class="logo-mark">✦</span> Nutri<span>Fit</span></a>
<p class="nav-caption">KHÔNG GIAN CỦA BẠN</p>
<nav class="side-nav" aria-label="Điều hướng chính">
<a href="<%= Html.escape(ctx) %>/dashboard"><span>▦</span> Tổng quan</a>
<a href="<%= Html.escape(ctx) %>/workout"><span>◈</span> Bài tập</a>
<a href="<%= Html.escape(ctx) %>/workout/plan"><span>▤</span> Lịch tập</a>
<a href="<%= Html.escape(ctx) %>/nutrition/recommendations" class="active" aria-current="page"><span>◉</span> Dinh dưỡng</a>
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
<a href="<%= Html.escape(ctx) %>/nutrition/recommendations" class="active" aria-current="page">◉ Thực đơn</a>
<a href="<%= Html.escape(ctx) %>/nutrition/history">▤ Lịch sử</a>
<a href="<%= Html.escape(ctx) %>/nutrition/preferences">♡ Sở thích</a>
</nav>
<header class="nf-head"><div><h1>Thực đơn hôm nay</h1><p>Ba món cho ba bữa, dựa trên mục tiêu và nhật ký trong ngày của bạn.</p></div></header>
<% if (notice != null) { %><p class="nf-success" role="status"><%= Html.escape(notice) %></p><% } %>
<% if (suggestion == null) { %>
<p class="nf-error" role="status"><%= Html.escape(request.getAttribute("suggestionError")) %></p>
<form method="post" action="<%= Html.escape(ctx) %>/nutrition/recommendations" data-submit-once>
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="action" value="regenerate"><button type="submit">Gợi ý lại</button></form>
<% } else { %>
<p class="nf-muted"><%= suggestion.personalized() ? "Premium: loại nguyên liệu DISLIKE và ưu tiên LIKE." : "Thực đơn Free theo mục tiêu calories trong hồ sơ." %></p>
<div class="nf-suggestion-grid">
<% for (SuggestedMeal meal : suggestion.meals()) {
    NutritionFacts f = meal.nutrition();
    java.math.BigDecimal[] values = {f.caloriesKcal(), f.proteinG(), f.carbsG(), f.fatG(), f.fiberG()};
    String label = meal.mealType() == MealEntry.MealType.BREAKFAST ? "Bữa sáng" : meal.mealType() == MealEntry.MealType.LUNCH ? "Bữa trưa" : "Bữa tối";
%>
<section class="nf-card nf-suggested-meal" data-suggestion-meal="<%= meal.mealType().name() %>">
<h2><%= label %></h2>
<img class="nf-recipe-image" src="<%= Html.escape(RecipeImage.url(ctx,meal.imageUrl())) %>" data-recipe-image data-fallback="<%= Html.escape(ctx + RecipeImage.FALLBACK) %>" alt="<%= Html.escape(meal.name()) %>" width="800" height="450" loading="lazy">
<h3><%= Html.escape(meal.name()) %></h3>
<dl class="nf-suggestion-facts"><% for (int i=0; i<factKeys.length; i++) { %>
<div><dt><%= factLabels[i] %></dt><dd><%= NutritionDisplay.integer(values[i]) %></dd></div>
<% } %></dl></section><% } %></div>
<section class="nf-card"><h2>Tổng dinh dưỡng ba bữa</h2>
<% NutritionFacts total = suggestion.total();
   java.math.BigDecimal[] totals = {total.caloriesKcal(), total.proteinG(), total.carbsG(), total.fatG(), total.fiberG()}; %>
<dl class="nf-suggestion-facts nf-suggestion-totals"><% for (int i=0; i<factKeys.length; i++) { %>
<div><dt><%= factLabels[i] %></dt><dd><%= NutritionDisplay.integer(totals[i]) %></dd></div>
<% } %></dl>
<p>Mục tiêu ngày: <strong><%= NutritionDisplay.integer(suggestion.targetKcal()) %></strong> kcal.
Chênh lệch của thực đơn: <strong><%= NutritionDisplay.integer(suggestion.differenceKcal()) %></strong> kcal.</p>
<% if (!blocked) { %>
<p>Nếu lưu thêm: <strong><%= NutritionDisplay.integer(suggestion.projectedDay().caloriesKcal()) %></strong> kcal cả ngày;
chênh lệch <strong><%= NutritionDisplay.integer(suggestion.projectedDifferenceKcal()) %></strong> kcal.</p>
<% if (suggestion.exceedsTarget()) { %><p class="nf-error" role="status">Lưu thêm thực đơn này sẽ vượt mục tiêu ngày. Hãy cân nhắc những món đã ghi nhận bên dưới trước khi lưu.</p><% } %>
<% } %>
<% if (!suggestion.warnings().isEmpty()) { %><ul class="nf-muted" aria-label="Lưu ý về thực đơn"><% for (String warning : suggestion.warnings()) { %><li><%= Html.escape(warning) %></li><% } %></ul><% } %>
<p class="nf-muted">Ảnh món ăn dùng để minh họa; dinh dưỡng là ước lượng. Các số hiển thị được làm tròn từ dữ liệu gốc; khi cộng có thể chênh 1 đơn vị.</p>
<p class="nf-muted">Chênh lệch dương là vượt mục tiêu, âm là còn thiếu. Các món đã ghi nhận được giữ nguyên.</p>
<div class="nf-suggestion-actions">
<form method="post" action="<%= Html.escape(ctx) %>/nutrition/recommendations" data-submit-once>
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="action" value="regenerate">
<button type="submit">Gợi ý lại</button></form>
<form method="post" action="<%= Html.escape(ctx) %>/nutrition/recommendations" data-submit-once>
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="suggestionToken" value="<%= Html.escape(suggestionToken) %>">
<input type="hidden" name="action" value="save">
<button type="submit" data-save-suggestion <%= blocked ? "disabled" : "" %>><%= saved ? "Đã lưu thực đơn" : "Lưu thực đơn vào nhật ký" %></button>
</form></div>
<% if (blocked && !saved) { %><p class="nf-error" role="status">Lần lưu trước chưa xác định được kết quả. Hãy kiểm tra nhật ký trước khi chủ động tạo gợi ý khác; không gửi lưu lại.</p><% } %>
<p class="nf-muted">Cả ba món được lưu cùng nhau. Món trùng cùng bữa được cộng theo snapshot đang lưu; tổng dự kiến cả ngày đã tính theo quy tắc này.</p>
</section><% } %>
<section class="nf-card" aria-labelledby="recorded-heading"><h2 id="recorded-heading">Đã ghi nhận hôm nay</h2>
<% if (today.entries().isEmpty()) { %><p class="nf-muted">Chưa có món nào được ghi nhận hôm nay.</p>
<% } else { %>
<p>Tổng đã ghi: <strong><%= NutritionDisplay.integer(today.total().caloriesKcal()) %></strong> kcal · Protein <%= NutritionDisplay.integer(today.total().proteinG()) %> g · Carbs <%= NutritionDisplay.integer(today.total().carbsG()) %> g · Fat <%= NutritionDisplay.integer(today.total().fatG()) %> g · Fiber <%= NutritionDisplay.integer(today.total().fiberG()) %> g.</p>
<ul class="nf-journal-list">
<% for (MealEntry entry : today.entries()) {
String mealLabel = entry.getMealType() == MealEntry.MealType.BREAKFAST ? "Bữa sáng" : entry.getMealType() == MealEntry.MealType.LUNCH ? "Bữa trưa" : "Bữa tối";
%><li class="nf-journal-item"><div><strong><%= Html.escape(entry.getRecipeNameSnapshot()) %></strong> <span class="nf-muted">· <%= mealLabel %></span>
<p><%= NutritionDisplay.integer(entry.getCaloriesKcal()) %> kcal · Protein <%= NutritionDisplay.integer(entry.getProteinG()) %> g · Carbs <%= NutritionDisplay.integer(entry.getCarbsG()) %> g · Fat <%= NutritionDisplay.integer(entry.getFatG()) %> g · Fiber <%= NutritionDisplay.integer(entry.getFiberG()) %> g</p></div>
<div class="nf-journal-actions">
<form method="post" action="<%= Html.escape(ctx) %>/nutrition/meal-planner" data-submit-once data-confirm="Xóa món này khỏi nhật ký hôm nay?">
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="action" value="delete"><input type="hidden" name="entryId" value="<%= entry.getEntryId() %>">
<button type="submit" class="nf-danger nf-small">Xóa</button></form>
<% if (!recipes.isEmpty()) { %><details class="nf-edit"><summary>Đổi món</summary>
<form method="post" action="<%= Html.escape(ctx) %>/nutrition/meal-planner" class="nf-edit-form" data-recipe-form data-submit-once>
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="action" value="changeRecipe"><input type="hidden" name="entryId" value="<%= entry.getEntryId() %>">
<label>Bữa ăn<select name="mealType" data-meal-select required><% for (MealEntry.MealType type : MealEntry.MealType.values()) { %><option value="<%= type.name() %>" <%= type == entry.getMealType() ? "selected" : "" %>><%= type == MealEntry.MealType.BREAKFAST ? "Sáng" : type == MealEntry.MealType.LUNCH ? "Trưa" : "Tối" %></option><% } %></select></label>
<label>Món ăn<select name="recipeId" data-recipe-select required><% for (RecipeCandidate recipe : recipes) { %><option value="<%= recipe.recipeId() %>" data-meal="<%= recipe.mealType().name() %>" <%= recipe.recipeId() == entry.getRecipeId() ? "selected" : "" %>><%= Html.escape(recipe.name()) %></option><% } %></select></label>
<button type="submit">Đổi món</button><p class="nf-muted" data-empty-recipes hidden role="status">Chưa có món phù hợp cho bữa này.</p>
</form></details><% } %></div></li><% } %></ul><% } %></section>
<details class="nf-card nf-manual-add"><summary>Thêm món thủ công</summary>
<% if (recipes.isEmpty()) { %><p class="nf-muted">Chưa có công thức hợp lệ để chọn.</p><% } else { %>
<form method="post" action="<%= Html.escape(ctx) %>/nutrition/meal-planner" class="nf-form" data-recipe-form data-submit-once>
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="action" value="addStandard">
<label>Bữa ăn<select name="mealType" data-meal-select required><option value="BREAKFAST">Sáng</option><option value="LUNCH">Trưa</option><option value="DINNER">Tối</option></select></label>
<label>Món ăn<select name="recipeId" data-recipe-select required><% for (RecipeCandidate recipe : recipes) { %><option value="<%= recipe.recipeId() %>" data-meal="<%= recipe.mealType().name() %>"><%= Html.escape(recipe.name()) %></option><% } %></select></label>
<button type="submit">Thêm món</button><p class="nf-muted" data-empty-recipes hidden role="status">Chưa có món phù hợp cho bữa này.</p>
</form><% } %></details>
<footer class="nf-footer">© NutriFit · Sống khỏe mỗi ngày</footer></main></div></div><script src="<%= Html.escape(ctx) %>/assets/js/nutrition.js" defer></script><script>
function toggleNutritionMenu(button){
  var sidebar=document.getElementById('sidebar');
  var expanded=sidebar.classList.toggle('open');
  button.setAttribute('aria-expanded',String(expanded));
}
</script></body></html>
