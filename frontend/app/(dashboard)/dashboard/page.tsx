"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { analytics, OverviewResponse, SmartRecommendation } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { badgeVariants } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { buttonVariants } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import { BookOpen, Brain, TrendingUp, Zap, ArrowRight, Loader2 } from "lucide-react";

export default function DashboardPage() {
  const [overview, setOverview] = useState<OverviewResponse | null>(null);
  const [recommendation, setRecommendation] = useState<SmartRecommendation | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([analytics.overview(), analytics.recommendSmart()])
      .then(([ov, rec]) => { setOverview(ov); setRecommendation(rec); })
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

  const topics = overview?.topics ?? [];
  const weakTopics = overview?.weak_topics ?? [];
  const confidenceMap = overview?.confidence_map ?? {};

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">Your study overview at a glance</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Topics Uploaded</CardTitle>
            <BookOpen className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{topics.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Weak Topics</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">{weakTopics.length}</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg Confidence</CardTitle>
            <Brain className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold">
              {topics.length > 0
                ? `${Math.round((Object.values(confidenceMap).reduce((a, b) => a + b, 0) / topics.length) * 100)}%`
                : "—"}
            </p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Smart Recommendation */}
        <Card className="border-primary/30 bg-primary/5">
          <CardHeader>
            <div className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-primary" />
              <CardTitle>Study Now</CardTitle>
            </div>
            <CardDescription>AI-recommended topic based on your performance</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {recommendation?.recommended_topic ? (
              <>
                <p className="text-xl font-semibold capitalize">{recommendation.recommended_topic}</p>
                {typeof recommendation.reason === "object" && (
                  <div className="space-y-2 text-sm text-muted-foreground">
                    <div className="flex justify-between">
                      <span>Weakness</span>
                      <span>{Math.round((recommendation.reason.weakness ?? 0) * 100)}%</span>
                    </div>
                    <Progress value={(recommendation.reason.weakness ?? 0) * 100} className="h-1.5" />
                    <div className="flex justify-between">
                      <span>Forgetting</span>
                      <span>{Math.round((recommendation.reason.forgetting ?? 0) * 100)}%</span>
                    </div>
                    <Progress value={(recommendation.reason.forgetting ?? 0) * 100} className="h-1.5" />
                  </div>
                )}
                <Link
                  href={`/quiz?topic=${encodeURIComponent(recommendation.recommended_topic)}`}
                  className={cn(buttonVariants(), "w-full")}
                >
                  Start Quiz <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </>
            ) : (
              <div className="space-y-3">
                <p className="text-muted-foreground">No study material yet.</p>
                <Link href="/upload" className={cn(buttonVariants({ variant: "outline" }), "w-full")}>
                  Upload your first PDF
                </Link>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Confidence by topic */}
        <Card>
          <CardHeader>
            <CardTitle>Confidence by Topic</CardTitle>
            <CardDescription>How well you know each subject</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {topics.length === 0 ? (
              <p className="text-sm text-muted-foreground">Upload a PDF to get started.</p>
            ) : (
              topics.slice(0, 6).map((t) => {
                const conf = confidenceMap[t] ?? 0;
                return (
                  <div key={t} className="space-y-1">
                    <div className="flex items-center justify-between text-sm">
                      <span className="capitalize">{t}</span>
                      <span className="text-muted-foreground">{Math.round(conf * 100)}%</span>
                    </div>
                    <Progress value={conf * 100} className="h-2" />
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>
      </div>

      {/* Weak topics */}
      {weakTopics.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Topics to Focus On</CardTitle>
            <CardDescription>These need the most attention</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-wrap gap-2">
              {weakTopics.map((wt) => (
                <Link
                  key={wt.topic}
                  href={`/quiz?topic=${encodeURIComponent(wt.topic)}`}
                  className={cn(badgeVariants({ variant: "destructive" }), "cursor-pointer capitalize")}
                >
                  {wt.topic}
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Separator />

      {/* Quick Actions */}
      <div>
        <h2 className="mb-4 text-sm font-semibold text-muted-foreground uppercase tracking-wider">Quick Actions</h2>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          {[
            { label: "Upload PDF",    href: "/upload",    icon: BookOpen },
            { label: "Ask AI",        href: "/ask",       icon: Brain },
            { label: "Take a Quiz",   href: "/quiz",      icon: Zap },
            { label: "Analytics",     href: "/analytics", icon: TrendingUp },
          ].map(({ label, href, icon: Icon }) => (
            <Link key={href} href={href} className={cn(buttonVariants({ variant: "outline" }), "h-auto flex-col gap-2 py-4")}>
              <Icon className="h-5 w-5" />
              <span className="text-xs">{label}</span>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
