"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Bot, User, Send, Loader2,
  ChevronDown, ChevronUp, FileText,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface Source {
  text: string;
  doc_id: string;
  score: number;
}

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  confidence?: number;
}

function SourcesPanel({ sources, confidence }: { sources: Source[]; confidence: number }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="mt-2 rounded-lg border border-border bg-background/60 text-xs">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between px-3 py-2 text-muted-foreground hover:text-foreground transition-colors"
      >
        <span className="flex items-center gap-1.5">
          <FileText className="h-3.5 w-3.5" />
          Sources from your PDF
          <Badge variant="secondary" className="ml-1 text-[10px] px-1.5 py-0">
            {Math.round(confidence * 100)}% match
          </Badge>
        </span>
        {open ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
      </button>
      {open && (
        <div className="divide-y divide-border border-t border-border">
          {sources.map((src, i) => (
            <div key={i} className="px-3 py-2.5 space-y-1">
              <div className="flex items-center justify-between text-[10px] text-muted-foreground">
                <span className="font-medium truncate max-w-[70%]">{src.doc_id || `Passage ${i + 1}`}</span>
                <span className="shrink-0">similarity {Math.round(src.score * 100)}%</span>
              </div>
              <p className="leading-relaxed text-foreground/80 italic">
                &ldquo;{src.text}{src.text.length >= 280 ? "…" : ""}&rdquo;
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

const SUGGESTION_CHIPS = [
  "Summarize the key concepts",
  "What are the main topics covered?",
  "Explain this in simple terms",
];

export default function AskPage() {
  const { name } = useAuth();
  const firstName = name?.split(" ")[0] ?? "there";

  const [sessionId, setSessionId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const authHeaders = (): Record<string, string> => {
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    return {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function getOrCreateSession(): Promise<number> {
    if (sessionId) return sessionId;
    const res = await fetch(`${BASE_URL}/chat/sessions`, { method: "POST", headers: authHeaders() });
    if (!res.ok) throw new Error("Failed to create session");
    const data = await res.json();
    setSessionId(data.id);
    return data.id;
  }

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || streaming) return;

    const question = input.trim();
    setInput("");

    let sid: number;
    try {
      sid = await getOrCreateSession();
    } catch {
      return;
    }

    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
      { role: "assistant", content: "" },
    ]);
    setStreaming(true);

    try {
      const res = await fetch(`${BASE_URL}/chat/sessions/${sid}/ask-stream`, {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({ question }),
      });

      if (!res.ok || !res.body) throw new Error("Request failed");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";

        for (const line of lines) {
          if (!line.startsWith("data: ")) continue;
          const payload = line.slice(6).trim();
          if (payload === "[DONE]") break;
          if (payload.startsWith("[SOURCES]")) {
            try {
              const meta = JSON.parse(payload.slice(9));
              setMessages((prev) => {
                const updated = [...prev];
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  sources: meta.sources,
                  confidence: meta.confidence,
                };
                return updated;
              });
            } catch { /* skip */ }
            continue;
          }
          try {
            const text: string = JSON.parse(payload);
            setMessages((prev) => {
              const updated = [...prev];
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content: updated[updated.length - 1].content + text,
              };
              return updated;
            });
          } catch { /* skip */ }
        }
      }
    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          ...updated[updated.length - 1],
          content: `Sorry, something went wrong. ${(err as Error).message}`,
        };
        return updated;
      });
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div className="flex h-full min-h-0">
      <div className="flex-1 min-w-0 flex flex-col rounded-xl border border-border bg-card overflow-hidden">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 min-h-0">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center gap-4 px-4">
              <div className="h-14 w-14 rounded-full bg-primary/10 flex items-center justify-center">
                <Bot className="h-7 w-7 text-primary" />
              </div>
              <div>
                <h2 className="text-xl font-semibold tracking-tight">Hey {firstName}! 👋</h2>
                <p className="text-sm text-muted-foreground mt-1.5 max-w-xs leading-relaxed">
                  Ready to explore your study materials? Ask me anything about your uploaded documents.
                </p>
              </div>
              <div className="flex flex-wrap gap-2 justify-center mt-1">
                {SUGGESTION_CHIPS.map((chip) => (
                  <button
                    key={chip}
                    onClick={() => setInput(chip)}
                    className="text-xs px-3 py-1.5 rounded-full border border-border hover:bg-muted transition-colors text-muted-foreground hover:text-foreground"
                  >
                    {chip}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6 max-w-3xl mx-auto">
              {messages.map((msg, i) => (
                <div key={i} className={cn("flex gap-3", msg.role === "user" ? "flex-row-reverse" : "flex-row")}>
                  <div
                    className={cn(
                      "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
                      msg.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted"
                    )}
                  >
                    {msg.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4 text-primary" />}
                  </div>

                  <div className={cn("max-w-[80%]", msg.role === "user" ? "items-end" : "items-start")}>
                    <div
                      className={cn(
                        "rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap",
                        msg.role === "user"
                          ? "bg-primary text-primary-foreground rounded-tr-sm"
                          : "bg-muted text-foreground rounded-tl-sm"
                      )}
                    >
                      {msg.content}
                      {!msg.content && streaming && i === messages.length - 1 && (
                        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                      )}
                    </div>
                    {msg.role === "assistant" && msg.sources && msg.sources.length > 0 && (
                      <SourcesPanel sources={msg.sources} confidence={msg.confidence ?? 0} />
                    )}
                  </div>
                </div>
              ))}
              <div ref={bottomRef} />
            </div>
          )}
        </div>

        <Separator />

        <form onSubmit={handleSend} className="flex gap-3 p-4">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask something about your study material…"
            disabled={streaming}
            className="flex-1"
            autoFocus
          />
          <Button type="submit" disabled={streaming || !input.trim()} size="icon">
            <Send className="h-4 w-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}
