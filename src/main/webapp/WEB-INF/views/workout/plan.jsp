<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<%@ taglib prefix="fmt" uri="jakarta.tags.fmt" %>
<c:set var="ctx" value="${pageContext.request.contextPath}" />
<!DOCTYPE html><html lang="vi"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Lộ trình 7 ngày | NutriFit</title>
<link rel="stylesheet" href="${ctx}/assets/css/workout-pages.css">
</head><body><div class="layout">
<aside class="sidebar">
<a class="brand" href="${ctx}/dashboard">✳ NutriFit</a>
<div class="side-label">MENU CHÍNH</div>
<a href="${ctx}/dashboard">▦ Tổng quan</a>
<a href="${ctx}/workout">◉ Bài tập</a>
<a class="active" href="${ctx}/workout/plan">▤ Lịch tập</a>
<a href="${ctx}/nutrition/meal-planner">♧ Dinh dưỡng</a>
<a href="${ctx}/chatbot">✧ AI Chatbot</a>
<a href="${ctx}/payment">♛ Premium</a>
<a href="${ctx}/profile">♙ Hồ sơ</a>
<%@ include file="/WEB-INF/views/shared/admin-navigation.jspf" %>
</aside>
<main class="main">
<div class="eyebrow">NUTRIFIT / WORKOUT / LỘ TRÌNH</div>
<a class="back" href="${ctx}/workout">← Quay lại danh sách bài tập</a>
<section class="hero plan-hero"><div><span class="pill">KẾ HOẠCH LUYỆN TẬP</span><h1>Lộ trình tập 7 ngày</h1><p>Xây dựng và điều chỉnh kế hoạch phù hợp với bạn</p></div>
<form method="post" action="${ctx}/workout/plan/generate"><button class="btn light" type="submit"><c:choose><c:when test="${empty plan}">+ Tạo lộ trình</c:when><c:otherwise>↻ Tạo lộ trình mới</c:otherwise></c:choose></button></form>
</section>
<c:choose><c:when test="${empty plan}">
<section class="panel empty"><div class="empty-icon">▤</div><h2>Bạn chưa có lộ trình nào</h2><p>Nhấn “Tạo lộ trình” để bắt đầu kế hoạch 7 ngày.</p></section>
</c:when><c:otherwise>
<section class="plan-heading"><div><h2><c:out value="${plan.plan.planName}"/></h2><p><c:out value="${plan.plan.startDate}"/> → <c:out value="${plan.plan.endDate}"/></p></div></section>
<div class="day-grid">
<c:forEach var="dayView" items="${plan.days}">
<section class="panel day-card">
<div class="day-top"><div><span class="day-caption">NGÀY TẬP LUYỆN</span><h2><c:out value="${dayView.day.dayName}"/></h2><p><c:out value="${dayView.day.focusArea}"/></p></div>
<c:choose><c:when test="${dayView.day.restDay}"><span class="rest-badge">Ngày nghỉ</span></c:when><c:otherwise><span class="pill green">Tập luyện</span></c:otherwise></c:choose></div>
<c:choose><c:when test="${dayView.day.restDay}"><div class="rest-content">☘ Hôm nay là ngày nghỉ. Hãy dành thời gian phục hồi.</div></c:when><c:otherwise>
<div class="exercise-list">
<c:forEach var="item" items="${dayView.items}">
<div class="exercise">
<div class="exercise-title"><strong><c:out value="${item.workoutName}"/></strong><span><fmt:formatNumber value="${item.calories}" maxFractionDigits="0"/> kcal</span></div>
<div class="exercise-actions">
<form method="post" action="${ctx}/workout/plan/duration">
<input type="hidden" name="detailId" value="${item.detail.detailId}">
<label>Phút <input aria-label="Thời lượng bài tập" type="number" name="minutes" min="1" value="${item.detail.durationMinutes}" required></label>
<button class="btn small" type="submit">Lưu</button>
</form>
<form method="post" action="${ctx}/workout/plan/remove">
<input type="hidden" name="detailId" value="${item.detail.detailId}">
<button class="btn danger small" type="submit">Xóa</button>
</form>
</div></div>
</c:forEach>
</div>
<div class="total">Tổng năng lượng ngày <strong><fmt:formatNumber value="${dayView.totalCalories}" maxFractionDigits="0"/> kcal</strong></div>
<form class="add-form" method="post" action="${ctx}/workout/plan/add">
<input type="hidden" name="dayId" value="${dayView.day.planDayId}">
<label>Thêm bài tập
<select name="workoutId" required><c:forEach var="w" items="${workouts}"><option value="${w.workoutId}"><c:out value="${w.workoutName}"/></option></c:forEach></select></label>
<label>Phút <input type="number" name="minutes" min="1" value="30" required></label>
<button class="btn" type="submit">+ Thêm bài</button>
</form>
</c:otherwise></c:choose>
</section>
</c:forEach>
</div>
</c:otherwise></c:choose>
</main></div></body></html>
