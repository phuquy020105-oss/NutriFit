<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.util.*,com.nutrifit.model.*,com.nutrifit.dto.*,com.nutrifit.util.Html" %>
<%
Boolean premium = (Boolean) request.getAttribute("premium");
MealEntry.MealType type = (MealEntry.MealType) request.getAttribute("mealType");
List<RecommendedRecipe> recommendations = (List<RecommendedRecipe>) request.getAttribute("recommendations");
String ctx = request.getContextPath();
String csrf = (String) request.getAttribute("csrf");
%>
<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gợi ý món ăn - NutriFit</title><link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/meal-planner.css"></head>
<body class="nf-page"><main class="nf-wrap"><header class="nf-head"><div><h1>Gợi ý món ăn cá nhân hóa</h1><p>Loại trừ nguyên liệu không thích; ưu tiên nguyên liệu bạn thích và gần mục tiêu năng lượng.</p></div>
<nav><a href="<%= Html.escape(ctx) %>/nutrition/meal-planner">Hôm nay</a><a href="<%= Html.escape(ctx) %>/nutrition/preferences">Sở thích</a></nav></header>
<% if (!Boolean.TRUE.equals(premium)) { %><section class="nf-card"><h2>Cần Premium</h2>
<p>Tài khoản hiện chưa có quyền truy cập gợi ý Premium. Bạn vẫn có thể ghi nhật ký và quản lý sở thích ăn uống.</p></section>
<% } else { %><section class="nf-card"><form method="get" action="<%= Html.escape(ctx) %>/nutrition/recommendations" class="nf-form">
<label>Bữa ăn<select name="mealType"><% for(MealEntry.MealType t:MealEntry.MealType.values()) { %>
<option value="<%= t.name() %>" <%= t==type?"selected":"" %>><%= t==MealEntry.MealType.BREAKFAST?"Sáng":t==MealEntry.MealType.LUNCH?"Trưa":"Tối" %></option>
<% } %></select></label><button type="submit">Gợi ý</button></form></section>
<section class="nf-card"><h2>Món được đề xuất</h2>
<% if(recommendations == null || recommendations.isEmpty()) { %><p>Chưa có công thức phù hợp với sở thích và bữa ăn này.</p><% } else { %>
<div class="nf-table-scroll"><table><thead><tr><th>Công thức</th><th>Kcal / khẩu phần</th><th>Protein (g)</th><th>Carbs (g)</th><th>Fat (g)</th><th>Fiber (g)</th><th>Lý do</th><th>Ghi nhận</th></tr></thead><tbody>
<% for(RecommendedRecipe r: recommendations) { %><tr><td><%= Html.escape(r.recipe().name()) %></td>
<td><%= Html.escape(r.recipe().perServing().caloriesKcal()) %></td>
<td><%= Html.escape(r.recipe().perServing().proteinG()) %></td><td><%= Html.escape(r.recipe().perServing().carbsG()) %></td>
<td><%= Html.escape(r.recipe().perServing().fatG()) %></td><td><%= Html.escape(r.recipe().perServing().fiberG()) %></td>
<td><%= Html.escape(r.reason()) %></td><td>
<form method="post" action="<%= Html.escape(ctx) %>/nutrition/meal-planner" class="nf-edit-form">
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="action" value="add">
<input type="hidden" name="recipeId" value="<%= r.recipe().recipeId() %>"><input type="hidden" name="mealType" value="<%= r.recipe().mealType().name() %>">
<label>Khẩu phần<input type="number" name="servings" min="0.01" max="999999.99" step="0.01" value="1" required></label>
<button type="submit" class="nf-small">Ghi nhận đã ăn</button></form></td></tr><% } %></tbody></table></div><% } %>
<p class="nf-muted">Ghi nhận sẽ thêm món vào nhật ký hôm nay. Nếu đã có món trong cùng bữa, khẩu phần được cộng thêm. Chỉ xem gợi ý không thay đổi nhật ký.</p>
<p class="nf-muted">Đây là gợi ý theo quy tắc đơn giản, không thay thế tư vấn dinh dưỡng chuyên môn.</p></section><% } %>
</main></body></html>
