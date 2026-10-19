<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.util.*,com.nutrifit.model.*,com.nutrifit.dto.*,com.nutrifit.util.Html" %>
<%
boolean premium = Boolean.TRUE.equals(request.getAttribute("premium"));
List<FoodPreferenceView> prefs = (List<FoodPreferenceView>) request.getAttribute("preferences");
List<FoodOption> foods = (List<FoodOption>) request.getAttribute("foods");
String csrf = (String) request.getAttribute("csrf"); String ctx = request.getContextPath();
%>
<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Sở thích thực phẩm - NutriFit</title><link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/dashboard.css">
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
<a href="<%= Html.escape(ctx) %>/nutrition/recommendations">✧ Gợi ý món ăn</a>
<a href="<%= Html.escape(ctx) %>/nutrition/history">▤ Lịch sử</a>
<a href="<%= Html.escape(ctx) %>/nutrition/preferences" class="active" aria-current="page">♡ Sở thích</a>
</nav>
<header class="nf-head"><div><h1>Sở thích nguyên liệu</h1><p>Đánh dấu nguyên liệu bạn thích hoặc không thích để cá nhân hóa gợi ý món ăn.</p></div>
<nav><a href="<%= Html.escape(ctx) %>/nutrition/meal-planner">Hôm nay</a><a href="<%= Html.escape(ctx) %>/nutrition/recommendations">Gợi ý</a></nav></header>
<% if ("saved".equals(request.getParameter("message"))) { %><p class="nf-success" role="status">Đã lưu thay đổi sở thích.</p><% } %>
<% if (!premium) { %><section class="nf-card"><h2>Sở thích nguyên liệu dành cho Premium</h2>
<p>Bạn vẫn có thể gợi ý và lưu thực đơn ba bữa với tài khoản Free. Premium cho phép quản lý LIKE/DISLIKE và cá nhân hóa theo nguyên liệu.</p>
<a href="<%= Html.escape(ctx) %>/payment">Nâng cấp Premium</a> · <a href="<%= Html.escape(ctx) %>/nutrition/recommendations">Gợi ý thực đơn</a></section>
<% } else { %><section class="nf-card"><h2>Thêm hoặc đổi sở thích</h2>
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
</tbody></table></div></section><% } %><footer class="nf-footer">© NutriFit · Sống khỏe mỗi ngày</footer></main></div></div><script src="<%= Html.escape(ctx) %>/assets/js/nutrition.js" defer></script><script>
function toggleNutritionMenu(button){
  var sidebar=document.getElementById('sidebar');
  var expanded=sidebar.classList.toggle('open');
  button.setAttribute('aria-expanded',String(expanded));
}
</script></body></html>
