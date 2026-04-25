"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { quiz, analytics } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Loader2, Brain, ChevronRight } from "lucide-react";
import { toast } from "sonner";

const DIFFICULTY_LABELS: Record<number, string> = {
  1: "Beginner", 2: "Easy", 3: "Medium", 4: "Hard", 5: "Expert",
};

function QuizGenerateForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const prefillTopic = searchParams.get("topic") ?? "";

  const [topic, setTopic] = useState(prefillTopic);
  const [numQuestions, setNumQuestions] = useState(5);
  const [difficulty, setDifficulty] = useState<number | null>(null);
  const [topics, setTopics] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    analytics.allTopics().then((r) => setTopics(r.topics)).catch(() => {});
  }, []);

  async function handleGenerate() {
    setError("");
    setLoading(true);
    try {
      const res = await quiz.generate({
        topic: topic.trim() || undefined,
        num_questions: numQuestions,
        difficulty: difficulty ?? undefined,
      });
      toast.success(`Quiz created! ${res.total_questions} questions on "${res.topic}"`);
      router.push(`/quiz/${res.quiz_id}`);
    } catch (err) {
      setError((err as Error).message ?? "Failed to generate quiz");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Generate Quiz</h1>
        <p className="text-muted-foreground">Create an adaptive quiz from your study material</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Quiz Settings</CardTitle>
          <CardDescription>
            Leave topic blank to let the AI pick the best topic based on your weak areas.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Topic */}
          <div className="space-y-2">
            <Label htmlFor="topic">Topic</Label>
            <Input
              id="topic"
              placeholder="e.g. Machine Learning"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
            {topics.length > 0 && (
              <div className="flex flex-wrap gap-1.5 pt-1">
                {topics.map((t) => (
                  <Badge
                    key={t}
                    variant={topic === t ? "default" : "secondary"}
                    className="cursor-pointer capitalize"
                    onClick={() => setTopic(topic === t ? "" : t)}
                  >
                    {t}
                  </Badge>
                ))}
              </div>
            )}
          </div>

          {/* Number of questions */}
          <div className="space-y-2">
            <Label>Number of Questions: <span className="font-semibold">{numQuestions}</span></Label>
            <div className="flex gap-2">
              {[3, 5, 7, 10].map((n) => (
                <Button
                  key={n}
                  size="sm"
                  variant={numQuestions === n ? "default" : "outline"}
                  onClick={() => setNumQuestions(n)}
                >
                  {n}
                </Button>
              ))}
            </div>
          </div>

          {/* Difficulty */}
          <div className="space-y-2">
            <Label>
              Difficulty
              {difficulty === null && (
                <span className="ml-2 text-xs text-muted-foreground font-normal">
                  — picked automatically based on your performance
                </span>
              )}
            </Label>
            <div className="flex gap-2 flex-wrap">
              <Button
                size="sm"
                variant={difficulty === null ? "default" : "outline"}
                onClick={() => setDifficulty(null)}
              >
                Auto
              </Button>
              {Object.entries(DIFFICULTY_LABELS).map(([d, label]) => (
                <Button
                  key={d}
                  size="sm"
                  variant={difficulty === Number(d) ? "default" : "outline"}
                  onClick={() => setDifficulty(Number(d))}
                >
                  {label}
                </Button>
              ))}
            </div>
          </div>

          <Button className="w-full" onClick={handleGenerate} disabled={loading}>
            {loading ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Generating with AI…</>
            ) : (
              <><Brain className="mr-2 h-4 w-4" /> Generate Quiz</>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Info card */}
      <Card className="bg-muted/40">
        <CardContent className="pt-6">
          <div className="flex gap-4 text-sm text-muted-foreground">
            <ChevronRight className="h-4 w-4 shrink-0 mt-0.5 text-primary" />
            <p>
              Difficulty adapts automatically after each quiz based on your performance.
              A score ≥ 80% increases difficulty; below 40% decreases it.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function QuizPage() {
  return (
    <Suspense>
      <QuizGenerateForm />
    </Suspense>
  );
}
