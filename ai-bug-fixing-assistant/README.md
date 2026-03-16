# 🐛 AI Bug Fixing Assistant

> **RAG-powered code analysis that finds bugs static tools miss.**  
> Combines FAISS vector retrieval with GPT-4o to detect security vulnerabilities, logic errors, and performance issues across any GitHub repository.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react)](https://react.dev)
[![OpenAI](https://img.shields.io/badge/GPT--4o-RAG-412991?style=flat-square&logo=openai)](https://openai.com)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker)](https://docker.com)

---

## Features

- **Dual-pass detection** — instant regex rules + deep LLM semantic analysis
- **RAG pipeline** — retrieves similar code patterns for richer context before LLM inference
- **10+ bug categories** — security, performance, logic, concurrency, type errors, and more
- **Async repo analysis** — clones, chunks, embeds, and analyses large repos without blocking
- **Structured reports** — risk scores, severity breakdowns, diff-style fix suggestions
- **Conversational AI** — ask follow-up questions about any finding via chat interface
- **Multi-language** — Python, JavaScript, TypeScript, Java, Go, Rust, C++, and more

## Architecture

```
React SPA  ──HTTP──►  FastAPI  ──►  RepoAnalyzer  ──►  FileParser + Chunker
                          │                                      │
                          ▼                                      ▼
                     BugDetector                        EmbeddingEngine (OpenAI)
                    /           \                               │
           StaticPattern    Semantic                     FAISS Retriever
           Detector         Detector                            │
                                \                               │
                                 ──────►  RAGPipeline ◄─────────
                                               │
                                          GPT-4o LLM
                                               │
                                        ReportGenerator
```

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- OpenAI API key

### 1. Clone & configure

```bash
git clone https://github.com/your-username/ai-bug-fixing-assistant
cd ai-bug-fixing-assistant
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Backend

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the API server
python -m backend.main
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI, set DEBUG=true)
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

### 4. Docker (recommended for production)

```bash
docker compose up --build
# Backend  → http://localhost:8000
# Frontend → http://localhost:3000
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analyze/repo` | Submit GitHub repo for async analysis |
| `GET`  | `/api/v1/analyze/{session_id}` | Poll analysis status |
| `POST` | `/api/v1/analyze/snippet` | Synchronously analyse a code snippet |
| `POST` | `/api/v1/chat` | Chat about analysis results |
| `GET`  | `/health` | Health check |

### Example: Analyse a snippet

```bash
curl -X POST http://localhost:8000/api/v1/analyze/snippet \
  -H "Content-Type: application/json" \
  -d '{
    "code": "password = \"admin123\"\nresult = eval(user_input)",
    "language": "python",
    "focus_areas": ["security"]
  }'
```

## Running Tests

```bash
pytest tests/ -v
# With coverage report:
pytest tests/ --cov --cov-report=html
open coverage_html/index.html
```

## Project Structure

```
ai-bug-fixing-assistant/
├── backend/
│   ├── main.py              # FastAPI app factory, middleware, lifespan
│   ├── config.py            # Pydantic-settings configuration
│   ├── api/
│   │   ├── routes.py        # All REST endpoints
│   │   └── schemas.py       # Pydantic request/response models
│   ├── services/
│   │   ├── repo_analyzer.py # Git clone + file collection
│   │   ├── bug_detector.py  # Dual-pass detection orchestrator
│   │   └── report_generator.py  # Risk scoring + Markdown reports
│   └── utils/
│       ├── file_parser.py   # Language detection + metadata extraction
│       └── chunking.py      # Semantic + sliding-window code chunking
├── ai_engine/
│   ├── embeddings.py        # OpenAI embedding API with retry + cache
│   ├── retriever.py         # FAISS vector store (build/load/search)
│   ├── rag_pipeline.py      # RAG loop: retrieve → augment → generate → parse
│   └── prompts.py           # Version-controlled prompt templates
├── frontend/
│   └── src/
│       ├── pages/           # Dashboard, Analysis, Chat
│       ├── components/      # Sidebar, shared UI
│       └── services/api.js  # HTTP client with error handling
├── tests/
│   ├── test_bug_detector.py
│   ├── test_repo_analyzer.py
│   ├── test_report_generator.py
│   └── test_api_routes.py
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
├── docs/
│   └── architecture.md
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Configuration

All settings live in `.env` (see `.env.example`). Key options:

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | required | OpenAI API key |
| `GITHUB_TOKEN` | optional | For private repo access |
| `LLM_MODEL` | `gpt-4o` | LLM model for semantic analysis |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `TOP_K_RESULTS` | `10` | FAISS retrieval k |
| `CHUNK_SIZE` | `1000` | Characters per code chunk |
| `DEBUG` | `false` | Enables Swagger UI + verbose logs |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI 0.115, Pydantic v2, uvicorn |
| AI | OpenAI GPT-4o, text-embedding-3-small |
| Vector DB | FAISS (faiss-cpu) |
| Async I/O | asyncio, aiofiles |
| Logging | structlog (JSON) |
| Rate limiting | slowapi |
| Frontend | React 18, Vite 5 |
| Containerisation | Docker, Docker Compose, Nginx |
| Testing | pytest, pytest-asyncio, pytest-cov |

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/my-feature`
3. Run tests: `pytest tests/ -v`
4. Open a PR with a clear description

## License

MIT — see [LICENSE](LICENSE)
