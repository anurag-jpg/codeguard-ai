<div align="center">

# 🛡️ CodeGuard AI

### Intelligent Code Security & Bug Detection Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![Gemini](https://img.shields.io/badge/Gemini-2.0_Flash-4285F4?style=flat-square&logo=google)](https://ai.google.dev)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**AI-powered code analysis that finds bugs, vulnerabilities, and security issues  
that traditional static analysis tools miss.**

[Demo](#demo) · [Features](#features) · [Quick Start](#quick-start) · [Architecture](#architecture) · [API Docs](#api-reference)

</div>

---

## 📌 Overview

**CodeGuard AI** is a full-stack AI application that combines **Retrieval-Augmented Generation (RAG)** with **Google Gemini 2.0** to perform deep semantic code analysis. Unlike traditional linters, CodeGuard understands the *intent* of your code and detects complex bugs including logic errors, race conditions, and security vulnerabilities.

> Built as a production-grade portfolio project demonstrating RAG architecture, vector search, async APIs, and modern React development.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **RAG-Powered Analysis** | FAISS vector store + Gemini LLM for semantic bug detection |
| 🔐 **Security Scanning** | Detects OWASP Top 10 vulnerabilities, SQL injection, XSS, hardcoded secrets |
| ⚡ **Multi-Language Support** | Python, JavaScript, TypeScript, Java, Go, Rust, C++ |
| 📊 **Risk Scoring** | Quantitative risk score (0–10) per repository |
| 🤖 **AI Chat Interface** | Ask follow-up questions about any detected bug |
| 🐙 **GitHub Integration** | Shallow-clone and analyse any public repository |
| 📈 **Real-time Dashboard** | Live bug statistics and category breakdowns |
| 🐳 **Docker Ready** | One-command deployment with Docker Compose |

---

## 🖥️ Demo

### Dashboard
![Dashboard showing real-time bug statistics and category breakdown]

### Code Analysis
![Analysis page showing detected bugs with severity levels]

### AI Chat
![AI chat interface explaining security vulnerabilities]

---

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 20+
- Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com/apikey))

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/codeguard-ai.git
cd codeguard-ai
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 3. Run with Docker (Recommended)
```bash
docker compose up --build
```

### 4. Run locally
```bash
# Terminal 1 — Backend
pip install -r requirements.txt
python -m backend.main

# Terminal 2 — Frontend
cd frontend
npm install
npm run dev
```

### 5. Open the app
```
Frontend  →  http://localhost:3000
API Docs  →  http://localhost:8000/docs
```

---

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────┐
│              React Frontend (Vite)               │
│     Dashboard · Analysis · AI Chat Interface     │
└──────────────────────┬──────────────────────────┘
                       │ REST API
┌──────────────────────▼──────────────────────────┐
│              FastAPI Backend                     │
│   Routes → BugDetector → ReportGenerator        │
└──────────────────────┬──────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────┐
│                 AI Engine                        │
│                                                  │
│  EmbeddingEngine → FAISS Retriever               │
│         │                  │                     │
│         └──── RAGPipeline ─┘                    │
│                    │                             │
│            Gemini 2.0 Flash                      │
└─────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, Vite 5, CSS Variables |
| **Backend** | FastAPI 0.115, Pydantic v2, Uvicorn |
| **AI/ML** | Google Gemini 2.0 Flash, FAISS |
| **Vector DB** | FAISS (faiss-cpu) |
| **Async** | asyncio, aiofiles |
| **DevOps** | Docker, Docker Compose, Nginx |
| **Testing** | pytest, pytest-asyncio |

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analyze/code` | Analyse a code snippet (sync) |
| `POST` | `/api/v1/analyze/repo` | Submit GitHub repo for analysis (async) |
| `POST` | `/api/v1/analyze/upload` | Upload files for analysis |
| `GET` | `/api/v1/analyze/status/{job_id}` | Poll job status |
| `POST` | `/api/v1/analyze/chat` | Chat about analysis results |
| `GET` | `/api/v1/reports` | List all reports |
| `GET` | `/health` | Health check |

Full interactive docs available at `/docs` when running in debug mode.

---

## 🔍 Detected Bug Categories

| Category | Examples |
|----------|---------|
| 🔐 **Security** | SQL injection, XSS, hardcoded secrets, eval() usage |
| 🧠 **Logic Errors** | Off-by-one, incorrect conditionals, dead code |
| ⚠️ **Exception Handling** | Bare except, swallowed exceptions |
| 🏃 **Performance** | N+1 queries, blocking I/O, memory leaks |
| 🔄 **Race Conditions** | Unsynchronised shared state, deadlocks |
| 🏷️ **Type Errors** | Type mismatches, null dereferences |

---

## ⚙️ Configuration

All settings via `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_API_KEY` | required | Google Gemini API key |
| `LLM_MODEL` | `gemini-2.0-flash` | Gemini model to use |
| `EMBEDDING_MODEL` | `models/embedding-001` | Embedding model |
| `EMBEDDING_DIMENSION` | `768` | Vector dimension |
| `CHUNK_SIZE` | `1000` | Code chunk size |
| `TOP_K_RETRIEVAL` | `5` | RAG retrieval count |
| `DEBUG` | `false` | Enable debug mode |

---

## 🧪 Running Tests
```bash
# Run all tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov --cov-report=html
open coverage_html/index.html
```

---

## 📁 Project Structure
```
codeguard-ai/
├── backend/
│   ├── api/
│   │   ├── routes.py        # All REST endpoints
│   │   └── schemas.py       # Pydantic models
│   ├── services/
│   │   ├── bug_detector.py  # Core detection logic
│   │   ├── repo_analyzer.py # GitHub repo cloning
│   │   └── report_generator.py
│   ├── utils/
│   │   ├── chunking.py      # Code chunking
│   │   └── file_parser.py   # File parsing
│   ├── config.py            # Settings management
│   └── main.py              # FastAPI app
├── ai_engine/
│   ├── embeddings.py        # Gemini embeddings
│   ├── retriever.py         # FAISS vector store
│   ├── rag_pipeline.py      # RAG orchestration
│   └── prompts.py           # LLM prompt templates
├── frontend/
│   └── src/
│       ├── pages/           # Dashboard, Analysis, Chat
│       ├── components/      # Sidebar
│       └── services/api.js  # HTTP client
├── tests/                   # pytest test suite
├── docker/                  # Dockerfiles + Nginx
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit changes: `git commit -m "feat: add your feature"`
4. Push: `git push origin feat/your-feature`
5. Open a Pull Request

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Deepa** — Built as an industry-level portfolio project  
demonstrating full-stack AI/ML engineering skills.

[![GitHub](https://img.shields.io/badge/GitHub-anurag-jpg-181717?style=flat-square&logo=github)](https://github.com/anurag-jpg)
[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin)](https://linkedin.com/in/anurag yadav)

---

<div align="center">

⭐ **Star this repo if you found it useful!** ⭐

*Built with ❤️ using FastAPI, React, FAISS, and Google Gemini*

</div>