
<%@ page contentType="text/html; charset=UTF-8"
         pageEncoding="UTF-8" %>

<%!
    private String escapeHtml(Object value) {
        if (value == null) return "";

        return value.toString()
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace("\"", "&quot;")
                .replace("'", "&#39;");
    }
%>

<!DOCTYPE html>
<html lang="vi">

<head>
    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1">

    <title>Đăng ký tài khoản | NutriFit</title>

    <link rel="stylesheet" href="<%= request.getContextPath() %>/assets/css/auth.css?v=${applicationScope.assetVersion}">
</head>

<body>
<div class="nf-auth-layout">
<aside class="nf-auth-brand" aria-label="Giới thiệu NutriFit">
<div class="nf-auth-mark"><span class="nf-auth-logo" aria-hidden="true">♥</span> NutriFit</div>
<div class="nf-brand-copy"><h2>Khỏe hơn mỗi ngày, bắt đầu từ hôm nay.</h2><p>Dinh dưỡng thông minh, tập luyện phù hợp và mục tiêu được cá nhân hóa cho chính bạn.</p></div>
<small>© NutriFit · Your wellness companion</small></aside>
<main class="nf-auth-main"><div class="nf-auth-eyebrow">NUTRIFIT / TÀI KHOẢN</div>


<div class="register-box">

    <h1>NutriFit</h1>

    <p class="subtitle">
        Đăng ký tài khoản để bắt đầu
        hành trình chăm sóc sức khỏe
    </p>

    <%
        Object error = request.getAttribute("error");
    %>

    <% if (error != null) { %>
        <div class="error">
            <%= escapeHtml(error) %>
        </div>
    <% } %>

    <!-- FORM ĐĂNG KÝ -->
    <form
        method="post"
        action="<%= request.getContextPath() %>/register"
        accept-charset="UTF-8"
    >

        <!-- CSRF TOKEN -->
        <input
            type="hidden"
            name="_csrf"
            value="<%= escapeHtml(
                session.getAttribute("csrfToken")
            ) %>"
        >

        <!-- HỌ VÀ TÊN -->
        <label for="fullName">
            Họ và tên
        </label>

        <input
            id="fullName"
            type="text"
            name="fullName"
            placeholder="Nhập họ và tên"
            value="<%= escapeHtml(
                request.getAttribute("fullName")
            ) %>"
            maxlength="150"
            autocomplete="name"
            required
        >

        <!-- EMAIL -->
        <label for="email">
            Địa chỉ email
        </label>

        <input
            id="email"
            type="email"
            name="email"
            placeholder="example@gmail.com"
            value="<%= escapeHtml(
                request.getAttribute("email")
            ) %>"
            maxlength="255"
            autocomplete="email"
            required
        >

        <!-- MẬT KHẨU -->
        <label for="password">
            Mật khẩu
        </label>

        <input
            id="password"
            type="password"
            name="password"
            placeholder="Tối thiểu 8 ký tự"
            minlength="8"
            maxlength="72"
            autocomplete="new-password"
            required
        >

        <!-- NÚT ĐĂNG KÝ -->
        <button type="submit">
            Đăng ký và nhận OTP
        </button>

    </form>

    <div class="footer">
        Đã có tài khoản?

        <a href="<%= request.getContextPath() %>/login">
            Đăng nhập
        </a>
    </div>

</div>

</main>
</div>
</body>
</html>
