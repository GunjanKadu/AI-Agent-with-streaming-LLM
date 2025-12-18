<template>
  <div :class="['app-container', { dark: isDarkMode }]">
    <!-- History Sidebar -->
    <div :class="['history-sidebar', { open: showHistory }]">
      <div class="history-header">
        <h3><span class="icon-chat"></span> History</h3>
        <button class="close-btn" @click="showHistory = false">×</button>
      </div>
      <div class="history-search">
        <input
          v-model="historySearchQuery"
          placeholder="Search history..."
          class="search-input"
        />
      </div>
      <div class="history-list">
        <div
          v-for="(item, idx) in filteredHistory"
          :key="idx"
          class="history-item"
        >
          <div class="history-content" @click="loadHistory(item)">
            <div class="history-question">{{ item.question }}</div>
            <div class="history-time">{{ item.timestamp }}</div>
          </div>
          <button
            class="delete-history-item-btn"
            @click.stop="deleteHistoryItem(idx)"
            title="Delete this conversation"
          >
            <span class="icon-trash"></span>
          </button>
        </div>
        <div
          v-if="filteredHistory.length === 0 && conversationHistory.length > 0"
          class="history-empty"
        >
          No matching conversations
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
        <span class="icon-trash"></span> Clear All
      </button>
    </div>

    <!-- Main Content -->
    <div class="container">
      <div class="header">
        <div class="header-content">
          <div class="header-left">
            <div class="logo-container">
              <div class="logo-icon"></div>
              <div>
                <h1>AI Code Assistant</h1>
                <p class="subtitle">
                  Powered by Llama 3.1 with Real-time Analysis
                </p>
              </div>
            </div>
          </div>
          <div class="header-actions">
            <button
              class="icon-btn"
              @click="showHistory = !showHistory"
              title="View History"
            >
              <span class="icon-history"></span>
            </button>
          </div>
        </div>
      </div>

      <!-- Example Prompts -->
      <div class="example-prompts">
        <h3><span class="icon-sparkle"></span> Try these examples:</h3>
        <div class="prompt-grid">
          <div
            v-for="(prompt, idx) in examplePrompts"
            :key="idx"
            class="prompt-card"
            @click="useExample(prompt)"
          >
            <span
              class="prompt-icon"
              v-html="getPromptIcon(prompt.icon)"
            ></span>
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
        <button
          class="voice-btn"
          @click="toggleVoiceInput"
          :class="{ listening: isListening }"
          :disabled="isProcessing"
          title="Voice Input"
        >
          <span :class="isListening ? 'icon-mic-active' : 'icon-mic'"></span>
        </button>
        <button @click="send" :disabled="isProcessing" class="send-btn">
          <span v-if="!isProcessing" class="icon-send"></span>
          <span v-else class="loading-spinner"></span>
          <span v-if="!isProcessing">Send</span>
          <span v-else>Processing</span>
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
            <span
              class="bubble-icon-styled"
              v-html="getBubbleIconStyled(item.type)"
            ></span>
            <span class="meta">{{ getMetaLabel(item.type) }}</span>
            <!-- Edit button for user messages -->
            <button
              v-if="item.type === 'user' && !isProcessing"
              class="edit-btn"
              @click="editMessage(item.text)"
              title="Edit & Resend"
            >
              <span class="icon-edit"></span>
            </button>
          </div>
          <div class="text" v-html="renderMarkdown(item.text)"></div>
          <!-- Copy button for final answers -->
          <button
            v-if="item.type === 'final'"
            class="copy-btn"
            @click="copyToClipboard(item.text)"
            :class="{ copied: copiedMessageIdx === idx }"
          >
            <span
              :class="copiedMessageIdx === idx ? 'icon-check' : 'icon-copy'"
            ></span>
            {{ copiedMessageIdx === idx ? "Copied!" : "Copy" }}
          </button>
        </div>

        <!-- Response Time Display -->
        <div v-if="responseTime > 0 && !isProcessing" class="response-time">
          ⚡ Answered in {{ (responseTime / 1000).toFixed(1) }}s
        </div>

        <!-- File References Section -->
        <div
          v-if="fileReferences.length > 0 && !isProcessing"
          class="file-references-section"
        >
          <div class="file-references-header">
            <span class="icon-sparkle"></span>
            <h3>📂 Referenced Files</h3>
          </div>
          <div class="file-references-list">
            <div
              v-for="(ref, idx) in fileReferences"
              :key="'ref-' + idx"
              class="file-reference-item"
              @click="openInEditor(ref.file, ref.line)"
            >
              <div class="file-ref-icon">📄</div>
              <div class="file-ref-details">
                <div class="file-ref-name">{{ ref.file }}</div>
                <div class="file-ref-line">Line {{ ref.line }}</div>
              </div>
              <div class="file-ref-arrow">→</div>
            </div>
          </div>
        </div>

        <!-- Directory Tree Section -->
        <div
          v-if="directoryTrees.length > 0 && !isProcessing"
          class="directory-tree-section"
        >
          <div class="directory-tree-header">
            <span class="tree-icon">🌳</span>
            <h3>📂 Codebase Structure</h3>
          </div>
          <div
            v-for="(tree, idx) in directoryTrees"
            :key="'tree-' + idx"
            class="directory-tree-card"
          >
            <pre class="tree-content">{{ tree.tree }}</pre>
          </div>
        </div>

        <!-- Code Snippets Section -->
        <div
          v-if="codeSnippets.length > 0 && !isProcessing"
          class="code-snippets-section"
        >
          <div class="code-snippets-header">
            <span class="code-icon">📄</span>
            <span class="code-title">Referenced Code Files</span>
          </div>
          <div
            v-for="(snippet, idx) in codeSnippets"
            :key="'snippet-' + idx"
            class="code-snippet-card"
          >
            <div class="snippet-header">
              <div class="snippet-info">
                <div class="snippet-file-row">
                  <span class="snippet-file">📁 {{ snippet.file }}</span>
                  <span class="snippet-language">{{
                    getLanguageLabel(snippet.language)
                  }}</span>
                </div>
                <span class="snippet-lines">Lines: {{ snippet.lines }}</span>
              </div>
              <button
                class="copy-btn-small"
                @click="copyCodeSnippet(snippet.code, idx)"
                :class="{ copied: copiedSnippetIdx === idx }"
              >
                {{ copiedSnippetIdx === idx ? "✓" : "📋" }}
              </button>
            </div>
            <pre
              class="code-block"
            ><code :class="'language-' + snippet.language">{{ snippet.code }}</code></pre>
          </div>
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
import Prism from "prismjs";
import "prismjs/themes/prism-tomorrow.css";
// Import language support
import "prismjs/components/prism-python";
import "prismjs/components/prism-javascript";
import "prismjs/components/prism-typescript";
import "prismjs/components/prism-java";
import "prismjs/components/prism-json";
import "prismjs/components/prism-yaml";
import "prismjs/components/prism-markdown";

export default {
  data() {
    return {
      question: "",
      permanentMessages: [],
      thinkingSteps: [],
      codeSnippets: [],
      fileReferences: [],
      directoryTrees: [],
      isProcessing: false,
      responseTime: 0,
      startTime: 0,
      copiedMessageIdx: null,
      copiedSnippetIdx: null,
      isDarkMode: false,
      showHistory: false,
      conversationHistory: [],
      examplePrompts: [
        { icon: "🌐", text: "What is SAP BTP and its key services?" },
        { icon: "🧮", text: "What is 156 multiplied by 89?" },
        {
          icon: "🔎",
          text: "Explain how the updateIdentityProvider endpoint works",
        },
        {
          icon: "📂",
          text: "What files are in the XSUAA uaa-security-provisioning repository?",
        },
        { icon: "💡", text: "How does token refresh work in the code?" },
        {
          icon: "💡",
          text: "Explain how the createIdentityProvider endpoint works",
        },
      ],
      // New features
      historySearchQuery: "",
      isListening: false,
      recognition: null,
      showStats: false,
      sessionStats: {
        totalQuestions: 0,
        avgResponseTime: 0,
        totalTime: 0,
      },
      responseTimes: [],
    };
  },
  computed: {
    filteredHistory() {
      if (!this.historySearchQuery.trim()) {
        return this.conversationHistory;
      }
      const query = this.historySearchQuery.toLowerCase();
      return this.conversationHistory.filter(
        (item) =>
          item.question.toLowerCase().includes(query) ||
          item.answer.toLowerCase().includes(query)
      );
    },
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

    // Initialize Web Speech API for voice input
    if ("webkitSpeechRecognition" in window || "SpeechRecognition" in window) {
      const SpeechRecognition =
        window.SpeechRecognition || window.webkitSpeechRecognition;
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.lang = "en-US";

      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        this.question = transcript;
        this.isListening = false;
      };

      this.recognition.onerror = () => {
        this.isListening = false;
      };

      this.recognition.onend = () => {
        this.isListening = false;
      };
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
    getBubbleIconStyled(type) {
      const icons = {
        user: '<div class="icon-user-bubble"></div>',
        final: '<div class="icon-success-bubble"></div>',
        error: '<div class="icon-error-bubble"></div>',
      };
      return icons[type] || '<div class="icon-message-bubble"></div>';
    },
    getMetaLabel(type) {
      const labels = {
        user: "You",
        final: "Assistant",
        error: "Error",
        analysis: "Analyzing",
        step: "Processing",
      };
      return labels[type] || type;
    },
    getPromptIcon(iconType) {
      const iconMap = {
        "🌐": '<div class="icon-globe"></div>',
        "🧮": '<div class="icon-calc"></div>',
        "🔎": '<div class="icon-search"></div>',
        "🔍": '<div class="icon-search"></div>',
        "📄": '<div class="icon-file"></div>',
        "🔐": '<div class="icon-lock"></div>',
        "📂": '<div class="icon-folder"></div>',
        "💡": '<div class="icon-lightbulb"></div>',
      };
      return iconMap[iconType] || '<div class="icon-default"></div>';
    },
    getStepIcon(type) {
      const icons = {
        analysis: "🔍",
        step: "⚙️",
        error: "❌",
      };
      return icons[type] || "•";
    },
    getLanguageLabel(lang) {
      const labels = {
        python: "Python",
        javascript: "JavaScript",
        typescript: "TypeScript",
        java: "Java",
        vue: "Vue",
        json: "JSON",
        yaml: "YAML",
        markdown: "Markdown",
        plaintext: "Text",
      };
      return labels[lang] || lang.charAt(0).toUpperCase() + lang.slice(1);
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
    copyCodeSnippet(code, idx) {
      // Remove line numbers before copying
      const cleanCode = code
        .split("\n")
        .map((line) => {
          // Remove the line number prefix (e.g., "  10 | ")
          return line.replace(/^\s*\d+\s*\|\s*/, "");
        })
        .join("\n");

      navigator.clipboard.writeText(cleanCode).then(() => {
        this.copiedSnippetIdx = idx;
        setTimeout(() => {
          this.copiedSnippetIdx = null;
        }, 2000);
      });
    },
    loadHistory(item) {
      this.permanentMessages = [
        { type: "user", text: item.question },
        { type: "final", text: item.answer },
      ];
      this.fileReferences = item.fileReferences || [];
      this.codeSnippets = item.codeSnippets || [];
      this.directoryTrees = item.directoryTrees || [];
      this.showHistory = false;
      // Apply syntax highlighting after loading code snippets
      if (this.codeSnippets.length > 0) {
        this.$nextTick(() => {
          Prism.highlightAll();
        });
      }
    },
    clearHistory() {
      this.conversationHistory = [];
      localStorage.removeItem("conversationHistory");
      this.sessionStats = {
        totalQuestions: 0,
        avgResponseTime: 0,
        totalTime: 0,
      };
      this.responseTimes = [];
    },
    deleteHistoryItem(idx) {
      // Remove the item at the specified index
      this.conversationHistory.splice(idx, 1);
      // Update localStorage
      localStorage.setItem(
        "conversationHistory",
        JSON.stringify(this.conversationHistory)
      );
    },
    toggleVoiceInput() {
      if (!this.recognition) {
        alert(
          "Voice input is not supported in your browser. Please use Chrome, Edge, or Safari."
        );
        return;
      }

      if (this.isListening) {
        this.recognition.stop();
        this.isListening = false;
      } else {
        this.recognition.start();
        this.isListening = true;
      }
    },
    editMessage(text) {
      this.question = text;
      // Scroll to input
      this.$nextTick(() => {
        const input = document.querySelector(".input-row input");
        if (input) {
          input.focus();
          window.scrollTo({ top: 0, behavior: "smooth" });
        }
      });
    },
    updateStats(responseTime) {
      this.responseTimes.push(responseTime);
      this.sessionStats.totalQuestions++;
      this.sessionStats.totalTime += responseTime;
      this.sessionStats.avgResponseTime = (
        this.sessionStats.totalTime /
        this.sessionStats.totalQuestions /
        1000
      ).toFixed(1);
    },
    openInEditor(file, line) {
      // Open file in VS Code using vscode:// protocol
      const fullPath = `/Users/I567440/Desktop/Coding/SAP/xsuaa/${file}`;
      const url = `vscode://file${fullPath}:${line}`;
      window.location.href = url;
    },
    saveToHistory(question, answer) {
      const timestamp = new Date().toLocaleString();
      this.conversationHistory.unshift({
        question,
        answer,
        timestamp,
        fileReferences: [...this.fileReferences],
        codeSnippets: [...this.codeSnippets],
        directoryTrees: [...this.directoryTrees],
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
      this.codeSnippets = [];
      this.fileReferences = [];
      this.directoryTrees = [];
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
                // Update stats
                this.updateStats(this.responseTime);
                // Save to history
                this.saveToHistory(currentQuestion, obj.text);
              } else if (obj.type === "code_snippet") {
                // Add code snippet to display
                this.codeSnippets.push(obj);
                // Apply syntax highlighting after DOM update
                this.$nextTick(() => {
                  Prism.highlightAll();
                });
              } else if (obj.type === "file_reference") {
                // Add file reference to display
                this.fileReferences.push(obj);
              } else if (obj.type === "directory_tree") {
                // Add directory tree to display
                this.directoryTrees.push(obj);
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

/* Modern Icon Styles */
.icon-chat::before,
.icon-trash::before,
.icon-stats::before,
.icon-history::before,
.icon-sun::before,
.icon-moon::before,
.icon-sparkle::before,
.icon-send::before,
.icon-mic::before,
.icon-mic-active::before,
.icon-edit::before,
.icon-copy::before,
.icon-check::before {
  content: "";
  display: inline-block;
  width: 18px;
  height: 18px;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  vertical-align: middle;
}

.icon-chat::before {
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor'%3E%3Cpath d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.icon-trash::before {
  background: currentColor;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor'%3E%3Cpolyline points='3 6 5 6 21 6'/%3E%3Cpath d='M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.icon-stats::before {
  background: currentColor;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor'%3E%3Cline x1='12' y1='20' x2='12' y2='10'/%3E%3Cline x1='18' y1='20' x2='18' y2='4'/%3E%3Cline x1='6' y1='20' x2='6' y2='16'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.icon-history::before {
  background: currentColor;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor'%3E%3Cpolyline points='1 4 1 10 7 10'/%3E%3Cpath d='M3.51 15a9 9 0 1 0 2.13-9.36L1 10'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.icon-sun::before {
  background: currentColor;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor'%3E%3Ccircle cx='12' cy='12' r='5'/%3E%3Cline x1='12' y1='1' x2='12' y2='3'/%3E%3Cline x1='12' y1='21' x2='12' y2='23'/%3E%3Cline x1='4.22' y1='4.22' x2='5.64' y2='5.64'/%3E%3Cline x1='18.36' y1='18.36' x2='19.78' y2='19.78'/%3E%3Cline x1='1' y1='12' x2='3' y2='12'/%3E%3Cline x1='21' y1='12' x2='23' y2='12'/%3E%3Cline x1='4.22' y1='19.78' x2='5.64' y2='18.36'/%3E%3Cline x1='18.36' y1='5.64' x2='19.78' y2='4.22'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.icon-moon::before {
  background: currentColor;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor'%3E%3Cpath d='M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.icon-sparkle::before {
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='currentColor'%3E%3Cpath d='M12 2l2.5 7.5L22 12l-7.5 2.5L12 22l-2.5-7.5L2 12l7.5-2.5z'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.icon-send::before {
  background: currentColor;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor'%3E%3Cline x1='22' y1='2' x2='11' y2='13'/%3E%3Cpolygon points='22 2 15 22 11 13 2 9 22 2'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.icon-mic::before {
  background: currentColor;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor'%3E%3Cpath d='M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z'/%3E%3Cpath d='M19 10v2a7 7 0 0 1-14 0v-2'/%3E%3Cline x1='12' y1='19' x2='12' y2='23'/%3E%3Cline x1='8' y1='23' x2='16' y2='23'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.icon-mic-active::before {
  background: currentColor;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='currentColor' stroke='currentColor'%3E%3Cpath d='M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z'/%3E%3Cpath d='M19 10v2a7 7 0 0 1-14 0v-2'/%3E%3Cline x1='12' y1='19' x2='12' y2='23'/%3E%3Cline x1='8' y1='23' x2='16' y2='23'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.icon-edit::before {
  background: currentColor;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor'%3E%3Cpath d='M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7'/%3E%3Cpath d='M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.icon-copy::before {
  background: currentColor;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor'%3E%3Crect x='9' y='9' width='13' height='13' rx='2' ry='2'/%3E%3Cpath d='M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.icon-check::before {
  background: currentColor;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor'%3E%3Cpolyline points='20 6 9 17 4 12'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

/* Prompt Card Icons */
.icon-globe,
.icon-calc,
.icon-search,
.icon-file,
.icon-lock,
.icon-folder,
.icon-lightbulb,
.icon-default {
  width: 24px;
  height: 24px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.icon-globe::before {
  content: "🌐";
}
.icon-calc::before {
  content: "∑";
  font-weight: bold;
  font-size: 18px;
}
.icon-search::before {
  content: "⌕";
  font-weight: bold;
  font-size: 18px;
}
.icon-file::before {
  content: "📄";
  font-size: 16px;
}
.icon-lock::before {
  content: "🔒";
  font-size: 16px;
}
.icon-folder::before {
  content: "📁";
  font-size: 16px;
}
.icon-lightbulb::before {
  content: "💡";
  font-size: 16px;
}
.icon-default::before {
  content: "•";
  font-size: 18px;
}

/* Bubble Icons */
.icon-user-bubble,
.icon-success-bubble,
.icon-error-bubble,
.icon-message-bubble {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

.icon-user-bubble {
  background: rgba(255, 255, 255, 0.3);
  border: 2px solid rgba(255, 255, 255, 0.5);
}

.icon-user-bubble::before {
  content: "";
  width: 16px;
  height: 16px;
  background: white;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='currentColor'%3E%3Cpath d='M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2'/%3E%3Ccircle cx='12' cy='7' r='4'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.icon-success-bubble {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.icon-success-bubble::before {
  content: "";
  width: 16px;
  height: 16px;
  background: white;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='3'%3E%3Cpolyline points='20 6 9 17 4 12'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.icon-error-bubble {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
}

.icon-error-bubble::before {
  content: "";
  width: 16px;
  height: 16px;
  background: white;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='3'%3E%3Cline x1='18' y1='6' x2='6' y2='18'/%3E%3Cline x1='6' y1='6' x2='18' y2='18'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.icon-message-bubble {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}

/* Loading Spinner */
.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 0.8s linear infinite;
  margin-right: 8px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Logo Container */
.logo-container {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo-icon {
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
  position: relative;
  overflow: hidden;
}

.logo-icon::before {
  content: "";
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 28px;
  height: 28px;
  background: white;
  mask: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'%3E%3Cpath d='M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'/%3E%3Cpath d='M9 10h.01M15 10h.01M9.5 14c.5.5 1.5 1 2.5 1s2-.5 2.5-1'/%3E%3C/svg%3E")
    center/contain no-repeat;
}

.dark .logo-icon {
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.4);
}

.header-left {
  display: flex;
  align-items: center;
}

.app-container {
  position: relative;
  min-height: 100vh;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  transition: background 0.3s;
}

.app-container.dark {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
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

/* History Search */
.history-search {
  padding: 12px;
  border-bottom: 2px solid #e2e8f0;
}

.dark .history-search {
  border-bottom-color: #4a5568;
}

.search-input {
  width: 100%;
  padding: 10px 14px;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  background: #f8fafc;
  color: #1a202c;
  transition: all 0.2s;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
  background: white;
}

.dark .search-input {
  background: #374151;
  border-color: #4a5568;
  color: #e2e8f0;
}

.dark .search-input:focus {
  border-color: #3b82f6;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px;
  margin-bottom: 10px;
  background: #f8fafc;
  border-radius: 8px;
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

.history-content {
  flex: 1;
  min-width: 0;
  cursor: pointer;
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

.delete-history-item-btn {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  padding: 0;
  background: #fee2e2;
  color: #dc2626;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
  opacity: 0.7;
}

.delete-history-item-btn:hover {
  background: #fecaca;
  opacity: 1;
  transform: scale(1.1);
}

.dark .delete-history-item-btn {
  background: #7f1d1d;
  color: #fca5a5;
}

.dark .delete-history-item-btn:hover {
  background: #991b1b;
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
  margin-bottom: 32px;
  padding: 28px 32px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.dark .header {
  background: #1e293b;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  border-color: rgba(71, 85, 105, 0.5);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.header-actions {
  display: flex;
  gap: 8px;
}

.icon-btn {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  border: 1px solid #cbd5e1;
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  padding: 0;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.icon-btn:hover {
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
  border-color: #94a3b8;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.dark .icon-btn {
  background: linear-gradient(135deg, #334155 0%, #475569 100%);
  border-color: #475569;
  color: #e2e8f0;
}

.dark .icon-btn:hover {
  background: linear-gradient(135deg, #475569 0%, #64748b 100%);
  border-color: #64748b;
}

.icon-btn span {
  color: #475569;
}

.dark .icon-btn span {
  color: #cbd5e1;
}

h1 {
  margin: 0 0 4px 0;
  font-size: 28px;
  font-weight: 800;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -0.5px;
}

.subtitle {
  margin: 0;
  font-size: 14px;
  color: #64748b;
  font-weight: 500;
}

.dark .subtitle {
  color: #94a3b8;
}

/* Example Prompts */
.example-prompts {
  margin-bottom: 24px;
  background: white;
  padding: 28px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.dark .example-prompts {
  background: #1e293b;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  border-color: rgba(71, 85, 105, 0.5);
}

.example-prompts h3 {
  margin: 0 0 20px 0;
  font-size: 17px;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 10px;
}

.dark .example-prompts h3 {
  color: #f1f5f9;
}

.prompt-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}

.prompt-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  border: 2px solid #e2e8f0;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.prompt-card:hover {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-color: #3b82f6;
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.2);
}

.dark .prompt-card {
  background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  border-color: #334155;
}

.dark .prompt-card:hover {
  background: linear-gradient(135deg, #334155 0%, #475569 100%);
  border-color: #3b82f6;
  box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
}

.prompt-icon {
  flex-shrink: 0;
}

.prompt-text {
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  flex: 1;
  line-height: 1.4;
}

.dark .prompt-text {
  color: #e2e8f0;
}

.input-row {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  background: white;
  padding: 16px;
  border-radius: 16px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(226, 232, 240, 0.8);
}

.dark .input-row {
  background: #1e293b;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
  border-color: rgba(71, 85, 105, 0.5);
}

input {
  flex: 1;
  padding: 14px 18px;
  font-size: 15px;
  border: 2px solid #e2e8f0;
  border-radius: 10px;
  transition: all 0.2s;
  background: #f8fafc;
  color: #1e293b;
  font-weight: 500;
}

.dark input {
  background: #1e293b;
  border-color: #334155;
  color: #e2e8f0;
}

input:focus {
  outline: none;
  border-color: #3b82f6;
  background: white;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
}

.dark input:focus {
  background: #1e293b;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.15);
}

input:disabled {
  background: #f1f5f9;
  cursor: not-allowed;
  opacity: 0.6;
}

.dark input:disabled {
  background: #0f172a;
}

input::placeholder {
  color: #94a3b8;
  font-weight: 400;
}

button {
  padding: 14px 28px;
  font-size: 15px;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 600;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
  display: flex;
  align-items: center;
  gap: 8px;
  justify-content: center;
}

button:hover:not(:disabled) {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.35);
}

button:active:not(:disabled) {
  transform: translateY(0);
}

button:disabled {
  background: linear-gradient(135deg, #cbd5e1 0%, #94a3b8 100%);
  cursor: not-allowed;
  box-shadow: none;
  opacity: 0.6;
}

/* Voice Input Button */
.voice-btn {
  padding: 14px 18px;
  min-width: 52px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
}

.voice-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.35);
}

.voice-btn.listening {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  animation: pulse 1.5s ease-in-out infinite;
}

.send-btn {
  min-width: 120px;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
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

/* Edit Button */
.edit-btn {
  margin-left: auto;
  background: rgba(255, 255, 255, 0.15);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 6px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  color: white;
  display: flex;
  align-items: center;
  gap: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.edit-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  border-color: rgba(255, 255, 255, 0.5);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
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
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  margin-left: auto;
  max-width: 85%;
  border: none;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.25);
}

.bubble.final {
  background: white;
  border: 2px solid #10b981;
  color: #1e293b;
  box-shadow: 0 4px 16px rgba(16, 185, 129, 0.12);
}

.dark .bubble.final {
  background: #1e293b;
  color: #e2e8f0;
  border-color: #10b981;
}

.bubble.final .meta {
  color: #10b981;
}

.bubble.error {
  background: #fee2e2;
  border: 2px solid #ef4444;
  color: #7f1d1d;
}

.dark .bubble.error {
  background: #7f1d1d;
  color: #fecaca;
}

/* Copy Button */
.copy-btn {
  margin-top: 12px;
  padding: 10px 18px;
  font-size: 14px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 600;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.25);
}

.copy-btn:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.35);
}

.copy-btn.copied {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
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

/* Directory Tree Section */
.directory-tree-section {
  margin: 20px 0;
  animation: fadeIn 0.3s ease-out;
}

.directory-tree-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
  border-radius: 10px;
  border: 2px solid #22c55e;
}

.dark .directory-tree-header {
  background: linear-gradient(135deg, #14532d 0%, #166534 100%);
  border-color: #22c55e;
}

.directory-tree-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #166534;
}

.dark .directory-tree-header h3 {
  color: #86efac;
}

.tree-icon {
  font-size: 20px;
}

.directory-tree-card {
  background: white;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
  overflow-x: auto;
}

.dark .directory-tree-card {
  background: #1e293b;
  border-color: #4a5568;
}

.tree-content {
  font-family: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas,
    "Courier New", monospace;
  font-size: 13px;
  line-height: 1.6;
  margin: 0;
  color: #1e293b;
  white-space: pre;
  overflow-x: auto;
}

.dark .tree-content {
  color: #e2e8f0;
}

/* File References Section */
.file-references-section {
  margin: 20px 0;
  animation: fadeIn 0.3s ease-out;
}

.file-references-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
  border-radius: 10px;
  border: 2px solid #3b82f6;
}

.dark .file-references-header {
  background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
  border-color: #3b82f6;
}

.file-references-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #1e40af;
}

.dark .file-references-header h3 {
  color: #93c5fd;
}

.file-references-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-reference-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: white;
  border-radius: 10px;
  border: 2px solid #e2e8f0;
  cursor: pointer;
  transition: all 0.2s ease;
}

.file-reference-item:hover {
  background: #f8fafc;
  border-color: #3b82f6;
  transform: translateX(4px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.dark .file-reference-item {
  background: #1e293b;
  border-color: #4a5568;
}

.dark .file-reference-item:hover {
  background: #334155;
  border-color: #3b82f6;
}

.file-ref-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.file-ref-details {
  flex: 1;
  min-width: 0;
}

.file-ref-name {
  font-family: "SF Mono", Monaco, "Cascadia Code", "Roboto Mono", Consolas,
    "Courier New", monospace;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  word-break: break-all;
}

.dark .file-ref-name {
  color: #e2e8f0;
}

.file-ref-line {
  font-size: 12px;
  color: #64748b;
  margin-top: 4px;
}

.dark .file-ref-line {
  color: #94a3b8;
}

.file-ref-arrow {
  font-size: 20px;
  color: #3b82f6;
  flex-shrink: 0;
  opacity: 0.6;
  transition: opacity 0.2s ease;
}

.file-reference-item:hover .file-ref-arrow {
  opacity: 1;
}

/* Code Snippets Section */
.code-snippets-section {
  margin: 20px 0;
  animation: fadeIn 0.3s ease-out;
}

.code-snippets-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: linear-gradient(135deg, #e0e7ff 0%, #c7d2fe 100%);
  border-radius: 10px;
  border: 2px solid #6366f1;
}

.dark .code-snippets-header {
  background: linear-gradient(135deg, #4c1d95 0%, #5b21b6 100%);
  border-color: #7c3aed;
}

.code-icon {
  font-size: 20px;
}

.code-title {
  font-size: 16px;
  font-weight: 700;
  color: #3730a3;
}

.dark .code-title {
  color: #c4b5fd;
}

.code-snippet-card {
  background: white;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  padding: 16px;
  margin-bottom: 16px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.code-snippet-card:hover {
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.12);
  transform: translateY(-2px);
}

.dark .code-snippet-card {
  background: #1e293b;
  border-color: #4a5568;
}

.snippet-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e2e8f0;
}

.dark .snippet-header {
  border-bottom-color: #4a5568;
}

.snippet-info {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
}

.snippet-file-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.snippet-file {
  font-size: 14px;
  font-weight: 600;
  color: #3b82f6;
  font-family: "Monaco", "Menlo", monospace;
}

.dark .snippet-file {
  color: #60a5fa;
}

.snippet-lines {
  font-size: 12px;
  color: #64748b;
  font-weight: 500;
  padding: 2px 8px;
  background: #f1f5f9;
  border-radius: 4px;
  display: inline-block;
}

.dark .snippet-lines {
  background: #374151;
  color: #94a3b8;
}

.snippet-language {
  font-size: 12px;
  color: white;
  font-weight: 700;
  text-transform: uppercase;
  padding: 4px 12px;
  background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
  border-radius: 6px;
  display: inline-block;
  letter-spacing: 0.5px;
}

.dark .snippet-language {
  background: linear-gradient(135deg, #7c3aed 0%, #a855f7 100%);
  color: white;
}

.copy-btn-small {
  padding: 6px 12px;
  background: #f1f5f9;
  color: #475569;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
  font-weight: 500;
}

.copy-btn-small:hover {
  background: #e2e8f0;
}

.copy-btn-small.copied {
  background: #6366f1;
  color: white;
}

.dark .copy-btn-small {
  background: #374151;
  color: #94a3b8;
}

.dark .copy-btn-small:hover {
  background: #4a5568;
}

.code-block {
  margin: 0;
  padding: 0;
  background: #2d2d2d;
  border-radius: 8px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.6;
  border: 1px solid #e2e8f0;
}

.dark .code-block {
  background: #1e1e1e;
  border-color: #334155;
}

.code-block code {
  font-family: "Monaco", "Menlo", "Courier New", monospace;
  display: block;
  white-space: pre;
  padding: 16px;
}

/* Override Prism theme for better visibility */
.code-block code[class*="language-"] {
  background: transparent;
  text-shadow: none;
}

.dark .code-block code {
  color: #e2e8f0;
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

/* Stats Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  animation: fadeIn 0.2s ease-out;
}

.stats-modal {
  background: white;
  border-radius: 16px;
  padding: 0;
  max-width: 600px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: slideUp 0.3s ease-out;
}

.dark .stats-modal {
  background: #2d3748;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stats-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  border-bottom: 2px solid #e2e8f0;
}

.dark .stats-header {
  border-bottom-color: #4a5568;
}

.stats-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #1a202c;
}

.dark .stats-header h2 {
  color: #e2e8f0;
}

.stats-content {
  padding: 24px;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
  gap: 16px;
}

.stat-card {
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  padding: 20px;
  border-radius: 12px;
  text-align: center;
  transition: all 0.2s;
  border: 2px solid #e2e8f0;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  border-color: #3b82f6;
}

.dark .stat-card {
  background: linear-gradient(135deg, #374151 0%, #1f2937 100%);
  border-color: #4a5568;
}

.dark .stat-card:hover {
  border-color: #3b82f6;
}

.stat-icon {
  font-size: 32px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1a202c;
  margin-bottom: 4px;
}

.dark .stat-value {
  color: #e2e8f0;
}

.stat-label {
  font-size: 12px;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-weight: 600;
}

.dark .stat-label {
  color: #94a3b8;
}
</style>
