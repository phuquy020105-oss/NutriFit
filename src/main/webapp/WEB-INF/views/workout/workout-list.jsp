<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<c:set var="ctx" value="${pageContext.request.contextPath}" />
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Bài tập</title>
    <link rel="stylesheet" href="${ctx}/assets/css/workout.css">
</head>
<body>
    <h1>Danh sách bài tập</h1>
    <p><a href="${ctx}/workout/plan">Xem lộ trình tập của tôi</a></p>

    <c:if test="${empty workouts}">
        <p>Chưa có bài tập nào.</p>
    </c:if>

    <table border="1" cellpadding="6">
        <thead>
            <tr>
                <th>Tên bài</th>
                <th>Nhóm cơ</th>
                <th>Độ khó</th>
                <th>MET</th>
                <th>Thời lượng mặc định</th>
                <th>Gói</th>
            </tr>
        </thead>
        <tbody>
            <c:forEach var="w" items="${workouts}">
                <tr>
                    <td>
                        <a href="${ctx}/workout/detail?id=${w.workoutId}">
                            <c:out value="${w.workoutName}" />
                        </a>
                    </td>
                    <td><c:out value="${w.muscleGroup}" /></td>
                    <td><c:out value="${w.difficultyLevel}" /></td>
                    <td>${w.metValue}</td>
                    <td>${w.defaultDurationMinutes} phút</td>
                    <td><c:out value="${w.accessLevel}" /></td>
                </tr>
            </c:forEach>
        </tbody>
    </table>
</body>
</html>