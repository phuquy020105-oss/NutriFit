
<%@ page contentType="text/html; charset=UTF-8"
         pageEncoding="UTF-8" %>
<%@ page import="com.nutrifit.model.User" %>

<%!
    // Chống XSS khi hiển thị dữ liệu người dùng
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
    User user = (User) request.getAttribute("user");

    String error = (String) request.getAttribute("error");
    String success = (String) request.getAttribute("success");

    String contextPath = request.getContextPath();
%>

<!DOCTYPE html>
<html lang="vi">

<head>
    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>Hồ sơ cá nhân - NutriFit</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            padding: 30px 16px;
            background: #f1f5f9;
            font-family: Arial, sans-serif;
            color: #1e293b;
        }

        .container {
            max-width: 680px;
            margin: auto;
        }

        h1 {
            color: #15803d;
            margin-bottom: 26px;
            font-size: 36px;
        }

        h2 {
            font-size: 24px;
            margin-top: 0;
            margin-bottom: 24px;
        }

        .card {
            background: white;
            border-radius: 14px;
            padding: 28px 24px;
            margin-bottom: 20px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
        }

        .info {
            margin: 14px 0;
            font-size: 16px;
            line-height: 1.5;
            overflow-wrap: anywhere;
        }

        label {
            display: block;
            margin: 16px 0 7px;
            font-weight: bold;
            font-size: 15px;
        }

        input:not([type="hidden"]) {
            width: 100%;
            padding: 12px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            font-size: 15px;
            outline: none;
        }

        input:focus {
            border-color: #16a34a;
            box-shadow: 0 0 0 3px rgba(22, 163, 74, 0.12);
        }

        button {
            margin-top: 20px;
            padding: 12px 22px;
            border: none;
            border-radius: 8px;
            background: #16a34a;
            color: white;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
        }

        button:hover {
            background: #15803d;
        }

        button:active {
            transform: scale(0.98);
        }

        .danger {
            background: #dc2626;
        }

        .danger:hover {
            background: #b91c1c;
        }

        .success {
            background: #dcfce7;
            color: #166534;
            padding: 14px;
            border-radius: 9px;
            margin-bottom: 18px;
            line-height: 1.5;
        }

        .error {
            background: #fee2e2;
            color: #991b1b;
            padding: 14px;
            border-radius: 9px;
            margin-bottom: 18px;
            line-height: 1.5;
        }

        .hint {
            font-size: 13px;
            color: #64748b;
            margin-top: 8px;
            line-height: 1.5;
        }

        .badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            background: #dcfce7;
            color: #166534;
            font-size: 13px;
            font-weight: bold;
        }

        .premium {
            background: #fef3c7;
            color: #92400e;
        }

        .footer {
            text-align: center;
            margin-top: 25px;
            color: #64748b;
            font-size: 13px;
        }

        @media (max-width: 600px) {
            body {
                padding: 20px 12px;
            }

            h1 {
                font-size: 29px;
            }

            h2 {
                font-size: 21px;
            }

            .card {
                padding: 22px 18px;
            }

            button {
                width: 100%;
            }
        }
    </style>
</head>

<body>

<div class="container">

    <!-- TIÊU ĐỀ -->
    <h1>Hồ sơ cá nhân</h1>

    <!-- THÔNG BÁO THÀNH CÔNG -->
    <% if (success != null) { %>

        <div class="success" role="status">
            <%= escapeHtml(success) %>
        </div>

    <% } %>

    <!-- THÔNG BÁO LỖI -->
    <% if (error != null) { %>

        <div class="error" role="alert">
            <%= escapeHtml(error) %>
        </div>

    <% } %>


    <!-- ========================================= -->
    <!-- 1. THÔNG TIN TÀI KHOẢN -->
    <!-- ========================================= -->

    <div class="card">

        <h2>Thông tin tài khoản</h2>

        <p class="info">
            <strong>Email:</strong>
            <%= escapeHtml(user.getEmail()) %>
        </p>

        <p class="info">
            <strong>Vai trò:</strong>
            <%= user.getRole() %>
        </p>

        <p class="info">
            <strong>Gói tài khoản:</strong>

            <% if (user.getSubscriptionStatus() != null
                    && "PREMIUM".equals(
                        user.getSubscriptionStatus().name())) { %>

                <span class="badge premium">
                    PREMIUM
                </span>

            <% } else { %>

                <span class="badge">
                    <%= user.getSubscriptionStatus() %>
                </span>

            <% } %>
        </p>

        <% if (user.getPremiumExpiresAt() != null) { %>

            <p class="info">
                <strong>Premium hết hạn:</strong>
                <%= user.getPremiumExpiresAt() %>
            </p>

        <% } %>


        <!-- FORM CẬP NHẬT HỌ TÊN -->

        <form method="post"
              action="<%= contextPath %>/profile">

            <!-- CSRF TOKEN -->
            <input type="hidden"
                   name="_csrf"
                   value="${sessionScope.csrfToken}">

            <!-- ACTION -->
            <input type="hidden"
                   name="action"
                   value="updateProfile">

            <label for="fullName">
                Họ và tên
            </label>

            <input type="text"
                   id="fullName"
                   name="fullName"
                   maxlength="100"
                   value="<%= escapeHtml(user.getFullName()) %>"
                   autocomplete="name"
                   required>

            <p class="hint">
                Họ tên phải có từ 1 đến 100 ký tự.
            </p>

            <button type="submit">
                Lưu thay đổi
            </button>

        </form>

    </div>


    <!-- ========================================= -->
    <!-- 2. ĐỔI MẬT KHẨU -->
    <!-- ========================================= -->

    <div class="card">

        <h2>Đổi mật khẩu</h2>

        <form method="post"
              action="<%= contextPath %>/profile">

            <!-- CSRF TOKEN -->
            <input type="hidden"
                   name="_csrf"
                   value="${sessionScope.csrfToken}">

            <!-- ACTION -->
            <input type="hidden"
                   name="action"
                   value="changePassword">


            <!-- MẬT KHẨU HIỆN TẠI -->

            <label for="currentPassword">
                Mật khẩu hiện tại
            </label>

            <input type="password"
                   id="currentPassword"
                   name="currentPassword"
                   autocomplete="current-password"
                   required>


            <!-- MẬT KHẨU MỚI -->

            <label for="newPassword">
                Mật khẩu mới
            </label>

            <input type="password"
                   id="newPassword"
                   name="newPassword"
                   minlength="8"
                   autocomplete="new-password"
                   required>

            <p class="hint">
                Mật khẩu mới phải có ít nhất 8 ký tự
                và khác mật khẩu hiện tại.
            </p>


            <!-- XÁC NHẬN MẬT KHẨU -->

            <label for="confirmPassword">
                Xác nhận mật khẩu mới
            </label>

            <input type="password"
                   id="confirmPassword"
                   name="confirmPassword"
                   minlength="8"
                   autocomplete="new-password"
                   required>


            <button type="submit">
                Đổi mật khẩu
            </button>

        </form>

    </div>


    <!-- ========================================= -->
    <!-- 3. ĐĂNG XUẤT -->
    <!-- ========================================= -->

    <div class="card">

        <h2>Phiên đăng nhập</h2>

        <p class="hint">
            Đăng xuất khỏi tài khoản NutriFit
            trên trình duyệt hiện tại.
        </p>

        <form method="post"
              action="<%= contextPath %>/logout">

            <!-- CSRF TOKEN CHO LOGOUT -->
            <input type="hidden"
                   name="_csrf"
                   value="${sessionScope.csrfToken}">

            <button type="submit" class="danger">
                Đăng xuất
            </button>

        </form>

    </div>


    <!-- FOOTER -->

    <div class="footer">
        NutriFit - Hệ thống quản lý dinh dưỡng
        và luyện tập
    </div>

</div>

</body>
</html>
