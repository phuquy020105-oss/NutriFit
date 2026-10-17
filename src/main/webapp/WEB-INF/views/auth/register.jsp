
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

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            font-family: Arial, sans-serif;
            background: linear-gradient(
                135deg, #e6f5ed, #edf5ff
            );
        }

        .register-box {
            background: #fff;
            width: 420px;
            max-width: 92%;
            padding: 35px;
            border-radius: 18px;
            box-shadow: 0 12px 35px rgba(0, 0, 0, .09);
        }

        h1 {
            color: #168451;
            text-align: center;
            margin: 0 0 10px;
        }

        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 25px;
            line-height: 1.5;
        }

        label {
            display: block;
            margin: 15px 0 7px;
            font-weight: bold;
            font-size: 14px;
        }

        input:not([type="hidden"]) {
            width: 100%;
            padding: 12px;
            border: 1px solid #d1d5db;
            border-radius: 9px;
            font-size: 15px;
        }

        input:focus {
            outline: none;
            border-color: #168451;
        }

        button {
            width: 100%;
            margin-top: 25px;
            padding: 13px;
            border: none;
            border-radius: 9px;
            background: #168451;
            color: white;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
        }

        button:hover {
            background: #116b41;
        }

        .error {
            background: #fff1f1;
            color: #b42318;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 14px;
        }

        .footer {
            text-align: center;
            margin-top: 22px;
            font-size: 14px;
        }

        a {
            color: #168451;
            text-decoration: none;
            font-weight: bold;
        }

        a:hover {
            text-decoration: underline;
        }

        @media (max-width: 480px) {
            .register-box {
                padding: 25px 20px;
            }
        }
    </style>
</head>

<body>

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

</body>
</html>
