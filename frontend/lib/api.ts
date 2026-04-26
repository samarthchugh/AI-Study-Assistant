const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("access_token");
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
  };

  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (!res.ok) {
    if (res.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      window.location.replace("/");
      throw new Error("Session expired. Please log in again.");
    }
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail ?? "Request failed");
  }

  return res.json() as Promise<T>;
}

// ── Auth ──────────────────────────────────────────────────────────────────────

export interface SignupPayload {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export const auth = {
  signup: (data: SignupPayload) =>
    request<{ id: number; email: string; provider: string; created_at: string }>(
      "/auth/signup",
      { method: "POST", body: JSON.stringify(data) }
    ),

  login: (email: string, password: string) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);
    return request<TokenResponse>("/auth/token", {
      method: "POST",
      body: form.toString(),
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
  },
};

// ── Documents ─────────────────────────────────────────────────────────────────

export const documents = {
  upload: (file: File, topic: string) => {
    const form = new FormData();
    form.append("file", file);
    form.append("topic", topic);
    return request<{ status: string; message: string }>(
      `/documents/upload?topic=${encodeURIComponent(topic)}`,
      { method: "POST", body: form }
    );
  },
};

// ── RAG ───────────────────────────────────────────────────────────────────────

export interface AskResponse {
  answer: string;
  sources: string[];
  confidence: number;
}

export const rag = {
  ask: (question: string) =>
    request<AskResponse>("/rag/ask", {
      method: "POST",
      body: JSON.stringify({ question }),
    }),
};

// ── Quiz ──────────────────────────────────────────────────────────────────────

export interface QuizSummary {
  quiz_id: number;
  topic: string;
  difficulty: number;
  total_questions: number;
}

export interface Question {
  question_id: number;
  question_text: string;
  options: Record<string, string> | null;
}

export interface QuizDetail extends QuizSummary {
  questions: Question[];
}

export interface AnswerItem {
  question_id: number;
  answer: string;
}

export interface SubmitResult {
  quiz_id: number;
  score_ratio: number;
  correct_answers: number;
  total_questions: number;
  new_difficulty: number;
  updated_mastery: number;
  time_taken_seconds: number;
}

export interface QuizListItem {
  quiz_id: number;
  topic: string;
  difficulty: number;
  total_questions: number;
  status: "not_started" | "in_progress" | "completed";
  created_at: string;
  completed_at: string | null;
  score_ratio: number | null;
  time_taken_seconds: number | null;
  attempt_id: number | null;
}

export const quiz = {
  generate: (params: { topic?: string; num_questions?: number; difficulty?: number }) => {
    const qs = new URLSearchParams();
    if (params.topic) qs.set("topic", params.topic);
    if (params.num_questions) qs.set("num_questions", String(params.num_questions));
    if (params.difficulty) qs.set("difficulty", String(params.difficulty));
    return request<QuizSummary>(`/quiz/generate?${qs}`, { method: "POST" });
  },

  get: (quiz_id: number) => request<QuizDetail>(`/quiz/${quiz_id}`),

  start: (quiz_id: number) =>
    request<{ message: string; attempt_id?: number }>(`/quiz/${quiz_id}/start`, { method: "POST" }),

  submit: (quiz_id: number, attempt_id: number, answers: AnswerItem[]) =>
    request<SubmitResult>(`/quiz/${quiz_id}/submit?attempt_id=${attempt_id}`, {
      method: "POST",
      body: JSON.stringify({ answers }),
    }),

  list: () => request<{ quizzes: QuizListItem[] }>("/quiz/my-quizzes"),
};

// ── Analytics ─────────────────────────────────────────────────────────────────

export interface WeakTopic {
  topic: string;
  weakness: number;
  confidence: number;
}

export interface RevisionTopic {
  topic: string;
  confidence: number;
  retention: number;
  revision_priority: number;
}

export interface OverviewResponse {
  user_id: number;
  topics: string[];
  weak_topics: WeakTopic[];
  confidence_map: Record<string, number>;
}

export interface SmartRecommendation {
  recommended_topic: string | null;
  reason: {
    topic: string;
    confidence: number;
    weakness: number;
    retention: number;
    forgetting: number;
    combined_score: number;
  } | string;
}

export interface ScheduleItem {
  day: string;
  date: string;
  topic: string;
  task: "revise" | "practice";
  priority: "high" | "medium" | "low";
  instruction?: string;
}

export const analytics = {
  overview: () => request<OverviewResponse>("/analytics/overview"),

  weakTopics: () =>
    request<{ user_id: number; weak_topics: WeakTopic[] }>("/analytics/weak-topics"),

  allTopics: () =>
    request<{ user_id: number; topics: string[] }>("/analytics/all-topics"),

  confidence: (topic: string) =>
    request<{ user_id: number; topic: string; confidence: number }>(
      `/analytics/confidence?topic=${encodeURIComponent(topic)}`
    ),

  revision: (top_k = 3) =>
    request<{ user_id: number; revision_topics: RevisionTopic[] }>(
      `/analytics/revision?top_k=${top_k}`
    ),

  recommendSmart: () => request<SmartRecommendation>("/analytics/recommend-smart"),

  weeklyPlan: () =>
    request<{ user_id: number; weekly_plan: ScheduleItem[] }>("/analytics/weekly-plan"),
};
