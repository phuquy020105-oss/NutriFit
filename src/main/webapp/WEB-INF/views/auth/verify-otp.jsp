
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

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
            font-family: Arial, Helvetica, sans-serif;
            background: linear-gradient(
                135deg,
                #e8f7f0 0%,
                #edf5ff 100%
            );
        }

        .verify-card {
            width: 100%;
            max-width: 504px;
            padding: 56px 42px 42px;
            background: #ffffff;
            border-radius: 22px;
            box-shadow: 0 18px 45px rgba(0, 0, 0, 0.08);
            text-align: center;
        }

        h1 {
            margin: 8px 0 26px;
            color: #168653;
            font-size: 38px;
            font-weight: 700;
        }

        .description {
            color: #666;
            font-size: 18px;
            line-height: 1.7;
            margin-bottom: 24px;
        }

        .email {
            color: #555;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 28px;
            overflow-wrap: anywhere;
        }

        .otp-input {
            display: block;
            width: 100%;
            height: 70px;
            padding: 12px;
            border: 1.5px solid #d3dce4;
            border-radius: 11px;
            outline: none;
            background: #fff;
            text-align: center;
            font-size: 30px;
            letter-spacing: 10px;
            color: #333;
            transition: border-color 0.2s;
        }

        .otp-input:focus {
            border-color: #168653;
            box-shadow: 0 0 0 3px rgba(22, 134, 83, 0.1);
        }

        .submit-btn {
            width: 100%;
            margin-top: 24px;
            padding: 17px;
            border: none;
            border-radius: 10px;
            background: #168653;
            color: white;
            font-size: 17px;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.2s;
        }

        .submit-btn:hover {
            background: #116d43;
        }

        .back-link {
            display: inline-block;
            margin-top: 25px;
            color: #168653;
            font-size: 17px;
            font-weight: 500;
            text-decoration: none;
        }

        .back-link:hover {
            text-decoration: underline;
        }

        .error-message {
            padding: 12px 15px;
            margin-bottom: 22px;
            background: #fff0f0;
            border: 1px solid #f5c2c7;
            border-radius: 9px;
            color: #b42318;
            font-size: 14px;
            line-height: 1.5;
        }

        @media (max-width: 540px) {
            .verify-card {
                padding: 40px 24px 32px;
            }

            h1 {
                font-size: 30px;
            }

            .description,
            .email {
                font-size: 16px;
            }

            .otp-input {
                font-size: 26px;
                letter-spacing: 8px;
            }
        }
    </style>
</head>

<body>

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

</body>
</html>
