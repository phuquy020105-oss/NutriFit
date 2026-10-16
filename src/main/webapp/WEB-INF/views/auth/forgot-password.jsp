
<%@ page contentType="text/html; charset=UTF-8"
         pageEncoding="UTF-8" %>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1">
    <title>Quên mật khẩu - NutriFit</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background: #f2f7f3;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
        }
        .card {
            background: white;
            padding: 35px;
            border-radius: 16px;
            width: 360px;
            max-width: 90%;
            box-shadow: 0 8px 25px #00000012;
        }
        h2 { color: #228b50; }
        input, button {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            box-sizing: border-box;
        }
        input { border: 1px solid #ddd; border-radius: 8px; }
        button {
            background: #228b50;
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
        }
        .error { color: #c62828; }
        .success { color: #228b50; }
        a { color: #228b50; }
    </style>
</head>
<body>
<div class="card">
    <h2>Quên mật khẩu</h2>
    <p>Nhập email đã đăng ký để nhận mã OTP.</p>

    <p class="error">${error}</p>
    <p class="success">${success}</p>

    <form method="post"
    <input type="hidden" name="_csrf" value="${sessionScope.csrfToken}">
          action="${pageContext.request.contextPath}/forgot-password">

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
</body>
</html>
