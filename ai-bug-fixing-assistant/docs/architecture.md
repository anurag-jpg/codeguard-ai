# Architecture — AI Bug Fixing Assistant

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        React Frontend                        │
│         Dashboard · Analysis Form · Chat Interface           │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP / REST
┌───────────────────────────▼─────────────────────────────────┐
│                      FastAPI Backend                         │
│                                                              │
│  Routes ──► RepoAnalyzer ──► BugDetector ──► ReportGen      │
│                    │              │                          │
│                    │         StaticPatternDetector           │
│                    │         SemanticDetector                │
│                    │              │                          │
└────────────────────┼──────────────┼──────────────────────────┘
                     │              │
        ┌────────────▼──────────────▼────────────┐
        │            AI Engine                    │
        │                                         │
        │  EmbeddingEngine ──► Retriever (FAISS)  │
        │        │                    │           │
        │        └──► RAGPipeline ◄───┘           │
        │                  │                      │
        │             OpenAI GPT-4o               │
        └─────────────────────────────────────────┘
```

## Data Flow

### Repository Analysis (Async)

1. **POST /api/v1/analyze/repo** — Client submits GitHub URL
2. **RepoAnalyzer** — Shallow git clone, file collection, language detection
3. **FileParser** — Normalises encoding, extracts imports/classes/functions
4. **CodeChunker** — Splits files at function/class boundaries
5. **EmbeddingEngine** — Batch-embeds all chunks via OpenAI `text-embedding-3-small`
6. **Retriever** — Stores vectors in FAISS IndexFlatIP (cosine similarity)
7. **BugDetector** (dual-pass):
   - **StaticPatternDetector** — Regex rules for 10+ patterns (eval, bare except, hardcoded secrets…)
   - **SemanticDetector** → **RAGPipeline**:
     - Retrieves similar code chunks for context
     - Builds augmented prompt with context
     - Calls GPT-4o with structured JSON response schema
     - Parses + validates response into BugReport objects
8. **ReportGenerator** — Calculates risk score, generates Markdown report
9. Client polls **GET /api/v1/analyze/{session_id}** until `status=completed`

### Snippet Analysis (Sync)

Same pipeline but without the git clone step. Returns synchronously.

### Conversational Chat

- Uses the existing bug list + report as context
- RAGPipeline builds a conversation prompt with last 6 turns
- Returns reply + referenced bug IDs

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| FAISS over Pinecone/Weaviate | Zero infra cost, runs in-process, sufficient for repo-scale retrieval |
| Background tasks over Celery | Simpler setup; Celery/Redis upgrade path preserved via same interface |
| Pydantic v2 schemas | Fast validation, auto-generated OpenAPI docs |
| Dual-pass detection | Static is instant + zero cost; LLM catches semantic bugs static misses |
| Semantic boundary chunking | Better embeddings than naive character splits → higher retrieval quality |
| Shallow git clone (depth=1) | Reduces clone time from minutes to seconds for large repos |

## Scaling Considerations

- **Session store**: Replace in-memory `_sessions` dict with Redis (`redis-py`) for multi-worker deployments
- **Job queue**: Wrap background tasks with Celery + Redis for distributed processing
- **FAISS**: Replace with a managed vector DB (Pinecone, Qdrant) for multi-tenancy
- **LLM calls**: Add a queue/throttle layer to respect rate limits at high concurrency
- **Caching**: Embeddings are cached in-process; replace with Redis for cross-instance sharing

## Security Notes

- GitHub tokens injected via env var, never logged
- All API inputs validated by Pydantic with strict constraints
- Rate limiting applied at route level (slowapi)
- Backend runs as non-root user inside Docker
- CORS restricted to configured origins
