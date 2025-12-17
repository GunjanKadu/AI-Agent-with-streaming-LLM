# 🤖 AI Agent with Streaming LLM - SAP BTP Assistant

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.x-green.svg)](https://vuejs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An intelligent AI assistant powered by local LLMs (via Ollama) that demonstrates advanced agent capabilities including tool calling, streaming responses, and real-time reasoning display. Built with FastAPI backend and Vue.js frontend.

![Demo](https://img.shields.io/badge/demo-live-brightgreen)

## ✨ Features

- 🧠 **LLM-Powered Intelligence**: Uses Llama 3.1 (8B) for natural language understanding
- 🛠️ **Tool Calling**: Automatic tool selection for mathematical operations
- 📡 **Real-time Streaming**: See the AI's reasoning process as it happens
- 💭 **Thinking Display**: Temporary "thinking" section shows intermediate steps
- 🎯 **Smart Routing**: Knowledge questions answered directly, math delegated to tools
- ⚡ **Fast & Local**: All processing happens on your machine, no cloud dependencies
- 🔄 **Async Architecture**: Non-blocking streaming with asyncio and async generators
- 📊 **Beautiful UI**: Modern Vue.js interface with smooth animations

## 🏗️ Architecture

```
┌─────────────────┐
│   Vue.js UI     │  User asks question
│  (Frontend)     │
└────────┬────────┘
         │ HTTP POST /api/ask
         ▼
┌─────────────────┐
│  FastAPI        │  NDJSON Streaming Response
│  (Backend)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  LangChain      │  Model with Tools
│  Agent          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Ollama         │  llama3.1:8b
│  (Local LLM)    │
└─────────────────┘
```

## 📋 Prerequisites

- **Python 3.10+** with virtualenv
- **Node.js 16+** and npm
- **[Ollama](https://ollama.ai/)** running locally with `llama3.1:8b` model

## Setup

### 1. Install Python Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies

```bash
cd frontend-vue
npm install
cd ..
```

### 3. Ensure Ollama is Running

```bash
# Check if Ollama is running
ps aux | grep ollama

# If not running, start Ollama and pull the model
ollama serve
ollama pull llama3.1:8b
```

## Running the Application

### Option 1: Using the Management Script (Recommended)

```bash
# Start backend
./backend.sh start

# Check status
./backend.sh status

# View logs
./backend.sh logs

# Follow logs in real-time
./backend.sh logs -f

# Stop backend
./backend.sh stop

# Restart backend
./backend.sh restart
```

### Option 2: Manual Start

#### Start Backend (Terminal 1)

```bash
cd /path/to/BuildCustomAgent
source .venv/bin/activate
AGENT_CALLABLE=backend.agent:stream_agent uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

You should see: `✓ Loaded agent from: backend.agent:stream_agent`

#### Start Frontend (Terminal 2)

```bash
cd frontend-vue
npm run dev
```

The frontend will be available at http://localhost:5173 (or another port shown in terminal)

## 🎯 How It Works

### Request Flow

1. **User Input**: Question entered in Vue.js frontend
2. **HTTP Request**: POST to `/api/ask` with JSON payload
3. **LLM Processing**: Backend invokes Ollama with tools bound
4. **Streaming Response**: NDJSON (Newline-Delimited JSON) events:
   - `analysis`: LLM's reasoning and thought process
   - `step`: Tool execution results (e.g., `multiply -> 45`)
   - `final`: Complete answer
5. **Progressive Display**: Frontend shows thinking section, then final answer

### Agent Decision Flow

```python
# Simplified logic
if question requires calculation:
    LLM -> Identifies need for tool
    LLM -> Calls tool (add/multiply/divide)
    Backend -> Executes tool
    Backend -> Returns result to LLM
    LLM -> Formulates final answer
else:
    LLM -> Answers directly from knowledge
```

## 🛠️ Tech Stack

**Backend:**

- FastAPI - Modern async Python web framework
- LangChain - LLM orchestration and tool binding
- LangGraph - Agent workflow management
- Ollama (langchain_ollama) - Local LLM integration
- Uvicorn - ASGI server

**Frontend:**

- Vue.js 3 - Progressive JavaScript framework
- Vite - Next-generation frontend tooling
- Native Fetch API - Streaming response handling

**LLM:**

- Llama 3.1 (8B parameters) - Meta's open-source model
- Tool calling - Built-in function calling capabilities

## Testing

```bash
# Test knowledge question
curl -X POST http://127.0.0.1:8000/api/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"What is SAP BTP?"}'

# Test math question
curl -X POST http://127.0.0.1:8000/api/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Calculate 15 times 3 plus 7"}'
```

## 📁 Project Structure

```
.
├── backend/
│   ├── __init__.py          # Package marker
│   ├── main.py              # FastAPI app, streaming endpoint
│   └── agent.py             # LangChain agent with tools
├── frontend-vue/
│   ├── src/
│   │   ├── App.vue          # Main Vue component
│   │   └── main.js          # Vue app entry
│   ├── index.html
│   ├── package.json
│   └── vite.config.js       # Vite config with proxy
├── agent.ipynb              # Original Jupyter notebook
├── backend.sh               # Backend management script
├── requirements.txt         # Python dependencies
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 🐛 Troubleshooting

| Issue                        | Solution                                             |
| ---------------------------- | ---------------------------------------------------- |
| **"Address already in use"** | `./backend.sh stop` or `lsof -ti:8000 \| xargs kill` |
| **LLM not responding**       | Ensure Ollama is running: `ollama serve`             |
| **Model not found**          | Pull the model: `ollama pull llama3.1:8b`            |
| **Tool decorator errors**    | Ensure all `@tool` functions have docstrings         |
| **Async generator errors**   | Set `AGENT_CALLABLE` env var when starting uvicorn   |
| **Frontend not loading**     | Check if Vite dev server is running on port 5173     |
| **CORS errors**              | Verify Vite proxy is configured in `vite.config.js`  |

## 🔮 Future Enhancements

- [ ] Add more sophisticated tools (web search, database queries)
- [ ] Support multiple LLM providers (OpenAI, Anthropic)
- [ ] Implement conversation history and context
- [ ] Add authentication and user sessions
- [ ] Deploy to cloud (Docker, Kubernetes)
- [ ] Add unit and integration tests
- [ ] Implement rate limiting and caching
- [ ] Add voice input/output capabilities

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [LangChain](https://github.com/langchain-ai/langchain) - For the amazing LLM orchestration framework
- [Ollama](https://ollama.ai/) - For making local LLMs accessible
- [Meta AI](https://ai.meta.com/llama/) - For the Llama model family
- [FastAPI](https://fastapi.tiangolo.com/) - For the excellent async web framework
- [Vue.js](https://vuejs.org/) - For the progressive frontend framework

## 📧 Contact

For questions or feedback, please open an issue on GitHub.

---

**Note**: This is a demonstration project for educational purposes. For production use, implement proper security, error handling, and monitoring.
