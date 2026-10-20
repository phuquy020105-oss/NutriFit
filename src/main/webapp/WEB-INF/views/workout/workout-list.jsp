<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<%@ taglib prefix="fn" uri="jakarta.tags.functions" %>
<c:set var="ctx" value="${pageContext.request.contextPath}" />
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Thư viện bài tập - NutriFit</title>
  <link rel="stylesheet" href="${ctx}/assets/css/workout.css?v=${applicationScope.assetVersion}">
  <link rel="stylesheet" href="${ctx}/assets/css/workout-categories.css?v=${applicationScope.assetVersion}">
  <script src="${ctx}/assets/js/workout-categories.js?v=${applicationScope.assetVersion}" defer></script>
</head>
<body>
  <main class="nf-page" style="max-width:1160px;margin:0 auto;padding:32px 20px">
    <div class="nf-workout-actions">
      <div><p class="nf-workout-meta">NUTRIFIT / WORKOUT</p><h1>Khám phá bài tập</h1><p class="nf-workout-meta">Chọn nhóm bài tập trước khi xem danh sách.</p></div>
      <a href="${ctx}/workout/plan" class="nf-workout-badge">Xem lộ trình 7 ngày →</a>
    </div>
    <section id="nf-category-panel" class="nf-category-panel">
      <h2>Nhóm bài tập</h2>
      <c:choose>
        <c:when test="${empty categories}"><p class="nf-workout-empty">Chưa có nhóm bài tập nào.</p></c:when>
        <c:otherwise>
          <div class="nf-category-grid">
            <c:forEach var="category" items="${categories}">
              <button type="button" class="nf-category-button" data-open-category="${category.categoryId}" data-category-name="${category.categoryName}">
                <div class="nf-category-icon">🏋️</div>
                <strong><c:out value="${category.categoryName}" /></strong>
                <span>Bấm để xem các bài tập trong nhóm →</span>
              </button>
            </c:forEach>
          </div>
        </c:otherwise>
      </c:choose>
    </section>
    <section id="nf-workout-panel" class="nf-workout-panel" hidden>
      <button id="nf-back-categories" class="nf-back" type="button">← Tất cả nhóm</button>
      <h2 class="nf-workout-heading" id="nf-selected-category"></h2>
      <input id="nf-workout-search" class="nf-workout-search" type="search" placeholder="Tìm bài tập trong nhóm..." aria-label="Tìm bài tập">
      <div class="nf-workout-grid">
        <c:forEach var="w" items="${workouts}">
          <article class="nf-workout-card" data-category="${w.categoryId}" data-search="${fn:toLowerCase(w.workoutName)}">
            <span class="nf-workout-badge"><c:out value="${w.accessLevel}" /></span>
            <h3><c:out value="${w.workoutName}" /></h3>
            <p class="nf-workout-meta">Nhóm cơ: <c:out value="${w.muscleGroup}" /></p>
            <p class="nf-workout-meta">Độ khó: <c:out value="${w.difficultyLevel}" /></p>
            <p class="nf-workout-meta">${w.defaultDurationMinutes} phút · MET ${w.metValue}</p>
            <a href="${ctx}/workout/detail?id=${w.workoutId}">Xem chi tiết →</a>
          </article>
        </c:forEach>
      </div>
      <p id="nf-filter-empty" class="nf-workout-empty" hidden>Không có bài tập phù hợp trong nhóm này.</p>
    </section>
  </main>
</body>
</html>
