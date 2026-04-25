# Backend — Complete Technical Documentation

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Directory Structure](#2-directory-structure)
3. [Tech Stack](#3-tech-stack)
4. [Configuration & Environment](#4-configuration--environment)
5. [Database Layer](#5-database-layer)
6. [Authentication & Security](#6-authentication--security)
7. [RAG Pipeline — End-to-End Flow](#7-rag-pipeline--end-to-end-flow)
8. [Vector Store (FAISS)](#8-vector-store-faiss)
9. [Embedding Model](#9-embedding-model)
10. [Quiz Engine](#10-quiz-engine)
11. [Intelligence Service](#11-intelligence-service)
12. [Agent Pipeline (LangGraph)](#12-agent-pipeline-langgraph)
13. [API Layer](#13-api-layer)
14. [Logging](#14-logging)
15. [Redis Usage Map](#15-redis-usage-map)
16. [Complete E2E User Journey](#16-complete-e2e-user-journey)
17. [Data Flow Diagrams](#17-data-flow-diagrams)
18. [Error Handling Strategy](#18-error-handling-strategy)

---

## 1. Architecture Overview

The backend is a FastAPI application that combines a RAG (Retrieval-Augmented Generation) study Q&A system with an adaptive quiz engine and a personalised learning analytics layer.

```
┌──────────────────────────────────────────────────────────────┐
│                         FastAPI App                          │
│                                                              │
│  ┌──────┐ ┌───────┐ ┌───────────┐ ┌─────┐ ┌────────────┐     │
│  │ Auth │ │ Users │ │ Documents │ │ RAG │ │    Quiz    │     │
│  └──────┘ └───────┘ └─────┬─────┘ └──┬──┘ └─────┬──────┘     │
│                           │          │          │            │
│            ┌──────────────▼──────────▼──────────▼──────┐     │
│            │              Intelligence / Analytics     │     │
│            └───────────────────────────────────────────┘     │
└──────────────────────────────┬───────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
    PostgreSQL             FAISS Index            Redis
   (structured data)    (vector store)          (caching &
    Users, Quizzes,      Embeddings +            analytics
    Attempts, Progress   Chunk metadata          signals)
```

**Three storage layers:**

| Layer | Technology | Stores |
|---|---|---|
| Relational DB | PostgreSQL + SQLAlchemy | Users, quizzes, questions, attempts, topic progress |
| Vector Store | FAISS (flat inner-product index) | Chunk embeddings + metadata (text, user\_id, topic) |
| Cache / Signal Store | Redis | Attempt history, confidence scores, weak topics, forgetting curve state |

---

## 2. Directory Structure

```
backend/
├── app/
│   ├── main.py                        # FastAPI app, router registration
│   ├── config.py                      # Pydantic settings, Redis client
│   ├── dependencies.py                # JWT decode → get_current_user()
│   │
│   ├── api/v1/
│   │   ├── auth.py                    # /auth/* — signup, login
│   │   ├── users.py                   # /users/me
│   │   ├── documents.py               # /documents/upload
│   │   ├── rag.py                     # /rag/ask
│   │   ├── quiz.py                    # /quiz/* — generate, fetch, start, submit
│   │   └── analytics.py               # /analytics/* — 8 endpoints
│   │
│   ├── db/
│   │   ├── session.py                 # SQLAlchemy engine + get_db()
│   │   ├── models.py                  # ORM models (5 tables)
│   │   └── crud.py                    # DB helper functions
│   │
│   ├── rag/
│   │   ├── ingestion.py               # PDF → pages → chunks → FAISS
│   │   ├── chunking.py                # Text chunking logic
│   │   ├── embeddings.py              # SentenceTransformer singleton
│   │   ├── retriever.py               # Query → FAISS search → filtered chunks
│   │   ├── pipeline.py                # RAG orchestration (retrieve + LLM)
│   │   ├── prompts.py                 # LLM prompt templates
│   │   └── contracts.py               # RetrievedChunk Pydantic model
│   │
│   ├── services/
│   │   ├── llm.py                     # Groq API client
│   │   ├── vector_store.py            # FAISSVectorStore class
│   │   ├── vector_store_instance.py   # Global singleton instance
│   │   ├── security.py                # Password hashing, JWT creation/verify
│   │   ├── quiz_engine.py             # Quiz generation, scoring, mastery update
│   │   └── intelligence_service.py    # Adaptive learning signals (Redis)
│   │
│   ├── agents/
│   │   ├── graph.py                   # LangGraph StateGraph (3 nodes)
│   │   ├── analyzer_agent.py          # Node 1: reads learning state
│   │   ├── planner_agent.py           # Node 2: builds prioritised task list
│   │   └── scheduler.py              # Node 3: maps tasks to calendar days
│   │
│   ├── schemas/
│   │   ├── user.py                    # UserCreate, UserResponse
│   │   ├── token.py                   # Token
│   │   ├── quiz.py                    # SubmitQuizRequest/Response, AnswerItem
│   │   └── request.py                 # AskRequest, AskResponse
│   │
│   └── utils/
│       ├── logging.py                 # RotatingFileHandler per module
│       └── topic_utils.py             # normalize_topic()
│
├── faiss_data/faiss/                  # Persisted FAISS index files
│   ├── index_v1_flat.faiss
│   └── index_v1_flat.meta.pkl
│
├── logs/                              # Per-module rotating log files
├── requirements.txt
├── openapi.yaml                       # OpenAPI 3.1 spec
├── BACKEND_DOCS.md                    # This file
└── README.md
```

---

## 3. Tech Stack

| Category | Library / Tool | Version / Notes |
|---|---|---|
| Web framework | FastAPI | With Uvicorn (ASGI) |
| ORM | SQLAlchemy | Session-based, `autoflush=False` |
| Database | PostgreSQL | via psycopg2-binary |
| Migrations | Alembic | (configured, run manually) |
| Authentication | python-jose (JWT) + passlib (Argon2) | HS256 tokens |
| PDF parsing | PyMuPDF (fitz) | Page-level text extraction |
| Embeddings | sentence-transformers | `all-MiniLM-L6-v2` — 384 dimensions |
| Vector store | faiss-cpu | `IndexFlatIP` (inner-product / cosine) |
| LLM inference | Groq API | `llama-3.1-8b-instant` |
| Caching | Redis (redis-py) | `decode_responses=True` |
| Agent orchestration | LangGraph + LangChain | 3-node directed graph |
| Config management | pydantic-settings | `.env` file injection |
| Validation | Pydantic v2 | Request/response schemas |
| Logging | stdlib `logging` | RotatingFileHandler, per-module |
| Testing | pytest + httpx | Unit and integration tests |

---

## 4. Configuration & Environment

All settings are managed by `app/config.py` via `pydantic_settings.BaseSettings`.

### Environment Variables

Create a `.env` file in the **project root** (one level above `backend/`):

```env
# Application
ENV=development

# Security
SECRET_KEY=<generate with: openssl rand -hex 32>
ACCESS_TOKEN_EXPIRE_MINUTES=60

# PostgreSQL
DATABASE_URL=postgresql+psycopg2://<user>:<password>@<host>:<port>/<dbname>

# FAISS
FAISS_DATA_DIR=faiss_data

# LLM — local model (optional fallback)
LLM_MODEL_PATH=models/Phi-3-mini-4k-instruct-q4.gguf

# LLM — Groq (primary)
GROQ_API_KEY=<your groq api key>
GROQ_MODEL_NAME=llama-3.1-8b-instant

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### Computed Config Properties

| Property | Computed As |
|---|---|
| `FAISS_DIR` | `DATA_DIR / "faiss"` (auto-created) |
| `FAISS_INDEX_PATH` | `FAISS_DIR / "index_v1_flat.faiss"` |
| `FAISS_META_PATH` | `FAISS_DIR / "index_v1_flat.meta.pkl"` |

### Global Singletons (in `config.py`)

```python
settings = Settings()        # loaded once at import time
redis_client = redis.Redis(  # shared across all services
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True
)
```

---

## 5. Database Layer

### SQLAlchemy Setup (`db/session.py`)

```python
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)
```

- `pool_pre_ping=True` — validates connections before use, handles stale pool connections gracefully.
- `autoflush=False` — writes only happen on explicit `.commit()`, preventing partial state leaks.

### ORM Models (`db/models.py`)

#### `users`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | Auto-increment |
| `email` | String UNIQUE | Not null |
| `hashed_password` | String | Argon2 hash |
| `provider` | String | Default `"local"` |
| `created_at` | DateTime(tz) | UTC |

#### `quizzes`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | FK → users.id | |
| `topic` | String | Normalised lowercase |
| `difficulty_level` | Integer | CHECK 1–5 |
| `status` | String | `active` / `completed` |
| `total_questions` | Integer | |
| `created_at` | DateTime(tz) | |
| `completed_at` | DateTime(tz) | Nullable |

#### `questions`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `quiz_id` | FK → quizzes.id | |
| `question_text` | Text | |
| `question_type` | String | `mcq` / `short` |
| `options` | JSONB | Nullable (MCQ only) |
| `correct_answer` | Text | |
| `explanation` | Text | Nullable |
| `difficulty_level` | Integer | CHECK 1–5 |
| `created_at` | DateTime(tz) | |

#### `quiz_attempts`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `quiz_id` | FK → quizzes.id | |
| `user_id` | FK → users.id | |
| `score` | Float | Nullable |
| `max_score` | Float | Nullable |
| `score_ratio` | Float | 0.0–1.0 |
| `confidence_score` | Float | Nullable |
| `start_time` | DateTime(tz) | Set on `/start` |
| `submitted_at` | DateTime(tz) | Set on `/submit` |
| `time_taken_seconds` | Integer | `submitted_at - start_time` |

#### `question_attempts`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `quiz_attempt_id` | FK → quiz_attempts.id | |
| `question_id` | FK → questions.id | |
| `user_answer` | Text | |
| `is_correct` | Integer | 0 or 1 |
| `score` | Float | Per-question score |
| `confidence_score` | Float | Nullable |
| `answered_at` | DateTime(tz) | |

#### `user_topic_progress`
| Column | Type | Notes |
|---|---|---|
| `id` | Integer PK | |
| `user_id` | FK → users.id | |
| `topic` | String | |
| `current_difficulty` | Integer | Default 2, range 1–5 |
| `mastery_score` | Float | 0.0–1.0, default 0.0 |
| `last_attempt_at` | DateTime(tz) | Nullable |
| `total_attempts` | Integer | Default 0 |
| `correct_attempts` | Integer | Default 0 |
| `updated_at` | DateTime(tz) | |
| **UNIQUE** | `(user_id, topic)` | One row per user/topic pair |

---

## 6. Authentication & Security

### Flow

```
Client                          Backend
  │                                │
  │  POST /auth/signup             │
  │  {email, password}  ─────────► │  1. Hash password (Argon2)
  │                                │  2. Insert User row
  │  ◄──────  UserResponse         │  3. Return {id, email, provider, created_at}
  │                                │
  │  POST /auth/token              │
  │  form: {username, password} ──►│  1. Lookup user by email
  │                                │  2. Verify Argon2 hash
  │  ◄──────  {access_token}       │  3. Sign JWT (sub=user_id, exp=60min)
  │                                │
  │  GET /any-protected            │
  │  Authorization: Bearer <jwt> ─►│  1. Decode JWT (python-jose)
  │                                │  2. Extract sub → user_id
  │  ◄──────  response             │  3. Inject as Depends(get_current_user)
```

### JWT Claims

```json
{
  "sub": "4",
  "exp": 1714000000
}
```

- `sub` carries the `user_id` as a string.
- All protected routes call `int(current_user)` to convert back to an integer before DB/Redis queries.

### Password Hashing

- Algorithm: **Argon2** (via passlib + argon2-cffi)
- Argon2 is the winner of the Password Hashing Competition — chosen over bcrypt for better resistance to GPU attacks.

---

## 7. RAG Pipeline — End-to-End Flow

### 7.1 Document Ingestion (`POST /documents/upload`)

```
Client uploads PDF + topic
           │
           ▼
  documents.py endpoint
           │
           ├── Validate: file must be .pdf
           ├── Save temp file to disk
           ├── normalize_topic(topic)
           │
           ▼
  ingest_pdf_to_vectorstore()        [rag/ingestion.py]
           │
           ├─► load_pdf()            [PyMuPDF]
           │       └── Extract text page-by-page
           │           Clean whitespace, preserve structure
           │
           ├─► create_chunks()       [rag/chunking.py]
           │       └── Split pages into overlapping chunks
           │           Assign chunk_id, doc_id, page number
           │
           ├─► embed_text()          [rag/embeddings.py]
           │       └── SentenceTransformer.encode()
           │           all-MiniLM-L6-v2 → 384-dim L2-normalised vectors
           │
           ├─► vector_store.add()    [services/vector_store.py]
           │       └── FAISS IndexFlatIP.add(embeddings)
           │           Append metadata to in-memory list
           │
           └─► vector_store.save()
                   └── Write .faiss index to disk
                       Pickle metadata list to .meta.pkl

After ingestion:
  └── redis_client.sadd(f"user:{user_id}:topics", topic)
      Register topic in user's topic set
```

**Chunk metadata stored per vector:**
```python
{
    "chunk_id": "<uuid>",
    "doc_id": "<uuid>",
    "chunk_index": 0,
    "page": 1,
    "source": "user_upload",
    "created_at": "2026-04-22T10:00:00",
    "user_id": 5,          # integer
    "topic": "deep learning",
    "text": "..."           # stored for retrieval
}
```

### 7.2 Query Answering (`POST /rag/ask`)

```
Client sends {question: "What is backpropagation?"}
           │
           ▼
  QueryAnswerPipeline              [rag/pipeline.py]
           │
           ├─► embed_text([question])
           │       384-dim query vector
           │
           ├─► Retriever.retrieve()  [rag/retriever.py]
           │       │
           │       ├── vector_store.search(
           │       │       query_vec,
           │       │       top_k=16,        # over-fetch 2×
           │       │       filters={"user_id": user_id},
           │       │       search_k=48      # 6× for filter headroom
           │       │   )
           │       │
           │       │   Inside search():
           │       │   1. Pre-filter metadata by user_id (type-coerced string comparison)
           │       │   2. Reconstruct vectors for valid indices only
           │       │   3. Normalize → dot product with query vec
           │       │   4. argsort descending → top_k
           │       │
           │       ├── Filter: score >= 0.10 (cosine similarity threshold)
           │       ├── Sort by score descending
           │       └── Truncate: max 8 chunks OR 8000 chars total
           │
           ├─► Build prompt with retrieved chunks as context
           │       [rag/prompts.py]
           │
           ├─► Groq LLM call        [services/llm.py]
           │       llama-3.1-8b-instant
           │
           └─► Return {answer, sources, confidence}
```

**Key retrieval parameters:**

| Parameter | Value | Why |
|---|---|---|
| `score_threshold` | 0.10 | Lowered from 0.15 after diagnosing that ecomm chunks scored max 0.138 |
| `top_k` | 8 | Final chunks returned to LLM |
| Over-fetch multiplier | 2× | Compensates for score filtering drop-off |
| `max_context_chars` | 8000 | Prevents token overflow in LLM prompt |

---

## 8. Vector Store (FAISS)

**Class:** `FAISSVectorStore` in `services/vector_store.py`

**Index type:** `faiss.IndexFlatIP` (flat inner-product index)

- Exact nearest-neighbour search (no approximation).
- Inner product on L2-normalised vectors = cosine similarity.
- Suitable for the current data size; can be swapped for `IndexIVFFlat` if scale grows.

### add()

```python
def add(self, embeddings: np.ndarray, metadatas: List[Dict]) -> None
```

- Validates shape: `embeddings.shape[0] == len(metadatas)`.
- Casts to `float32` before FAISS insert.
- Appends metadatas to the in-memory `self.metadata` list.
- FAISS vector indices and metadata list indices are always in sync.

### search()

```python
def search(self, query_embeddings, top_k=8, filters=None, search_k=40) -> List[Tuple[float, Dict]]
```

**Algorithm (5 steps):**

1. **Pre-filter**: Iterate `self.metadata`, keep indices where all filter keys match.
   - Type-coerced comparison: `str(stored) == str(v)` handles int/string mismatches from old ingested data.
2. **Reconstruct**: `index.reconstruct(i)` for each valid index → avoids searching the entire index.
3. **Normalize**: L2-normalise reconstructed vectors to prevent score distortion.
4. **Score**: `np.dot(vectors, query_vec)` — cosine similarity via inner product.
5. **Rank**: `argsort` descending, take `top_k`.

### Persistence

| File | Content |
|---|---|
| `faiss_data/faiss/index_v1_flat.faiss` | Binary FAISS index |
| `faiss_data/faiss/index_v1_flat.meta.pkl` | Pickled `List[Dict]` metadata |

Loaded automatically on `__init__` if the index file exists.

---

## 9. Embedding Model

**Model:** `sentence-transformers/all-MiniLM-L6-v2`

| Property | Value |
|---|---|
| Embedding dimensions | 384 |
| Max input tokens | 256 |
| Output normalisation | L2 (unit vectors) |
| Loading strategy | Singleton — loaded once per process |
| Batch encoding | Yes — all chunk texts in one `.encode()` call |

**Singleton pattern** in `rag/embeddings.py`:

```python
class EmbeddingModel:
    _model: SentenceTransformer | None = None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        if cls._model is None:
            cls._model = SentenceTransformer('all-MiniLM-L6-v2')
        return cls._model
```

The global instance is warmed up at import time in `vector_store_instance.py`:

```python
_dummy = embed_text(["warmup"])  # triggers model load
embedding_dim = _dummy.shape[1]  # → 384
vector_store = FAISSVectorStore(embedding_dim=embedding_dim)
```

---

## 10. Quiz Engine

**Class:** `QuizEngine` in `services/quiz_engine.py`

### Quiz Generation Flow (`POST /quiz/generate`)

```
1. Resolve topic
   └── If no topic given → IntelligenceService.recommend_smart_topic()

2. Get user's current difficulty
   └── Query UserTopicProgress (or default difficulty=2)

3. Retrieve RAG chunks
   └── Retriever.retrieve(query=topic, filters={"user_id": user_id, "topic": topic})

4. Build quiz prompt
   └── Include chunks as context + difficulty + num_questions

5. Call Groq LLM
   └── Returns JSON array of questions

6. Normalize / validate LLM output
   └── _normalize_quiz_payload()
   └── Fallback: _fallback_quiz_generation() if LLM output malformed

7. Persist to DB
   └── INSERT Quiz row
   └── INSERT Question rows (with correct_answer, options as JSONB)

8. Return {quiz_id, topic, difficulty, total_questions}
```

### Adaptive Difficulty

After quiz submission (`POST /quiz/{quiz_id}/submit`):

```
score_ratio = correct_answers / total_questions

if score_ratio >= 0.8:   difficulty += 1  (cap at 5)
elif score_ratio < 0.4:  difficulty -= 1  (floor at 1)
else:                    difficulty unchanged

mastery_score updated as:
  new_mastery = (old_mastery * total_prev_attempts + score_ratio) / (total_prev_attempts + 1)
  # running average clamped to [0, 1]
```

These values are written back to `UserTopicProgress`.

### Scoring Flow (`POST /quiz/{quiz_id}/submit`)

```
1. Validate quiz belongs to current user
2. Load all questions for this quiz
3. For each submitted answer:
   └── Compare user_answer to correct_answer (case-insensitive strip)
   └── Write QuestionAttempt row (is_correct, score)
4. Calculate score_ratio
5. Update UserTopicProgress (difficulty, mastery)
6. Mark Quiz as completed, set completed_at
7. Update QuizAttempt (score_ratio, time_taken_seconds)
8. Fire IntelligenceService.process_attempt() → Redis signals
9. Return SubmitQuizResponse
```

---

## 11. Intelligence Service

**Class:** `IntelligenceService` in `services/intelligence_service.py`

All data is stored in Redis, fully namespaced per user. No cross-user data sharing is possible.

### Redis Key Schema

| Key Pattern | Type | Stores |
|---|---|---|
| `user:{id}:topic:{topic}:attempts` | List | JSON attempt records (newest first, capped at 20) |
| `user:{id}:topic:{topic}:confidence` | String | Float 0.0–1.0 |
| `user:{id}:weak_topics` | ZSet | topic → weakness\_score (1 - confidence) |
| `user:{id}:topics` | Set | All topic names the user has uploaded |

Attempt lists expire after **7 days** (TTL refreshed on each new attempt).

### process_attempt() — Called After Every Quiz Submission

```
Input: user_id, topic, score_ratio, time_taken, difficulty, mastery_score

1. _record_attempt()
   └── LPUSH user:{id}:topic:{topic}:attempts  ← new attempt JSON
   └── LTRIM  (keep latest 20)
   └── EXPIRE 7 days

2. _get_recent_attempts()
   └── LRANGE 0 -1 → parse JSON list (newest → oldest)

3. _compute_recency_score(attempts)
   └── Exponential decay: weight_i = e^(-0.3 × i)
   └── recency_score = Σ(score_i × weight_i) / Σ(weight_i)
   └── Recent attempts count more than older ones

4. _compute_confidence(recency_score, mastery_score)
   └── confidence = 0.7 × recency_score + 0.3 × mastery_score
   └── Clamped to [0, 1]

5. redis.set(user:{id}:topic:{topic}:confidence, confidence)

6. _update_weak_topics()
   └── weakness = 1 - confidence
   └── ZADD user:{id}:weak_topics {topic: weakness}
```

### Forgetting Curve (`_compute_forgetting_score`)

```python
retention = confidence × e^(-0.1 × time_gap_hours)
```

- Models Ebbinghaus forgetting: retention decays exponentially with time since last study.
- `revision_priority = 1 - retention` — higher means more urgent.

### Smart Recommendation (`recommend_smart_topic`)

Scores every known topic:

```
combined_score = 0.6 × weakness + 0.4 × forgetting
```

- **Weakness (60%)** — how poorly the user performs on the topic.
- **Forgetting (40%)** — how much time has passed since last study relative to confidence.
- Returns the highest-scoring topic with full diagnostic breakdown.

---

## 12. Agent Pipeline (LangGraph)

**File:** `agents/graph.py`

A three-node directed acyclic graph built with LangGraph's `StateGraph`.

### State Schema

```python
class AgentState(TypedDict):
    user_id: int
    analysis: dict    # output of AnalyzerAgent
    plan: list        # output of PlannerAgent
    schedule: list    # output of Scheduler
```

### Graph Topology

```
START → analyze → plan → schedule → END
```

### Node 1: AnalyzerAgent

**File:** `agents/analyzer_agent.py`

Reads the user's current learning state from Redis via `IntelligenceService`:

- `_get_weak_topics(user_id)` — ZSET query for bottom performers
- `get_revision_topics(user_id)` — forgetting curve ranking
- `recommend_smart_topic(user_id)` — combined weakness + forgetting score

Returns:
```python
{
    "weak_topics": [...],
    "revision_topics": [...],
    "recommend": {...}
}
```

### Node 2: PlannerAgent

**File:** `agents/planner_agent.py`

Converts analysis into an ordered task list:

1. **High priority (revise):** Top 3 revision topics (forgotten/urgent)
2. **Medium priority (practice):** Top 2 weak topics (struggling)

Returns a list of `{"topic", "task", "priority"}` dicts.

### Node 3: Scheduler

**File:** `agents/scheduler.py`

Maps each task to a calendar day starting from today:

```python
day = datetime.now() + timedelta(days=i)
```

Returns:
```python
[
    {"day": "Thursday", "date": "2026-04-24", "topic": "deep learning", "task": "revise", "priority": "high"},
    ...
]
```

---

## 13. API Layer

All protected endpoints require `Authorization: Bearer <JWT>` header.

### Router Prefixes

| Router | Prefix | Tag |
|---|---|---|
| auth.py | `/auth` | AUTH |
| users.py | `/users` | USERS |
| documents.py | `/documents` | DOCUMENTS |
| rag.py | `/rag` | RAG |
| quiz.py | `/quiz` | QUIZ |
| analytics.py | `/analytics` | ANALYTICS |

### Complete Endpoint Reference

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | No | Health check |
| POST | `/auth/signup` | No | Register new user |
| POST | `/auth/token` | No | Login, get JWT |
| GET | `/users/me` | Yes | Current user info |
| POST | `/documents/upload` | Yes | Upload PDF for a topic |
| POST | `/rag/ask` | Yes | Q&A over uploaded docs |
| POST | `/quiz/generate` | Yes | Generate adaptive quiz |
| GET | `/quiz/{quiz_id}` | Yes | Fetch quiz + questions |
| POST | `/quiz/{quiz_id}/start` | Yes | Start quiz attempt |
| POST | `/quiz/{quiz_id}/submit` | Yes | Submit answers, get score |
| GET | `/analytics/all-topics` | Yes | All user topics |
| GET | `/analytics/confidence` | Yes | Topic confidence score |
| GET | `/analytics/weak-topics` | Yes | Top 5 weak topics |
| GET | `/analytics/overview` | Yes | Combined analytics |
| GET | `/analytics/recommend` | Yes | Next topic to study |
| GET | `/analytics/revision` | Yes | Topics needing revision |
| GET | `/analytics/recommend-smart` | Yes | Smart recommendation |
| GET | `/analytics/weekly-plan` | Yes | AI-generated weekly plan |

Full request/response schemas are documented in `openapi.yaml`.

---

## 14. Logging

**File:** `utils/logging.py`

Each module calls `get_logger(__name__)` which creates a module-specific logger with:

- **Console handler** (stdout)
- **Rotating file handler** — `logs/{module.name}.log`, 5 MB per file, 5 backups

Log format:
```
2026-04-22 16:01:44,262 | app.services.intelligence_service | INFO | Fetched 1 attempts for user 5, topic deep learning
```

Modules with separate log files:
- `app.api.v1.documents`
- `app.rag.ingestion`, `app.rag.retriever`
- `app.services.vector_store`, `app.services.quiz_engine`, `app.services.intelligence_service`
- `app.agents.analyzer_agent`, `app.agents.planner_agent`, `app.agents.scheduler`, `app.agents.graph`

---

## 15. Redis Usage Map

```
Redis DB 0
│
├── user:{id}:topics                   [SET]
│   └── All topic names user uploaded
│       Added: POST /documents/upload
│       Read:  /analytics/all-topics, recommend_smart_topic, get_revision_topics
│
├── user:{id}:topic:{t}:attempts       [LIST, max 20, TTL 7d]
│   └── JSON-encoded attempt records: {score_ratio, time_taken, difficulty, timestamp}
│       Push: IntelligenceService.process_attempt()
│       Read: _get_recent_attempts() → recency score
│
├── user:{id}:topic:{t}:confidence     [STRING]
│   └── Float 0.0–1.0
│       Write: process_attempt() after every quiz submit
│       Read:  /analytics/confidence, recommend_smart_topic, get_revision_topics
│
└── user:{id}:weak_topics              [ZSET]
    └── member=topic, score=weakness (1 - confidence)
        Write: _update_weak_topics() after every quiz submit
        Read:  /analytics/weak-topics, recommend_topic, AnalyzerAgent
```

---

## 16. Complete E2E User Journey

### New User Onboarding

```
1. POST /auth/signup   → create account
2. POST /auth/token    → get JWT
```

### Study Material Upload

```
3. POST /documents/upload  (PDF + topic)
   → PDF extracted into ~N chunks
   → Embedded and stored in FAISS with user_id + topic
   → Topic added to Redis user:{id}:topics set
```

### Q&A Session

```
4. POST /rag/ask  {question: "..."}
   → Query embedded
   → FAISS filtered by user_id
   → Top 8 chunks retrieved (score ≥ 0.10)
   → Chunks + question sent to Groq LLM
   → Answer returned with source references
```

### Quiz Session

```
5. POST /quiz/generate  ?topic=deep+learning
   → Adaptive difficulty looked up from UserTopicProgress
   → RAG chunks retrieved for topic
   → Groq LLM generates N questions
   → Quiz + Questions persisted to DB
   → Returns quiz_id

6. GET /quiz/{quiz_id}
   → Questions and options returned (correct_answer hidden)

7. POST /quiz/{quiz_id}/start
   → QuizAttempt row created, start_time recorded

8. POST /quiz/{quiz_id}/submit  ?attempt_id=N  {answers: [...]}
   → Answers scored per question
   → score_ratio calculated
   → Difficulty adjusted (±1 based on score_ratio thresholds)
   → Mastery score updated (running average)
   → QuizAttempt and Quiz marked completed
   → IntelligenceService.process_attempt() fires:
       - Attempt pushed to Redis list
       - Recency-weighted confidence computed
       - Confidence stored in Redis
       - Weak topics ZSET updated
```

### Analytics & Recommendation

```
9. GET /analytics/overview
   → All topics + weak topics + confidence map

10. GET /analytics/recommend-smart
    → Combined weakness + forgetting score across all topics
    → Returns highest-priority topic

11. GET /analytics/revision
    → Forgetting curve applied to each topic
    → Returns topics sorted by revision_priority

12. GET /analytics/weekly-plan
    → LangGraph agent pipeline:
        AnalyzerAgent → PlannerAgent → Scheduler
    → Returns day-by-day study plan
```

---

## 17. Data Flow Diagrams

### Document Upload

```
User ──► POST /documents/upload (PDF, topic)
                 │
         [documents.py]
                 │
         temp save to disk
                 │
         ingest_pdf_to_vectorstore()
                 │
         ┌───────┴──────────────────┐
         ▼                          ▼
    load_pdf()                 normalize_topic()
    (PyMuPDF)
         │
    create_chunks()
    (chunking.py)
         │
    embed_text()
    (SentenceTransformer)
         │
    vector_store.add()
    vector_store.save()
    (FAISS on disk)
         │
    redis.sadd(user topics)
         │
    ◄─── 200 {status: "success"}
```

### Quiz Submit → Intelligence Update

```
User ──► POST /quiz/{id}/submit {answers}
                 │
         [quiz.py → quiz_engine.py]
                 │
         Score each answer
         Update UserTopicProgress (DB commit)
         Update QuizAttempt (DB commit)
                 │
         IntelligenceService.process_attempt()
                 │
         ┌───────┴────────────────────────────┐
         ▼                                    ▼
    LPUSH attempt to Redis list          ZADD weakness to ZSET
    Compute recency score                (1 - confidence)
    Compute confidence
    SET confidence in Redis
                 │
         ◄─── SubmitQuizResponse
```

---

## 18. Error Handling Strategy

| Layer | Strategy |
|---|---|
| API endpoints | Try/except → `raise HTTPException(status_code=5xx, detail=str(e))` |
| Quiz engine | LLM output normalisation failures → `_fallback_quiz_generation()` |
| Vector store search | Empty filter results → return `[]` immediately |
| Intelligence service | All methods wrapped in try/except → return safe defaults (`0.0`, `[]`) |
| Agent nodes | Each agent wraps logic in try/except → returns empty defaults so graph continues |
| PDF ingestion | Custom `PDFIngestionError` domain exception re-raised with original cause |
| Redis operations | All Redis calls in try/except → logged and return defaults; never crash request |
| DB sessions | `get_db()` dependency ensures `db.close()` always runs via `finally` |

**Design principle:** Service layer failures degrade gracefully (return empty/zero defaults) rather than crashing the HTTP request. The API layer is the only place that raises `HTTPException`.
