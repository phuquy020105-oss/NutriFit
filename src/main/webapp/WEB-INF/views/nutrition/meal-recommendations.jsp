<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.util.*,com.nutrifit.model.*,com.nutrifit.dto.*,com.nutrifit.util.Html" %>
<%
Boolean premium = (Boolean) request.getAttribute("premium");
MealEntry.MealType type = (MealEntry.MealType) request.getAttribute("mealType");
List<RecommendedRecipe> recommendations = (List<RecommendedRecipe>) request.getAttribute("recommendations");
String ctx = request.getContextPath();
%>
<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Gợi ý món ăn - NutriFit</title><link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/meal-planner.css"></head>
<body><main class="nf-wrap"><header class="nf-head"><div><h1>Gợi ý món ăn cá nhân hóa</h1><p>Loại trừ nguyên liệu DISLIKE; ưu tiên nguyên liệu LIKE và gần mục tiêu năng lượng.</p></div>
<nav><a href="<%= Html.escape(ctx) %>/nutrition/meal-planner">Hôm nay</a><a href="<%= Html.escape(ctx) %>/nutrition/preferences">Sở thích</a></nav></header>
<% if (!Boolean.TRUE.equals(premium)) { %><section class="nf-card"><h2>Cần Premium</h2>
<p>Tài khoản hiện chưa có quyền truy cập gợi ý Premium. Chức năng kiểm tra quyền sẽ được kết nối chính thức với module Payment của nhóm.</p></section>
<% } else { %><section class="nf-card"><form method="get" action="<%= Html.escape(ctx) %>/nutrition/recommendations" class="nf-form">
<label>Bữa ăn<select name="mealType"><% for(MealEntry.MealType t:MealEntry.MealType.values()) { %>
<option value="<%= t.name() %>" <%= t==type?"selected":"" %>><%= t==MealEntry.MealType.BREAKFAST?"Sáng":t==MealEntry.MealType.LUNCH?"Trưa":"Tối" %></option>
<% } %></select></label><button type="submit">Gợi ý</button></form></section>
<section class="nf-card"><h2>Món được đề xuất</h2>
<% if(recommendations == null || recommendations.isEmpty()) { %><p>Chưa có công thức phù hợp với sở thích và bữa ăn này.</p><% } else { %>
<div class="nf-table-scroll"><table><thead><tr><th>Công thức</th><th>Kcal / khẩu phần</th><th>Protein</th><th>Carbs</th><th>Fat</th><th>Fiber</th><th>Lý do</th></tr></thead><tbody>
<% for(RecommendedRecipe r: recommendations) { %><tr><td><%= Html.escape(r.recipe().name()) %></td>
<td><%= Html.escape(r.recipe().perServing().caloriesKcal()) %></td>
<td><%= Html.escape(r.recipe().perServing().proteinG()) %></td><td><%= Html.escape(r.recipe().perServing().carbsG()) %></td>
<td><%= Html.escape(r.recipe().perServing().fatG()) %></td><td><%= Html.escape(r.recipe().perServing().fiberG()) %></td>
<td><%= Html.escape(r.reason()) %></td></tr><% } %></tbody></table></div><% } %>
<p class="nf-muted">Đây là gợi ý theo quy tắc đơn giản, không thay thế tư vấn dinh dưỡng chuyên môn.</p></section><% } %>
</main></body></html>
