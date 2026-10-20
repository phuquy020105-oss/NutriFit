<%@ taglib prefix="c" uri="jakarta.tags.core" %>

<%@ page contentType="text/html; charset=UTF-8"
         pageEncoding="UTF-8" %>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1">
    <title>Quên mật khẩu - NutriFit</title>
    <link rel="stylesheet" href="<%= request.getContextPath() %>/assets/css/auth.css?v=${applicationScope.assetVersion}">
</head>
<body>
<div class="nf-auth-layout">
<aside class="nf-auth-brand" aria-label="Giới thiệu NutriFit">
<div class="nf-auth-mark"><span class="nf-auth-logo" aria-hidden="true">♥</span> NutriFit</div>
<div class="nf-brand-copy"><h2>Khỏe hơn mỗi ngày, bắt đầu từ hôm nay.</h2><p>Dinh dưỡng thông minh, tập luyện phù hợp và mục tiêu được cá nhân hóa cho chính bạn.</p></div>
<small>© NutriFit · Your wellness companion</small></aside>
<main class="nf-auth-main"><div class="nf-auth-eyebrow">NUTRIFIT / TÀI KHOẢN</div>

<div class="card">
    <h2>Quên mật khẩu</h2>
    <p>Nhập email đã đăng ký để nhận mã OTP và đặt lại mật khẩu.</p>

    <c:if test="${not empty error}">
        <p class="error" role="alert"><c:out value="${error}"/></p>
    </c:if>
    <c:if test="${not empty success}">
        <p class="success" role="status"><c:out value="${success}"/></p>
    </c:if>

    <form method="post" action="${pageContext.request.contextPath}/forgot-password">
        <input type="hidden" name="_csrf" value="${sessionScope.csrfToken}">

        <input type="email" name="email"
               placeholder="Email của bạn" required>

        <button type="submit">Gửi mã OTP</button>
    </form>

    <p>
        <a href="${pageContext.request.contextPath}/reset-password">
            Đã có mã OTP? Đặt lại mật khẩu
        </a>
    </p>
    <p>
        <a href="${pageContext.request.contextPath}/login">
            Quay lại đăng nhập
        </a>
    </p>
</div>
</main>
</div>
</body>
</html>
