<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.util.List,java.util.Locale,java.text.NumberFormat,com.nutrifit.model.SubscriptionPlan,com.nutrifit.util.HtmlEscaper" %>
<%
    String ctx = request.getContextPath();
    List<SubscriptionPlan> plans = (List<SubscriptionPlan>) request.getAttribute("plans");
    String csrf = String.valueOf(request.getAttribute("csrf"));
    boolean configured = Boolean.TRUE.equals(request.getAttribute("vnpConfigured"));

    SubscriptionPlan month = null;
    SubscriptionPlan year = null;
    if (plans != null) {
        for (SubscriptionPlan plan : plans) {
            if (plan.durationDays() == 30 && (month == null || plan.priceVnd() < month.priceVnd())) month = plan;
            if (plan.durationDays() == 365 && (year == null || plan.priceVnd() < year.priceVnd())) year = plan;
        }
    }
    NumberFormat money = NumberFormat.getIntegerInstance(Locale.forLanguageTag("vi-VN"));
    boolean hasAnyPaidPlan = month != null || year != null;
    String notice = request.getParameter("notice");
%>
<!doctype html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="theme-color" content="#1b332d">
    <title>NutriFit Premium | Chăm sóc sức khỏe mỗi ngày</title>
    <link rel="stylesheet" href="<%=ctx%>/assets/css/payment-modern.css?v=20261017-premium2">
</head>
<body class="premium-layout">
<aside class="sidebar" aria-label="Điều hướng NutriFit">
    <a class="sidebar-brand" href="<%=ctx%>/dashboard">
        <span class="brand-symbol">✳</span>
        <span><strong>nutrifit</strong><small>YOUR WELLNESS SPACE</small></span>
    </a>
    <div class="workspace-tile"><span class="workspace-icon">✦</span><span><b>Không gian của bạn</b><small>Personal wellness</small></span><span aria-hidden="true">⌄</span></div>
    <div class="side-label">KHÁM PHÁ</div>
    <nav class="side-nav" aria-label="Các tính năng">
        <a href="<%=ctx%>/dashboard"><span class="nav-icon">▦</span><span>Tổng quan</span></a>
        <span class="nav-soon" title="Module khác của nhóm đang triển khai"><span class="nav-icon">♧</span><span>Dinh dưỡng</span><em>Sắp có</em></span>
        <span class="nav-soon" title="Module khác của nhóm đang triển khai"><span class="nav-icon">♜</span><span>Thực đơn AI</span><em>Sắp có</em></span>
        <span class="nav-soon" title="Module khác của nhóm đang triển khai"><span class="nav-icon">⚒</span><span>Luyện tập</span><em>Sắp có</em></span>
        <a href="<%=ctx%>/chatbot"><span class="nav-icon">✧</span><span>Trợ lý AI</span><span class="pill">AI</span></a>
        <a href="<%=ctx%>/profile"><span class="nav-icon">♙</span><span>Hồ sơ của tôi</span></a>
        <a class="active" aria-current="page" href="<%=ctx%>/payment"><span class="nav-icon">♛</span><span>Gói Premium</span></a>
    </nav>
    <div class="sidebar-promo"><span class="sparkle">✦</span><strong>NUTRIFIT PREMIUM</strong><p>Đầu tư cho một phiên bản khỏe mạnh hơn.</p><a href="#goi-premium">Khám phá gói Pro ↗</a></div>
    <div class="sidebar-foot">NutriFit Studio</div>
</aside>
<div class="main-shell">
    <header class="topbar"><span>Ứng dụng <span class="crumb">/</span> <strong>Gói Premium</strong></span><div class="top-links"><a href="<%=ctx%>/chatbot">✧ Trợ lý AI</a><a href="<%=ctx%>/profile">Hồ sơ</a><span class="account-avatar" aria-label="Tài khoản">N</span></div></header>
    <main class="premium-main" id="goi-premium">
        <div class="section-kicker">NÂNG TẦM SỨC KHỎE</div>
        <h1>NutriFit <span>Premium</span></h1>
        <p class="lead">Chọn gói phù hợp với nhu cầu luyện tập và chăm sóc dinh dưỡng.</p>
        <div class="payment-method-line"><span class="status-dot"></span><span>Thanh toán an toàn với VNPay</span></div>
        <% if ("setup".equals(notice) || !configured) { %>
            <div class="notice warning" role="status"><strong>Thanh toán VNPay chưa sẵn sàng.</strong><span>Quản trị viên cần hoàn tất cấu hình cổng thanh toán. Bạn vẫn có thể xem các gói và giá.</span></div>
        <% } else if ("invalid-plan".equals(notice)) { %>
            <div class="notice warning" role="status"><strong>Gói chưa hợp lệ hoặc không còn hoạt động.</strong><span>Vui lòng tải lại bảng giá và chọn một gói đang hoạt động.</span></div>
        <% } %>
        <% if (!hasAnyPaidPlan) { %>
            <div class="notice info" role="status"><strong>Chưa có gói Premium đang hoạt động.</strong><span>Quản trị viên cần cập nhật gói 30 ngày hoặc 365 ngày trong cơ sở dữ liệu.</span></div>
        <% } %>
        <section class="pricing-grid" aria-label="Bảng giá NutriFit Premium">
            <article class="pricing-card free-plan">
                <span class="plan-badge">NutriFit</span>
                <h2>Khám phá</h2>
                <p class="subtitle">Bắt đầu hành trình wellness.</p>
                <div class="price-line"><strong>0₫</strong><small>/ miễn phí</small></div>
                <ul class="benefits"><li>Truy cập tổng quan cá nhân</li><li>Sử dụng các tính năng cơ bản</li><li>Trò chuyện với trợ lý AI NutriFit</li><li>Nâng cấp khi bạn sẵn sàng</li></ul>
                <a class="plan-action free-action" href="<%=ctx%>/dashboard">Bắt đầu miễn phí <span>→</span></a>
            </article>
            <article class="pricing-card recommended">
                <span class="recommended-badge">✦ Đề xuất</span>
                <h2>Premium tháng</h2>
                <p class="subtitle">Mở khóa nội dung chuyên sâu.</p>
                <div class="price-line">
                    <% if (month != null) { %><strong><%=money.format(month.priceVnd())%>₫</strong><small>/ 30 ngày</small>
                    <% } else { %><strong class="unavailable">Chưa có giá</strong><small>/ 30 ngày</small><% } %>
                </div>
                <ul class="benefits"><li>Quyền lợi của gói Khám phá</li><li>Nội dung luyện tập Premium</li><li>Lưu sở thích dinh dưỡng</li><li>Gợi ý theo sở thích của bạn</li></ul>
                <% if (month != null && configured) { %>
                    <form method="post" action="<%=ctx%>/payment"><input type="hidden" name="csrf" value="<%=HtmlEscaper.escape(csrf)%>"><input type="hidden" name="planId" value="<%=month.id()%>"><button class="plan-action primary-action" type="submit" aria-label="Thanh toán gói Premium tháng qua VNPay">Thanh toán gói tháng <span>→</span></button></form>
                <% } else { %><button class="plan-action primary-action" type="button" disabled title="Thanh toán chưa sẵn sàng hoặc gói chưa được mở bán">Chưa thể thanh toán <span>→</span></button><% } %>
            </article>
            <article class="pricing-card long-term">
                <span class="plan-badge">NutriFit</span>
                <h2>Premium dài hạn</h2>
                <p class="subtitle">Đồng hành lâu hơn với sức khỏe.</p>
                <div class="price-line">
                    <% if (year != null) { %><strong><%=money.format(year.priceVnd())%>₫</strong><small>/ 365 ngày</small>
                    <% } else { %><strong class="unavailable">Chưa có giá</strong><small>/ 365 ngày</small><% } %>
                </div>
                <ul class="benefits"><li>Đầy đủ quyền lợi Premium tháng</li><li>Thời hạn sử dụng 365 ngày</li><li>Quản lý quyền lợi trong hồ sơ</li><li>Gia hạn cộng dồn khi còn hiệu lực</li></ul>
                <% if (year != null && configured) { %>
                    <form method="post" action="<%=ctx%>/payment"><input type="hidden" name="csrf" value="<%=HtmlEscaper.escape(csrf)%>"><input type="hidden" name="planId" value="<%=year.id()%>"><button class="plan-action light-action" type="submit" aria-label="Thanh toán gói Premium dài hạn qua VNPay">Thanh toán gói dài hạn <span>→</span></button></form>
                <% } else { %><button class="plan-action light-action" type="button" disabled title="Thanh toán chưa sẵn sàng hoặc gói chưa được mở bán">Chưa thể thanh toán <span>→</span></button><% } %>
            </article>
        </section>
        <section class="why-card"><div><div class="section-kicker">CÙNG NUTRIFIT PHÁT TRIỂN</div><h3>Vì sao nên chọn NutriFit?</h3><p>Chăm sóc sức khỏe theo cách phù hợp với chính bạn — từ dinh dưỡng đến luyện tập.</p></div><div class="trust-points"><span>✓ Dữ liệu giá lấy từ MySQL</span><span>✓ Thanh toán qua VNPay</span><span>✓ Premium chỉ kích hoạt khi IPN đã xác thực</span></div></section>
        <p class="payment-disclaimer">🔒 Thanh toán được xác minh qua VNPay trước khi kích hoạt Premium. Cổng thanh toán hiện tại không trừ tiền thật.</p>
    </main>
</div>
</body>
</html>
