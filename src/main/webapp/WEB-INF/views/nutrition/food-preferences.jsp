<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.util.*,com.nutrifit.model.*,com.nutrifit.dto.*,com.nutrifit.util.Html" %>
<%
List<FoodPreferenceView> prefs = (List<FoodPreferenceView>) request.getAttribute("preferences");
List<FoodOption> foods = (List<FoodOption>) request.getAttribute("foods");
String csrf = (String) request.getAttribute("csrf"); String ctx = request.getContextPath();
%>
<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sở thích thực phẩm - NutriFit</title><link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/meal-planner.css"></head>
<body class="nf-page"><main class="nf-wrap"><header class="nf-head"><div><h1>Sở thích nguyên liệu</h1><p>Đánh dấu nguyên liệu bạn thích hoặc không thích để cá nhân hóa gợi ý món ăn.</p></div>
<nav><a href="<%= Html.escape(ctx) %>/nutrition/meal-planner">Hôm nay</a><a href="<%= Html.escape(ctx) %>/nutrition/recommendations">Gợi ý</a></nav></header>
<% if ("saved".equals(request.getParameter("message"))) { %><p class="nf-success" role="status">Đã lưu thay đổi sở thích.</p><% } %>
<section class="nf-card"><h2>Thêm hoặc đổi sở thích</h2>
<% if(foods.isEmpty()) { %><p>Chưa có nguyên liệu hoạt động trong hệ thống.</p><% } else { %>
<form method="post" action="<%= Html.escape(ctx) %>/nutrition/preferences" class="nf-form">
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="action" value="save">
<label>Nguyên liệu<select name="foodId" required><% for(FoodOption f:foods){ %>
<option value="<%= f.foodId() %>"><%= Html.escape(f.name()) %></option><% } %></select></label>
<label>Mức độ<select name="type"><option value="LIKE">Thích (LIKE)</option><option value="DISLIKE">Không thích (DISLIKE)</option></select></label>
<button type="submit">Lưu</button></form><% } %></section>
<section class="nf-card"><h2>Đã lưu</h2><div class="nf-table-scroll"><table><thead><tr><th>Nguyên liệu</th><th>Trạng thái</th><th>Cập nhật</th><th>Thao tác</th></tr></thead><tbody>
<% for(FoodPreferenceView p:prefs){ %><tr><td><%= Html.escape(p.foodName()) %><% if(!p.active()){ %><small class="nf-muted nf-block">Nguyên liệu hiện ngừng sử dụng</small><% } %></td>
<td><%= p.type()==FoodPreference.PreferenceType.LIKE?"Thích":"Không thích" %></td><td><%= Html.escape(p.updatedAt()) %></td>
<td><% if(p.active()){ %><form method="post" action="<%= Html.escape(ctx) %>/nutrition/preferences" class="nf-action">
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="action" value="save">
<input type="hidden" name="foodId" value="<%= p.foodId() %>"><input type="hidden" name="type" value="<%= p.type()==FoodPreference.PreferenceType.LIKE?"DISLIKE":"LIKE" %>">
<button type="submit" class="nf-small"><%= p.type()==FoodPreference.PreferenceType.LIKE?"Đổi sang không thích":"Đổi sang thích" %></button></form><% } %>
<form method="post" action="<%= Html.escape(ctx) %>/nutrition/preferences" class="nf-action" data-confirm="Bỏ sở thích đã lưu cho nguyên liệu này?">
<input type="hidden" name="csrfToken" value="<%= Html.escape(csrf) %>"><input type="hidden" name="action" value="delete">
<input type="hidden" name="foodId" value="<%= p.foodId() %>"><button class="nf-danger nf-small" type="submit">Bỏ đánh dấu</button></form></td></tr><% } %>
<% if(prefs.isEmpty()) { %><tr><td colspan="4">Chưa có sở thích.</td></tr><% } %>
</tbody></table></div></section></main><script src="<%= Html.escape(ctx) %>/assets/js/nutrition.js" defer></script></body></html>
