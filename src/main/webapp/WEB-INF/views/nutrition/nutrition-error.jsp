<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="com.nutrifit.util.Html" %>
<% String ctx = request.getContextPath(); %>
<!DOCTYPE html>
<html lang="vi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Không thể hoàn tất yêu cầu - NutriFit</title>
<link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/dashboard.css?v=${applicationScope.assetVersion}">
<link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/nutrition.css?v=${applicationScope.assetVersion}"></head>
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
<a href="<%= Html.escape(ctx) %>/nutrition/history">▤ Lịch sử</a>
<a href="<%= Html.escape(ctx) %>/nutrition/preferences">♡ Sở thích</a>
</nav>

<section class="nf-card"><h1>Không thể hoàn tất yêu cầu</h1>
<p class="nf-error" role="alert"><%= Html.escape(request.getAttribute("errorMessage")) %></p>
<p>Mã phản hồi: <%= Html.escape(request.getAttribute("errorStatus")) %></p>
<nav aria-label="Quay lại Nutrition">
<a href="<%= Html.escape(ctx) %>/nutrition/recommendations">Thực đơn</a>
<a href="<%= Html.escape(ctx) %>/nutrition/history">Lịch sử</a>
<a href="<%= Html.escape(ctx) %>/nutrition/preferences">Sở thích</a>
</nav></section><footer class="nf-footer">© NutriFit · Sống khỏe mỗi ngày</footer></main></div></div><script>
function toggleNutritionMenu(button){
  var sidebar=document.getElementById('sidebar');
  var expanded=sidebar.classList.toggle('open');
  button.setAttribute('aria-expanded',String(expanded));
}
</script></body></html>
