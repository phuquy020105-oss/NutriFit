
<%@ page contentType="text/html; charset=UTF-8"
         pageEncoding="UTF-8" %>

<%!
    // Escape dữ liệu trước khi hiển thị trong HTML
    private String escapeHtml(String value) {
        if (value == null) {
            return "";
        }

        return value.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace("\"", "&quot;")
                    .replace("'", "&#39;");
    }
%>

<%
    String contextPath = request.getContextPath();

    // Thông báo lỗi đăng nhập
    String error = (String) request.getAttribute("error");

    // Thông báo sau khi đổi mật khẩu
    String loginSuccess = null;

    if (session != null) {
        loginSuccess =
                (String) session.getAttribute("loginSuccess");

        if (loginSuccess != null) {
            session.removeAttribute("loginSuccess");
        }
    }
%>

<!DOCTYPE html>
<html lang="vi">

<head>
    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>Đăng nhập - NutriFit</title>

    <link rel="stylesheet" href="<%= request.getContextPath() %>/assets/css/auth.css?v=2">
</head>

<body>
<div class="nf-auth-layout">
<aside class="nf-auth-brand" aria-label="Giới thiệu NutriFit">
<div class="nf-auth-mark"><span class="nf-auth-logo" aria-hidden="true">♥</span> NutriFit</div>
<div class="nf-brand-copy"><h2>Khỏe hơn mỗi ngày, bắt đầu từ hôm nay.</h2><p>Dinh dưỡng thông minh, tập luyện phù hợp và mục tiêu được cá nhân hóa cho chính bạn.</p></div>
<small>© NutriFit · Your wellness companion</small></aside>
<main class="nf-auth-main"><div class="nf-auth-eyebrow">NUTRIFIT / TÀI KHOẢN</div>


<div class="login-box">

    <!-- LOGO / TÊN ỨNG DỤNG -->

    <h2>NutriFit</h2>
    <h3>Đăng nhập</h3>


    <!-- THÔNG BÁO ĐỔI MẬT KHẨU THÀNH CÔNG -->

    <% if (loginSuccess != null) { %>

        <div class="success" role="status">
            <%= escapeHtml(loginSuccess) %>
        </div>

    <% } %>


    <!-- THÔNG BÁO LỖI ĐĂNG NHẬP -->

    <% if (error != null) { %>

        <div class="error" role="alert">
            <%= escapeHtml(error) %>
        </div>

    <% } %>


    <!-- FORM ĐĂNG NHẬP -->

    <form method="post"
          action="<%= contextPath %>/login">

        <!-- CSRF TOKEN -->
        <input type="hidden"
               name="_csrf"
               value="${sessionScope.csrfToken}">


        <!-- EMAIL -->

        <label for="email">
            Email
        </label>

        <input type="email"
               id="email"
               name="email"
               placeholder="Nhập email của bạn"
               autocomplete="username"
               maxlength="255"
               required>


        <!-- MẬT KHẨU -->

        <label for="password">
            Mật khẩu
        </label>

        <input type="password"
               id="password"
               name="password"
               placeholder="Nhập mật khẩu"
               autocomplete="current-password"
               required>


        <!-- NÚT ĐĂNG NHẬP -->

        <button type="submit">
            Đăng nhập
        </button>

    </form>


    <!-- LIÊN KẾT ĐĂNG KÝ / QUÊN MẬT KHẨU -->

    <div class="links">

        <p>
            <a href="<%= contextPath %>/forgot-password">
                Quên / đổi mật khẩu bằng OTP?
            </a>
        </p>

        <p>
            Chưa có tài khoản?
            <a href="<%= contextPath %>/register">
                Đăng ký ngay
            </a>
        </p>

    </div>


    <!-- FOOTER -->

    <div class="footer">
        NutriFit - Hệ thống quản lý dinh dưỡng và luyện tập
    </div>

</div>

</main>
</div>
</body>
</html>
