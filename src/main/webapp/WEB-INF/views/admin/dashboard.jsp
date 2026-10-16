
<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.util.Objects" %>
<%
    String contextPath = request.getContextPath();
    String fullName = Objects.toString(
            session.getAttribute("fullName"), "Admin");

    long totalUsers = (Long) request.getAttribute("totalUsers");
    long totalAdmins = (Long) request.getAttribute("totalAdmins");
    long totalPremiumUsers = (Long) request.getAttribute("totalPremiumUsers");
    long newUsersToday = (Long) request.getAttribute("newUsersToday");
%>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport"
          content="width=device-width, initial-scale=1">
    <title>Admin Dashboard - NutriFit</title>
    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f7f5;
            color: #24352b;
        }
        header {
            background: #176b45;
            color: white;
            padding: 20px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
        }
        header h1 { margin: 0; font-size: 24px; }
        nav { display: flex; gap: 12px; align-items: center; }
        nav a, nav button {
            background: white;
            color: #176b45;
            padding: 10px 15px;
            border: none;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            cursor: pointer;
        }
        main {
            max-width: 1100px;
            margin: 35px auto;
            padding: 0 20px;
        }
        .cards {
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(210px, 1fr));
            gap: 20px;
            margin-top: 25px;
        }
        .card {
            background: white;
            border-radius: 14px;
            padding: 25px;
            box-shadow: 0 4px 15px #0000000d;
        }
        .card h3 {
            margin: 0 0 18px;
            color: #64756a;
            font-size: 15px;
        }
        .card strong {
            font-size: 34px;
            color: #176b45;
        }
        .action {
            display: inline-block;
            margin-top: 28px;
            padding: 13px 20px;
            background: #176b45;
            color: white;
            border-radius: 9px;
            text-decoration: none;
        }
    </style>
</head>
<body>
<header>
    <h1>NutriFit Admin</h1>
    <nav>
        <a href="<%= contextPath %>/admin">Dashboard</a>
        <a href="<%= contextPath %>/admin/users">Người dùng</a>
        <form method="post"
              action="<%= contextPath %>/logout"
              style="margin:0">
            <input type="hidden" name="_csrf"
                   value="${sessionScope.csrfToken}">
            <button type="submit">Đăng xuất</button>
        </form>
    </nav>
</header>

<main>
    <h2>Tổng quan hệ thống</h2>
    <p>Thống kê tài khoản NutriFit từ cơ sở dữ liệu MySQL.</p>

    <section class="cards">
        <div class="card">
            <h3>Tổng người dùng</h3>
            <strong><%= totalUsers %></strong>
        </div>
        <div class="card">
            <h3>Tài khoản Admin</h3>
            <strong><%= totalAdmins %></strong>
        </div>
        <div class="card">
            <h3>Tài khoản Premium</h3>
            <strong><%= totalPremiumUsers %></strong>
        </div>
        <div class="card">
            <h3>Đăng ký hôm nay</h3>
            <strong><%= newUsersToday %></strong>
        </div>
    </section>

    <a class="action" href="<%= contextPath %>/admin/users">
        Quản lý người dùng →
    </a>
</main>
</body>
</html>
