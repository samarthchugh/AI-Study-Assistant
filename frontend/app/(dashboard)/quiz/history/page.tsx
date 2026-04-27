"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { quiz as quizApi, QuizListItem } from "@/lib/api";
import { buttonVariants } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2, Plus, Trophy, Clock, BookOpen, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

const DIFFICULTY: Record<number, string> = {
  1: "Beginner", 2: "Easy", 3: "Medium", 4: "Hard", 5: "Expert",
};

const STATUS_BADGE: Record<QuizListItem["status"], string> = {
  not_started: "bg-secondary text-secondary-foreground",
  in_progress:  "bg-yellow-500/10 text-yellow-600",
  completed:    "bg-green-500/10 text-green-600",
};

const STATUS_LABEL: Record<QuizListItem["status"], string> = {
  not_started: "Not Started",
  in_progress:  "In Progress",
  completed:    "Completed",
};

function scoreColor(ratio: number) {
  if (ratio >= 0.7) return "text-green-600";
  if (ratio >= 0.4) return "text-yellow-600";
  return "text-destructive";
}

function formatTime(seconds: number) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

function QuizCard({ item }: { item: QuizListItem }) {
  return (
    <Card className="transition-colors hover:bg-muted/40">
      <CardContent className="flex items-center gap-4 p-4">
        {/* Topic + meta */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-semibold capitalize truncate">{item.topic}</p>
            <Badge variant="secondary" className={cn("text-xs", STATUS_BADGE[item.status])}>
              {STATUS_LABEL[item.status]}
            </Badge>
          </div>
          <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <BookOpen className="h-3 w-3" />
              {item.total_questions} questions
            </span>
            <span>{DIFFICULTY[item.difficulty]}</span>
            <span>Created {formatDate(item.created_at)}</span>
          </div>
        </div>

        {/* Score / time (completed) */}
        {item.status === "completed" && item.score_ratio !== null && (
          <div className="flex flex-col items-end text-right shrink-0">
            <span className={cn("text-lg font-bold", scoreColor(item.score_ratio))}>
              {Math.round(item.score_ratio * 100)}%
            </span>
            {item.time_taken_seconds !== null && (
              <span className="flex items-center gap-1 text-xs text-muted-foreground">
                <Clock className="h-3 w-3" />
                {formatTime(item.time_taken_seconds)}
              </span>
            )}
          </div>
        )}

        {/* Action button */}
        <div className="shrink-0 flex gap-2">
          {item.status === "completed" ? (
            <>
              <Link
                href={`/quiz/${item.quiz_id}/review`}
                className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
              >
                Review
              </Link>
              <Link
                href={`/quiz?topic=${encodeURIComponent(item.topic)}`}
                className={cn(buttonVariants({ size: "sm" }))}
              >
                Retake
              </Link>
            </>
          ) : (
            <Link
              href={`/quiz/${item.quiz_id}`}
              className={cn(buttonVariants({ size: "sm" }), "gap-1")}
            >
              {item.status === "in_progress" ? "Resume" : "Start"}
              <ChevronRight className="h-3.5 w-3.5" />
            </Link>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

function EmptyState({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      <Trophy className="h-10 w-10 text-muted-foreground/30" />
      <p className="text-sm text-muted-foreground">{label}</p>
      <Link href="/quiz" className={cn(buttonVariants({ variant: "outline", size: "sm" }))}>
        Generate a quiz
      </Link>
    </div>
  );
}

function QuizList({ items, emptyLabel }: { items: QuizListItem[]; emptyLabel: string }) {
  if (items.length === 0) return <EmptyState label={emptyLabel} />;
  return (
    <div className="space-y-2 mt-4">
      {items.map((item) => <QuizCard key={item.quiz_id} item={item} />)}
    </div>
  );
}

export default function QuizHistoryPage() {
  const [quizzes, setQuizzes] = useState<QuizListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    quizApi.list()
      .then((r) => setQuizzes(r.quizzes))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  const notStarted  = quizzes.filter((q) => q.status === "not_started");
  const inProgress  = quizzes.filter((q) => q.status === "in_progress");
  const completed   = quizzes.filter((q) => q.status === "completed");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">My Quizzes</h1>
          <p className="text-muted-foreground">All quizzes you have generated</p>
        </div>
        <Link href="/quiz" className={cn(buttonVariants(), "gap-2")}>
          <Plus className="h-4 w-4" /> New Quiz
        </Link>
      </div>

      {/* Summary strip */}
      <div className="grid grid-cols-3 gap-3 text-center">
        {[
          { label: "Not Started", count: notStarted.length,  color: "text-muted-foreground" },
          { label: "In Progress", count: inProgress.length,  color: "text-yellow-600" },
          { label: "Completed",   count: completed.length,   color: "text-green-600" },
        ].map(({ label, count, color }) => (
          <div key={label} className="rounded-lg border border-border bg-card p-3">
            <p className={cn("text-2xl font-bold", color)}>{count}</p>
            <p className="text-xs text-muted-foreground">{label}</p>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <Tabs defaultValue={inProgress.length > 0 ? "in_progress" : "all"}>
        <TabsList>
          <TabsTrigger value="all">All ({quizzes.length})</TabsTrigger>
          <TabsTrigger value="not_started">Not Started ({notStarted.length})</TabsTrigger>
          <TabsTrigger value="in_progress">In Progress ({inProgress.length})</TabsTrigger>
          <TabsTrigger value="completed">Completed ({completed.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="all">
          <QuizList
            items={quizzes}
            emptyLabel="No quizzes yet. Generate your first one!"
          />
        </TabsContent>
        <TabsContent value="not_started">
          <QuizList
            items={notStarted}
            emptyLabel="No pending quizzes — you've started them all!"
          />
        </TabsContent>
        <TabsContent value="in_progress">
          <QuizList
            items={inProgress}
            emptyLabel="No quizzes in progress."
          />
        </TabsContent>
        <TabsContent value="completed">
          <QuizList
            items={completed}
            emptyLabel="No completed quizzes yet. Take one!"
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}
