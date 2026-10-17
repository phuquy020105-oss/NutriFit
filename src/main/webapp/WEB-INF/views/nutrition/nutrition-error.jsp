<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="com.nutrifit.util.Html" %>
<% String ctx = request.getContextPath(); %>
<!DOCTYPE html>
<html lang="vi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Không thể hoàn tất yêu cầu - NutriFit</title>
<link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/meal-planner.css"></head>
<body class="nf-page"><main class="nf-wrap">
<section class="nf-card"><h1>Không thể hoàn tất yêu cầu</h1>
<p class="nf-error" role="alert"><%= Html.escape(request.getAttribute("errorMessage")) %></p>
<p>Mã phản hồi: <%= Html.escape(request.getAttribute("errorStatus")) %></p>
<nav aria-label="Quay lại Nutrition">
<a href="<%= Html.escape(ctx) %>/nutrition/meal-planner">Nhật ký hôm nay</a>
<a href="<%= Html.escape(ctx) %>/nutrition/history">Lịch sử</a>
<a href="<%= Html.escape(ctx) %>/nutrition/preferences">Sở thích</a>
<a href="<%= Html.escape(ctx) %>/nutrition/recommendations">Gợi ý</a>
</nav></section></main></body></html>
