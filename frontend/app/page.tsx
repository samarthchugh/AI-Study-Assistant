"use client";

import Link from "next/link";
import { useAuth } from "@/lib/auth";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import {
  GraduationCap,
  Brain,
  Upload,
  MessageSquare,
  BarChart3,
  Sparkles,
  ChevronRight,
  CheckCircle,
  Zap,
  Target,
  Calendar,
  LayoutDashboard,
} from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";

const features = [
  {
    icon: Upload,
    title: "Upload Your Notes",
    description:
      "Drag and drop any PDF. SmartLearnAI indexes and embeds your content instantly, ready for intelligent retrieval.",
    color: "text-blue-500",
    bg: "bg-blue-500/10",
  },
  {
    icon: MessageSquare,
    title: "Ask AI Anything",
    description:
      "Chat with your documents. Get streamed, context-aware answers grounded entirely in your own study material.",
    color: "text-purple-500",
    bg: "bg-purple-500/10",
  },
  {
    icon: Brain,
    title: "Adaptive Quizzes",
    description:
      "AI generates MCQs and short-answer questions that dynamically adjust difficulty based on your real performance.",
    color: "text-green-500",
    bg: "bg-green-500/10",
  },
  {
    icon: BarChart3,
    title: "Deep Analytics",
    description:
      "Track confidence per topic, spot knowledge gaps, and visualise your progress over time with rich charts.",
    color: "text-amber-500",
    bg: "bg-amber-500/10",
  },
  {
    icon: Target,
    title: "Weak Topic Detection",
    description:
      "The engine continuously maps your weakest areas and surfaces them so you always focus where it counts most.",
    color: "text-red-500",
    bg: "bg-red-500/10",
  },
  {
    icon: Calendar,
    title: "Weekly Study Plan",
    description:
      "An AI agent pipeline builds a personalised day-by-day revision schedule modelled on the forgetting curve.",
    color: "text-cyan-500",
    bg: "bg-cyan-500/10",
  },
];

const steps = [
  {
    number: "01",
    title: "Upload your material",
    description:
      "Add any PDF — lecture notes, textbooks, research papers. SmartLearnAI processes and indexes them automatically.",
  },
  {
    number: "02",
    title: "Study with AI",
    description:
      "Ask questions, generate quizzes, and get instant feedback. The system learns your strengths and knowledge gaps.",
  },
  {
    number: "03",
    title: "Follow your plan",
    description:
      "Receive a personalised study schedule. Revise at the right intervals, target weak spots, and ace your exams.",
  },
];

const trust = [
  "Adaptive difficulty",
  "Forgetting-curve revision",
  "RAG-powered answers",
  "Weekly AI plans",
];

export default function HomePage() {
  const { token, isLoading } = useAuth();

  if (isLoading) return null;

  const isLoggedIn = !!token;

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* ── Topbar ────────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-border/60 bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          {/* Brand */}
          <Link href="/" className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary shadow-sm">
              <GraduationCap className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-lg font-bold tracking-tight">SmartLearnAI</span>
          </Link>

          {/* Nav links — hidden on mobile */}
          <nav className="hidden items-center gap-7 text-sm text-muted-foreground md:flex">
            <a href="#features" className="transition-colors hover:text-foreground">
              Features
            </a>
            <a href="#how-it-works" className="transition-colors hover:text-foreground">
              How it works
            </a>
          </nav>

          {/* Auth CTAs */}
          <div className="flex items-center gap-1.5">
            <ThemeToggle />
            {isLoggedIn ? (
              <Link
                href="/dashboard"
                className={cn(buttonVariants({ size: "sm" }), "gap-1.5")}
              >
                Go to Dashboard <ChevronRight className="h-3.5 w-3.5" />
              </Link>
            ) : (
              <>
                <Link
                  href="/login"
                  className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}
                >
                  Sign in
                </Link>
                <Link
                  href="/signup"
                  className={cn(buttonVariants({ size: "sm" }), "gap-1.5")}
                >
                  Get started <ChevronRight className="h-3.5 w-3.5" />
                </Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-6 pb-28 pt-24 text-center">
        {/* Pill badge */}
        <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-border bg-muted/50 px-4 py-1.5 text-sm text-muted-foreground">
          <Sparkles className="h-3.5 w-3.5 text-primary" />
          AI-powered adaptive learning
        </div>

        <h1 className="mx-auto max-w-3xl text-5xl font-bold leading-tight tracking-tight sm:text-6xl">
          Study smarter with{" "}
          <span className="text-primary">personalised AI</span>
        </h1>

        <p className="mx-auto mt-6 max-w-xl text-lg text-muted-foreground">
          Upload your notes, chat with your documents, take adaptive quizzes, and get a
          custom revision plan — all driven by AI that grows with you.
        </p>

        {/* Primary CTAs */}
        <div className="mt-10 flex flex-col items-center justify-center gap-3 sm:flex-row">
          {isLoggedIn ? (
            <Link
              href="/dashboard"
              className={cn(buttonVariants({ size: "lg" }), "gap-2 px-8")}
            >
              <LayoutDashboard className="h-4 w-4" /> Back to Dashboard
            </Link>
          ) : (
            <Link
              href="/signup"
              className={cn(buttonVariants({ size: "lg" }), "gap-2 px-8")}
            >
              <Zap className="h-4 w-4" /> Start for free
            </Link>
          )}
          <a
            href="#features"
            className={cn(buttonVariants({ variant: "outline", size: "lg" }))}
          >
            See features
          </a>
        </div>

        {/* Trust strip */}
        <div className="mt-14 flex flex-wrap items-center justify-center gap-6 text-sm text-muted-foreground">
          {trust.map((item) => (
            <div key={item} className="flex items-center gap-1.5">
              <CheckCircle className="h-4 w-4 text-green-500" />
              {item}
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────────────────── */}
      <section id="features" className="border-t border-border bg-muted/20 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-14 text-center">
            <h2 className="text-3xl font-bold tracking-tight">
              Everything you need to excel
            </h2>
            <p className="mt-3 text-muted-foreground">
              Six intelligent tools working together in one platform
            </p>
          </div>

          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {features.map(({ icon: Icon, title, description, color, bg }) => (
              <div
                key={title}
                className="rounded-xl border border-border bg-card p-6 transition-shadow hover:shadow-md"
              >
                <div
                  className={cn(
                    "mb-4 inline-flex h-10 w-10 items-center justify-center rounded-lg",
                    bg
                  )}
                >
                  <Icon className={cn("h-5 w-5", color)} />
                </div>
                <h3 className="mb-2 font-semibold">{title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ──────────────────────────────────────────────────── */}
      <section id="how-it-works" className="py-24">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-14 text-center">
            <h2 className="text-3xl font-bold tracking-tight">How it works</h2>
            <p className="mt-3 text-muted-foreground">
              Three steps to transform how you study
            </p>
          </div>

          <div className="grid gap-10 md:grid-cols-3">
            {steps.map(({ number, title, description }, i) => (
              <div key={number} className="relative text-center">
                {/* Connector line (between cards, desktop only) */}
                {i < steps.length - 1 && (
                  <div className="absolute left-full top-7 hidden h-px w-10 -translate-x-5 bg-border md:block" />
                )}
                <div className="mb-5 inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-2xl font-bold text-primary">
                  {number}
                </div>
                <h3 className="mb-2 text-lg font-semibold">{title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">
                  {description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA banner ────────────────────────────────────────────────────── */}
      <section className="border-t border-border bg-primary/5 py-20">
        <div className="mx-auto max-w-2xl px-6 text-center">
          <h2 className="text-3xl font-bold tracking-tight">
            Ready to ace your exams?
          </h2>
          <p className="mt-4 text-muted-foreground">
            Join SmartLearnAI and let AI handle the heavy lifting while you focus on
            mastering the concepts.
          </p>
          <div className="mt-9 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            {isLoggedIn ? (
              <Link
                href="/dashboard"
                className={cn(buttonVariants({ size: "lg" }), "gap-2 px-8")}
              >
                <LayoutDashboard className="h-4 w-4" /> Back to Dashboard
              </Link>
            ) : (
              <>
                <Link
                  href="/signup"
                  className={cn(buttonVariants({ size: "lg" }), "gap-2 px-8")}
                >
                  <GraduationCap className="h-4 w-4" /> Get started free
                </Link>
                <Link
                  href="/login"
                  className={cn(buttonVariants({ variant: "outline", size: "lg" }))}
                >
                  Sign in
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────────────────── */}
      <footer className="border-t border-border py-8">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 sm:flex-row">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <GraduationCap className="h-4 w-4 text-primary" />
            SmartLearnAI
          </div>
          <p className="text-xs text-muted-foreground">
            © {new Date().getFullYear()} SmartLearnAI. Built for learners, powered by AI.
          </p>
        </div>
      </footer>
    </div>
  );
}
