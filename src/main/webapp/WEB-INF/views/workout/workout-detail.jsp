<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<%@ taglib prefix="fmt" uri="jakarta.tags.fmt" %>
<c:set var="ctx" value="${pageContext.request.contextPath}" />
<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title><c:out value="${workout.workoutName}"/> | NutriFit</title>
<link rel="stylesheet" href="${ctx}/assets/css/workout-pages.css">
</head>
<body>
<div class="layout">
<aside class="sidebar">
<a class="brand" href="${ctx}/dashboard">✳ NutriFit</a>
<div class="side-label">MENU CHÍNH</div>
<a href="${ctx}/dashboard">▦ Tổng quan</a>
<a class="active" href="${ctx}/workout">◉ Bài tập</a>
<a href="${ctx}/workout/plan">▤ Lộ trình 7 ngày</a>
<a href="${ctx}/nutrition/meal-planner">♧ Dinh dưỡng</a>
<a href="${ctx}/chatbot">✧ AI Chatbot</a>
<a href="${ctx}/payment">♛ Premium</a>
<a href="${ctx}/profile">♙ Hồ sơ</a>
</aside>
<main class="main">
<div class="eyebrow">NUTRIFIT / WORKOUT / CHI TIẾT</div>
<a class="back" href="${ctx}/workout">← Quay lại danh sách bài tập</a>
<section class="hero">
<div><span class="pill"><c:out value="${workout.accessLevel}"/></span>
<h1><c:out value="${workout.workoutName}"/></h1>
<p>Chi tiết bài tập và hướng dẫn thực hiện</p></div>
</section>
<c:if test="${not empty param.kcal}"><div class="success">✓ Đã ghi lại buổi tập. Năng lượng tiêu hao ước tính: <strong><fmt:formatNumber value="${param.kcal}" maxFractionDigits="0"/> kcal</strong></div></c:if>
<div class="stats">
<div class="stat"><small>Nhóm cơ</small><strong><c:out value="${workout.muscleGroup}"/></strong></div>
<div class="stat"><small>Độ khó</small><strong><c:out value="${workout.difficultyLevel}"/></strong></div>
<div class="stat"><small>Thời lượng</small><strong>${workout.defaultDurationMinutes} phút</strong></div>
<div class="stat"><small>MET</small><strong>${workout.metValue}</strong></div>
</div>
<div class="columns">
<div class="stack">
<section class="panel"><h2>Giới thiệu bài tập</h2><p class="multiline"><c:out value="${workout.description}"/></p>
<div class="detail-grid"><div><small>Dụng cụ</small><strong><c:out value="${workout.equipment}"/></strong></div><div><small>Mục tiêu</small><strong><c:out value="${workout.targetGoal}"/></strong></div></div></section>
<section class="panel"><h2>Hướng dẫn thực hiện</h2><p class="multiline"><c:out value="${workout.instructions}"/></p>
<c:if test="${not empty workout.videoUrl}"><c:url var="videoHref" value="${workout.videoUrl}"/><a class="btn outline" href="<c:out value='${workout.videoUrl}'/>" target="_blank" rel="noopener noreferrer">▶ Xem video hướng dẫn ↗</a></c:if>
</section>
</div>
<section class="panel record"><h2>Ghi lại buổi tập</h2><p>Hoàn thành bài tập? Lưu số phút để theo dõi tiến độ.</p>
<form method="post" action="${ctx}/workout/log">
<input type="hidden" name="workoutId" value="${workout.workoutId}">
<label for="minutes">Thời gian tập (phút)</label>
<input id="minutes" type="number" name="minutes" min="1" value="${workout.defaultDurationMinutes}" required>
<button class="btn" type="submit">✓ Ghi lại buổi tập</button>
</form>
<a class="secondary-link" href="${ctx}/workout/plan">Xem lộ trình 7 ngày →</a>
</section>
</div>
</main></div>
</body></html>
