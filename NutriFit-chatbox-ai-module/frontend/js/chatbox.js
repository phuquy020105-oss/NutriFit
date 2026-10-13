(() => {
  'use strict';

  const CHAT_API_URL = `${String(window.NUTRIFIT_API_BASE_URL || 'http://127.0.0.1:5000').replace(/\/+$/, '')}/api/chatbot/chat`;
  const CHAT_STORAGE_KEY = 'nutrifit_chat_history_v1';
  const MAX_MESSAGE_LENGTH = 2000;
  const MAX_HISTORY = 12;
  const MAX_STORED_MESSAGES = 60;

  function loadConversation() {
    try {
      const value = JSON.parse(sessionStorage.getItem(CHAT_STORAGE_KEY) || '[]');
      if (!Array.isArray(value)) return [];
      return value.filter(item => item && ['user', 'assistant'].includes(item.role) && typeof item.content === 'string')
        .slice(-MAX_STORED_MESSAGES);
    } catch (_) {
      return [];
    }
  }

  function saveConversation(items) {
    try {
      sessionStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(items.slice(-MAX_STORED_MESSAGES)));
    } catch (error) {
      console.warn('Không thể lưu lịch sử NutriFit AI:', error);
    }
  }

  function formatReply(value) {
    return String(value || '')
      .replace(/```[\w-]*\s*/g, '')
      .replace(/```/g, '')
      .replace(/`([^`]+)`/g, '$1')
      .replace(/\*\*(.*?)\*\*/gs, '$1')
      .replace(/__(.*?)__/gs, '$1')
      .replace(/(^|\n)#{1,6}\s+/g, '$1')
      .replace(/(^|\n)\s*[-*]\s+/g, '$1• ')
      .trim();
  }

  function initChatbox() {
    if (document.getElementById('nf-chat-panel')) return;

    const launcher = document.createElement('button');
    launcher.type = 'button';
    launcher.id = 'nf-chat-launcher';
    launcher.className = 'nf-chat-launcher';
    launcher.textContent = '✦';
    launcher.setAttribute('aria-label', 'Mở NutriFit AI');
    launcher.setAttribute('aria-expanded', 'false');

    const panel = document.createElement('section');
    panel.id = 'nf-chat-panel';
    panel.className = 'nf-chat-panel';
    panel.setAttribute('aria-label', 'NutriFit AI Chatbox');
    panel.setAttribute('aria-hidden', 'true');
    panel.innerHTML = `
      <header class="nf-chat-header">
        <div class="nf-chat-avatar" aria-hidden="true">✦</div>
        <div class="nf-chat-heading"><strong>NutriFit AI</strong><small>Trợ lý hỗ trợ người dùng</small></div>
        <button type="button" class="nf-chat-close" id="nf-chat-close" aria-label="Đóng khung chat">×</button>
      </header>
      <div class="nf-chat-messages" id="nf-chat-messages" role="log" aria-live="polite" aria-label="Nội dung hội thoại"></div>
      <div class="nf-chat-footer">
        <form class="nf-chat-form" id="nf-chat-form">
          <textarea class="nf-chat-input" id="nf-chat-input" rows="1" maxlength="${MAX_MESSAGE_LENGTH}" placeholder="Nhập câu hỏi của bạn..." aria-label="Tin nhắn" required></textarea>
          <button class="nf-chat-send" id="nf-chat-send" type="submit" aria-label="Gửi tin nhắn" disabled>➤</button>
        </form>
        <p class="nf-chat-note">NutriFit AI có thể mắc lỗi. Hãy kiểm tra thông tin quan trọng.</p>
      </div>`;

    document.body.append(launcher, panel);

    const messages = panel.querySelector('#nf-chat-messages');
    const input = panel.querySelector('#nf-chat-input');
    const send = panel.querySelector('#nf-chat-send');
    const form = panel.querySelector('#nf-chat-form');
    const close = panel.querySelector('#nf-chat-close');
    let conversation = loadConversation();
    let isSending = false;

    const scrollBottom = () => { messages.scrollTop = messages.scrollHeight; };

    function addMessage(role, value, error = false) {
      const bubble = document.createElement('div');
      bubble.className = `nf-chat-message ${role === 'user' ? 'nf-chat-user' : 'nf-chat-assistant'}${error ? ' nf-chat-error' : ''}`;
      // textContent is intentional: model output must never be treated as HTML.
      bubble.textContent = role === 'assistant' && !error ? formatReply(value) : String(value || '');
      messages.append(bubble);
      scrollBottom();
      return bubble;
    }

    function addWelcome() {
      addMessage('assistant', 'Xin chào! Mình là NutriFit AI. Mình có thể hỗ trợ bạn sử dụng website, tìm hiểu dinh dưỡng và xây dựng thói quen luyện tập.');
      const suggestions = document.createElement('div');
      suggestions.className = 'nf-chat-suggestions';
      [
        'NutriFit có những chức năng nào?',
        'BMR và TDEE là gì?',
        'Gợi ý món gà dưới 500 kcal'
      ].forEach(prompt => {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'nf-chat-suggestion';
        button.textContent = prompt;
        button.addEventListener('click', () => sendMessage(prompt));
        suggestions.append(button);
      });
      messages.append(suggestions);
      scrollBottom();
    }

    function showTyping() {
      const node = document.createElement('div');
      node.className = 'nf-chat-typing';
      node.setAttribute('role', 'status');
      node.textContent = 'NutriFit AI đang trả lời…';
      messages.append(node);
      scrollBottom();
      return node;
    }

    function updateSendButton() {
      send.disabled = isSending || !input.value.trim();
    }

    function openChat() {
      panel.classList.add('nf-chat-open');
      panel.setAttribute('aria-hidden', 'false');
      launcher.setAttribute('aria-expanded', 'true');
      input.focus();
      scrollBottom();
    }

    function closeChat() {
      panel.classList.remove('nf-chat-open');
      panel.setAttribute('aria-hidden', 'true');
      launcher.setAttribute('aria-expanded', 'false');
      launcher.focus();
    }

    function parseSseBlock(block, onChunk) {
      const payload = block.split(/\r?\n/)
        .filter(line => line.startsWith('data:'))
        .map(line => line.slice(5).trim())
        .join('\n');
      if (!payload) return null;
      let event;
      try { event = JSON.parse(payload); } catch (_) { return null; }
      if (event.type === 'chunk' && typeof event.text === 'string') onChunk(event.text);
      return event;
    }

    async function consumeStream(response, onChunk) {
      if (!response.body || typeof response.body.getReader !== 'function') {
        throw new Error('Trình duyệt không hỗ trợ đọc phản hồi streaming.');
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let finished = false;
      let streamError = null;

      while (true) {
        const { value, done } = await reader.read();
        buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

        let match;
        while ((match = /\r?\n\r?\n/.exec(buffer))) {
          const block = buffer.slice(0, match.index);
          buffer = buffer.slice(match.index + match[0].length);
          const event = parseSseBlock(block, onChunk);
          if (event?.type === 'done') finished = true;
          if (event?.type === 'error') streamError = event.message || 'AI gặp lỗi. Vui lòng thử lại.';
        }

        if (done) {
          if (buffer.trim()) {
            const event = parseSseBlock(buffer, onChunk);
            if (event?.type === 'done') finished = true;
            if (event?.type === 'error') streamError = event.message || 'AI gặp lỗi. Vui lòng thử lại.';
          }
          break;
        }
        if (streamError) {
          await reader.cancel().catch(() => {});
          break;
        }
      }

      if (streamError) throw new Error(streamError);
      if (!finished) throw new Error('Kết nối đã kết thúc trước khi AI hoàn tất câu trả lời.');
    }

    async function sendMessage(raw) {
      const message = String(raw || '').trim();
      if (!message || isSending) return;
      if (message.length > MAX_MESSAGE_LENGTH) {
        addMessage('assistant', 'Câu hỏi tối đa 2000 ký tự.', true);
        return;
      }

      const history = conversation.filter(item => !item.error).slice(-MAX_HISTORY).map(item => ({ role: item.role, content: item.content }));
      messages.querySelector('.nf-chat-suggestions')?.remove();
      addMessage('user', message);
      conversation.push({ role: 'user', content: message });
      saveConversation(conversation);
      input.value = '';
      input.style.height = 'auto';
      isSending = true;
      updateSendButton();
      const typing = showTyping();
      let replyBubble = null;
      let fullReply = '';

      try {
        const response = await fetch(CHAT_API_URL, {
          method: 'POST',
          credentials: 'omit',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message, history, stream: true })
        });

        const contentType = response.headers.get('content-type') || '';
        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          throw new Error(data.message || `Yêu cầu thất bại (HTTP ${response.status}).`);
        }

        if (!contentType.includes('text/event-stream')) {
          const data = await response.json().catch(() => ({}));
          if (!data.success || !data.reply) throw new Error(data.message || 'AI chưa trả về nội dung. Vui lòng thử lại.');
          fullReply = data.reply;
          typing.remove();
          replyBubble = addMessage('assistant', fullReply);
        } else {
          await consumeStream(response, piece => {
            fullReply += piece;
            if (!replyBubble) {
              typing.remove();
              replyBubble = addMessage('assistant', '');
            }
            replyBubble.textContent = formatReply(fullReply);
            scrollBottom();
          });
          if (!fullReply.trim()) throw new Error('AI chưa trả về nội dung. Vui lòng thử lại.');
        }

        conversation.push({ role: 'assistant', content: fullReply });
        saveConversation(conversation);
      } catch (error) {
        console.error('NutriFit Chatbox error:', error);
        const messageText = error?.message || 'Không thể kết nối NutriFit AI. Hãy kiểm tra Backend.';
        if (fullReply.trim()) {
          addMessage('assistant', 'Phản hồi có thể chưa đầy đủ do kết nối bị gián đoạn. Hãy thử hỏi tiếp nếu cần.', true);
          conversation.push({ role: 'assistant', content: fullReply, error: true });
        } else {
          addMessage('assistant', messageText, true);
          conversation.push({ role: 'assistant', content: messageText, error: true });
        }
        saveConversation(conversation);
      } finally {
        typing.remove();
        isSending = false;
        updateSendButton();
        if (panel.classList.contains('nf-chat-open')) input.focus();
      }
    }

    launcher.addEventListener('click', () => panel.classList.contains('nf-chat-open') ? closeChat() : openChat());
    close.addEventListener('click', closeChat);
    form.addEventListener('submit', event => { event.preventDefault(); sendMessage(input.value); });
    input.addEventListener('input', () => {
      input.style.height = 'auto';
      input.style.height = `${Math.min(input.scrollHeight, 110)}px`;
      updateSendButton();
    });
    input.addEventListener('keydown', event => {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        if (!send.disabled) form.requestSubmit();
      }
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && panel.classList.contains('nf-chat-open')) closeChat();
    });
    document.addEventListener('nutrifit:session-cleared', () => {
      conversation = [];
      saveConversation(conversation);
      messages.replaceChildren();
      addWelcome();
      closeChat();
    });

    if (conversation.length) {
      conversation.forEach(item => addMessage(item.role, item.content, Boolean(item.error)));
    } else {
      addWelcome();
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initChatbox, { once: true });
  else initChatbox();
})();
