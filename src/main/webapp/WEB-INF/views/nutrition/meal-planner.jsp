<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.util.*,java.math.BigDecimal,com.nutrifit.dto.*,com.nutrifit.model.*,com.nutrifit.util.Html" %>
<%
DaySummary day = (DaySummary) request.getAttribute("today");
List<RecipeCandidate> recipes = (List<RecipeCandidate>) request.getAttribute("recipes");
String csrf = (String) request.getAttribute("csrf");
String ctx = request.getContextPath();
BigDecimal targetKcal = (BigDecimal) request.getAttribute("targetKcal");
String message = request.getParameter("message");
String notice = message == null ? null : switch (message) {
    case "added" -> "Đã ghi nhận món ăn. Nếu món đã có trong cùng bữa, khẩu phần được cộng thêm.";
    case "updated" -> "Đã cập nhật món ăn.";
    case "deleted" -> "Đã xóa món ăn khỏi nhật ký hôm nay.";
    case "saved" -> "Đã lưu thay đổi.";
    default -> null;
};
%>
<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Meal Planner - NutriFit</title><link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/meal-planner.css"></head>
<body class="nf-page"><main class="nf-wrap">
<header class="nf-head"><div><h1>Nhật ký ăn uống hôm nay</h1><p><%= Html.escape(day.date()) %> · Chọn món là ghi nhận đã ăn.</p></div>
<nav><a href="<%= Html.escape(ctx) %>/nutrition/history">Lịch sử</a><a href="<%= Html.escape(ctx) %>/nutrition/preferences">Sở thích</a><a href="<%= Html.escape(ctx) %>/nutrition/recommendations">Gợi ý Premium</a></nav></header>
<% if (notice != null) { %><p class="nf-success" role="status"><%= Html.escape(notice) %></p><% } %>
<section class="nf-card"><h2>Tổng dinh dưỡng trong ngày</h2>
<div class="nf-stats"><div><strong><%= Html.escape(day.total().caloriesKcal()) %></strong><small>kcal</small></div>
<div><strong><%= Html.escape(day.total().proteinG()) %></strong><small>Protein (g)</small></div>
<div><strong><%= Html.escape(day.total().carbsG()) %></strong><small>Carbs (g)</small></div>
<div><strong><%= Html.escape(day.total().fatG()) %></strong><small>Fat (g)</small></div>
<div><strong><%= Html.escape(day.total().fiberG()) %></strong><small>Fiber (g)</small></div></div>
<% if (targetKcal != null) { %><p class="nf-target">Mục tiêu năng lượng hiện tại: <strong><%= Html.escape(targetKcal) %> kcal/ngày</strong>.</p>
<% } else { %><p class="nf-muted">Chưa có mục tiêu năng lượng trong hồ sơ. Bạn vẫn có thể ghi nhật ký ăn uống.</p><% } %></section>
<section class="nf-card"><h2>Ghi nhận món ăn</h2>
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
</main>
<script src="<%= Html.escape(ctx) %>/assets/js/nutrition.js" defer></script></body></html>
