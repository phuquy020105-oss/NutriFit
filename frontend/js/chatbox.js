(() => {
    "use strict";

    const CHAT_API_URL = "http://127.0.0.1:5000/api/chatbot/chat";
    const CHAT_STORAGE_KEY = "nutrifit_chat_history_v1";
    const MAX_MESSAGE_LENGTH = 2000;
    const MAX_HISTORY = 12;
    const MAX_STORED_MESSAGES = 60;

    // Đọc lịch sử đã lưu trong tab hiện tại.
    function loadStoredConversation() {
        try {
            const raw = sessionStorage.getItem(CHAT_STORAGE_KEY);
            const parsed = raw ? JSON.parse(raw) : [];

            if (!Array.isArray(parsed)) return [];

            return parsed
                .filter(item =>
                    item &&
                    ["user", "assistant"].includes(item.role) &&
                    typeof item.content === "string"
                )
                .slice(-MAX_STORED_MESSAGES);
        } catch (error) {
            console.warn("Không thể đọc lịch sử Chatbox:", error);
            return [];
        }
    }

    // Loại bỏ các ký hiệu Markdown thông dụng khi hiển thị.
    function formatReply(text) {
        return String(text || "")
            .replace(/```[\w-]*\s*/g, "")
            .replace(/`([^`]+)`/g, "$1")
            .replace(/\*\*(.*?)\*\*/gs, "$1")
            .replace(/__(.*?)__/gs, "$1")
            .replace(/(^|\n)#{1,6}\s+/g, "$1")
            .replace(/(^|\n)\s*[-*]\s+/g, "$1• ")
            .trim();
    }

    function initChatbox() {
        if (
            document.getElementById("nf-chat-panel") ||
            document.getElementById("nf-chat-launcher")
        ) {
            return;
        }

        // Nút mở Chatbox.
        const launcher = document.createElement("button");
        launcher.type = "button";
        launcher.className = "nf-chat-launcher";
        launcher.id = "nf-chat-launcher";
        launcher.textContent = "✦";
        launcher.setAttribute("aria-label", "Mở NutriFit AI");
        launcher.setAttribute("aria-expanded", "false");

        // Khung chat.
        const panel = document.createElement("section");
        panel.className = "nf-chat-panel";
        panel.id = "nf-chat-panel";
        panel.setAttribute("aria-label", "NutriFit AI Chatbox");
        panel.setAttribute("aria-hidden", "true");

        panel.innerHTML = `
            <header class="nf-chat-header">
                <div class="nf-chat-avatar" aria-hidden="true">✦</div>

                <div class="nf-chat-heading">
                    <strong>NutriFit AI</strong>
                    <small>Trợ lý hỗ trợ người dùng</small>
                </div>

                <button
                    type="button"
                    class="nf-chat-close"
                    id="nf-chat-close"
                    aria-label="Đóng khung chat"
                >×</button>
            </header>

            <div
                class="nf-chat-messages"
                id="nf-chat-messages"
                role="log"
                aria-live="polite"
                aria-label="Nội dung hội thoại"
            ></div>

            <div class="nf-chat-footer">
                <form class="nf-chat-form" id="nf-chat-form">
                    <textarea
                        class="nf-chat-input"
                        id="nf-chat-input"
                        rows="1"
                        maxlength="${MAX_MESSAGE_LENGTH}"
                        placeholder="Nhập câu hỏi của bạn..."
                        aria-label="Tin nhắn"
                        required
                    ></textarea>

                    <button
                        class="nf-chat-send"
                        id="nf-chat-send"
                        type="submit"
                        aria-label="Gửi tin nhắn"
                        disabled
                    >➤</button>
                </form>

                <p class="nf-chat-note">
                    NutriFit AI có thể mắc lỗi. Hãy kiểm tra thông tin quan trọng.
                </p>
            </div>
        `;

        document.body.append(launcher, panel);

        const messagesEl = panel.querySelector("#nf-chat-messages");
        const inputEl = panel.querySelector("#nf-chat-input");
        const sendEl = panel.querySelector("#nf-chat-send");
        const formEl = panel.querySelector("#nf-chat-form");
        const closeEl = panel.querySelector("#nf-chat-close");

        let conversation = loadStoredConversation();
        let isSending = false;

        function saveConversation() {
            try {
                conversation = conversation.slice(-MAX_STORED_MESSAGES);

                sessionStorage.setItem(
                    CHAT_STORAGE_KEY,
                    JSON.stringify(conversation)
                );
            } catch (error) {
                console.warn("Không thể lưu lịch sử Chatbox:", error);
            }
        }

        function scrollToBottom() {
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        function addMessage(role, text, extraClass = "") {
            const bubble = document.createElement("div");

            bubble.className = [
                "nf-chat-message",
                role === "user"
                    ? "nf-chat-user"
                    : "nf-chat-assistant",
                extraClass
            ].filter(Boolean).join(" ");

            // Không chèn HTML do AI trả về để tránh XSS.
            bubble.textContent =
                role === "assistant" && !extraClass.includes("nf-chat-error")
                    ? formatReply(text)
                    : text;

            messagesEl.appendChild(bubble);
            scrollToBottom();

            return bubble;
        }

        function addWelcome() {
            addMessage(
                "assistant",
                "Xin chào! Mình là NutriFit AI. " +
                "Mình có thể hỗ trợ bạn sử dụng website, " +
                "tìm hiểu dinh dưỡng và xây dựng thói quen luyện tập."
            );

            const suggestions = document.createElement("div");
            suggestions.className = "nf-chat-suggestions";

            [
                "NutriFit có những chức năng nào?",
                "BMR và TDEE là gì?",
                "Gợi ý món gà dưới 500 kcal"
            ].forEach(prompt => {
                const button = document.createElement("button");

                button.type = "button";
                button.className = "nf-chat-suggestion";
                button.textContent = prompt;

                button.addEventListener("click", () => {
                    sendMessage(prompt);
                });

                suggestions.appendChild(button);
            });

            messagesEl.appendChild(suggestions);
            scrollToBottom();
        }

        function showTyping() {
            const typing = document.createElement("div");

            typing.className = "nf-chat-typing";
            typing.textContent = "NutriFit AI đang trả lời...";
            typing.setAttribute("role", "status");

            messagesEl.appendChild(typing);
            scrollToBottom();

            return typing;
        }

        function updateSendButton() {
            sendEl.disabled = isSending || !inputEl.value.trim();
        }

        function openChat() {
            panel.classList.add("nf-chat-open");
            panel.setAttribute("aria-hidden", "false");
            launcher.setAttribute("aria-expanded", "true");

            inputEl.focus();
            scrollToBottom();
        }

        function closeChat() {
            panel.classList.remove("nf-chat-open");
            panel.setAttribute("aria-hidden", "true");
            launcher.setAttribute("aria-expanded", "false");

            launcher.focus();
        }

        async function sendMessage(rawMessage) {
            const message = rawMessage.trim();

            if (!message || isSending) return;

            if (message.length > MAX_MESSAGE_LENGTH) {
                addMessage(
                    "assistant",
                    "Câu hỏi tối đa 2000 ký tự.",
                    "nf-chat-error"
                );
                return;
            }

            // Lấy lịch sử trước khi thêm câu hỏi hiện tại.
            const history = conversation
                .filter(item => !item.error)
                .slice(-MAX_HISTORY)
                .map(item => ({
                    role: item.role,
                    content: item.content
                }));

            const suggestions = messagesEl.querySelector(
                ".nf-chat-suggestions"
            );

            if (suggestions) suggestions.remove();

            // Đánh dấu đang gửi ngay để tránh gửi trùng.
            isSending = true;
            updateSendButton();

            addMessage("user", message);

            conversation.push({
                role: "user",
                content: message
            });

            saveConversation();

            inputEl.value = "";
            inputEl.style.height = "auto";

            const typing = showTyping();

            let replyBubble = null;
            let fullReply = "";

            try {
                const response = await fetch(CHAT_API_URL, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        message,
                        history,
                        stream: true
                    })
                });

                if (!response.ok) {
                    const data = await response.json().catch(() => ({}));

                    throw new Error(
                        data.message ||
                        `Yêu cầu thất bại (HTTP ${response.status}).`
                    );
                }

                const contentType =
                    response.headers.get("content-type") || "";

                // Tương thích cả API JSON không streaming.
                if (!contentType.includes("text/event-stream")) {
                    const data = await response.json();

                    if (!data.success || !data.reply) {
                        throw new Error(
                            data.message || "AI chưa tạo được câu trả lời."
                        );
                    }

                    fullReply = data.reply;
                    typing.remove();

                    replyBubble = addMessage("assistant", fullReply);
                } else {
                    if (!response.body) {
                        throw new Error(
                            "Trình duyệt không hỗ trợ đọc phản hồi streaming."
                        );
                    }

                    const reader = response.body.getReader();
                    const decoder = new TextDecoder();

                    let buffer = "";
                    let streamFinished = false;
                    let streamError = null;

                    function handleEvent(block) {
                        const payload = block
                            .split(/\r?\n/)
                            .filter(line => line.startsWith("data:"))
                            .map(line => line.slice(5).trim())
                            .join("\n");

                        if (!payload) return;

                        let event;

                        try {
                            event = JSON.parse(payload);
                        } catch {
                            return;
                        }

                        if (event.type === "chunk") {
                            if (!replyBubble) {
                                typing.remove();
                                replyBubble = addMessage("assistant", "");
                            }

                            fullReply += event.text || "";

                            // Cập nhật cùng một bong bóng, không tạo
                            // bong bóng mới cho từng đoạn Gemini gửi.
                            replyBubble.textContent = formatReply(fullReply);
                            scrollToBottom();
                        } else if (event.type === "error") {
                            streamError =
                                event.message || "AI gặp lỗi. Vui lòng thử lại.";
                        } else if (event.type === "done") {
                            streamFinished = true;
                        }
                    }

                    while (true) {
                        const { value, done } = await reader.read();

                        buffer += decoder.decode(
                            value || new Uint8Array(),
                            { stream: !done }
                        );

                        let separator;

                        while (
                            (separator = buffer.match(/\r?\n\r?\n/))
                        ) {
                            const block = buffer.slice(0, separator.index);

                            buffer = buffer.slice(
                                separator.index + separator[0].length
                            );

                            handleEvent(block);

                            if (streamError) {
                                await reader.cancel().catch(() => {});
                                throw new Error(streamError);
                            }
                        }

                        if (done) {
                            if (buffer.trim()) {
                                handleEvent(buffer);
                            }
                            break;
                        }

                        if (streamError) {
                            await reader.cancel().catch(() => {});
                            throw new Error(streamError);
                        }
                    }

                    if (streamError) {
                        throw new Error(streamError);
                    }

                    if (!streamFinished) {
                        throw new Error(
                            "Kết nối bị ngắt trước khi AI trả lời xong."
                        );
                    }
                }

                if (!fullReply.trim()) {
                    throw new Error(
                        "AI chưa trả về nội dung. Vui lòng thử lại."
                    );
                }

                // Chuẩn hóa câu trả lời hiển thị cuối cùng.
                if (replyBubble) {
                    replyBubble.textContent = formatReply(fullReply);
                }

                conversation.push({
                    role: "assistant",
                    content: fullReply
                });

                saveConversation();
            } catch (error) {
                console.error("NutriFit Chatbox error:", error);

                const errorMessage =
                    error.message ||
                    "Không thể kết nối với NutriFit AI. Hãy kiểm tra Backend.";

                // Nếu đã có câu trả lời một phần, giữ phần đó và báo lỗi.
                if (!fullReply.trim()) {
                    addMessage(
                        "assistant",
                        errorMessage,
                        "nf-chat-error"
                    );
                } else {
                    addMessage(
                        "assistant",
                        "Kết nối bị gián đoạn. Câu trả lời có thể chưa đầy đủ.",
                        "nf-chat-error"
                    );
                }

                conversation.push({
                    role: "assistant",
                    content: errorMessage,
                    error: true
                });

                saveConversation();
            } finally {
                typing.remove();

                isSending = false;
                updateSendButton();

                if (panel.classList.contains("nf-chat-open")) {
                    inputEl.focus();
                }
            }
        }

        launcher.addEventListener("click", () => {
            if (panel.classList.contains("nf-chat-open")) {
                closeChat();
            } else {
                openChat();
            }
        });

        closeEl.addEventListener("click", closeChat);

        formEl.addEventListener("submit", event => {
            event.preventDefault();
            sendMessage(inputEl.value);
        });

        inputEl.addEventListener("input", () => {
            inputEl.style.height = "auto";
            inputEl.style.height =
                `${Math.min(inputEl.scrollHeight, 100)}px`;

            updateSendButton();
        });

        inputEl.addEventListener("keydown", event => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();

                if (!sendEl.disabled) {
                    formEl.requestSubmit();
                }
            }
        });

        document.addEventListener("keydown", event => {
            if (
                event.key === "Escape" &&
                panel.classList.contains("nf-chat-open")
            ) {
                closeChat();
            }
        });

        // Khôi phục hội thoại khi tải lại trang.
        if (conversation.length > 0) {
            conversation.forEach(item => {
                addMessage(
                    item.role,
                    item.content,
                    item.error ? "nf-chat-error" : ""
                );
            });
        } else {
            addWelcome();
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initChatbox, {
            once: true
        });
    } else {
        initChatbox();
    }
})();