<%@ page contentType="text/html; charset=UTF-8" pageEncoding="UTF-8" %>
<%@ page import="java.util.List,com.nutrifit.model.ChatConversation,com.nutrifit.model.ChatMessage,com.nutrifit.util.HtmlEscaper" %>
<%
    List<ChatConversation> conversations = (List<ChatConversation>) request.getAttribute("conversations");
    List<ChatMessage> messages = (List<ChatMessage>) request.getAttribute("messages");
    Long selected = (Long) request.getAttribute("conversationId");
    long current = selected == null ? 0L : selected;
    String ctx = request.getContextPath();
    String rawModel = String.valueOf(request.getAttribute("geminiModel"));
    String modelName = rawModel.equals("gemini-4-argon") ? "Gemini 4 Argon" :
            rawModel.equals("gemini-3.8-flash") ? "Gemini 3.8 Flash" : rawModel;
    Object nameObj = session.getAttribute("fullName");
    String displayName = nameObj == null ? "bạn" : String.valueOf(nameObj);
    boolean emptyChat = messages == null || messages.isEmpty();
%>
<!doctype html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
    <meta name="theme-color" content="#f5faf7">
    <title>NutriFit AI – Trợ lý dinh dưỡng thông minh</title>
    <link rel="stylesheet" href="<%=ctx%>/assets/css/chat-modern.css?v=20261017-ui2">
    <script defer src="<%=ctx%>/assets/js/chat-modern.js?v=20261017-ui2"></script>
</head>
<body class="chat-page">
<div class="chat-app">
    <button type="button" class="sidebar-scrim" id="sidebarScrim" aria-label="Đóng menu hội thoại"></button>
    <aside class="chat-sidebar" id="chatSidebar" aria-label="Danh sách hội thoại">
        <a class="brand" href="<%=ctx%>/dashboard" aria-label="Về NutriFit Dashboard">
            <span class="brand-mark" aria-hidden="true">✳</span>
            <span class="brand-text">Nutri<span>Fit</span><small>YOUR WELLNESS SPACE</small></span>
        </a>
        <div class="sidebar-body">
            <a class="new-chat" href="<%=ctx%>/chatbot"><span class="new-chat-symbol">＋</span><span>Cuộc trò chuyện mới</span><span class="new-chat-arrow">↗</span></a>
            <div class="section-caption"><span>GẦN ĐÂY</span><span class="section-line"></span></div>
            <nav class="history-list" aria-label="Các hội thoại đã lưu">
                <% if (conversations == null || conversations.isEmpty()) { %>
                    <div class="history-empty">Chưa có hội thoại nào.<br>Bắt đầu bằng một câu hỏi nhé!</div>
                <% } else { for (ChatConversation conv : conversations) { %>
                    <a class="history-item <%=conv.id() == current ? "active" : ""%>" href="<%=ctx%>/chatbot?conversationId=<%=conv.id()%>" aria-current="<%=conv.id() == current ? "page" : "false"%>">
                        <span class="history-glyph" aria-hidden="true">▤</span>
                        <span class="history-title"><%=HtmlEscaper.escape(conv.title())%></span>
                    </a>
                <% }} %>
            </nav>
        </div>
        <div class="sidebar-footer">
            <div class="sidebar-tip"><span aria-hidden="true">✦</span><div><strong>Chăm sóc bản thân mỗi ngày</strong><small>Dinh dưỡng tốt · Tập luyện đều</small></div></div>
            <a class="back-link" href="<%=ctx%>/payment">&#9733; Nâng cấp Premium</a>
<a class="back-link" href="<%=ctx%>/dashboard"><span aria-hidden="true">↖</span> Quay lại NutriFit</a>
        </div>
    </aside>

    <main class="chat-main">
        <header class="chat-topbar">
            <div class="topbar-left">
                <button type="button" id="mobileMenu" class="mobile-menu" aria-label="Mở menu hội thoại" aria-expanded="false" aria-controls="chatSidebar">☰</button>
                <span class="topbar-avatar" aria-hidden="true">✳</span>
                <div class="topbar-heading"><strong>NutriFit AI</strong><span><i class="status-dot"></i> Trợ lý sức khỏe của bạn</span></div>
            </div>
            <div class="topbar-right"><span class="model-pill" title="Model được cấu hình trên máy chủ"><span aria-hidden="true">✧</span> <%=HtmlEscaper.escape(modelName)%></span><a href="<%=ctx%>/dashboard" class="topbar-close" title="Về Dashboard" aria-label="Về Dashboard">↗</a></div>
        </header>

        <section class="chat-content" aria-label="Nội dung hội thoại">
            <div class="chat-scroll" id="chatScroll" aria-live="polite" aria-relevant="additions">
                <% if (emptyChat) { %>
                    <div class="welcome-state">
                        <div class="hero-orbit" aria-hidden="true"><div class="hero-badge">✳</div><span class="orbit-star top">✧</span><span class="orbit-star bottom">✦</span></div>
                        <span class="eyebrow">NUTRIFIT INTELLIGENT ASSISTANT</span>
                        <h1>Chào <%=HtmlEscaper.escape(displayName)%>! <span class="greet-wave">👋</span><br><span>Hôm nay bạn muốn khỏe hơn thế nào?</span></h1>
                        <p>Khám phá chế độ ăn phù hợp, lịch tập khoa học và những thói quen tốt – tất cả trong một cuộc trò chuyện.</p>
                        <div class="suggestions" aria-label="Gợi ý câu hỏi">
                            <button type="button" class="prompt-chip" data-prompt="Gợi ý thực đơn lành mạnh 1 ngày cho người mới bắt đầu tập gym, kèm lượng protein ước tính."><span class="chip-icon orange">🥗</span><span><strong>Ăn uống lành mạnh</strong><small>Thực đơn dinh dưỡng mỗi ngày</small></span><span class="chip-chevron">↗</span></button>
                            <button type="button" class="prompt-chip" data-prompt="Hãy lên lịch tập gym 3 buổi mỗi tuần cho người mới bắt đầu, gồm khởi động và cách tăng dần cường độ."><span class="chip-icon blue">🏋️</span><span><strong>Lịch tập cá nhân</strong><small>Kế hoạch cho người mới tập</small></span><span class="chip-chevron">↗</span></button>
                            <button type="button" class="prompt-chip" data-prompt="Để tăng cơ an toàn, tôi cần chú ý gì về bữa ăn, giấc ngủ và thời gian phục hồi?"><span class="chip-icon purple">🌙</span><span><strong>Phục hồi & tăng cơ</strong><small>Ngủ đủ, ăn tốt, luyện tập đúng</small></span><span class="chip-chevron">↗</span></button>
                            <button type="button" class="prompt-chip" data-prompt="Cho tôi 5 mẹo xây dựng thói quen vận động và ăn uống khoa học dễ duy trì trong 30 ngày."><span class="chip-icon mint">💚</span><span><strong>Thói quen tốt</strong><small>Chăm sóc sức khỏe bền vững</small></span><span class="chip-chevron">↗</span></button>
                        </div>
                    </div>
                <% } else { %>
                    <div class="thread-intro"><span class="thread-intro-icon">✦</span><span>Hội thoại của bạn với NutriFit AI</span></div>
                    <div class="thread-messages">
                        <% for (ChatMessage message : messages) {
                            boolean user = "USER".equals(message.senderRole());
                            boolean system = "SYSTEM".equals(message.senderRole());
                        %>
                        <article class="message-row <%=user ? "from-user" : (system ? "from-system" : "from-assistant")%>">
                            <span class="message-avatar" aria-hidden="true"><%=user ? "B" : (system ? "!" : "✳")%></span>
                            <div class="message-body"><div class="message-head"><strong><%=user ? "Bạn" : (system ? "Thông báo hệ thống" : "NutriFit AI")%></strong><% if(!user && !system){ %><span class="answer-badge">AI</span><% } %></div>
                                <div class="message-text"><%=HtmlEscaper.escape(message.content())%></div>
                                <% if(!user && !system){ %><button type="button" class="copy-answer" title="Sao chép câu trả lời" aria-label="Sao chép câu trả lời">▣ <span>Sao chép</span></button><% } %>
                            </div>
                        </article>
                        <% } %>
                    </div>
                <% } %>
            </div>
        </section>

        <section class="composer-area" aria-label="Nhập câu hỏi">
            <form id="chatForm" method="post" action="<%=ctx%>/chatbot" class="composer" autocomplete="off">
                <input type="hidden" name="csrf" value="<%=HtmlEscaper.escape(request.getAttribute("csrf"))%>">
                <input type="hidden" name="conversationId" value="<%=current%>">
                <label class="visually-hidden" for="chatMessage">Câu hỏi dành cho NutriFit AI</label>
                <textarea id="chatMessage" name="text" rows="1" maxlength="2000" required placeholder="Hỏi NutriFit AI bất cứ điều gì về sức khỏe và luyện tập..." aria-describedby="composerHelp"></textarea>
                <div class="composer-actions"><div class="composer-meta"><span class="hint-stars">✦</span><span id="charCount">0 / 2000</span></div><button id="sendButton" type="submit" class="send-btn" aria-label="Gửi tin nhắn"><span>Gửi</span><span aria-hidden="true">↗</span></button></div>
            </form>
            <p id="composerHelp" class="composer-disclaimer">NutriFit AI có thể chưa chính xác. Hãy tham khảo chuyên gia khi đưa ra quyết định về sức khỏe. <span>Enter để gửi · Shift+Enter để xuống dòng</span></p>
        </section>
    </main>
</div>
</body>
</html>
