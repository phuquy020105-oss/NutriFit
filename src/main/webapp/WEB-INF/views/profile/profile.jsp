
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
    @SuppressWarnings("unchecked")
    java.util.Map<String, String> bodyProfile =
        (java.util.Map<String, String>) request.getAttribute("bodyProfile");
    if (bodyProfile == null) bodyProfile = java.util.Collections.emptyMap();

%>

<!DOCTYPE html>
<html lang="vi">

<head>
    <meta charset="UTF-8">

    <meta name="viewport"
          content="width=device-width, initial-scale=1.0">

    <title>Hồ sơ cá nhân - NutriFit</title>

    <link rel="stylesheet" href="${pageContext.request.contextPath}/assets/css/profile.css">
</head>

<body>
<div class="nf-layout">
    <aside class="nf-sidebar" aria-label="Điều hướng NutriFit">
        <a class="nf-logo" href="<%= contextPath %>/dashboard"><span class="nf-logo-icon">✦</span>NutriFit</a>
        <div class="nf-nav-label">KHÔNG GIAN CỦA BẠN</div>
        <nav class="nf-nav">
            <a href="<%= contextPath %>/dashboard"><span class="nf-nav-symbol">▦</span>Tổng quan</a>
            <a href="<%= contextPath %>/workout"><span class="nf-nav-symbol">◇</span>Bài tập</a>
            <a href="<%= contextPath %>/nutrition"><span class="nf-nav-symbol">◉</span>Dinh dưỡng</a>
            <a href="<%= contextPath %>/chatbot"><span class="nf-nav-symbol">✧</span>AI Chatbot</a>
            <a href="<%= contextPath %>/profile" aria-current="page"><span class="nf-nav-symbol">◎</span>Hồ sơ</a>
        </nav>
        <div class="nf-side-note"><strong>Mỗi ngày tốt hơn 1%</strong>Kiên trì từng bước nhỏ để đạt mục tiêu sức khỏe.</div>
    </aside>
    <main class="nf-main">


<div class="container">

    <!-- TIÊU ĐỀ -->
    <div class="nf-heading">
        <div><div class="nf-eyebrow">TÀI KHOẢN CỦA BẠN</div>
        <h1>Hồ sơ cá nhân</h1>
        <p class="nf-description">Quản lý tài khoản, thông số cơ thể và mục tiêu sức khỏe.</p></div>
        <a class="nf-back" href="<%= contextPath %>/dashboard">← Về tổng quan</a>
    </div>

    <section class="v3-hero" aria-label="Tài khoản NutriFit">
      <div class="v3-hero-inner">
        <div class="v3-avatar" aria-hidden="true">NF</div>
        <div><span class="v3-hero-tag">NUTRIFIT · MY WELLNESS SPACE</span>
          <div class="v3-hero-name"><%= escapeHtml(user.getFullName()) %></div>
          <div class="v3-hero-sub"><%= escapeHtml(user.getEmail()) %></div>
        </div>
      </div>
    </section>
    <nav class="v3-tabs" aria-label="Các mục hồ sơ" role="tablist">
      <button type="button" class="v3-tab" data-v3-tab="overview" role="tab" aria-selected="true" aria-controls="v3-overview">◫ Tổng quan sức khỏe</button>
      <button type="button" class="v3-tab" data-v3-tab="body" role="tab" aria-selected="false" aria-controls="v3-body">♡ Chỉnh sửa thể chất</button>
    </nav>
    <section class="v3-section" id="v3-overview" role="tabpanel">
      <div class="v3-overview-grid">
        <div class="v3-overview-tile"><div class="v3-tile-label">Chiều cao</div><div class="v3-tile-value"><%= escapeHtml(bodyProfile.getOrDefault("height_cm","—")) %> cm</div></div>
        <div class="v3-overview-tile"><div class="v3-tile-label">Cân nặng hiện tại</div><div class="v3-tile-value"><%= escapeHtml(bodyProfile.getOrDefault("weight_kg","—")) %> kg</div></div>
        <div class="v3-overview-tile"><div class="v3-tile-label">Mục tiêu calo</div><div class="v3-tile-value"><%= escapeHtml(bodyProfile.getOrDefault("target_kcal","—")) %> kcal</div></div>
      </div>
      <div class="card"><h2>Hành trình sức khỏe của bạn</h2>
        <p class="v3-overview-intro">Theo dõi các chỉ số sức khỏe và điều chỉnh mục tiêu tập luyện phù hợp với bạn.</p>
        <a class="v3-link" href="#body" data-v3-open="body">Xem và cập nhật thông số cơ thể →</a>
      </div>
    </section>
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


<section class="v3-section" id="v3-body" role="tabpanel">
    <!-- ========================================= -->
    <!-- HỒ SƠ THỂ CHẤT -->
    <!-- ========================================= -->
    <div class="card" id="body-profile">
        <h2>Hồ sơ thể chất</h2>
        <% if (bodyProfile.isEmpty()) { %>
            <p class="hint">Bạn chưa có thông số thể chất. Hãy hoàn tất thiết lập ban đầu.</p>
            <a href="<%= contextPath %>/onboarding">Thiết lập thông số</a>
        <% } else { %>
            <div class="body-grid">
                <div class="body-stat">BMR <strong><%= escapeHtml(bodyProfile.get("bmr")) %> kcal</strong></div>
                <div class="body-stat">TDEE <strong><%= escapeHtml(bodyProfile.get("tdee")) %> kcal</strong></div>
                <div class="body-stat">Calo mục tiêu <strong><%= escapeHtml(bodyProfile.get("target_kcal")) %> kcal/ngày</strong></div>
                <div class="body-stat">Nước mục tiêu <strong><%= escapeHtml(bodyProfile.get("target_water_ml")) %> ml/ngày</strong></div>
            </div>
        <% } %>
        <form method="post" action="<%= contextPath %>/profile">
            <input type="hidden" name="_csrf" value="${sessionScope.csrfToken}">
            <input type="hidden" name="action" value="updateBodyProfile">
            <div class="body-grid">
                <div>
                    <label for="bodyGoal">Mục tiêu tập luyện</label>
                    <select id="bodyGoal" name="goal" required>
                        <option value="lose" <%= "lose".equals(bodyProfile.get("goal")) ? "selected" : "" %>>Giảm cân</option>
                        <option value="maintain" <%= "maintain".equals(bodyProfile.get("goal")) ? "selected" : "" %>>Duy trì cân nặng</option>
                        <option value="gain" <%= "gain".equals(bodyProfile.get("goal")) ? "selected" : "" %>>Tăng cân</option>
                    </select>
                </div>
                <div>
                    <label for="bodyGender">Giới tính dùng tính BMR</label>
                    <select id="bodyGender" name="gender" required>
                        <option value="male" <%= "male".equals(bodyProfile.get("gender")) ? "selected" : "" %>>Nam</option>
                        <option value="female" <%= "female".equals(bodyProfile.get("gender")) ? "selected" : "" %>>Nữ</option>
                    </select>
                </div>
                <div>
                    <label for="bodyAge">Tuổi</label>
                    <input id="bodyAge" type="number" name="age" min="18" max="100" required value="<%= escapeHtml(bodyProfile.get("age")) %>">
                </div>
                <div>
                    <label for="bodyHeight">Chiều cao (cm)</label>
                    <input id="bodyHeight" type="number" name="heightCm" min="100" max="250" step="0.01" required value="<%= escapeHtml(bodyProfile.get("height_cm")) %>">
                </div>
                <div>
                    <label for="bodyWeight">Cân nặng (kg)</label>
                    <input id="bodyWeight" type="number" name="weightKg" min="25" max="350" step="0.01" required value="<%= escapeHtml(bodyProfile.get("weight_kg")) %>">
                </div>
                <div>
                    <label for="bodyActivity">Mức độ vận động</label>
                    <select id="bodyActivity" name="activityLevel" required>
                        <option value="sedentary" <%= "sedentary".equals(bodyProfile.get("activity_level")) ? "selected" : "" %>>Ít vận động</option>
                        <option value="light" <%= "light".equals(bodyProfile.get("activity_level")) ? "selected" : "" %>>Nhẹ (1–3 buổi/tuần)</option>
                        <option value="moderate" <%= "moderate".equals(bodyProfile.get("activity_level")) ? "selected" : "" %>>Trung bình (3–5 buổi/tuần)</option>
                        <option value="high" <%= "high".equals(bodyProfile.get("activity_level")) ? "selected" : "" %>>Cao (6–7 buổi/tuần)</option>
                        <option value="very_high" <%= "very_high".equals(bodyProfile.get("activity_level")) ? "selected" : "" %>>Rất cao</option>
                    </select>
                </div>
            </div>
            <p class="hint">Lưu thay đổi sẽ tự tính lại BMR, TDEE, calo và nước mục tiêu.</p>
            <button type="submit">Lưu thông số thể chất</button>
        </form>
    </div>

</section>
<!-- FOOTER -->

    <div class="footer">
        NutriFit - Hệ thống quản lý dinh dưỡng
        và luyện tập
    </div>

</div>

    </main>
</div>

<script src="${pageContext.request.contextPath}/assets/js/profile.js" defer></script>
</body>
</html>
