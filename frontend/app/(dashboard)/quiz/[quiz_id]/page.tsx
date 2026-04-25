"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { quiz as quizApi, QuizDetail, SubmitResult, AnswerItem } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, CheckCircle, XCircle, Trophy, ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

const DIFFICULTY_LABELS: Record<number, string> = {
  1: "Beginner", 2: "Easy", 3: "Medium", 4: "Hard", 5: "Expert",
};

type Phase = "loading" | "ready" | "active" | "submitting" | "results" | "error";

export default function QuizTakePage({ params }: { params: Promise<{ quiz_id: string }> }) {
  const router = useRouter();
  const [quizId, setQuizId] = useState<number | null>(null);
  const [quizData, setQuizData] = useState<QuizDetail | null>(null);
  const [attemptId, setAttemptId] = useState<number | null>(null);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [current, setCurrent] = useState(0);
  const [result, setResult] = useState<SubmitResult | null>(null);
  const [phase, setPhase] = useState<Phase>("loading");
  const [error, setError] = useState("");

  // Resolve async params (Next.js 16)
  useEffect(() => {
    params.then(({ quiz_id }) => setQuizId(Number(quiz_id)));
  }, [params]);

  // Load quiz
  useEffect(() => {
    if (!quizId) return;
    quizApi.get(quizId)
      .then((q) => { setQuizData(q); setPhase("ready"); })
      .catch((e) => { setError(e.message); setPhase("error"); });
  }, [quizId]);

  async function startQuiz() {
    if (!quizId) return;
    try {
      const res = await quizApi.start(quizId);
      setAttemptId(res.attempt_id ?? null);
      setPhase("active");
    } catch (e) {
      toast.error((e as Error).message);
    }
  }

  function selectAnswer(qId: number, answer: string) {
    setAnswers((prev) => ({ ...prev, [qId]: answer }));
  }

  async function submitQuiz() {
    if (!quizId || !quizData) return;
    const unanswered = quizData.questions.filter((q) => !answers[q.question_id]);
    if (unanswered.length > 0) {
      toast.warning(`Please answer all questions (${unanswered.length} remaining)`);
      return;
    }

    setPhase("submitting");
    const payload: AnswerItem[] = quizData.questions.map((q) => ({
      question_id: q.question_id,
      answer: answers[q.question_id] ?? "",
    }));

    try {
      const res = await quizApi.submit(quizId, attemptId ?? 0, payload);
      setResult(res);
      setPhase("results");
    } catch (e) {
      toast.error((e as Error).message);
      setPhase("active");
    }
  }

  // ── Loading / Submitting ───────────────────────────────────────────────────
  if (phase === "loading" || phase === "submitting") {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (phase === "error") {
    return (
      <div className="mx-auto max-w-lg pt-20">
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button variant="outline" className="mt-4" onClick={() => router.push("/quiz")}>
          Back to Quiz
        </Button>
      </div>
    );
  }

  // ── Results ────────────────────────────────────────────────────────────────
  if (phase === "results" && result) {
    const pct = Math.round(result.score_ratio * 100);
    return (
      <div className="mx-auto max-w-lg space-y-6">
        <Card className="text-center">
          <CardHeader>
            <div className="flex justify-center mb-2">
              <Trophy className={cn("h-12 w-12", pct >= 80 ? "text-yellow-500" : pct >= 50 ? "text-blue-500" : "text-muted-foreground")} />
            </div>
            <CardTitle className="text-3xl">{pct}%</CardTitle>
            <CardDescription>
              {result.correct_answers} / {result.total_questions} correct
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Progress value={pct} className="h-3" />

            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="rounded-lg bg-muted p-3">
                <p className="text-muted-foreground">Time taken</p>
                <p className="font-semibold">{result.time_taken_seconds}s</p>
              </div>
              <div className="rounded-lg bg-muted p-3">
                <p className="text-muted-foreground">New difficulty</p>
                <p className="font-semibold">{DIFFICULTY_LABELS[result.new_difficulty]}</p>
              </div>
              <div className="rounded-lg bg-muted p-3">
                <p className="text-muted-foreground">Mastery</p>
                <p className="font-semibold">{Math.round(result.updated_mastery * 100)}%</p>
              </div>
              <div className="rounded-lg bg-muted p-3">
                <p className="text-muted-foreground">Score ratio</p>
                <p className="font-semibold">{result.score_ratio.toFixed(2)}</p>
              </div>
            </div>

            <Separator />

            <div className="flex flex-col gap-2">
              <Button onClick={() => router.push("/quiz")}>Take Another Quiz</Button>
              <Button variant="outline" onClick={() => router.push("/analytics")}>View Analytics</Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ── Ready / Active ─────────────────────────────────────────────────────────
  if (!quizData) return null;

  const q = quizData.questions[current];
  const totalQ = quizData.questions.length;
  const answered = Object.keys(answers).length;

  const OPTION_LABELS = ["A", "B", "C", "D"];

  // Normalise options: LLM may return an array (keys 0,1,2,3) or a dict (keys A,B,C,D).
  // Always produce [{label: "A", text: "..."}, ...] so submission always uses A/B/C/D.
  const options = q?.options
    ? Object.entries(q.options).map(([key, text], idx) => ({
        label: /^\d+$/.test(key) ? (OPTION_LABELS[parseInt(key)] ?? key) : key,
        text: text as string,
      }))
    : null;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-bold capitalize">{quizData.topic}</h1>
          <p className="text-muted-foreground">
            {totalQ} questions · {DIFFICULTY_LABELS[quizData.difficulty]}
          </p>
        </div>
        <Badge variant="outline">{answered}/{totalQ} answered</Badge>
      </div>

      {/* Progress */}
      <Progress value={((current + 1) / totalQ) * 100} className="h-1.5" />

      {/* Start screen */}
      {phase === "ready" && (
        <Card>
          <CardHeader>
            <CardTitle>Ready to start?</CardTitle>
            <CardDescription>
              Your timer will begin when you click Start. Answer all questions, then submit.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button className="w-full" onClick={startQuiz}>Start Quiz</Button>
          </CardContent>
        </Card>
      )}

      {/* Active quiz */}
      {phase === "active" && q && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <Badge variant="secondary">Q{current + 1} of {totalQ}</Badge>
              {answers[q.question_id] && <CheckCircle className="h-4 w-4 text-green-500" />}
            </div>
            <CardTitle className="text-base leading-relaxed mt-2">
              {q.question_text}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {options ? (
              // MCQ
              options.map(({ label, text }) => (
                <button
                  key={label}
                  onClick={() => selectAnswer(q.question_id, label)}
                  className={cn(
                    "w-full rounded-lg border px-4 py-3 text-left text-sm transition-colors",
                    answers[q.question_id] === label
                      ? "border-primary bg-primary/10 text-primary font-medium"
                      : "border-border hover:bg-accent"
                  )}
                >
                  <span className="font-semibold mr-2">{label}.</span> {text}
                </button>
              ))
            ) : (
              // Short answer
              <textarea
                className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-ring"
                rows={3}
                placeholder="Type your answer…"
                value={answers[q.question_id] ?? ""}
                onChange={(e) => selectAnswer(q.question_id, e.target.value)}
              />
            )}
          </CardContent>
        </Card>
      )}

      {/* Navigation */}
      {phase === "active" && (
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={() => setCurrent((c) => Math.max(0, c - 1))}
            disabled={current === 0}
          >
            <ChevronLeft className="h-4 w-4 mr-1" /> Prev
          </Button>

          {current < totalQ - 1 ? (
            <Button onClick={() => setCurrent((c) => Math.min(totalQ - 1, c + 1))}>
              Next <ChevronRight className="h-4 w-4 ml-1" />
            </Button>
          ) : (
            <Button onClick={submitQuiz}>
              Submit Quiz
            </Button>
          )}
        </div>
      )}

      {/* Question dots */}
      {phase === "active" && (
        <div className="flex flex-wrap gap-1.5">
          {quizData.questions.map((question, i) => (
            <button
              key={question.question_id}
              onClick={() => setCurrent(i)}
              className={cn(
                "h-7 w-7 rounded text-xs font-medium transition-colors",
                i === current
                  ? "bg-primary text-primary-foreground"
                  : answers[question.question_id]
                  ? "bg-green-500/20 text-green-600"
                  : "bg-muted text-muted-foreground hover:bg-accent"
              )}
            >
              {i + 1}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
