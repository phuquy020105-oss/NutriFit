<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="com.nutrifit.model.User" %>
<%!
    private String escapeHtml(String value) {
        if (value == null) return "";
        return value.replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;").replace("\"", "&quot;")
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
            ? String.valueOf(user.getSubscriptionStatus()) : "FREE";
    boolean isPremium = "PREMIUM".equalsIgnoreCase(subscriptionStatus);
%>
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Tổng quan | NutriFit</title>
    <link rel="stylesheet" href="<%= contextPath %>/assets/css/dashboard.css">
</head>
<body>
<div class="app-shell">
    <aside class="sidebar" id="sidebar">
        <a class="logo" href="<%= contextPath %>/dashboard"><span class="logo-mark">✦</span> Nutri<span>Fit</span></a>
        <p class="nav-caption">KHÔNG GIAN CỦA BẠN</p>
        <nav class="side-nav" aria-label="Điều hướng chính">
            <a class="active" aria-current="page" href="<%= contextPath %>/dashboard"><span>▦</span> Tổng quan</a>
            <a href="<%= contextPath %>/workout"><span>◈</span> Bài tập</a>
            <a href="<%= contextPath %>/workout/plan"><span>▤</span> Lịch tập</a>
            <a href="<%= contextPath %>/nutrition/recommendations"><span>◉</span> Dinh dưỡng</a>
            <a href="<%= contextPath %>/chatbot"><span>✧</span> AI Chatbot</a>
            <a href="<%= contextPath %>/payment"><span>♛</span> Premium</a>
            <a href="<%= contextPath %>/profile"><span>◎</span> Hồ sơ</a>
            <%@ include file="/WEB-INF/views/shared/admin-navigation.jspf" %>
        </nav>
        <div class="sidebar-bottom">
            <div class="mini-promo"><strong>Mỗi ngày tốt hơn 1%</strong><p>Kiên trì từng bước nhỏ để đạt mục tiêu sức khỏe.</p></div>
            <form method="post" action="<%= contextPath %>/logout">
                <input type="hidden" name="_csrf" value="${sessionScope.csrfToken}">
                <button class="logout" type="submit">↪ Đăng xuất</button>
            </form>
        </div>
    </aside>

    <div class="app-content">
        <header class="topbar">
            <div class="topbar-left"><button class="menu-toggle" type="button" aria-label="Mở menu" aria-controls="sidebar" aria-expanded="false" onclick="toggleMenu(this)">☰</button><span>Không gian sức khỏe của bạn</span></div>
            <div class="topbar-right"><span class="status <%= isPremium ? "status-premium" : "" %>"><%= escapeHtml(subscriptionStatus) %></span><a class="avatar" href="<%= contextPath %>/profile" aria-label="Hồ sơ cá nhân">☺</a></div>
        </header>

        <main class="page">
            <section class="hero">
                <div><span class="eyebrow">NUTRIFIT · TỔNG QUAN</span><h1>Xin chào, <%= escapeHtml(user != null ? user.getFullName() : "bạn") %> <span aria-hidden="true">👋</span></h1><p>Hành trình khỏe mạnh bắt đầu từ những lựa chọn nhỏ mỗi ngày.</p><a class="hero-button" href="<%= contextPath %>/workout">Khám phá bài tập <span aria-hidden="true">→</span></a></div>
                <div class="hero-decoration" aria-hidden="true"><div class="hero-circle">✦</div><span>MOVE • EAT • GROW</span></div>
            </section>

            <div class="section-heading"><div><span class="eyebrow">HÔM NAY</span><h2>Chỉ số sức khỏe</h2></div><a href="<%= contextPath %>/profile">Xem hồ sơ →</a></div>
            <section class="stats-grid" aria-label="Thống kê sức khỏe">
                <article class="stat-card"><div class="stat-head"><span class="stat-icon mint">◎</span><span class="stat-label">Mục tiêu năng lượng</span></div><div class="stat-value"><%= escapeHtml(display(request.getAttribute("targetCalories"), " kcal")) %></div><p>Mục tiêu calo mỗi ngày</p></article>
                <article class="stat-card"><div class="stat-head"><span class="stat-icon blue">◉</span><span class="stat-label">Nước đã uống</span></div><div class="stat-value"><%= escapeHtml(display(request.getAttribute("waterToday"), " ml")) %></div><p>Mục tiêu: <%= escapeHtml(display(request.getAttribute("targetWater"), " ml")) %></p></article>
                <article class="stat-card"><div class="stat-head"><span class="stat-icon orange">◈</span><span class="stat-label">Buổi tập hôm nay</span></div><div class="stat-value"><%= escapeHtml(display(request.getAttribute("workoutSessions"), " buổi")) %></div><p>Tổng thời gian: <%= escapeHtml(display(request.getAttribute("workoutMinutes"), " phút")) %></p></article>
                <article class="stat-card"><div class="stat-head"><span class="stat-icon rose">↗</span><span class="stat-label">Năng lượng tiêu hao</span></div><div class="stat-value"><%= escapeHtml(display(request.getAttribute("workoutCalories"), " kcal")) %></div><p>Ước tính từ nhật ký tập hôm nay</p></article>
            </section>

            <div class="section-heading"><div><span class="eyebrow">DÀNH CHO BẠN</span><h2>Hành trình của tôi</h2></div></div>
            <section class="details-grid">
                <article class="panel"><div class="panel-heading"><h3>Thông tin cơ thể</h3><a href="<%= contextPath %>/profile">Cập nhật →</a></div><div class="body-stats"><div><span>Chiều cao</span><strong><%= escapeHtml(display(request.getAttribute("height"), " cm")) %></strong></div><div><span>Cân nặng hồ sơ</span><strong><%= escapeHtml(display(request.getAttribute("profileWeight"), " kg")) %></strong></div><div><span>Cân nặng gần nhất</span><strong><%= escapeHtml(display(request.getAttribute("latestWeight"), " kg")) %></strong><small>Ngày ghi nhận: <%= escapeHtml(display(request.getAttribute("weightDate"), "")) %></small></div></div></article>
                <article class="panel account-panel"><div class="panel-heading"><h3>Gói thành viên</h3><span class="status <%= isPremium ? "status-premium" : "" %>"><%= escapeHtml(subscriptionStatus) %></span></div><div class="account-symbol" aria-hidden="true">♛</div><h4><%= isPremium ? "Thành viên Premium" : "Khám phá NutriFit Premium" %></h4><p><%= isPremium ? "Quản lý hoặc gia hạn gói thành viên của bạn." : "Khám phá các quyền lợi nâng cao dành cho hành trình của bạn." %></p><a class="primary-button" href="<%= contextPath %>/payment"><%= isPremium ? "Quản lý Premium" : "Khám phá Premium" %> →</a></article>
            </section>

            <div class="section-heading"><div><span class="eyebrow">TRUY CẬP NHANH</span><h2>Bạn muốn làm gì tiếp?</h2></div></div>
            <section class="quick-grid"><a href="<%= contextPath %>/workout"><span>◈</span><strong>Bắt đầu tập luyện</strong><small>Khám phá danh sách bài tập</small></a><a href="<%= contextPath %>/nutrition/recommendations"><span>◉</span><strong>Lên thực đơn</strong><small>Quản lý kế hoạch dinh dưỡng</small></a><a href="<%= contextPath %>/chatbot"><span>✧</span><strong>Hỏi AI NutriFit</strong><small>Trợ lý sức khỏe thông minh</small></a></section>
            <footer class="footer">© NutriFit · Sống khỏe mỗi ngày</footer>
        </main>
    </div>
</div>
<script>
function toggleMenu(button) {
    var sidebar = document.getElementById('sidebar');
    var expanded = sidebar.classList.toggle('open');
    button.setAttribute('aria-expanded', String(expanded));
}
</script>
</body>
</html>
