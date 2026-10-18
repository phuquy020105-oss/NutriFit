(() => {
  'use strict';
  const form = document.getElementById('chatForm');
  const textarea = document.getElementById('chatMessage');
  const sendButton = document.getElementById('sendButton');
  const count = document.getElementById('charCount');
  const scroll = document.getElementById('chatScroll');
  const sidebar = document.getElementById('chatSidebar');
  const scrim = document.getElementById('sidebarScrim');
  const menu = document.getElementById('mobileMenu');
  if (!form || !textarea) return;
  let sending = false;
  const refresh = () => {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
    count.textContent = `${textarea.value.length} / 2000`;
    sendButton.disabled = sending || !textarea.value.trim();
  };
  textarea.addEventListener('input', refresh);
  textarea.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      if (!sendButton.disabled) form.requestSubmit();
    }
  });
  document.querySelectorAll('[data-prompt]').forEach((button) => {
    button.addEventListener('click', () => {
      textarea.value = button.dataset.prompt || '';
      refresh();
      textarea.focus();
    });
  });
  document.querySelectorAll('.copy-answer').forEach((button) => {
    button.addEventListener('click', async () => {
      const text = button.closest('.message-body')?.querySelector('.message-text')?.textContent || '';
      try {
        await navigator.clipboard.writeText(text);
        const label = button.querySelector('span');
        if (label) label.textContent = 'Đã sao chép';
      } catch (_) { /* Clipboard unavailable: keep original button. */ }
    });
  });
  if (menu && scrim && sidebar) {
    const toggle = (opened) => {
      document.body.classList.toggle('sidebar-open', opened);
      menu.setAttribute('aria-expanded', String(opened));
    };
    menu.addEventListener('click', () => toggle(!document.body.classList.contains('sidebar-open')));
    scrim.addEventListener('click', () => toggle(false));
    document.addEventListener('keydown', (ev) => { if (ev.key === 'Escape') toggle(false); });
  }
  form.addEventListener('submit', (ev) => {
    if (sending || !textarea.value.trim()) { ev.preventDefault(); return; }
    sending = true;
    sendButton.innerHTML = '<span>Đang gửi...</span><span class="loading-spinner" aria-hidden="true"></span>';
    sendButton.disabled = true;
    // Standard POST continues, as in the existing Servlet. A visual state tells
    // the user the request is in progress; no fake or fabricated AI responses.
  });
  refresh();
  if (scroll) scroll.scrollTop = scroll.scrollHeight;
})();
