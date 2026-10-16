<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.util.*,com.nutrifit.model.*,com.nutrifit.dto.*,com.nutrifit.util.Html" %>
<%
List<MealPlan> history = (List<MealPlan>) request.getAttribute("history");
DaySummary selected = (DaySummary) request.getAttribute("selected");
String ctx = request.getContextPath();
%>
<!DOCTYPE html><html lang="vi"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Lịch sử ăn uống - NutriFit</title><link rel="stylesheet" href="<%= Html.escape(ctx) %>/assets/css/meal-planner.css"></head>
<body><main class="nf-wrap"><header class="nf-head"><div><h1>Lịch sử ăn uống</h1><p>Chỉ xem, không chỉnh sửa được dữ liệu ngày trước.</p></div>
<nav><a href="<%= Html.escape(ctx) %>/nutrition/meal-planner">Hôm nay</a><a href="<%= Html.escape(ctx) %>/nutrition/preferences">Sở thích</a></nav></header>
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
<% for(MealEntry e:selected.entries()) { %><tr><td><%= Html.escape(e.getMealType()) %></td>
<td><%= Html.escape(e.getRecipeNameSnapshot()) %></td><td><%= Html.escape(e.getServings()) %></td>
<td><%= Html.escape(e.getCaloriesKcal()) %></td><td><%= Html.escape(e.getProteinG()) %></td><td><%= Html.escape(e.getCarbsG()) %></td>
<td><%= Html.escape(e.getFatG()) %></td><td><%= Html.escape(e.getFiberG()) %></td></tr><% } %>
<% if(selected.entries().isEmpty()) { %><tr><td colspan="8">Không có món ăn.</td></tr><% } %></tbody></table></div>
</section><% } %></main></body></html>
