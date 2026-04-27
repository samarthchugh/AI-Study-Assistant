"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { quiz as quizApi, ReviewResult, QuestionResult } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { CheckCircle, XCircle, Trophy, Loader2, ArrowLeft, ChevronDown, Clock, BookOpen } from "lucide-react";
import { cn } from "@/lib/utils";

const DIFFICULTY_LABELS: Record<number, string> = {
  1: "Beginner", 2: "Easy", 3: "Medium", 4: "Hard", 5: "Expert",
};

const OPTION_LABELS = ["A", "B", "C", "D"];

function resolveOptionText(qr: QuestionResult, letter: string): string {
  if (!qr.options) return letter;
  const idx = OPTION_LABELS.indexOf(letter);
  if (Array.isArray(qr.options)) return qr.options[idx] ?? letter;
  const dict = qr.options as Record<string, string>;
  return dict[letter] ?? Object.values(dict)[idx] ?? letter;
}

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function ScoreRing({ pct }: { pct: number }) {
  const borderColor =
    pct >= 80 ? "border-yellow-400" :
    pct >= 50 ? "border-blue-400" :
    "border-red-400";

  const textColor =
    pct >= 80 ? "text-yellow-500" :
    pct >= 50 ? "text-blue-500" :
    "text-red-500";

  return (
    <div className={cn(
      "flex items-center justify-center w-36 h-36 rounded-full border-8 bg-background shadow-sm",
      borderColor
    )}>
      <span className={cn("text-4xl font-bold", textColor)}>{pct}%</span>
    </div>
  );
}

function QuestionAccordion({ qr, index }: { qr: QuestionResult; index: number }) {
  const [open, setOpen] = useState(!qr.is_correct);

  return (
    <div
      className={cn(
        "rounded-lg border overflow-hidden transition-colors",
        qr.is_correct ? "border-green-500/30" : "border-red-500/30"
      )}
    >
      {/* Header row — always visible */}
      <button
        onClick={() => setOpen((o) => !o)}
        className={cn(
          "w-full flex items-center gap-3 px-4 py-3 text-left transition-colors",
          qr.is_correct ? "bg-green-500/5 hover:bg-green-500/10" : "bg-red-500/5 hover:bg-red-500/10"
        )}
      >
        {qr.is_correct
          ? <CheckCircle className="h-4 w-4 text-green-500 shrink-0" />
          : <XCircle className="h-4 w-4 text-red-500 shrink-0" />
        }
        <span className="text-xs text-muted-foreground shrink-0 font-medium w-6">Q{index + 1}</span>
        <p className="text-sm font-medium flex-1 leading-snug line-clamp-1">{qr.question_text}</p>
        <ChevronDown className={cn(
          "h-4 w-4 text-muted-foreground shrink-0 transition-transform duration-200",
          open && "rotate-180"
        )} />
      </button>

      {/* Expanded content */}
      {open && (
        <div className="px-4 pb-4 pt-3 space-y-3 border-t border-border/50">
          <p className="text-sm font-medium leading-snug">{qr.question_text}</p>

          <div className="space-y-2 text-sm">
            <div className="flex items-start gap-2">
              <span className="text-muted-foreground w-28 shrink-0 pt-0.5">Your answer</span>
              <span className={cn("font-medium", qr.is_correct ? "text-green-600" : "text-red-600")}>
                {qr.question_type === "mcq"
                  ? `${qr.user_answer} — ${resolveOptionText(qr, qr.user_answer)}`
                  : qr.user_answer || <span className="italic text-muted-foreground">No answer</span>}
              </span>
            </div>

            {!qr.is_correct && (
              <div className="flex items-start gap-2">
                <span className="text-muted-foreground w-28 shrink-0 pt-0.5">Correct answer</span>
                <span className="font-medium text-green-600">
                  {qr.question_type === "mcq"
                    ? `${qr.correct_answer} — ${resolveOptionText(qr, qr.correct_answer)}`
                    : qr.correct_answer}
                </span>
              </div>
            )}
          </div>

          {qr.explanation && (
            <div className="border-l-2 border-muted pl-3">
              <p className="text-xs text-muted-foreground leading-relaxed">{qr.explanation}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ReviewPage({ params }: { params: Promise<{ quiz_id: string }> }) {
  const router = useRouter();
  const [data, setData] = useState<ReviewResult | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    params.then(({ quiz_id }) =>
      quizApi.review(Number(quiz_id))
        .then(setData)
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false))
    );
  }, [params]);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="mx-auto max-w-lg pt-20 space-y-4">
        <Alert variant="destructive">
          <AlertDescription>{error || "Could not load review."}</AlertDescription>
        </Alert>
        <Button variant="outline" onClick={() => router.push("/quiz/history")}>
          <ArrowLeft className="h-4 w-4 mr-2" /> Back to My Quizzes
        </Button>
      </div>
    );
  }

  const pct = Math.round(data.score_ratio * 100);
  const correct = data.correct_answers;
  const wrong = data.total_questions - correct;

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      {/* Back */}
      <Button variant="ghost" size="sm" onClick={() => router.push("/quiz/history")} className="-ml-2">
        <ArrowLeft className="h-4 w-4 mr-1" /> My Quizzes
      </Button>

      {/* ── Hero ───────────────────────────────────────────────────── */}
      <div className="flex flex-col items-center gap-4 text-center">
        <ScoreRing pct={pct} />

        <div>
          <h1 className="text-2xl font-bold capitalize">{data.topic}</h1>
          <p className="text-sm text-muted-foreground mt-0.5">{DIFFICULTY_LABELS[data.difficulty]}</p>
        </div>

        <Progress value={pct} className="h-2 w-64" />

        {/* Stat chips */}
        <div className="flex flex-wrap justify-center gap-3 text-sm">
          <div className="flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5">
            <Trophy className="h-3.5 w-3.5 text-muted-foreground" />
            <span>{correct} / {data.total_questions} correct</span>
          </div>
          {data.time_taken_seconds !== null && (
            <div className="flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5">
              <Clock className="h-3.5 w-3.5 text-muted-foreground" />
              <span>{formatTime(data.time_taken_seconds)}</span>
            </div>
          )}
          <div className="flex items-center gap-1.5 rounded-full border border-border px-3 py-1.5">
            <BookOpen className="h-3.5 w-3.5 text-muted-foreground" />
            <span>{data.total_questions} questions</span>
          </div>
        </div>

        <Button onClick={() => router.push(`/quiz?topic=${encodeURIComponent(data.topic)}`)}>
          Retake Quiz
        </Button>
      </div>

      {/* ── Question Breakdown ─────────────────────────────────────── */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold">Question Breakdown</h2>
          <div className="flex gap-2">
            <Badge variant="secondary" className="bg-green-500/10 text-green-600">
              {correct} correct
            </Badge>
            <Badge variant="secondary" className="bg-red-500/10 text-red-600">
              {wrong} wrong
            </Badge>
          </div>
        </div>

        <div className="space-y-2">
          {data.question_breakdown.map((qr, i) => (
            <QuestionAccordion key={qr.question_id} qr={qr} index={i} />
          ))}
        </div>
      </div>
    </div>
  );
}
