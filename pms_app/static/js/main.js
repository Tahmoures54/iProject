// Alpine.js Store for Dark Mode
document.addEventListener('alpine:init', () => {
  Alpine.store('theme', {
    dark: localStorage.getItem('theme') === 'dark' || 
          (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches),
    toggle() {
      this.dark = !this.dark;
      localStorage.setItem('theme', this.dark ? 'dark' : 'light');
      this.apply();
    },
    init() {
      this.apply();
    },
    apply() {
      if (this.dark) {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
    }
  });
  
  // Initialize immediately on load
  Alpine.store('theme').init();
});

// AI Chat Toggle Logic
function toggleChat() {
  const chat = document.getElementById('chat-window');
  const isHidden = chat.classList.contains('hidden');
  
  if (isHidden) {
    chat.classList.remove('hidden');
    chat.classList.add('flex');
    const messages = document.getElementById('chat-messages');
    messages.scrollTop = messages.scrollHeight;
  } else {
    chat.classList.add('hidden');
    chat.classList.remove('flex');
  }
}

// AI Chat Send Logic
function sendToAI() {
  const input = document.getElementById('ai-input');
  const messagesContainer = document.getElementById('chat-messages');
  const userVal = input.value.trim();
  
  if (!userVal) return;

  // User Message
  const userMsg = document.createElement('div');
  userMsg.className = 'bg-brand-600 text-white p-3 rounded-2xl rounded-tl-sm max-w-[85%] self-end shadow-sm';
  userMsg.innerText = userVal;
  messagesContainer.appendChild(userMsg);

  input.value = '';
  messagesContainer.scrollTop = messagesContainer.scrollHeight;

  // Simulated Bot "Typing..."
  setTimeout(() => {
    const typingMsg = document.createElement('div');
    typingMsg.className = 'bg-white dark:bg-slate-800 p-3 rounded-2xl rounded-tr-sm border border-slate-100 dark:border-slate-700 shadow-sm text-slate-500 dark:text-slate-400 max-w-[85%] self-start animate-pulse';
    typingMsg.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> در حال پردازش...';
    messagesContainer.appendChild(typingMsg);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    // Remove typing and add response
    setTimeout(() => {
      typingMsg.remove();
      const botMsg = document.createElement('div');
      botMsg.className = 'bg-white dark:bg-slate-800 p-3 rounded-2xl rounded-tr-sm border border-slate-100 dark:border-slate-700 shadow-sm text-slate-700 dark:text-slate-200 max-w-[85%] self-start';
      botMsg.innerText = 'این یک پاسخ آزمایشی از سمت سیستم است. برای اتصال به هوش مصنوعی واقعی، توکن API خود را در سرویس مربوطه قرار دهید.';
      messagesContainer.appendChild(botMsg);
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 1500);
  }, 500);
}