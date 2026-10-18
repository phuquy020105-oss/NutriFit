
<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%!
    private String escapeHtml(Object value) {
        if (value == null) return "";
        return String.valueOf(value)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;")
                .replace("'", "&#39;");
    }
%>
<%
    String contextPath = request.getContextPath();

    Object emailObj = request.getAttribute("email");
    if (emailObj == null) {
        emailObj = session.getAttribute("pendingEmail");
    }

    String email = escapeHtml(emailObj);
    String error = escapeHtml(request.getAttribute("error"));

    Object csrfObj = session.getAttribute("csrfToken");
    String csrfToken = escapeHtml(csrfObj);
%>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>Xác minh email | NutriFit</title>

    <link rel="stylesheet" href="<%= request.getContextPath() %>/assets/css/auth.css?v=2">
</head>

<body>
<div class="nf-auth-layout">
<aside class="nf-auth-brand" aria-label="Giới thiệu NutriFit">
<div class="nf-auth-mark"><span class="nf-auth-logo" aria-hidden="true">♥</span> NutriFit</div>
<div class="nf-brand-copy"><h2>Khỏe hơn mỗi ngày, bắt đầu từ hôm nay.</h2><p>Dinh dưỡng thông minh, tập luyện phù hợp và mục tiêu được cá nhân hóa cho chính bạn.</p></div>
<small>© NutriFit · Your wellness companion</small></aside>
<main class="nf-auth-main"><div class="nf-auth-eyebrow">NUTRIFIT / TÀI KHOẢN</div>


<div class="verify-card">

    <h1>Xác minh email</h1>

    <p class="description">
        Nhập mã OTP gồm 6 chữ số đã được gửi đến
        email của bạn.
    </p>

    <% if (!email.isEmpty()) { %>
        <div class="email"><%= email %></div>
    <% } %>

    <% if (!error.isEmpty()) { %>
        <div class="error-message">
            <%= error %>
        </div>
    <% } %>

    <!-- FORM XÁC MINH OTP -->
    <form method="post"
          action="<%= contextPath %>/verify-otp"
          accept-charset="UTF-8">

        <!-- CSRF TOKEN: phải nằm bên trong form -->
        <input type="hidden"
               name="_csrf"
               value="<%= csrfToken %>">

        <input
            type="text"
            name="otp"
            class="otp-input"
            placeholder="000000"
            maxlength="6"
            minlength="6"
            pattern="[0-9]{6}"
            inputmode="numeric"
            autocomplete="one-time-code"
            title="Vui lòng nhập đúng 6 chữ số OTP"
            required
            autofocus
        >

        <button type="submit" class="submit-btn">
            Xác minh và tạo tài khoản
        </button>

    </form>

    <a href="<%= contextPath %>/register"
       class="back-link">
        Quay lại đăng ký
    </a>

</div>

</main>
</div>
</body>
</html>
