<%@ page contentType="text/html;charset=UTF-8" pageEncoding="UTF-8" %>
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<%@ taglib prefix="fmt" uri="jakarta.tags.fmt" %>
<c:set var="ctx" value="${pageContext.request.contextPath}" />
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Lộ trình tập</title>
    <link rel="stylesheet" href="${ctx}/assets/css/workout.css">
</head>
<body>
    <p><a href="${ctx}/workout">&larr; Danh sách bài tập</a></p>
    <h1>Lộ trình tập 7 ngày</h1>

    <form method="post" action="${ctx}/workout/plan/generate">
        <button type="submit">
            <c:choose>
                <c:when test="${empty plan}">Tạo lộ trình</c:when>
                <c:otherwise>Tạo lộ trình mới (thay lộ trình hiện tại)</c:otherwise>
            </c:choose>
        </button>
    </form>

    <c:if test="${empty plan}">
        <p>Bạn chưa có lộ trình nào.</p>
    </c:if>

    <c:if test="${not empty plan}">
        <h2><c:out value="${plan.plan.planName}" /></h2>
        <p>${plan.plan.startDate} &rarr; ${plan.plan.endDate}</p>

        <c:forEach var="dayView" items="${plan.days}">
            <hr>
            <h3>
                <c:out value="${dayView.day.dayName}" /> -
                <c:out value="${dayView.day.focusArea}" />
            </h3>

            <c:if test="${dayView.day.restDay}">
                <p><em>Ngày nghỉ</em></p>
            </c:if>

            <c:if test="${not dayView.day.restDay}">
                <table border="1" cellpadding="6">
                    <thead>
                        <tr><th>Bài tập</th><th>Thời lượng</th><th>Calo (ước tính)</th><th></th></tr>
                    </thead>
                    <tbody>
                        <c:forEach var="item" items="${dayView.items}">
                            <tr>
                                <td><c:out value="${item.workoutName}" /></td>
                                <td>
                                    <form method="post" action="${ctx}/workout/plan/duration">
                                        <input type="hidden" name="detailId" value="${item.detail.detailId}">
                                        <input type="number" name="minutes" min="1" style="width:70px"
                                               value="${item.detail.durationMinutes}" required> phút
                                        <button type="submit">Lưu</button>
                                    </form>
                                </td>
                                <td><fmt:formatNumber value="${item.calories}" maxFractionDigits="0" /> kcal</td>
                                <td>
                                    <form method="post" action="${ctx}/workout/plan/remove">
                                        <input type="hidden" name="detailId" value="${item.detail.detailId}">
                                        <button type="submit">Xoá</button>
                                    </form>
                                </td>
                            </tr>
                        </c:forEach>
                    </tbody>
                </table>

                <p>Tổng ngày:
                    <strong><fmt:formatNumber value="${dayView.totalCalories}" maxFractionDigits="0" /> kcal</strong>
                </p>

                <form method="post" action="${ctx}/workout/plan/add">
                    <input type="hidden" name="dayId" value="${dayView.day.planDayId}">
                    <select name="workoutId" required>
                        <c:forEach var="w" items="${workouts}">
                            <option value="${w.workoutId}"><c:out value="${w.workoutName}" /></option>
                        </c:forEach>
                    </select>
                    <input type="number" name="minutes" min="1" value="30" style="width:70px" required> phút
                    <button type="submit">Thêm bài</button>
                </form>
            </c:if>
        </c:forEach>
    </c:if>
</body>
</html>