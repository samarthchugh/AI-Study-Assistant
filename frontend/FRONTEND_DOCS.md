# Frontend — Complete Technical Documentation

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Directory Structure](#2-directory-structure)
3. [Tech Stack](#3-tech-stack)
4. [Configuration & Environment](#4-configuration--environment)
5. [Authentication Layer](#5-authentication-layer)
6. [API Client](#6-api-client)
7. [Pages & Routes](#7-pages--routes)
8. [Components](#8-components)
9. [State Management](#9-state-management)
10. [Analytics & Visualisation](#10-analytics--visualisation)
11. [Theming](#11-theming)
12. [Data Flow Diagrams](#12-data-flow-diagrams)
13. [Error Handling Strategy](#13-error-handling-strategy)

---

## 1. Architecture Overview

The frontend is a Next.js 16 App Router application. It communicates exclusively with the FastAPI backend over HTTP. There is no server-side data fetching — all API calls are made from client components.

```
┌──────────────────────────────────────────────────────────────┐
│                     Next.js App (Client)                      │
│                                                               │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │  (auth)  │  │  (dash)  │  │ Analytics│  │  Landing   │  │
│  │ login    │  │ dashboard│  │ Charts   │  │  page      │  │
│  │ signup   │  │ upload   │  │ Revision │  │            │  │
│  └──────────┘  │ ask      │  │ WeekPlan │  └────────────┘  │
│                │ quiz     │  └──────────┘                   │
│                └──────────┘                                  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  lib/auth.tsx    lib/api.ts    lib/utils.ts           │  │
│  │  AuthContext     API client    cn() helper             │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────┬────────────────────────────────┘
                              │  HTTP (Bearer JWT)
                              ▼
                   FastAPI Backend (:8000)
```

**Key design decisions:**

| Decision | Rationale |
|---|---|
| Client-only data fetching | Simplifies auth (no server-side cookie/session needed), works with JWT in localStorage |
| Single `lib/api.ts` module | Centralised error handling, auth injection, and type definitions |
| Route groups `(auth)` / `(dashboard)` | Separate layouts without URL segments |
| Auth guard in layout | `(dashboard)/layout.tsx` redirects to `/` on token loss — catches logout race conditions |

---

## 2. Directory Structure

```
frontend/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx              # /login
│   │   └── signup/page.tsx             # /signup
│   │
│   ├── (dashboard)/
│   │   ├── layout.tsx                  # Auth guard + Sidebar wrapper
│   │   ├── dashboard/page.tsx          # /dashboard — stats + recommendations
│   │   ├── upload/page.tsx             # /upload — PDF ingestion
│   │   ├── ask/page.tsx                # /ask — RAG Q&A chat
│   │   ├── quiz/
│   │   │   ├── page.tsx                # /quiz — quiz generator form
│   │   │   ├── history/page.tsx        # /quiz/history — past quizzes
│   │   │   └── [quiz_id]/
│   │   │       ├── page.tsx            # /quiz/:id — quiz player + inline results
│   │   │       └── review/page.tsx     # /quiz/:id/review — standalone review page
│   │   └── analytics/page.tsx          # /analytics — full analytics view
│   │
│   ├── layout.tsx                      # Root layout: ThemeProvider, Toaster, fonts
│   ├── page.tsx                        # / — landing page
│   └── globals.css                     # Tailwind v4 CSS variables + dark mode
│
├── components/
│   ├── layout/
│   │   └── Sidebar.tsx                 # Nav sidebar (6 items + theme toggle + logout)
│   ├── theme-toggle.tsx                # Sun/Moon toggle button
│   └── ui/                             # shadcn/ui primitives
│       ├── alert.tsx
│       ├── badge.tsx
│       ├── button.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       ├── input.tsx
│       ├── label.tsx
│       ├── progress.tsx
│       ├── separator.tsx
│       ├── sonner.tsx
│       └── tabs.tsx
│
├── lib/
│   ├── api.ts                          # All API calls, types, request helper
│   ├── auth.tsx                        # AuthContext, AuthProvider, useAuth()
│   └── utils.ts                        # cn() (clsx + tailwind-merge)
│
├── public/                             # Static assets
├── next.config.ts
├── postcss.config.mjs
├── tailwind.config.ts
├── tsconfig.json
├── package.json
├── README.md
└── FRONTEND_DOCS.md                    # This file
```

---

## 3. Tech Stack

| Category | Library | Version | Notes |
|---|---|---|---|
| Framework | Next.js | 16.2.4 | App Router, no Pages Router |
| Language | TypeScript | 5 | Strict mode |
| UI | React | 19.2.4 | No legacy APIs |
| Styling | Tailwind CSS | v4 | OKLch colour space, CSS-first config |
| Component kit | shadcn/ui | 4.4.0 | Radix primitives + Tailwind |
| Icons | lucide-react | 1.11.0 | SVG icon set |
| Charts | recharts | 3.8.1 | Bar charts for confidence viz |
| Toasts | sonner | 2.0.7 | Non-blocking notifications |
| Theming | next-themes | 0.4.6 | Dark/light persistence via localStorage |
| Class merging | clsx + tailwind-merge | — | Safe conditional class composition via `cn()` |
| Variants | class-variance-authority | 0.7.1 | Button/badge variant definitions |
| Animation | tw-animate-css | 1.4.0 | Tailwind animation utilities |

---

## 4. Configuration & Environment

### Environment Variables

Create `.env.local` in the `frontend/` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

If omitted, `lib/api.ts` falls back to `http://localhost:8000`.

### `next.config.ts`

Currently uses all defaults — no custom rewrites, redirects, or image domains configured.

### `postcss.config.mjs`

```javascript
export default {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};
```

### `globals.css`

Tailwind v4 uses a CSS-first approach — all theme tokens are declared as CSS custom properties inside `@theme`:

```css
@theme {
  --color-primary: oklch(0.6 0.18 264);
  --color-background: oklch(1 0 0);
  --radius-md: 0.5rem;
  /* ... */
}

.dark {
  --color-background: oklch(0.14 0 0);
  /* ... dark overrides */
}
```

---

## 5. Authentication Layer

**File:** `lib/auth.tsx`

### Flow

```
App mount
  └── AuthProvider reads localStorage["access_token"]
      └── Sets token state (null if missing)
          └── isLoading = false

Login
  └── auth.login(email, password)  [lib/api.ts]
      └── POST /auth/token (form-encoded)
          └── Returns { access_token }
              └── localStorage.setItem("access_token", token)
              └── setToken(token)  → React state update
                  └── All protected routes re-render with valid token

Logout
  └── logout()
      └── localStorage.removeItem("access_token")
      └── setToken(null)
          └── (dashboard)/layout.tsx useEffect fires
              └── router.replace("/")  → redirected to home
```

### Context Interface

```typescript
interface AuthContextValue {
  token: string | null;
  isLoading: boolean;
  login(email: string, password: string): Promise<void>;
  signup(email: string, password: string): Promise<void>;
  logout(): void;
}
```

### `useAuth()` hook

```typescript
const { token, isLoading, login, signup, logout } = useAuth();
```

Only works inside components wrapped by `AuthProvider` (which is mounted in `app/layout.tsx`).

### Auth Guard (`(dashboard)/layout.tsx`)

```typescript
useEffect(() => {
  if (!isLoading && !token) router.replace("/");
}, [token, isLoading, router]);
```

- Runs whenever `token` changes — catches the logout event immediately.
- Uses `router.replace("/")` (not `/login`) so back-navigation after logout lands on home, not the auth page.
- Renders `null` while loading to prevent flash of dashboard content.

---

## 6. API Client

**File:** `lib/api.ts`

### Request Helper

```typescript
async function request<T>(path: string, options?: RequestInit & { auth?: boolean }): Promise<T>
```

- Reads `NEXT_PUBLIC_API_URL` for the base URL.
- Injects `Authorization: Bearer <token>` from `localStorage` when `auth: true` (default).
- Throws `Error` with the backend's `detail` message on non-2xx responses.

### Type Definitions

```typescript
// Auth
interface LoginResponse { access_token: string; token_type: string; }

// Quiz
interface QuizSummary  { quiz_id: number; topic: string; difficulty: number; total_questions: number; }
interface QuizDetail   { quiz_id: number; topic: string; difficulty: number; total_questions: number; questions: Question[]; }
interface Question     { question_id: number; question_text: string; options: Record<string, string> | null; }

interface QuestionResult {
  question_id: number; question_text: string; question_type: string;
  options: Record<string, string> | string[] | null;  // dict, list, or null
  user_answer: string; correct_answer: string;
  explanation: string | null; is_correct: boolean;
}

interface SubmitResult {
  quiz_id: number; score_ratio: number; correct_answers: number; total_questions: number;
  new_difficulty: number; updated_mastery: number; time_taken_seconds: number | null;
  question_breakdown: QuestionResult[];
}

interface ReviewResult {
  quiz_id: number; topic: string; difficulty: number; score_ratio: number;
  correct_answers: number; total_questions: number;
  time_taken_seconds: number | null; question_breakdown: QuestionResult[];
}

interface QuizListItem {
  quiz_id: number; topic: string; difficulty: number; total_questions: number;
  status: "not_started" | "in_progress" | "completed";
  created_at: string; completed_at: string | null;
  score_ratio: number | null; time_taken_seconds: number | null; attempt_id: number | null;
}

// Analytics
interface WeakTopic        { topic: string; confidence: number; weakness: number; }
interface RevisionTopic    { topic: string; retention: number; confidence: number; revision_priority: number; }
interface ScheduleItem     { day: string; date: string; topic: string; task: "revise" | "practice"; priority: "high" | "medium" | "low"; instruction?: string; }
interface SmartRecommendation { recommended_topic: string | null; reason: { topic: string; weakness: number; forgetting: number; confidence: number; retention: number; combined_score: number; } | string; }
interface OverviewResponse { user_id: number; topics: string[]; weak_topics: WeakTopic[]; confidence_map: Record<string, number>; }
```

### API Namespaces

#### `auth`

| Function | Method | Path | Notes |
|---|---|---|---|
| `auth.signup(email, password)` | POST | `/auth/signup` | JSON body |
| `auth.login(email, password)` | POST | `/auth/token` | `application/x-www-form-urlencoded` |

#### `documents`

| Function | Method | Path | Notes |
|---|---|---|---|
| `documents.upload(file, topic)` | POST | `/documents/upload` | multipart/form-data |

#### `rag`

| Function | Method | Path | Notes |
|---|---|---|---|
| `rag.ask(question)` | POST | `/rag/ask` | Returns `{ answer, sources: string[], confidence }` (non-streaming) |

> The `/ask` page uses `/rag/ask-stream` directly via `fetch` + manual SSE parsing (not wrapped in `lib/api.ts`). See the [Ask AI](#ask----ask-ai-appdashboardaskpagetsx) page section for the SSE protocol details.

#### `quiz`

| Function | Method | Path | Notes |
|---|---|---|---|
| `quiz.generate(params)` | POST | `/quiz/generate` | `params`: `{ topic?, num_questions?, difficulty? }` |
| `quiz.get(quiz_id)` | GET | `/quiz/{id}` | Returns `QuizDetail` |
| `quiz.start(quiz_id)` | POST | `/quiz/{id}/start` | Returns `{ message, attempt_id }` |
| `quiz.submit(quiz_id, attempt_id, answers)` | POST | `/quiz/{id}/submit` | Returns `SubmitResult` with `question_breakdown` |
| `quiz.list()` | GET | `/quiz/my-quizzes` | Returns `{ quizzes: QuizListItem[] }` |
| `quiz.review(quiz_id)` | GET | `/quiz/{id}/review` | Returns `ReviewResult` for the last completed attempt |

#### `analytics`

| Function | Method | Path | Notes |
|---|---|---|---|
| `analytics.overview()` | GET | `/analytics/overview` | Topics + weak topics + confidence map |
| `analytics.weakTopics()` | GET | `/analytics/weak-topics` | |
| `analytics.allTopics()` | GET | `/analytics/all-topics` | |
| `analytics.confidence(topic)` | GET | `/analytics/confidence` | |
| `analytics.revision(top_k)` | GET | `/analytics/revision` | Forgetting-curve ranked |
| `analytics.recommendSmart()` | GET | `/analytics/recommend-smart` | Returns `SmartRecommendation` |
| `analytics.weeklyPlan()` | GET | `/analytics/weekly-plan` | Returns `{ weekly_plan: ScheduleItem[] }` |

---

## 7. Pages & Routes

### `/` — Landing Page (`app/page.tsx`)

Public marketing page. Adapts based on auth state:

- **Guest**: "Sign in" + "Get started" CTAs in nav; hero CTA opens `/signup`.
- **Logged in**: "Go to Dashboard →" in nav; hero CTA goes to `/dashboard`.

Sections: hero, features (3-column grid), how-it-works (numbered steps), CTA banner.

Does **not** auto-redirect logged-in users — they can browse the landing page and navigate back to the dashboard manually.

### `/login` — Login Page (`app/(auth)/login/page.tsx`)

- "← Back to home" link at top.
- Email + password fields, form validation.
- On success: `router.replace("/dashboard")`.
- On error: inline alert with backend error message.

### `/signup` — Signup Page (`app/(auth)/signup/page.tsx`)

- Same layout as login.
- Additional confirm-password field.
- Client-side validation: passwords must match, min 8 characters.
- On success: `router.replace("/dashboard")`.

### `/dashboard` — Main Dashboard (`app/(dashboard)/dashboard/page.tsx`)

Loads on mount via `Promise.all`:
1. `analytics.overview()` — topics, weak topics, confidence map
2. `analytics.recommendSmart()` — smart study recommendation

Displays:
- **Stats row**: total topics, weak topic count, top confidence, lowest confidence
- **Study Now card**: recommended topic with weakness %, forgetting %, confidence %, combined score — links to `/ask?topic=...`
- **Weak Topics list**: top 5 with confidence bars — each links to `/quiz?topic=...`
- **Confidence Breakdown**: progress bars for all topics

### `/upload` — PDF Upload (`app/(dashboard)/upload/page.tsx`)

- Topic text input + file picker (`accept=".pdf"`).
- Calls `documents.upload(file, topic)` on submit.
- Shows success toast via Sonner on completion.
- Shows error alert inline on failure.

### `/ask` — Ask AI (`app/(dashboard)/ask/page.tsx`)

- Question input + submit button.
- Reads `?topic=` from URL to pre-fill context.
- Streams the answer from `POST /rag/ask-stream` using `fetch` + `ReadableStream`.
- **SSE parsing:** text chunks (`data: "..."`) are appended token-by-token to the message; `data: [SOURCES]{...}` sets the sources panel; `data: [DONE]` stops the stream.
- **Sources panel:** collapsible section below the answer. Shows one card per source document with a "% match" similarity badge and the retrieved passage text. Only chunks with cosine similarity ≥ 0.35 are shown.
- **Confidence:** average cosine similarity across the displayed source chunks — reflects retrieval quality, not answer correctness.

### `/quiz` — Quiz Generator (`app/(dashboard)/quiz/page.tsx`)

Form with three controls:
1. **Topic** — text input; reads `?topic=` from URL to pre-fill.
2. **Difficulty** — "Auto" button (default, sends no difficulty → adaptive backend path) + Beginner / Easy / Medium / Hard / Expert.
3. **Questions** — number input (default 5).

On generate:
1. `quiz.generate({ topic, num_questions, difficulty: difficulty ?? undefined })`
2. Navigates to `/quiz/{quiz_id}` on success.

### `/quiz/[quiz_id]` — Quiz Player (`app/(dashboard)/quiz/[quiz_id]/page.tsx`)

States: `loading` → `ready` → `active` → `submitting` → `results` | `error`

- **Ready**: shows quiz metadata (topic, difficulty, question count), "Start Quiz" button calls `quiz.start(quiz_id)` and stores the returned `attempt_id`.
- **Active**: question-by-question card interface. MCQ renders labelled option buttons (A/B/C/D); short-answer renders a textarea. Dot navigator at the bottom lets you jump between questions. Answered dots turn green.
- **Results**: score card (percentage, correct/total, time, new difficulty, mastery), then a per-question breakdown. Each card is green (correct) or red (incorrect), showing `user_answer`, `correct_answer` (if wrong), and `explanation`. MCQ answers display as `"A — option text"` — handles dict (`{"A": "text"}`), numeric-key dict (`{"0": "text"}`), and list (`["text"]`) option formats via `resolveOptionText()`.

### `/quiz/[quiz_id]/review` — Review Page (`app/(dashboard)/quiz/[quiz_id]/review/page.tsx`)

Standalone review of a past completed attempt, accessible from the My Quizzes history list.

- Fetches via `quiz.review(quiz_id)` → `GET /quiz/{id}/review`.
- **Hero section:** score ring (color-coded: gold ≥80%, blue ≥50%, red <50%), topic name, difficulty, progress bar, stat chips (correct count, time taken, question count), Retake Quiz button.
- **Accordion breakdown:** one collapsible row per question. Wrong answers auto-expand on load; correct answers are collapsed. Each row shows the full question text, your answer, correct answer (if wrong), and explanation.

### `/quiz/history` — Quiz History (`app/(dashboard)/quiz/history/page.tsx`)

Tabs: All | Not Started | In Progress | Completed. Summary strip shows counts per status.

Each quiz card shows: topic, difficulty, status badge, question count, creation date. For completed quizzes, the score percentage and time taken are also shown. Action buttons:
- **Completed** → "Review" (links to `/quiz/{id}/review`) + "Retake" (links to `/quiz?topic=...`)
- **In Progress** → "Resume" (links to `/quiz/{id}`)
- **Not Started** → "Start" (links to `/quiz/{id}`)

### `/analytics` — Analytics Dashboard (`app/(dashboard)/analytics/page.tsx`)

Four tabs:

| Tab | Content |
|---|---|
| **Overview** | Bar chart (confidence by topic, colour-coded green/amber/red) + topic breakdown list |
| **Weak Topics** | Cards with confidence bar + weakness % + "Quiz" button → `/quiz?topic=...` |
| **Revision** | Ranked by forgetting-curve priority. Each card has retention %, confidence %, priority badge, and "Revise" button → `/ask?topic=...` |
| **Weekly Plan** | Loads on demand (agent pipeline call). "Go" button routes to `/ask` for "Revise" tasks and `/quiz` for "Practice" tasks |

---

## 8. Components

### `Sidebar` (`components/layout/Sidebar.tsx`)

Fixed-width (`w-56`) left sidebar rendered inside `(dashboard)/layout.tsx`.

**Nav items:**

| Label | Route | Active matching |
|---|---|---|
| Dashboard | `/dashboard` | Exact |
| Upload PDF | `/upload` | Exact |
| Ask AI | `/ask` | Exact |
| New Quiz | `/quiz` | Exact |
| My Quizzes | `/quiz/history` | Exact |
| Analytics | `/analytics` | Prefix (`startsWith`) |

Active items receive `bg-primary text-primary-foreground`. Inactive items are `text-muted-foreground` with hover accent.

**Footer:**
- `ThemeToggle` component (dark / light).
- Sign out button: calls `logout()` then `router.push("/")`.

**Brand:**
- `<Link href="/">` wrapping GraduationCap icon + "SmartLearnAI" text.
- Navigates to the landing page without logging out.

### `ThemeToggle` (`components/theme-toggle.tsx`)

- Uses `useTheme()` from next-themes.
- Renders `<Sun>` in dark mode, `<Moon>` in light mode.
- Renders a blank placeholder until mounted to avoid hydration mismatch.

### shadcn/ui Primitives

All in `components/ui/`. These are thin Radix-primitive wrappers styled with Tailwind. Used across the app:

| Component | Used for |
|---|---|
| `Button` | All CTA buttons, form submits, nav actions |
| `Card` | Content containers on every page |
| `Input` | Text inputs in forms |
| `Label` | Form field labels |
| `Progress` | Confidence / score bars |
| `Badge` | Status indicators (difficulty, priority, quiz status) |
| `Tabs` | Analytics tabs, quiz history tabs |
| `Alert` | Inline error messages |
| `Separator` | Visual dividers in sidebar and plan list |
| `Sonner (Toaster)` | Success / error toast notifications |

---

## 9. State Management

There is no global state library. State is managed with:

| Mechanism | Where used |
|---|---|
| `AuthContext` (React Context) | Auth token, login/logout — app-wide |
| `useState` | Page-level data (quiz questions, analytics results, form inputs) |
| `useEffect` | Data fetching on mount, auth guard |
| URL search params (`?topic=`) | Passing context between pages (e.g. quiz generator pre-fill) |
| `localStorage` | JWT persistence across page reloads |

### Data fetching pattern

All pages follow the same pattern:

```typescript
const [data, setData] = useState<T | null>(null);
const [loading, setLoading] = useState(true);

useEffect(() => {
  apiCall()
    .then(setData)
    .catch(console.error)
    .finally(() => setLoading(false));
}, []);

if (loading) return <Loader2 ... />;
```

---

## 10. Analytics & Visualisation

### Confidence Bar Chart (`analytics/page.tsx`)

Built with Recharts `BarChart`. Data is derived from `confidenceMap` returned by `/analytics/overview`:

```typescript
const chartData = Object.entries(confidenceMap).map(([topic, confidence]) => ({
  topic: topic.length > 14 ? topic.slice(0, 12) + "…" : topic,
  confidence: Math.round(confidence * 100),
}));
```

Bar colour is determined per-cell:
- `>= 70%` → green (`#22c55e`)
- `40–69%` → amber (`#f59e0b`)
- `< 40%` → red (`#ef4444`)

A custom `ConfidenceTooltip` renders on hover with the full topic name and confidence value.

### Revision Priority

Computed server-side using Ebbinghaus forgetting curve:

```
retention = confidence × e^(-0.1 × hours_since_last_attempt)
revision_priority = 1 - retention
```

The frontend receives `revision_priority` directly from `/analytics/revision` and ranks cards highest-first. A "Revise" button links to `/ask?topic=...` so the user can review with AI before practising.

### Smart Recommendation (`SmartRecommendation`)

The `/analytics/recommend-smart` endpoint returns:

```json
{
  "recommended_topic": "deep learning",
  "reason": {
    "weakness": 0.72,
    "forgetting": 0.58,
    "confidence": 0.28,
    "retention": 0.19,
    "combined_score": 0.664
  }
}
```

The dashboard "Study Now" card reads `reason.weakness` and `reason.forgetting` directly. These are shown as percentages alongside the combined score to explain why this topic was chosen.

### Weekly Plan

The Weekly Plan tab renders items from the LangGraph agent pipeline. Each `ScheduleItem` has a `task` field (`"revise"` or `"practice"`) which determines the "Go" button destination:

```typescript
href={
  item.task.toLowerCase() === "revise"
    ? `/ask?topic=${encodeURIComponent(item.topic)}`
    : `/quiz?topic=${encodeURIComponent(item.topic)}`
}
```

Priority badges use colour classes:

| Priority | Classes |
|---|---|
| `high` | `text-red-500 bg-red-500/10` |
| `medium` | `text-yellow-500 bg-yellow-500/10` |
| `low` | `text-green-500 bg-green-500/10` |

---

## 11. Theming

**Provider:** `next-themes` `ThemeProvider` in `app/layout.tsx` with `attribute="class"`.

When dark mode is active, the `dark` class is added to `<html>`. Tailwind's dark variant (`dark:`) and CSS overrides inside `.dark { ... }` in `globals.css` switch all colour tokens.

**Hydration safety:**
- `<html>` has `suppressHydrationWarning` — required for `next-themes` to avoid attribute mismatch during SSR.
- `<body>` has `suppressHydrationWarning` — silences browser extensions (e.g. Grammarly) that inject `data-gr-*` attributes before React hydrates.

**`ThemeToggle` mount guard:**

```typescript
const [mounted, setMounted] = useState(false);
useEffect(() => setMounted(true), []);
if (!mounted) return <div className="h-9 w-9" />;
```

Renders an empty placeholder until the client has mounted to avoid showing the wrong icon on initial render.

---

## 12. Data Flow Diagrams

### Login Flow

```
User submits login form
        │
  auth.login(email, password)
        │
  POST /auth/token  (form-encoded)
        │
  { access_token }
        │
  localStorage.setItem("access_token", token)
  setToken(token)  [AuthContext]
        │
  router.replace("/dashboard")
        │
  (dashboard)/layout.tsx
        └── token is set → renders Sidebar + page
```

### Quiz Session Flow

```
User fills quiz form (/quiz)
        │
  quiz.generate({ topic, num_questions, difficulty? })
        │
  POST /quiz/generate
        │
  { quiz_id, topic, difficulty, total_questions }
        │
  router.push(`/quiz/${quiz_id}`)
        │
  /quiz/[quiz_id]
        │
  quiz.get(quiz_id)  →  GET /quiz/{id}
        │  Questions loaded (correct_answer hidden)
        │
  User clicks "Start Quiz"
        │
  quiz.start(quiz_id)  →  POST /quiz/{id}/start
        │  { attempt_id }
        │
  User answers all questions
        │
  quiz.submit(quiz_id, attempt_id, answers)
        │  POST /quiz/{id}/submit
        │
  SubmitResult { score_ratio, correct_answers, total_questions,
                 new_difficulty, updated_mastery, question_breakdown }
        │
  Results screen: score card + per-question accordion breakdown
        │
  (later) quiz.review(quiz_id)  →  GET /quiz/{id}/review
        │  Navigated from /quiz/history "Review" button
        │
  ReviewResult with same question_breakdown — hero + accordion layout
```

### Analytics Load Flow

```
/dashboard mounts
        │
  Promise.all([
    analytics.overview(),       → GET /analytics/overview
    analytics.recommendSmart(), → GET /analytics/recommend-smart
  ])
        │
  ┌─────────────────┐  ┌─────────────────────────────────────┐
  │ OverviewResponse │  │ SmartRecommendation                 │
  │ topics           │  │ recommended_topic                   │
  │ weak_topics      │  │ reason.weakness                     │
  │ confidence_map   │  │ reason.forgetting                   │
  └─────────────────┘  │ reason.confidence                   │
        │               │ reason.combined_score               │
        │               └─────────────────────────────────────┘
        │
  Render: stats row, Study Now card, weak topics list, confidence bars
```

### Weekly Plan Generation

```
User clicks "Generate Weekly Plan"
        │
  analytics.weeklyPlan()  →  GET /analytics/weekly-plan
        │
  Backend runs LangGraph pipeline:
    AnalyzerAgent → PlannerAgent → Scheduler
        │
  { weekly_plan: ScheduleItem[] }
        │
  Render day-by-day schedule
  "Go" button destination based on item.task:
    "revise"   → /ask?topic=...
    "practice" → /quiz?topic=...
```

---

## 13. Error Handling Strategy

| Layer | Strategy |
|---|---|
| `request()` helper | Parses `{ detail }` from non-2xx response, throws `Error(detail)` |
| Auth pages | `try/catch` in submit handler → inline `<Alert variant="destructive">` |
| Dashboard / analytics pages | `catch(console.error)` — failure leaves state empty, UI shows "no data" placeholders |
| Upload page | `try/catch` → Sonner `toast.error(message)` |
| Quiz player | `try/catch` on generate/submit → Sonner `toast.error()` |
| Auth guard | `useEffect` in layout — redirects rather than crashing on missing token |
| Hydration mismatches | `suppressHydrationWarning` on `<html>` and `<body>` |
| Theme toggle flash | Mount guard (`useState(false)`) — renders placeholder until client hydrates |

**Design principle:** User-facing errors are surfaced via inline alerts (forms) or Sonner toasts (actions). Data-fetch failures in analytics degrade to empty states rather than error pages, so partial data is still displayed where available.
