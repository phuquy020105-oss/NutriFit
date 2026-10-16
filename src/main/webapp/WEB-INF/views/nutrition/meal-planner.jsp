<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.util.*,java.math.BigDecimal,com.nutrifit.dto.*,com.nutrifit.model.*,com.nutrifit.util.Html" %>
<%
DaySummary day = (DaySummary) request.getAttribute("today");
List<RecipeCandidate> recipes = (List<RecipeCandidate>) request.getAttribute("recipes");
String csrf = (String) request.getAttribute("csrf");
String ctx = request.getContextPath();
%>
<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Meal Planner - NutriFit</title><link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/meal-planner.css"></head>
<body><main class="nf-wrap">
<header class="nf-head"><div><h1>Nhật ký ăn uống hôm nay</h1><p><%= Html.escape(day.date()) %> · Chọn món là ghi nhận đã ăn.</p></div>
<nav><a href="<%= Html.escape(ctx) %>/nutrition/history">Lịch sử</a><a href="<%= Html.escape(ctx) %>/nutrition/preferences">Sở thích</a><a href="<%= Html.escape(ctx) %>/nutrition/recommendations">Gợi ý Premium</a></nav></header>
<% if ("saved".equals(request.getParameter("message"))) { %><p class="nf-success">Đã lưu thay đổi.</p><% } %>
<section class="nf-card"><h2>Tổng dinh dưỡng trong ngày</h2>
<div class="nf-stats"><div><strong><%= Html.escape(day.total().caloriesKcal()) %></strong><small>kcal</small></div>
<div><strong><%= Html.escape(day.total().proteinG()) %></strong><small>Protein (g)</small></div>
<div><strong><%= Html.escape(day.total().carbsG()) %></strong><small>Carbs (g)</small></div>
<div><strong><%= Html.escape(day.total().fatG()) %></strong><small>Fat (g)</small></div>
<div><strong><%= Html.escape(day.total().fiberG()) %></strong><small>Fiber (g)</small></div></div></section>
<section class="nf-card"><h2>Ghi nhận món ăn</h2>
<% if (recipes.isEmpty()) { %><p>Chưa có công thức hợp lệ. Hãy thêm dữ liệu Food/Recipe trước khi chọn món.</p><% } else { %>
<form method="post" action="<%= Html.escape(ctx) %>/nutrition/meal-planner" class="nf-form" id="add-meal">
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="action" value="add">
<label>Bữa ăn<select name="mealType" id="mealType" required><option value="BREAKFAST">Sáng</option><option value="LUNCH">Trưa</option><option value="DINNER">Tối</option></select></label>
<label>Công thức<select name="recipeId" id="recipeId" required>
<% for (RecipeCandidate r : recipes) { %><option value="<%= r.recipeId() %>" data-meal="<%= r.mealType().name() %>">
<%= Html.escape(r.name()) %> — <%= Html.escape(r.perServing().caloriesKcal()) %> kcal / khẩu phần</option><% } %>
</select></label>
<label>Khẩu phần<input type="number" name="servings" value="1" min="0.01" max="999999.99" step="0.01" required></label>
<button type="submit">Thêm món</button></form>
<% } %></section>
<% for (MealEntry.MealType type : MealEntry.MealType.values()) {
String label = switch(type) {case BREAKFAST -> "Bữa sáng"; case LUNCH -> "Bữa trưa"; case DINNER -> "Bữa tối";};
%>
<section class="nf-card"><h2><%= label %></h2>
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
<td><form method="post" action="<%= Html.escape(ctx) %>/nutrition/meal-planner" onsubmit="return confirm('Xóa món này?')">
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="action" value="delete">
<input type="hidden" name="entryId" value="<%= e.getEntryId() %>"><button type="submit" class="nf-danger nf-small">Xóa</button></form></td></tr>
<% } if(!found){ %><tr><td colspan="8">Chưa ghi nhận món nào.</td></tr><% } %>
</tbody></table></div></section>
<% } %>
<p class="nf-muted">Dữ liệu dinh dưỡng được lưu tại thời điểm ghi nhận (snapshot). Các ngày trước chỉ được xem.</p>
</main>
<script>
(() => { const meal = document.getElementById('mealType'); const recipe = document.getElementById('recipeId');
if (!meal || !recipe) return;
function sync() { let first = null; for(const opt of recipe.options) { const matched = opt.dataset.meal === meal.value; opt.hidden = !matched; opt.disabled = !matched; if (matched && !first) first = opt; }
if(first) { recipe.value = first.value; recipe.disabled = false; } else { recipe.value = ''; recipe.disabled = true; } }
meal.addEventListener('change', sync); sync(); })();
</script></body></html>
