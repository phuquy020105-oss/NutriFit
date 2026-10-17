<%@ page contentType="text/html; charset=UTF-8"
         pageEncoding="UTF-8" %>
<%@ page import="com.nutrifit.model.User" %>

<%!
    private String escapeHtml(String value) {
        if (value == null) return "";
        return value.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace("\"", "&quot;")
                    .replace("'", "&#39;");
    }

    private String display(Object value, String suffix) {
        return value == null ? "Chưa có dữ liệu" : value + suffix;
    }
%>

<%
    User user = (User) request.getAttribute("user");
    String contextPath = request.getContextPath();
    String subscriptionStatus = user != null && user.getSubscriptionStatus() != null
            ? String.valueOf(user.getSubscriptionStatus())
            : "FREE";
    boolean isPremium = "PREMIUM".equalsIgnoreCase(subscriptionStatus);
%>

<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - NutriFit</title>

    <style>
        * { box-sizing: border-box; }
        body {
            margin: 0;
            background: #f3f6f8;
            font-family: Arial, sans-serif;
            color: #1e293b;
        }
        header {
            background: #ffffff;
            padding: 20px 6%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 15px;
            box-shadow: 0 2px 12px #0000000d;
        }
        .brand {
            font-size: 25px;
            font-weight: bold;
            color: #16a34a;
        }
        nav {
            display: flex;
            align-items: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        nav a {
            color: #334155;
            text-decoration: none;
            font-weight: 600;
        }
        nav a:hover { color: #16a34a; }
        /* Premium navigation: override the generic nav links. */
        nav a.premium-nav {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            background: #dcfce7;
            color: #166534;
            padding: 10px 15px;
            border: 1px solid #bbf7d0;
            border-radius: 12px;
            font-weight: 700;
            transition: background .2s ease, transform .2s ease;
        }
        nav a.premium-nav:hover {
            background: #bbf7d0;
            color: #14532d;
            transform: translateY(-1px);
        }
        main {
            max-width: 1150px;
            margin: 35px auto;
            padding: 0 20px;
        }
        .welcome { margin-bottom: 30px; }
        .welcome h1 {
            margin-bottom: 10px;
            font-size: 30px;
        }
        .welcome p { color: #64748b; }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 20px;
        }
        .card {
            background: white;
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 4px 16px #0000000a;
        }
        .card h3 {
            margin: 0 0 18px;
            color: #64748b;
            font-size: 16px;
        }
        .value {
            font-size: 27px;
            font-weight: bold;
            color: #15803d;
            overflow-wrap: anywhere;
        }
        .description {
            color: #64748b;
            font-size: 14px;
            margin-top: 12px;
            line-height: 1.5;
        }
        .section-title { margin: 35px 0 20px; }
        .logout {
            background: #dc2626;
            color: white;
            border: none;
            border-radius: 8px;
            padding: 10px 16px;
            cursor: pointer;
        }
        .logout:hover { background: #b91c1c; }
        .logout-form { margin: 0; }
        .premium { color: #b45309; }
        .account-card {
            border: 1px solid #d9efe1;
            background: linear-gradient(165deg, #ffffff 54%, #f1fbf5 100%);
        }
        .account-card .description { margin-bottom: 17px; }
        .upgrade-button {
            display: inline-flex;
            justify-content: center;
            align-items: center;
            gap: 8px;
            width: 100%;
            min-height: 44px;
            padding: 12px 15px;
            color: #fff;
            background: #15803d;
            border-radius: 10px;
            font-weight: 700;
            text-decoration: none;
            text-align: center;
            transition: background .2s ease, transform .2s ease;
        }
        .upgrade-button:hover {
            color: #fff;
            background: #166534;
            transform: translateY(-1px);
        }
        .upgrade-button:focus-visible,
        .premium-nav:focus-visible {
            outline: 3px solid #86efac;
            outline-offset: 3px;
        }
        @media (max-width: 600px) {
            header { padding: 18px; }
            nav { gap: 10px; }
            main { margin-top: 24px; }
            .welcome h1 { font-size: 25px; }
        }
    </style>
</head>
<body>
<header>
    <div class="brand">NutriFit</div>
    <nav>
        <a href="<%= contextPath %>/chatbot">&#129302; AI Chatbot</a>
        <a href="<%= contextPath %>/dashboard">Dashboard</a>
        <a href="<%= contextPath %>/profile">Hồ sơ</a>
        <a href="<%= contextPath %>/payment" class="premium-nav">&#128081; Gói Premium</a>
        <form class="logout-form" method="post" action="<%= contextPath %>/logout">
            <input type="hidden" name="_csrf" value="${sessionScope.csrfToken}">
            <button class="logout" type="submit">Đăng xuất</button>
        </form>
    </nav>
</header>
<main>
    <section class="welcome">
        <h1>Xin chào, <%= escapeHtml(user != null ? user.getFullName() : "bạn") %>!</h1>
        <p>Theo dõi sức khỏe, dinh dưỡng và luyện tập của bạn hôm nay.</p>
    </section>

    <div class="grid">
        <div class="card account-card">
            <h3>Gói tài khoản</h3>
            <div class="value <%= isPremium ? "premium" : "" %>">
                <%= escapeHtml(subscriptionStatus) %>
            </div>
            <div class="description">Trạng thái gói NutriFit hiện tại</div>
            <a class="upgrade-button" href="<%= contextPath %>/payment">
                <%= isPremium ? "&#128081; Gia hạn / quản lý Premium &#8594;" : "&#128081; Nâng cấp Premium &#8594;" %>
            </a>
        </div>

        <div class="card">
            <h3>Mục tiêu calories</h3>
            <div class="value"><%= escapeHtml(display(request.getAttribute("targetCalories"), " kcal")) %></div>
            <div class="description">Mục tiêu năng lượng mỗi ngày</div>
        </div>
        <div class="card">
            <h3>Nước đã uống hôm nay</h3>
            <div class="value"><%= escapeHtml(display(request.getAttribute("waterToday"), " ml")) %></div>
            <div class="description">Mục tiêu: <%= escapeHtml(display(request.getAttribute("targetWater"), " ml")) %></div>
        </div>
        <div class="card">
            <h3>Buổi tập hôm nay</h3>
            <div class="value"><%= escapeHtml(display(request.getAttribute("workoutSessions"), " buổi")) %></div>
            <div class="description">Tổng thời gian: <%= escapeHtml(display(request.getAttribute("workoutMinutes"), " phút")) %></div>
        </div>
        <div class="card">
            <h3>Calories tiêu hao khi tập</h3>
            <div class="value"><%= escapeHtml(display(request.getAttribute("workoutCalories"), " kcal")) %></div>
            <div class="description">Ước tính từ nhật ký luyện tập hôm nay</div>
        </div>
        <div class="card">
            <h3>Cân nặng gần nhất</h3>
            <div class="value"><%= escapeHtml(display(request.getAttribute("latestWeight"), " kg")) %></div>
            <div class="description">Ngày ghi nhận: <%= escapeHtml(display(request.getAttribute("weightDate"), "")) %></div>
        </div>
    </div>

    <h2 class="section-title">Thông tin cá nhân</h2>
    <div class="grid">
        <div class="card">
            <h3>Chiều cao</h3>
            <div class="value"><%= escapeHtml(display(request.getAttribute("height"), " cm")) %></div>
        </div>
        <div class="card">
            <h3>Cân nặng trong hồ sơ</h3>
            <div class="value"><%= escapeHtml(display(request.getAttribute("profileWeight"), " kg")) %></div>
        </div>
    </div>
</main>
</body>
</html>
