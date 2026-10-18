<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<%@ taglib prefix="fmt" uri="jakarta.tags.fmt" %>
<c:set var="ctx" value="${pageContext.request.contextPath}" />
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title><c:out value="${workout.workoutName}" /></title>
    <link rel="stylesheet" href="${ctx}/assets/css/workout.css">
</head>
<body>
    <p><a href="${ctx}/workout">&larr; Quay lại danh sách</a></p>

    <h1><c:out value="${workout.workoutName}" /></h1>

    <%-- Hiện sau khi ghi log (Servlet redirect kèm ?kcal=...) --%>
    <c:if test="${not empty param.kcal}">
        <p><strong>Đã ghi log. Ước tính tiêu hao:
            <fmt:formatNumber value="${param.kcal}" maxFractionDigits="0" /> kcal</strong></p>
    </c:if>

    <ul>
        <li>Nhóm cơ: <c:out value="${workout.muscleGroup}" /></li>
        <li>Độ khó: <c:out value="${workout.difficultyLevel}" /></li>
        <li>Dụng cụ: <c:out value="${workout.equipment}" /></li>
        <li>Mục tiêu: <c:out value="${workout.targetGoal}" /></li>
        <li>MET: ${workout.metValue}</li>
        <li>Thời lượng mặc định: ${workout.defaultDurationMinutes} phút</li>
        <li>Gói: <c:out value="${workout.accessLevel}" /></li>
    </ul>

    <h3>Mô tả</h3>
    <p><c:out value="${workout.description}" /></p>

    <h3>Hướng dẫn</h3>
    <p><c:out value="${workout.instructions}" /></p>

    <c:if test="${not empty workout.videoUrl}">
        <p><a href="<c:out value='${workout.videoUrl}' />" target="_blank" rel="noopener">Xem video</a></p>
    </c:if>

    <h3>Ghi lại buổi tập</h3>
    <form method="post" action="${ctx}/workout/log">
        <input type="hidden" name="workoutId" value="${workout.workoutId}">
        <label>Số phút:
            <input type="number" name="minutes" min="1"
                   value="${workout.defaultDurationMinutes}" required>
        </label>
        <button type="submit">Ghi log</button>
    </form>
</body>
</html>