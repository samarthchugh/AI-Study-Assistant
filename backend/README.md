# AI Study Assistant — Backend

FastAPI backend for an AI-powered study and revision agent. Combines a RAG-based Q&A system, an adaptive quiz engine, and a personalised learning analytics layer.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Environment Setup](#environment-setup)
- [Database Setup](#database-setup)
- [Running the Server](#running-the-server)
- [API Overview](#api-overview)
- [Running Tests](#running-tests)
- [Architecture Notes](#architecture-notes)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI + Uvicorn (ASGI) |
| Database | PostgreSQL + SQLAlchemy + Alembic |
| Authentication | JWT (python-jose) + Argon2 (passlib) |
| PDF parsing | PyMuPDF |
| Embeddings | sentence-transformers (`all-MiniLM-L6-v2`, 384-dim) |
| Vector store | FAISS (`IndexFlatIP`) |
| LLM (primary) | Groq API (`llama-3.1-8b-instant`) |
| Cache / signals | Redis |
| Agent orchestration | LangGraph |
| Config management | pydantic-settings |

---

## Prerequisites

Make sure the following are installed and running before starting:

- Python 3.11+
- PostgreSQL (running locally or remotely)
- Redis (running locally on port 6379)
- A [Groq API key](https://console.groq.com/) — free tier available

---

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Settings + Redis client
│   ├── dependencies.py          # JWT auth dependency
│   ├── api/v1/                  # Route handlers
│   ├── db/                      # SQLAlchemy models + session
│   ├── rag/                     # PDF ingestion, chunking, retriever, pipeline
│   ├── services/                # FAISS store, LLM, quiz engine, intelligence
│   ├── agents/                  # LangGraph nodes (analyzer, planner, scheduler)
│   ├── schemas/                 # Pydantic request/response models
│   └── utils/                   # Logging, topic normalisation
├── faiss_data/                  # Persisted FAISS index (auto-created)
├── logs/                        # Rotating log files (auto-created)
├── requirements.txt
├── openapi.yaml                 # OpenAPI 3.1 spec
├── BACKEND_DOCS.md              # Full technical documentation
└── README.md                    # This file
```

---

## Environment Setup

### 1. Clone and navigate

```bash
cd "AI Study and Revision Agent/backend"
```

### 2. Create virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the `.env` file

Create a `.env` file in the **project root** (one level above `backend/`):

```env
# Application
ENV=development

# Security — generate with: openssl rand -hex 32
SECRET_KEY=your_secret_key_here
ACCESS_TOKEN_EXPIRE_MINUTES=60

# PostgreSQL
DATABASE_URL=postgresql+psycopg2://<user>:<password>@localhost:5432/<dbname>

# FAISS vector store
FAISS_DATA_DIR=faiss_data

# LLM — local model (optional, used as fallback)
LLM_MODEL_PATH=models/Phi-3-mini-4k-instruct-q4.gguf

# LLM — Groq (primary)
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL_NAME=llama-3.1-8b-instant

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

> The config loader reads from `../.env` relative to the `backend/app/` directory, so the file belongs one level above `backend/`.

---

## Database Setup

### 1. Create the PostgreSQL database

```sql
CREATE DATABASE study_db;
```

### 2. Run migrations

```bash
cd backend
alembic upgrade head
```

If Alembic has not been initialised yet:

```bash
alembic init alembic
# Edit alembic.ini to point to your DATABASE_URL, then:
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

---

## Running the Server

From inside the `backend/` directory:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

| Flag | Purpose |
|---|---|
| `--reload` | Auto-restart on file changes (development only) |
| `--host 0.0.0.0` | Accept connections from any interface |
| `--port 8000` | Default port |

The server will be available at `http://localhost:8000`.

### Interactive API docs

| URL | Interface |
|---|---|
| `http://localhost:8000/docs` | Swagger UI (auto-generated) |
| `http://localhost:8000/redoc` | Redoc |
| `backend/openapi.yaml` | Static OpenAPI 3.1 spec (import into Postman) |

---

## API Overview

### Authentication

All endpoints except `/health`, `/auth/signup`, and `/auth/token` require a JWT bearer token.

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com", "password": "yourpassword"}'

# 2. Login
curl -X POST http://localhost:8000/auth/token \
  -F "username=you@example.com" \
  -F "password=yourpassword"

# Use the returned access_token in subsequent requests:
# Authorization: Bearer <token>
```

### Key Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/documents/upload` | Upload a PDF with a topic label |
| `POST` | `/rag/ask` | Ask a question over your uploaded docs |
| `POST` | `/quiz/generate` | Generate an adaptive quiz |
| `GET` | `/quiz/{quiz_id}` | Fetch quiz questions |
| `POST` | `/quiz/{quiz_id}/start` | Start a quiz attempt |
| `POST` | `/quiz/{quiz_id}/submit` | Submit answers and get scored |
| `GET` | `/analytics/overview` | Full analytics dashboard data |
| `GET` | `/analytics/recommend-smart` | AI topic recommendation |
| `GET` | `/analytics/weekly-plan` | AI-generated weekly study plan |

See `openapi.yaml` or `BACKEND_DOCS.md` for the complete reference.

---

## Running Tests

```bash
cd backend
pytest app/tests/ -v
```

Test files:

| File | Tests |
|---|---|
| `app/tests/test_rag.py` | RAG pipeline |
| `app/tests/test_pipeline.py` | Query answer pipeline |
| `app/tests/redis_test.py` | Redis connection |
| `app/tests/sanity_quiz_db_check.py` | DB quiz sanity checks |

---

## Architecture Notes

- **FAISS user isolation** — every vector is stored with `user_id` metadata. Searches always pass `filters={"user_id": user_id}` so users only retrieve their own content.
- **Redis key namespacing** — all Redis keys are prefixed `user:{id}:...`. There is no shared state between users.
- **Adaptive difficulty** — each quiz submission adjusts the user's `current_difficulty` in `UserTopicProgress` based on score thresholds (≥ 0.8 → up, < 0.4 → down).
- **Forgetting curve** — `IntelligenceService` models retention as `confidence × e^(-0.1 × hours_since_last_attempt)`. The `/analytics/revision` and `/analytics/weekly-plan` endpoints use this to surface topics that need review.
- **LLM fallback** — if the Groq response cannot be normalised into a valid quiz structure, `_fallback_quiz_generation()` generates questions directly from chunk text without LLM.
- **FAISS persistence** — the index is loaded from disk at startup and saved after every document upload. The metadata list is pickled alongside the binary index.

For a deep dive into every component, see [BACKEND_DOCS.md](BACKEND_DOCS.md).
