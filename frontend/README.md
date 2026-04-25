# AI Study Assistant — Frontend

Next.js frontend for the AI-powered study and revision agent. Provides a full-featured UI for document upload, RAG-based Q&A, adaptive quizzing, and personalised analytics.

---

## Table of Contents

- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Environment Setup](#environment-setup)
- [Running the Dev Server](#running-the-dev-server)
- [Pages Overview](#pages-overview)
- [Architecture Notes](#architecture-notes)

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Next.js 16 (App Router) |
| Language | TypeScript 5 |
| UI Library | React 19 |
| Styling | Tailwind CSS v4 (OKLch colour system) |
| Components | shadcn/ui |
| Icons | Lucide React |
| Charts | Recharts |
| Toasts | Sonner |
| Theming | next-themes (dark / light mode) |
| Auth | JWT via localStorage + React Context |

---

## Prerequisites

- Node.js 20+
- The backend server running on `http://localhost:8000` (or configured via env var)

---

## Project Structure

```
frontend/
├── app/
│   ├── (auth)/                  # Login and signup pages (no sidebar)
│   │   ├── login/page.tsx
│   │   └── signup/page.tsx
│   ├── (dashboard)/             # Protected pages (sidebar layout)
│   │   ├── layout.tsx           # Auth guard + sidebar wrapper
│   │   ├── dashboard/page.tsx   # Main dashboard
│   │   ├── upload/page.tsx      # PDF upload
│   │   ├── ask/page.tsx         # Ask AI (RAG chat)
│   │   ├── quiz/
│   │   │   ├── page.tsx         # Quiz generator
│   │   │   ├── history/page.tsx # Quiz history
│   │   │   └── [quiz_id]/page.tsx # Quiz player
│   │   └── analytics/page.tsx   # Analytics dashboard
│   ├── layout.tsx               # Root layout (ThemeProvider, Toaster)
│   ├── page.tsx                 # Landing / home page
│   └── globals.css              # Tailwind v4 theme variables
├── components/
│   ├── layout/Sidebar.tsx       # Navigation sidebar
│   ├── theme-toggle.tsx         # Dark / light toggle
│   └── ui/                      # shadcn/ui primitives
├── lib/
│   ├── api.ts                   # Typed API client + all fetch helpers
│   ├── auth.tsx                 # AuthContext, AuthProvider, useAuth()
│   └── utils.ts                 # cn() class merging utility
├── package.json
├── next.config.ts
└── FRONTEND_DOCS.md             # Full technical documentation
```

---

## Environment Setup

### 1. Navigate to the frontend directory

```bash
cd "AI Study and Revision Agent/frontend"
```

### 2. Install dependencies

```bash
npm install
```

### 3. Configure the API base URL (optional)

By default the client points to `http://localhost:8000`. To override, create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Running the Dev Server

```bash
npm run dev
```

The app will be available at `http://localhost:3000`.

| Command | Purpose |
|---|---|
| `npm run dev` | Start development server with hot reload |
| `npm run build` | Build for production |
| `npm run start` | Start production server (after build) |
| `npm run lint` | Run ESLint |

---

## Pages Overview

| Route | Description |
|---|---|
| `/` | Landing page — features, how it works, auth CTAs |
| `/login` | Sign-in form (email + password) |
| `/signup` | Registration form (email + password + confirm) |
| `/dashboard` | Stats overview, weak topics, smart study recommendation |
| `/upload` | PDF upload with topic label — ingested into FAISS vector store |
| `/ask` | RAG chat — ask questions over your uploaded documents |
| `/quiz` | Generate a new adaptive quiz (topic, difficulty, question count) |
| `/quiz/[quiz_id]` | Quiz player — MCQ and short-answer questions with scoring |
| `/quiz/history` | All past quizzes filtered by status (not started / in progress / completed) |
| `/analytics` | Confidence charts, weak topics, revision priorities, AI weekly plan |

All routes under `/dashboard`, `/upload`, `/ask`, `/quiz`, and `/analytics` are protected — unauthenticated users are redirected to `/`.

---

## Architecture Notes

- **Route groups** — `(auth)` and `(dashboard)` are Next.js route groups. They share no layout but organise files cleanly. The dashboard group's `layout.tsx` enforces the auth guard and renders the sidebar.
- **Auth state** — JWT is stored in `localStorage` under `access_token`. `AuthProvider` reads it on mount and exposes `token`, `login()`, `signup()`, and `logout()` via context. All API calls inject the token as a `Bearer` header automatically.
- **API client** — `lib/api.ts` is a single typed module. Every endpoint is a named function (`quiz.generate()`, `analytics.overview()`, etc.) wrapping a shared `request<T>()` helper that injects auth and throws typed errors.
- **Adaptive difficulty** — The quiz generator offers an "Auto" mode (sends no difficulty to the API, letting the backend choose based on the user's `UserTopicProgress`) and manual overrides (Beginner → Expert). Auto is selected by default.
- **Analytics routing** — In the Revision tab, "Revise" buttons navigate to `/ask?topic=...` (Ask AI). In the Weekly Plan, "Go" routes to `/ask` for "revise" tasks and `/quiz` for "practice" tasks.
- **Forgetting curve UI** — The Analytics page surfaces retention and revision priority from the backend's Ebbinghaus model. Topics with the steepest forgetting curve appear first in the Revision tab.
- **Dark mode** — Implemented with `next-themes`. Theme is persisted across sessions. `<html>` and `<body>` carry `suppressHydrationWarning` to silence browser-extension-injected attribute mismatches.

For a deep dive into every component and data flow, see [FRONTEND_DOCS.md](FRONTEND_DOCS.md).
