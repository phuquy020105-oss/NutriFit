
<%@ page contentType="text/html; charset=UTF-8"
         pageEncoding="UTF-8" %>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1">
    <title>Đặt lại mật khẩu - NutriFit</title>
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
    <h2>Đặt lại mật khẩu</h2>
    <p>Nhập OTP đã nhận và mật khẩu mới.</p>

    <p class="error">${error}</p>

    <form method="post" action="${pageContext.request.contextPath}/reset-password">
        <input type="hidden" name="_csrf" value="${sessionScope.csrfToken}">

        <input type="email" name="email"
               placeholder="Email đã đăng ký" required>

        <input type="text" name="otp"
               placeholder="Mã OTP 6 chữ số"
               pattern="[0-9]{6}" maxlength="6"
               inputmode="numeric" required>

        <input type="password" name="password"
               placeholder="Mật khẩu mới (ít nhất 8 ký tự)"
               minlength="8" required>

        <input type="password" name="confirmPassword"
               placeholder="Xác nhận mật khẩu mới"
               minlength="8" required>

        <button type="submit">Đổi mật khẩu</button>
    </form>

    <p>
        <a href="${pageContext.request.contextPath}/forgot-password">
            Gửi lại mã OTP
        </a>
    </p>
</div>
</main>
</div>
</body>
</html>
