
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

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            font-family: Arial, sans-serif;
            background: #f4f7f5;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
            color: #1f2937;
        }

        .login-box {
            background: white;
            padding: 35px;
            border-radius: 14px;
            width: 380px;
            max-width: 100%;
            box-shadow: 0 8px 30px rgba(0, 0, 0, 0.07);
        }

        h2 {
            text-align: center;
            color: #16804a;
            font-size: 30px;
            margin: 0 0 8px;
        }

        h3 {
            text-align: center;
            margin: 0 0 25px;
            font-size: 20px;
            font-weight: 500;
        }

        label {
            display: block;
            margin-top: 16px;
            font-weight: 600;
            font-size: 14px;
        }

        input:not([type="hidden"]) {
            width: 100%;
            padding: 12px;
            margin-top: 7px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 15px;
            outline: none;
        }

        input:focus {
            border-color: #16804a;
            box-shadow: 0 0 0 3px rgba(22, 128, 74, 0.1);
        }

        button {
            width: 100%;
            margin-top: 24px;
            padding: 13px;
            border: none;
            border-radius: 8px;
            background: #16804a;
            color: white;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
        }

        button:hover {
            background: #116b3e;
        }

        .error {
            background: #fee2e2;
            color: #991b1b;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 18px;
            font-size: 14px;
            line-height: 1.5;
            text-align: center;
        }

        .success {
            background: #dcfce7;
            color: #166534;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 18px;
            font-size: 14px;
            line-height: 1.5;
            text-align: center;
        }

        .links {
            margin-top: 20px;
            text-align: center;
        }

        .links p {
            margin: 12px 0;
            font-size: 14px;
        }

        .links a {
            color: #16804a;
            text-decoration: none;
            font-weight: 600;
        }

        .links a:hover {
            text-decoration: underline;
        }

        .footer {
            text-align: center;
            margin-top: 25px;
            font-size: 12px;
            color: #94a3b8;
        }

        @media (max-width: 480px) {
            .login-box {
                padding: 28px 22px;
            }
        }
    </style>
</head>

<body>

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
                Quên mật khẩu?
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

</body>
</html>
