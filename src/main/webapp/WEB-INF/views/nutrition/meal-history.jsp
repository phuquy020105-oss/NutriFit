<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.util.*,com.nutrifit.model.*,com.nutrifit.dto.*,com.nutrifit.util.Html" %>
<%
List<MealPlan> history = (List<MealPlan>) request.getAttribute("history");
DaySummary selected = (DaySummary) request.getAttribute("selected");
String ctx = request.getContextPath();
%>
<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lịch sử ăn uống - NutriFit</title><link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/dashboard.css">
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
<a href="<%= Html.escape(ctx) %>/nutrition/recommendations">◉ Thực đơn</a>
<a href="<%= Html.escape(ctx) %>/nutrition/history" class="active" aria-current="page">▤ Lịch sử</a>
<a href="<%= Html.escape(ctx) %>/nutrition/preferences">♡ Sở thích</a>
</nav>
<header class="nf-head"><div><h1>Lịch sử ăn uống</h1><p>Chỉ xem, không chỉnh sửa được dữ liệu ngày trước.</p></div>
</header>
<section class="nf-card"><h2>Xem theo ngày</h2>
<form method="get" action="<%= Html.escape(ctx) %>/nutrition/history" class="nf-form">
<label>Ngày đã qua<input type="date" name="date" min="1000-01-01" max="<%= Html.escape(request.getAttribute("latestDate")) %>" value="<%= selected==null?"":Html.escape(selected.date()) %>" required></label>
<button type="submit">Xem nhật ký</button></form>
<p class="nf-muted">Có thể chọn ngày cũ hơn danh sách bên dưới. Ngày chưa ghi nhận sẽ hiển thị tổng bằng 0.</p></section>
<section class="nf-card"><h2>30 ngày có nhật ký gần nhất</h2>
<% if(history.isEmpty()) { %><p>Chưa có ngày nào trong lịch sử.</p><% } else { %><ul class="nf-dates">
<% for(MealPlan p:history) { %><li><a href="<%= Html.escape(ctx) %>/nutrition/history?date=<%= Html.escape(p.getPlanDate()) %>"><%= Html.escape(p.getPlanDate()) %></a></li><% } %></ul><% } %></section>
<% if(selected != null) { %><section class="nf-card"><h2>Ngày <%= Html.escape(selected.date()) %></h2>
<div class="nf-stats"><div><strong><%= Html.escape(selected.total().caloriesKcal()) %></strong><small>kcal</small></div>
<div><strong><%= Html.escape(selected.total().proteinG()) %></strong><small>Protein (g)</small></div>
<div><strong><%= Html.escape(selected.total().carbsG()) %></strong><small>Carbs (g)</small></div>
<div><strong><%= Html.escape(selected.total().fatG()) %></strong><small>Fat (g)</small></div>
<div><strong><%= Html.escape(selected.total().fiberG()) %></strong><small>Fiber (g)</small></div></div>
<div class="nf-table-scroll"><table><thead><tr><th>Bữa</th><th>Món đã ghi nhận</th><th>Khẩu phần</th><th>Kcal</th><th>Protein</th><th>Carbs</th><th>Fat</th><th>Fiber</th></tr></thead><tbody>
<% for(MealEntry e:selected.entries()) { %><tr><td><%= e.getMealType()==MealEntry.MealType.BREAKFAST?"Sáng":e.getMealType()==MealEntry.MealType.LUNCH?"Trưa":"Tối" %></td>
<td><%= Html.escape(e.getRecipeNameSnapshot()) %></td><td><%= Html.escape(e.getServings()) %></td>
<td><%= Html.escape(e.getCaloriesKcal()) %></td><td><%= Html.escape(e.getProteinG()) %></td><td><%= Html.escape(e.getCarbsG()) %></td>
<td><%= Html.escape(e.getFatG()) %></td><td><%= Html.escape(e.getFiberG()) %></td></tr><% } %>
<% if(selected.entries().isEmpty()) { %><tr><td colspan="8">Không có món ăn.</td></tr><% } %></tbody></table></div>
</section><% } %><footer class="nf-footer">© NutriFit · Sống khỏe mỗi ngày</footer></main></div></div><script>
function toggleNutritionMenu(button){
  var sidebar=document.getElementById('sidebar');
  var expanded=sidebar.classList.toggle('open');
  button.setAttribute('aria-expanded',String(expanded));
}
</script></body></html>
