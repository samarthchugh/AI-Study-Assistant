# AI Study and Revision Agent

A full-stack, AI-powered study platform that helps students learn smarter. Upload your study materials as PDFs, ask questions about them, take adaptive quizzes, and get a personalised weekly revision schedule — all driven by RAG, vector search, and LLM inference.

---

## Features

- **PDF Ingestion** — Upload lecture notes, textbooks, or any PDF. The backend chunks, embeds, and indexes content into a FAISS vector store.
- **AI Chat (Ask AI)** — Ask natural-language questions about your uploaded material. Answers are grounded in your documents with source attribution and similarity scores.
- **Adaptive Quizzes** — Auto-generated MCQ and short-answer quizzes. Difficulty adjusts (1–5) based on your performance, and per-question explanations are shown after submission.
- **Quiz Review** — Revisit any completed quiz to see which questions you got right or wrong, with correct answers and explanations.
- **Analytics Dashboard** — Tracks confidence per topic, identifies weak areas, and surfaces what needs the most attention.
- **Smart Weekly Plan** — An agentic pipeline (LangGraph) builds a personalised 7-day revision schedule based on spaced repetition and your knowledge gaps.
- **Dark / Light Mode** — Full theme support via `next-themes`.

---

## Tech Stack

### Backend (Python / FastAPI)

| Layer | Technology |
|---|---|
| Framework | FastAPI + Uvicorn |
| Database | PostgreSQL 15 + SQLAlchemy ORM |
| Migrations | Alembic |
| Auth | JWT (python-jose) + Argon2 password hashing |
| Vector Store | FAISS (CPU) |
| Embeddings | Sentence Transformers |
| LLM | Groq API |
| Agent Orchestration | LangGraph + LangChain |
| Document Parsing | PyMuPDF |
| Caching | Redis 7 |
| Testing | Pytest |

### Frontend (TypeScript / Next.js)

| Layer | Technology |
|---|---|
| Framework | Next.js 16 (App Router) |
| Language | TypeScript + React 19 |
| Styling | Tailwind CSS v4 |
| Components | shadcn/ui |
| Icons | Lucide React |
| Charts | Recharts |
| Toasts | Sonner |

---

## Project Structure

```
AI Study and Revision Agent/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # Route handlers (auth, documents, rag, quiz, analytics)
│   │   ├── agents/          # LangGraph agent graph (analyzer, planner, scheduler)
│   │   ├── db/              # SQLAlchemy models, CRUD, session
│   │   ├── rag/             # RAG pipeline (ingestion, chunking, embeddings, retrieval)
│   │   ├── schemas/         # Pydantic request/response schemas
│   │   ├── services/        # Business logic (quiz engine, LLM, security, vector store)
│   │   ├── utils/           # Logging, topic utilities
│   │   └── main.py          # App entry point, router registration
│   ├── tests/               # Pytest test suite
│   ├── alembic/             # Database migration scripts
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── (auth)/          # Login and signup pages
│   │   └── (dashboard)/     # Protected pages: dashboard, upload, ask, quiz, analytics
│   ├── components/
│   │   ├── layout/          # Sidebar navigation
│   │   └── ui/              # shadcn/ui components
│   ├── lib/
│   │   ├── api.ts           # Typed API client
│   │   ├── auth.tsx         # Auth context and hooks
│   │   └── utils.ts         # cn() and helpers
│   ├── Dockerfile
│   └── package.json
└── infra/
    └── docker-compose.yaml  # Orchestrates db, redis, api, frontend
```

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) and Docker Compose
- A [Groq](https://console.groq.com/) API key

### 1. Clone the repository

```bash
git clone <repo-url>
cd "AI Study and Revision Agent"
```

### 2. Configure environment variables

**Backend** — create `backend/.env`:

```env
ENV=development
SECRET_KEY=your-secret-key-here

DATABASE_URL=postgresql://postgres:postgres@db:5432/study_db

FAISS_DATA_DIR=./faiss_data/faiss
GROQ_API_KEY=your-groq-api-key

REDIS_HOST=redis
REDIS_PORT=6379
```

**Frontend** — create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 3. Start with Docker Compose

```bash
cd infra
docker compose up --build
```

This starts four services:

| Service | URL |
|---|---|
| Frontend (Next.js) | http://localhost:3000 |
| Backend (FastAPI) | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| PostgreSQL | localhost:5432 |
| Redis | localhost:6379 |

### 4. Run without Docker (development)

**Backend:**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

---

## API Overview

All routes are prefixed with `/api/v1` (or bare, depending on config).

| Prefix | Description |
|---|---|
| `POST /auth/signup` | Register a new user |
| `POST /auth/token` | Login, returns JWT |
| `POST /documents/upload` | Upload a PDF for a topic |
| `POST /rag/ask` | Stream an AI answer from your documents |
| `POST /quiz/generate` | Generate a quiz for a topic |
| `GET  /quiz/{id}` | Get quiz questions |
| `POST /quiz/{id}/start` | Start a timed attempt |
| `POST /quiz/{id}/submit` | Submit answers, get scored results |
| `GET  /quiz/{id}/review` | Review a past completed attempt |
| `GET  /quiz/my-quizzes` | List all user quizzes |
| `GET  /analytics/overview` | Topics, confidence map, weak areas |
| `GET  /analytics/recommend-smart` | AI-powered topic recommendation |
| `GET  /analytics/weekly-plan` | Personalised 7-day study schedule |

Full interactive docs available at `/docs` when the backend is running.

---

## How It Works

### RAG Pipeline

1. Uploaded PDFs are parsed with PyMuPDF and split into overlapping chunks.
2. Each chunk is embedded using Sentence Transformers and stored in a per-user FAISS index.
3. On a question, the top-k nearest chunks are retrieved, filtered by a relevance threshold (≥ 0.35 cosine similarity), and deduplicated by source document.
4. The relevant passages are sent to the Groq LLM as context, and the answer is streamed back with source attribution.

### Adaptive Quiz Engine

1. A quiz is generated by prompting the Groq LLM with retrieved context for the chosen topic and difficulty.
2. After submission, each answer is graded and stored in `QuestionAttempt` records.
3. The user's mastery score and difficulty level are updated based on `score_ratio`.
4. The quiz review endpoint reconstructs the full breakdown from stored attempt records.

### Agentic Study Planner

A LangGraph agent graph runs an analysis → planning → scheduling pipeline:
- **Analyzer Agent** — identifies weak topics from quiz history.
- **Planner Agent** — maps topics to revision priority using forgetting curve logic.
- **Scheduler** — produces a 7-day study plan with task type (revise / practice) and priority.

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

---

## Environment Variables Reference

| Variable | Location | Description |
|---|---|---|
| `SECRET_KEY` | backend/.env | JWT signing secret |
| `DATABASE_URL` | backend/.env | PostgreSQL connection string |
| `GROQ_API_KEY` | backend/.env | Groq LLM API key |
| `FAISS_DATA_DIR` | backend/.env | Path to FAISS index storage |
| `REDIS_HOST` | backend/.env | Redis hostname |
| `REDIS_PORT` | backend/.env | Redis port (default 6379) |
| `NEXT_PUBLIC_API_URL` | frontend/.env.local | Backend base URL for the frontend |
