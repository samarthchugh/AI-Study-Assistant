"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  analytics,
  WeakTopic,
  RevisionTopic,
  ScheduleItem,
} from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Button, buttonVariants } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { cn } from "@/lib/utils";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import {
  Loader2,
  TrendingDown,
  RefreshCw,
  Calendar,
  Brain,
  AlertTriangle,
} from "lucide-react";

const PRIORITY_COLOR: Record<string, string> = {
  high: "text-red-500 bg-red-500/10",
  medium: "text-yellow-500 bg-yellow-500/10",
  low: "text-green-500 bg-green-500/10",
};

function ConfidenceTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-border bg-popover px-3 py-2 shadow-lg text-sm text-popover-foreground">
      <p className="font-medium capitalize mb-0.5">{label}</p>
      <p className="text-muted-foreground">
        Confidence:{" "}
        <span className="font-semibold text-popover-foreground">{payload[0].value}%</span>
      </p>
    </div>
  );
}

export default function AnalyticsPage() {
  const [weakTopics, setWeakTopics] = useState<WeakTopic[]>([]);
  const [revisionTopics, setRevisionTopics] = useState<RevisionTopic[]>([]);
  const [weeklyPlan, setWeeklyPlan] = useState<ScheduleItem[]>([]);
  const [confidenceMap, setConfidenceMap] = useState<Record<string, number>>({});
  const [loadingPlan, setLoadingPlan] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      analytics.overview(),
      analytics.revision(5),
    ])
      .then(([ov, rev]) => {
        setWeakTopics(ov.weak_topics);
        setRevisionTopics(rev.revision_topics);
        setConfidenceMap(ov.confidence_map);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  async function fetchWeeklyPlan() {
    setLoadingPlan(true);
    try {
      const res = await analytics.weeklyPlan();
      setWeeklyPlan(res.weekly_plan);
    } catch (e) {
      console.error(e);
    } finally {
      setLoadingPlan(false);
    }
  }

  // Bar chart data
  const chartData = Object.entries(confidenceMap).map(([topic, confidence]) => ({
    topic: topic.length > 14 ? topic.slice(0, 12) + "…" : topic,
    confidence: Math.round(confidence * 100),
  }));

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Analytics</h1>
        <p className="text-muted-foreground">Your learning signals and personalised insights</p>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="weak">Weak Topics</TabsTrigger>
          <TabsTrigger value="revision">Revision</TabsTrigger>
          <TabsTrigger value="plan">Weekly Plan</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="mt-6 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Brain className="h-5 w-5" /> Confidence by Topic
              </CardTitle>
              <CardDescription>Higher is better — based on recent quiz performance</CardDescription>
            </CardHeader>
            <CardContent>
              {chartData.length === 0 ? (
                <p className="text-sm text-muted-foreground">No data yet. Take a quiz to see results.</p>
              ) : (
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={chartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                    <XAxis dataKey="topic" tick={{ fontSize: 11 }} />
                    <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
                    <Tooltip content={<ConfidenceTooltip />} cursor={{ fill: "rgba(128,128,128,0.08)" }} />
                    <Bar dataKey="confidence" radius={[4, 4, 0, 0]}>
                      {chartData.map((entry, i) => (
                        <Cell
                          key={i}
                          fill={
                            entry.confidence >= 70
                              ? "#22c55e"
                              : entry.confidence >= 40
                              ? "#f59e0b"
                              : "#ef4444"
                          }
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              )}
            </CardContent>
          </Card>

          {/* Confidence list */}
          <Card>
            <CardHeader>
              <CardTitle>Topic Breakdown</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {Object.entries(confidenceMap).length === 0 ? (
                <p className="text-sm text-muted-foreground">Upload study material and take a quiz to see data.</p>
              ) : (
                Object.entries(confidenceMap).map(([topic, conf]) => (
                  <div key={topic} className="space-y-1.5">
                    <div className="flex items-center justify-between text-sm">
                      <span className="capitalize font-medium">{topic}</span>
                      <span className="text-muted-foreground">{Math.round(conf * 100)}%</span>
                    </div>
                    <Progress
                      value={conf * 100}
                      className="h-2"
                    />
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Weak Topics Tab */}
        <TabsContent value="weak" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingDown className="h-5 w-5 text-destructive" /> Weak Topics
              </CardTitle>
              <CardDescription>Topics where your confidence is lowest — click to quiz</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {weakTopics.length === 0 ? (
                <p className="text-sm text-muted-foreground">No weak topics detected yet. Keep quizzing!</p>
              ) : (
                weakTopics.map((wt) => (
                  <div key={wt.topic} className="flex items-center justify-between rounded-lg border border-border p-4">
                    <div className="space-y-1 flex-1 mr-4">
                      <p className="font-medium capitalize">{wt.topic}</p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <span>Confidence: {Math.round(wt.confidence * 100)}%</span>
                        <span>·</span>
                        <span>Weakness: {Math.round(wt.weakness * 100)}%</span>
                      </div>
                      <Progress value={wt.confidence * 100} className="h-1.5 mt-1" />
                    </div>
                    <Link href={`/quiz?topic=${encodeURIComponent(wt.topic)}`} className={cn(buttonVariants({ size: "sm" }))}>
                      Quiz
                    </Link>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Revision Tab */}
        <TabsContent value="revision" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <RefreshCw className="h-5 w-5 text-yellow-500" /> Revision Priorities
              </CardTitle>
              <CardDescription>
                Topics you should revisit soon — the longer since your last attempt, the higher the priority
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {revisionTopics.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  No revision data yet. Take a quiz on a topic first — your review schedule will appear here after an attempt.
                </p>
              ) : (
                revisionTopics.map((rt, i) => (
                  <div key={rt.topic} className="flex items-center gap-4 rounded-lg border border-border p-4">
                    <span className="text-2xl font-bold text-muted-foreground/40 w-6">
                      {i + 1}
                    </span>
                    <div className="flex-1 space-y-1">
                      <div className="flex items-center justify-between">
                        <p className="font-medium capitalize">{rt.topic}</p>
                        <Badge variant={rt.revision_priority > 0.7 ? "destructive" : "secondary"}>
                          Priority: {Math.round(rt.revision_priority * 100)}%
                        </Badge>
                      </div>
                      <div className="flex gap-4 text-xs text-muted-foreground">
                        <span>Retention: {Math.round(rt.retention * 100)}%</span>
                        <span>Confidence: {Math.round(rt.confidence * 100)}%</span>
                      </div>
                      <Progress value={rt.retention * 100} className="h-1.5" />
                    </div>
                    <Link href={`/ask?topic=${encodeURIComponent(rt.topic)}`} className={cn(buttonVariants({ size: "sm", variant: "outline" }))}>
                      Revise
                    </Link>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Weekly Plan Tab */}
        <TabsContent value="plan" className="mt-6 space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="h-5 w-5 text-primary" /> Weekly Study Plan
              </CardTitle>
              <CardDescription>
                A personalised study schedule to help you review and practise the right topics at the right time
              </CardDescription>
            </CardHeader>
            <CardContent>
              {weeklyPlan.length === 0 ? (
                <div className="space-y-4">
                  <div className="flex items-start gap-3 text-sm text-muted-foreground">
                    <AlertTriangle className="h-4 w-4 shrink-0 mt-0.5 text-yellow-500" />
                    <p>
                      Get a day-by-day study plan tailored to you. It looks at where you&apos;re struggling and what you&apos;re due to review, then builds a schedule so nothing slips through the cracks.
                    </p>
                  </div>
                  <Button onClick={fetchWeeklyPlan} disabled={loadingPlan}>
                    {loadingPlan ? (
                      <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Generating plan…</>
                    ) : (
                      <><Calendar className="mr-2 h-4 w-4" /> Generate Weekly Plan</>
                    )}
                  </Button>
                </div>
              ) : (
                <div className="space-y-3">
                  {weeklyPlan.map((item, i) => (
                    <div key={i} className="flex items-center gap-4 rounded-lg border border-border p-4">
                      <div className="text-center min-w-[60px]">
                        <p className="text-xs text-muted-foreground">{item.date}</p>
                        <p className="font-semibold text-sm">{item.day}</p>
                      </div>
                      <Separator orientation="vertical" className="h-10" />
                      <div className="flex-1">
                        <p className="font-medium capitalize">{item.topic}</p>
                        <p className="text-sm text-muted-foreground capitalize">{item.task}</p>
                      </div>
                      <Badge className={PRIORITY_COLOR[item.priority]} variant="outline">
                        {item.priority}
                      </Badge>
                      <Link
                        href={
                          item.task.toLowerCase() === "revise"
                            ? `/ask?topic=${encodeURIComponent(item.topic)}`
                            : `/quiz?topic=${encodeURIComponent(item.topic)}`
                        }
                        className={cn(buttonVariants({ size: "sm", variant: "outline" }))}
                      >
                        Go
                      </Link>
                    </div>
                  ))}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="w-full text-muted-foreground"
                    onClick={fetchWeeklyPlan}
                    disabled={loadingPlan}
                  >
                    {loadingPlan ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
                    Regenerate
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
