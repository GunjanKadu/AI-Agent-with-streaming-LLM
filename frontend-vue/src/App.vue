<template>
  <div :class="['app-container', { dark: isDarkMode }]">
    <!-- History Sidebar -->
    <div :class="['history-sidebar', { open: showHistory }]">
      <div class="history-header">
        <h3>💬 History</h3>
        <button class="close-btn" @click="showHistory = false">✕</button>
      </div>
      <div class="history-list">
        <div
          v-for="(item, idx) in conversationHistory"
          :key="idx"
          class="history-item"
          @click="loadHistory(item)"
        >
          <div class="history-question">{{ item.question }}</div>
          <div class="history-time">{{ item.timestamp }}</div>
        </div>
        <div v-if="conversationHistory.length === 0" class="history-empty">
          No conversations yet
        </div>
      </div>
      <button
        class="clear-history-btn"
        @click="clearHistory"
        v-if="conversationHistory.length > 0"
      >
        🗑️ Clear All
      </button>
    </div>

    <!-- Main Content -->
    <div class="container">
      <div class="header">
        <div class="header-content">
          <div>
            <h1>🤖 AI Assistant</h1>
            <p class="subtitle">
              Powered by Llama 3.1 with Real-time Reasoning
            </p>
          </div>
          <div class="header-actions">
            <button
              class="icon-btn"
              @click="showHistory = !showHistory"
              title="View History"
            >
              📋
            </button>
            <button
              class="icon-btn"
              @click="toggleDarkMode"
              title="Toggle Dark Mode"
            >
              {{ isDarkMode ? "☀️" : "🌙" }}
            </button>
          </div>
        </div>
      </div>

      <!-- Example Prompts -->
      <div
        class="example-prompts"
        v-if="permanentMessages.length === 0 && !isProcessing"
      >
        <h3>✨ Try these examples:</h3>
        <div class="prompt-grid">
          <div
            v-for="(prompt, idx) in examplePrompts"
            :key="idx"
            class="prompt-card"
            @click="useExample(prompt)"
          >
            <span class="prompt-icon">{{ prompt.icon }}</span>
            <span class="prompt-text">{{ prompt.text }}</span>
          </div>
        </div>
      </div>

      <div class="input-row">
        <input
          v-model="question"
          placeholder="Ask me anything about SAP BTP, technology, or calculations..."
          @keyup.enter="send"
          :disabled="isProcessing"
        />
        <button @click="send" :disabled="isProcessing">
          <span v-if="!isProcessing">Ask</span>
          <span v-else>Processing...</span>
        </button>
      </div>

      <div class="log">
        <!-- User question and answer -->
        <div
          v-for="(item, idx) in permanentMessages"
          :key="'perm-' + idx"
          :class="['bubble', item.type]"
        >
          <div class="bubble-header">
            <span class="bubble-icon">{{ getBubbleIcon(item.type) }}</span>
            <span class="meta">{{ item.type }}</span>
          </div>
          <div class="text" v-html="renderMarkdown(item.text)"></div>
          <!-- Copy button for final answers -->
          <button
            v-if="item.type === 'final'"
            class="copy-btn"
            @click="copyToClipboard(item.text)"
            :class="{ copied: copiedMessageIdx === idx }"
          >
            {{ copiedMessageIdx === idx ? "✓ Copied!" : "📋 Copy" }}
          </button>
        </div>

        <!-- Response Time Display -->
        <div v-if="responseTime > 0 && !isProcessing" class="response-time">
          ⚡ Answered in {{ (responseTime / 1000).toFixed(1) }}s
        </div>

        <!-- Thinking/processing section (shows immediately, updates with all steps) -->
        <div v-if="isProcessing" class="thinking-section">
          <div class="thinking-header">
            <span class="thinking-icon">🧠</span>
            <span class="thinking-text">AI is thinking...</span>
            <span class="spinner"></span>
          </div>
          <div class="thinking-content" v-if="thinkingSteps.length > 0">
            <div
              v-for="(step, idx) in thinkingSteps"
              :key="'think-' + idx"
              class="thinking-step"
            >
              <span class="step-icon">{{ getStepIcon(step.type) }}</span>
              <span class="step-text">{{ step.text }}</span>
            </div>
          </div>
          <div v-else class="thinking-placeholder">
            <span class="pulse-dot"></span>
            <span class="pulse-dot"></span>
            <span class="pulse-dot"></span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      question: "",
      permanentMessages: [],
      thinkingSteps: [],
      isProcessing: false,
      responseTime: 0,
      startTime: 0,
      copiedMessageIdx: null,
      isDarkMode: false,
      showHistory: false,
      conversationHistory: [],
      examplePrompts: [
        { icon: "🌐", text: "What is SAP BTP and its key services?" },
        { icon: "🔧", text: "Explain microservices architecture" },
        { icon: "🧮", text: "What is 156 multiplied by 89?" },
        { icon: "💡", text: "Best practices for cloud migration" },
      ],
    };
  },
  mounted() {
    // Load dark mode preference
    const savedTheme = localStorage.getItem("theme");
    if (savedTheme === "dark") {
      this.isDarkMode = true;
    }

    // Load conversation history
    const savedHistory = localStorage.getItem("conversationHistory");
    if (savedHistory) {
      this.conversationHistory = JSON.parse(savedHistory);
    }
  },
  methods: {
    getBubbleIcon(type) {
      const icons = {
        user: "👤",
        final: "✨",
        error: "❌",
      };
      return icons[type] || "💬";
    },
    getStepIcon(type) {
      const icons = {
        analysis: "🔍",
        step: "⚙️",
        error: "❌",
      };
      return icons[type] || "•";
    },
    toggleDarkMode() {
      this.isDarkMode = !this.isDarkMode;
      localStorage.setItem("theme", this.isDarkMode ? "dark" : "light");
    },
    useExample(prompt) {
      this.question = prompt.text;
      this.send();
    },
    copyToClipboard(text) {
      navigator.clipboard.writeText(text).then(() => {
        const idx = this.permanentMessages.findIndex(
          (m) => m.text === text && m.type === "final"
        );
        this.copiedMessageIdx = idx;
        setTimeout(() => {
          this.copiedMessageIdx = null;
        }, 2000);
      });
    },
    loadHistory(item) {
      this.permanentMessages = [
        { type: "user", text: item.question },
        { type: "final", text: item.answer },
      ];
      this.showHistory = false;
    },
    clearHistory() {
      this.conversationHistory = [];
      localStorage.removeItem("conversationHistory");
    },
    saveToHistory(question, answer) {
      const timestamp = new Date().toLocaleString();
      this.conversationHistory.unshift({
        question,
        answer,
        timestamp,
      });
      // Keep only last 10 conversations
      if (this.conversationHistory.length > 10) {
        this.conversationHistory.pop();
      }
      localStorage.setItem(
        "conversationHistory",
        JSON.stringify(this.conversationHistory)
      );
    },
    renderMarkdown(text) {
      if (!text) return "";
      let html = text;

      // Code blocks (triple backticks)
      html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
        return `<pre><code class="language-${
          lang || "plaintext"
        }">${this.escapeHtml(code.trim())}</code></pre>`;
      });

      // Inline code
      html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

      // Bold
      html = html.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
      html = html.replace(/__(.+?)__/g, "<strong>$1</strong>");

      // Italic
      html = html.replace(/\*(.+?)\*/g, "<em>$1</em>");
      html = html.replace(/_(.+?)_/g, "<em>$1</em>");

      // Links
      html = html.replace(
        /\[([^\]]+)\]\(([^)]+)\)/g,
        '<a href="$2" target="_blank">$1</a>'
      );

      // Lists (simple)
      html = html.replace(/^\s*[-*]\s+(.+)$/gm, "<li>$1</li>");
      html = html.replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>");

      // Line breaks
      html = html.replace(/\n/g, "<br>");

      return html;
    },
    escapeHtml(text) {
      const div = document.createElement("div");
      div.textContent = text;
      return div.innerHTML;
    },
    async send() {
      if (!this.question.trim() || this.isProcessing) return;

      this.isProcessing = true;
      this.permanentMessages = [];
      this.thinkingSteps = [];
      this.responseTime = 0;
      this.startTime = Date.now();

      const currentQuestion = this.question;

      // Add user question
      this.permanentMessages.push({ type: "user", text: this.question });

      // Scroll to show thinking section immediately
      this.$nextTick(() => window.scrollTo(0, document.body.scrollHeight));

      try {
        const resp = await fetch("/api/ask", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question: this.question }),
        });

        if (!resp.ok) {
          this.permanentMessages.push({
            type: "error",
            text: "Server error. Please try again.",
          });
          this.isProcessing = false;
          return;
        }

        const reader = resp.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buf += decoder.decode(value, { stream: true });
          let lines = buf.split("\n");
          buf = lines.pop();

          for (const line of lines) {
            if (!line.trim()) continue;
            try {
              const obj = JSON.parse(line);

              if (obj.type === "final") {
                // Stop thinking and show final answer
                this.isProcessing = false;
                this.thinkingSteps = [];
                this.permanentMessages.push(obj);
                this.responseTime = Date.now() - this.startTime;
                // Save to history
                this.saveToHistory(currentQuestion, obj.text);
              } else if (obj.type === "analysis" || obj.type === "step") {
                // Add ALL steps to thinking section
                this.thinkingSteps.push(obj);
              } else if (obj.type === "error") {
                this.isProcessing = false;
                this.thinkingSteps = [];
                this.permanentMessages.push(obj);
              }

              this.$nextTick(() =>
                window.scrollTo(0, document.body.scrollHeight)
              );
            } catch (e) {
              console.error("Parse error:", e);
            }
          }
        }
      } catch (error) {
        this.permanentMessages.push({
          type: "error",
          text: "Connection error. Please check if the backend is running.",
        });
      } finally {
        this.isProcessing = false;
      }
    },
  },
};
</script>

<style scoped>
* {
  box-sizing: border-box;
}

.app-container {
  position: relative;
  min-height: 100vh;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e9f2 100%);
  transition: background 0.3s;
}

.app-container.dark {
  background: linear-gradient(135deg, #1a202c 0%, #2d3748 100%);
}

/* History Sidebar */
.history-sidebar {
  position: fixed;
  top: 0;
  right: -350px;
  width: 350px;
  height: 100vh;
  background: white;
  box-shadow: -4px 0 12px rgba(0, 0, 0, 0.15);
  transition: right 0.3s ease;
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.dark .history-sidebar {
  background: #2d3748;
  color: #e2e8f0;
}

.history-sidebar.open {
  right: 0;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 2px solid #e2e8f0;
}

.dark .history-header {
  border-bottom-color: #4a5568;
}

.history-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #64748b;
  padding: 0;
  width: 32px;
  height: 32px;
  border-radius: 6px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #f1f5f9;
  color: #1a202c;
}

.dark .close-btn {
  color: #94a3b8;
}

.dark .close-btn:hover {
  background: #4a5568;
  color: #e2e8f0;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.history-item {
  padding: 14px;
  margin-bottom: 10px;
  background: #f8fafc;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 2px solid transparent;
}

.history-item:hover {
  background: #e0e7ff;
  border-color: #6366f1;
}

.dark .history-item {
  background: #374151;
}

.dark .history-item:hover {
  background: #4a5568;
  border-color: #6366f1;
}

.history-question {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 6px;
  color: #1a202c;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dark .history-question {
  color: #e2e8f0;
}

.history-time {
  font-size: 12px;
  color: #64748b;
}

.dark .history-time {
  color: #94a3b8;
}

.history-empty {
  text-align: center;
  color: #94a3b8;
  padding: 40px 20px;
  font-size: 14px;
}

.clear-history-btn {
  margin: 12px;
  padding: 12px;
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.clear-history-btn:hover {
  background: #dc2626;
  transform: translateY(-1px);
}

.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px 20px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
}

.header {
  text-align: center;
  margin-bottom: 32px;
  padding: 24px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
}

.dark .header {
  background: #2d3748;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.icon-btn {
  background: #f1f5f9;
  border: 2px solid #e2e8f0;
  width: 44px;
  height: 44px;
  border-radius: 10px;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.2s;
  padding: 0;
}

.icon-btn:hover {
  background: #e0e7ff;
  border-color: #6366f1;
  transform: translateY(-2px);
}

.dark .icon-btn {
  background: #374151;
  border-color: #4a5568;
}

.dark .icon-btn:hover {
  background: #4a5568;
  border-color: #6366f1;
}

h1 {
  color: #1a202c;
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 700;
}

.dark h1 {
  color: #e2e8f0;
}

.subtitle {
  color: #64748b;
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}

.dark .subtitle {
  color: #94a3b8;
}

/* Example Prompts */
.example-prompts {
  margin-bottom: 24px;
  background: white;
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
}

.dark .example-prompts {
  background: #2d3748;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.example-prompts h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 700;
  color: #1a202c;
}

.dark .example-prompts h3 {
  color: #e2e8f0;
}

.prompt-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.prompt-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  background: #f8fafc;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
}

.prompt-card:hover {
  background: #e0e7ff;
  border-color: #6366f1;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(99, 102, 241, 0.2);
}

.dark .prompt-card {
  background: #374151;
  border-color: #4a5568;
}

.dark .prompt-card:hover {
  background: #4a5568;
  border-color: #6366f1;
}

.prompt-icon {
  font-size: 20px;
  flex-shrink: 0;
}

.prompt-text {
  font-size: 14px;
  font-weight: 500;
  color: #1a202c;
  flex: 1;
}

.dark .prompt-text {
  color: #e2e8f0;
}

.input-row {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  background: white;
  padding: 12px;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.07);
}

.dark .input-row {
  background: #2d3748;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

input {
  flex: 1;
  padding: 14px 18px;
  font-size: 15px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  transition: all 0.2s;
  background: #f8fafc;
  color: #1a202c;
}

.dark input {
  background: #374151;
  border-color: #4a5568;
  color: #e2e8f0;
}

input:focus {
  outline: none;
  border-color: #3b82f6;
  background: white;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.dark input:focus {
  background: #374151;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

input:disabled {
  background: #f1f5f9;
  cursor: not-allowed;
  opacity: 0.6;
}

.dark input:disabled {
  background: #1a202c;
}

input::placeholder {
  color: #94a3b8;
}

button {
  padding: 14px 28px;
  font-size: 15px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

button:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(59, 130, 246, 0.4);
}

button:active:not(:disabled) {
  transform: translateY(0);
}

button:disabled {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
  cursor: not-allowed;
  box-shadow: none;
}

.log {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.bubble {
  padding: 18px 20px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
  animation: slideIn 0.3s ease-out;
  position: relative;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.bubble-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.bubble-icon {
  font-size: 18px;
}

.bubble .meta {
  font-size: 11px;
  color: inherit;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  font-weight: 600;
  opacity: 0.7;
}

.bubble .text {
  font-size: 15px;
  line-height: 1.7;
  white-space: pre-wrap;
  color: inherit;
}

/* Markdown Styling */
.text :deep(pre) {
  background: #1e293b;
  color: #e2e8f0;
  padding: 16px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 12px 0;
}

.text :deep(code) {
  background: #f1f5f9;
  color: #e11d48;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: "Courier New", monospace;
  font-size: 14px;
}

.dark .text :deep(code) {
  background: #1e293b;
  color: #fb7185;
}

.text :deep(pre code) {
  background: transparent;
  color: inherit;
  padding: 0;
}

.text :deep(strong) {
  font-weight: 700;
}

.text :deep(em) {
  font-style: italic;
}

.text :deep(a) {
  color: #3b82f6;
  text-decoration: underline;
}

.text :deep(a:hover) {
  color: #2563eb;
}

.text :deep(ul) {
  margin: 8px 0;
  padding-left: 24px;
}

.text :deep(li) {
  margin: 4px 0;
}

.bubble.user {
  background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
  color: white;
  margin-left: auto;
  max-width: 85%;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.bubble.final {
  background: white;
  border: 2px solid #10b981;
  color: #1a202c;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
}

.dark .bubble.final {
  background: #2d3748;
  color: #e2e8f0;
  border-color: #10b981;
}

.bubble.final .bubble-icon {
  color: #10b981;
}

.bubble.final .meta {
  color: #10b981;
}

.bubble.error {
  background: #fee2e2;
  border: 2px solid #ef4444;
  color: #991b1b;
}

.dark .bubble.error {
  background: #7f1d1d;
  color: #fecaca;
}

/* Copy Button */
.copy-btn {
  margin-top: 12px;
  padding: 8px 16px;
  font-size: 13px;
  background: #10b981;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 600;
  display: inline-block;
}

.copy-btn:hover {
  background: #059669;
  transform: translateY(-1px);
}

.copy-btn.copied {
  background: #6366f1;
}

/* Response Time */
.response-time {
  text-align: center;
  padding: 12px;
  background: #f0fdf4;
  border: 2px solid #10b981;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #065f46;
  animation: fadeIn 0.3s ease-out;
}

.dark .response-time {
  background: #064e3b;
  color: #6ee7b7;
}

/* Thinking section */
.thinking-section {
  background: white;
  border-radius: 12px;
  padding: 20px;
  border: 2px solid #f59e0b;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.15);
  animation: fadeIn 0.3s ease-out;
}

.dark .thinking-section {
  background: #2d3748;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.thinking-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding-bottom: 14px;
  border-bottom: 2px solid #fef3c7;
}

.dark .thinking-header {
  border-bottom-color: #78350f;
}

.thinking-icon {
  font-size: 24px;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
}

.thinking-text {
  font-weight: 700;
  color: #92400e;
  font-size: 15px;
  letter-spacing: 0.3px;
}

.dark .thinking-text {
  color: #fbbf24;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2.5px solid #fef3c7;
  border-top-color: #f59e0b;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin-left: auto;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.thinking-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.thinking-step {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
  background: #fffbeb;
  border-radius: 8px;
  border-left: 3px solid #f59e0b;
  font-size: 14px;
  color: #78350f;
  animation: slideIn 0.2s ease-out;
}

.dark .thinking-step {
  background: #374151;
  color: #fbbf24;
}

.step-icon {
  font-size: 18px;
  flex-shrink: 0;
  margin-top: 1px;
}

.step-text {
  flex: 1;
  line-height: 1.6;
}

.thinking-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 8px;
  padding: 20px;
}

.pulse-dot {
  width: 10px;
  height: 10px;
  background: #f59e0b;
  border-radius: 50%;
  animation: pulseDot 1.4s ease-in-out infinite;
}

.pulse-dot:nth-child(2) {
  animation-delay: 0.2s;
}

.pulse-dot:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes pulseDot {
  0%,
  80%,
  100% {
    transform: scale(0);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}
</style>
