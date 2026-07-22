# ABHEDYA AI Core

Production-grade AI platform for knowledge graphs, GraphRAG++, multi-agent intelligence, root cause analysis, and geospatial risk intelligence.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Uvicorn |
| Graph DB | Neo4j 5.x |
| Relational DB | PostgreSQL 16 |
| Cache | Redis 7 |
| Vector Store | FAISS (local) |
| Graph Framework | LangGraph |
| Embeddings | BAAI/bge-m3 |
| Reranker | BAAI/bge-reranker-v2-m3 |
| Primary LLM | Gemini 2.5 Flash |
| Fallback LLM | Groq (Llama 3.3 70B) |
| Logging | Loguru |
| Config | Pydantic Settings v2 |
| Dependency Mgr | uv |

## Project Structure

```
abhedya-ai-core/
├── app/
│   ├── api/v1/          # REST endpoints
│   ├── core/
│   │   ├── config/      # Modular settings (database, llm, security, logging, kafka)
│   │   ├── logger.py    # Structured logging
│   │   ├── lifespan.py  # FastAPI startup/shutdown
│   │   └── constants.py # Project-wide constants
│   ├── database/        # Connection managers (postgres, neo4j, redis)
│   ├── shared/          # Enums, exceptions, responses, middleware, types
│   ├── models/          # SQLAlchemy ORM models
│   ├── schemas/         # Pydantic schemas
│   ├── graph/           # Knowledge graph layer
│   ├── graphrag/        # GraphRAG++ retrieval pipeline
│   ├── agents/          # LangGraph multi-agent orchestration
│   ├── llm/             # LLM Gateway + Provider Router
│   ├── root_cause/      # Root Cause Analysis engine
│   ├── emergency/       # Emergency Response planner
│   ├── geospatial/      # Geospatial intelligence
│   ├── services/        # Shared business services
│   ├── events/          # Event streaming (Kafka)
│   └── utils/           # Helpers
├── tests/
├── docker/
├── docs/
├── scripts/
├── pyproject.toml       # Single source of truth for dependencies + tools
├── uv.lock              # Reproducible dependency lock file
├── docker-compose.yml
└── .env.example
```

## Quick Start

### Prerequisites
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (`pip install uv`)
- Docker Desktop

### 1. Clone and setup environment

```bash
git clone <repo-url>
cd abhedya-ai-core
uv sync --extra dev
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and add your API keys (GEMINI_API_KEY, etc.)
```

### 3. Start databases

```bash
docker compose up -d
```

### 4. Run the application

```bash
uv run uvicorn main:app --reload
```

### 5. Verify

| Endpoint | Purpose |
|---|---|
| `http://localhost:8000/` | Root status |
| `http://localhost:8000/health` | Platform health |
| `http://localhost:8000/api/v1/health` | Versioned health |
| `http://localhost:8000/docs` | Swagger UI |

## Development

```bash
# Run tests
uv run pytest

# Lint
uv run ruff check .

# Format
uv run black .

# Type check
uv run mypy app/
```

## Git Workflow

```
main           ← production releases
  └── develop  ← integration branch
        └── feature/<name>  ← one feature per branch
```

**Rule:** One feature = One branch = One PR = One merge.

## Milestone Roadmap

| # | Milestone | Status |
|---|---|---|
| 1 | Foundation (Config, Logging, DB, Health API, Docker) | ✅ In Progress |
| 2 | Knowledge Graph (Neo4j nodes, relationships, Cypher API) |  ✅ In Progress  |
| 3 | GraphRAG++ (Ingestion, Embeddings, Hybrid Retrieval, Reranker, LLM, Citation) |  ✅ In Progress  |
| 4 | Multi-Agent Orchestration (LangGraph) |  ✅ In Progress  |
| 5 | Root Cause Analysis Engine |  ✅ In Progress  |
| 6 | Emergency Response Planner |  ✅ In Progress  |
| 7 | Geospatial Risk Intelligence |  ✅ In Progress  |
