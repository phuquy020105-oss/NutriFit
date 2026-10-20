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
    <link rel="stylesheet" href="<%=ctx%>/assets/css/payment.css?v=${applicationScope.assetVersion}">
<link rel="stylesheet" href="<%=ctx%>/assets/css/workspace-nav.css?v=${applicationScope.assetVersion}"></head>
<body class="premium-layout nf-integrated-payment">
<button type="button" class="nf-global-scrim" id="nfGlobalScrim" aria-label="Đóng điều hướng" onclick="nfToggleNav()"></button>
<aside class="nf-global-sidebar" id="nfGlobalSidebar" aria-label="Điều hướng NutriFit">
  <a class="nf-global-logo" href="<%=ctx%>/dashboard"><span class="nf-global-logo-icon">✦</span> Nutri<span>Fit</span></a>
  <p class="nf-global-caption">KHÔNG GIAN CỦA BẠN</p>
  <nav class="nf-global-links">
    <a href="<%=ctx%>/dashboard">▦ <span>Tổng quan</span></a>
    <a href="<%=ctx%>/workout">◈ <span>Bài tập</span></a>
    <a href="<%=ctx%>/workout/plan">▤ <span>Lịch tập</span></a>
    <a href="<%=ctx%>/nutrition/recommendations">◉ <span>Dinh dưỡng</span></a>
    <a href="<%=ctx%>/chatbot" class="">✧ <span>AI Chatbot</span></a>
    <a href="<%=ctx%>/payment" class="active">♛ <span>Premium</span></a>
    <a href="<%=ctx%>/profile">◎ <span>Hồ sơ</span></a>
    <%@ include file="/WEB-INF/views/shared/admin-navigation.jspf" %>
  </nav>
  <div class="nf-global-bottom">
    <div class="nf-global-promo"><strong>Mỗi ngày tốt hơn 1%</strong><p>Kiên trì từng bước nhỏ để đạt mục tiêu sức khỏe.</p></div>
    <form method="post" action="<%=ctx%>/logout">
      <input type="hidden" name="_csrf" value="${sessionScope.csrfToken}">
      <button type="submit">↪ Đăng xuất</button>
    </form>
  </div>
</aside>

<div class="main-shell">
    <header class="topbar"><button type="button" class="nf-global-toggle" aria-label="Mở điều hướng NutriFit" aria-controls="nfGlobalSidebar" aria-expanded="false" onclick="nfToggleNav()">☰</button><span>Ứng dụng <span class="crumb">/</span> <strong>Gói Premium</strong></span><div class="top-links"><a href="<%=ctx%>/chatbot">✧ Trợ lý AI</a><a href="<%=ctx%>/profile">Hồ sơ</a><span class="account-avatar" aria-label="Tài khoản">N</span></div></header>
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
<script>
function nfToggleNav(){
 var nav=document.getElementById('nfGlobalSidebar'),scrim=document.getElementById('nfGlobalScrim');
 if(!nav||!scrim)return;
 var open=nav.classList.toggle('open');
 scrim.classList.toggle('open',open);
 document.querySelectorAll('.nf-global-toggle').forEach(function(b){b.setAttribute('aria-expanded',String(open));});
}
</script></body>
</html>
