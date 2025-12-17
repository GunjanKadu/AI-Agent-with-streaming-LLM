<template>
  <div class="container">
    <h1>🤖 SAP BTP AI Assistant</h1>
    <div class="input-row">
      <input
        v-model="question"
        placeholder="Ask me anything about SAP BTP or math calculations..."
        @keyup.enter="send"
        :disabled="isProcessing"
      />
      <button @click="send" :disabled="isProcessing">
        {{ isProcessing ? "Processing..." : "Send" }}
      </button>
    </div>

    <div class="log">
      <!-- User question -->
      <div
        v-for="(item, idx) in permanentMessages"
        :key="'perm-' + idx"
        :class="['bubble', item.type]"
      >
        <div class="meta">{{ item.type }}</div>
        <div class="text">{{ item.text }}</div>
      </div>

      <!-- Thinking/processing section (disappears when final answer arrives) -->
      <div v-if="thinkingSteps.length > 0" class="thinking-section">
        <div class="thinking-header">
          <span class="thinking-icon">💭</span>
          <span class="thinking-text">Thinking...</span>
          <span class="spinner"></span>
        </div>
        <div class="thinking-content">
          <div
            v-for="(step, idx) in thinkingSteps"
            :key="'think-' + idx"
            class="thinking-step"
          >
            <span class="step-icon">{{ getStepIcon(step.type) }}</span>
            <span class="step-text">{{ step.text }}</span>
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
      permanentMessages: [], // Only user question and final answer
      thinkingSteps: [], // Intermediate steps that disappear
      isProcessing: false,
    };
  },
  methods: {
    getStepIcon(type) {
      const icons = {
        analysis: "🔍",
        step: "⚙️",
        error: "❌",
      };
      return icons[type] || "•";
    },
    async send() {
      if (!this.question.trim() || this.isProcessing) return;

      this.isProcessing = true;
      this.permanentMessages = [];
      this.thinkingSteps = [];

      // Add user question
      this.permanentMessages.push({ type: "user", text: this.question });

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
                // Clear thinking steps and show final answer
                this.thinkingSteps = [];
                this.permanentMessages.push(obj);
              } else if (obj.type === "analysis" || obj.type === "step") {
                // Add to thinking steps (temporary)
                this.thinkingSteps.push(obj);
              } else if (obj.type === "error") {
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
.container {
  max-width: 900px;
  margin: 24px auto;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
    "Helvetica Neue", Arial, sans-serif;
  padding: 0 16px;
}

h1 {
  text-align: center;
  color: #2c3e50;
  margin-bottom: 32px;
}

.input-row {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

input {
  flex: 1;
  padding: 12px 16px;
  font-size: 16px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  transition: border-color 0.3s;
}

input:focus {
  outline: none;
  border-color: #4a90e2;
}

input:disabled {
  background: #f5f5f5;
  cursor: not-allowed;
}

button {
  padding: 12px 24px;
  font-size: 16px;
  background: #4a90e2;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s;
  font-weight: 600;
}

button:hover:not(:disabled) {
  background: #357abd;
}

button:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.log {
  margin-top: 16px;
}

.bubble {
  padding: 16px;
  border-radius: 12px;
  margin-bottom: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.bubble .meta {
  font-size: 11px;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
  font-weight: 600;
}

.bubble .text {
  font-size: 15px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.bubble.user {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  margin-left: auto;
  max-width: 80%;
}

.bubble.user .meta {
  color: rgba(255, 255, 255, 0.8);
}

.bubble.final {
  background: white;
  border: 2px solid #4a90e2;
  font-size: 16px;
}

.bubble.final .text {
  color: #2c3e50;
  font-weight: 500;
}

.bubble.error {
  background: #fee;
  border-left: 4px solid #e74c3c;
  color: #c0392b;
}

/* Thinking section styles */
.thinking-section {
  background: linear-gradient(135deg, #f5f7fa 0%, #e8eef5 100%);
  border-radius: 12px;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid #d0d7de;
  animation: fadeIn 0.3s ease-out;
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
  gap: 8px;
  margin-bottom: 12px;
  padding-bottom: 12px;
  border-bottom: 1px solid #d0d7de;
}

.thinking-icon {
  font-size: 20px;
}

.thinking-text {
  font-weight: 600;
  color: #586069;
  font-size: 14px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #d0d7de;
  border-top-color: #4a90e2;
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
  gap: 8px;
}

.thinking-step {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 8px;
  background: white;
  border-radius: 6px;
  font-size: 14px;
  color: #586069;
  animation: slideIn 0.2s ease-out;
}

.step-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.step-text {
  flex: 1;
  line-height: 1.5;
}
</style>
