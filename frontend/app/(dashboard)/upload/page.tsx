"use client";

import { useState, useRef, DragEvent, ChangeEvent } from "react";
import { documents } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Upload, FileText, CheckCircle, Loader2, X } from "lucide-react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  function handleFile(f: File) {
    if (f.type !== "application/pdf") {
      setError("Only PDF files are accepted.");
      return;
    }
    setError("");
    setSuccess(false);
    setFile(f);
  }

  function onFileChange(e: ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  }

  function onDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files?.[0];
    if (f) handleFile(f);
  }

  async function handleUpload() {
    if (!file) { setError("Please select a PDF file."); return; }
    if (!topic.trim()) { setError("Please enter a topic name."); return; }
    setError("");
    setLoading(true);
    try {
      await documents.upload(file, topic.trim());
      setSuccess(true);
      setFile(null);
      setTopic("");
      if (inputRef.current) inputRef.current.value = "";
      toast.success("Document uploaded and indexed successfully!");
    } catch (err) {
      setError((err as Error).message ?? "Upload failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Upload Study Material</h1>
        <p className="text-muted-foreground">Upload a PDF and tag it with a topic to get started</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>New Document</CardTitle>
          <CardDescription>
            The PDF will be chunked, embedded, and indexed for Q&amp;A and quiz generation.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          {success && (
            <Alert className="border-green-500/50 bg-green-500/10 text-green-500">
              <CheckCircle className="h-4 w-4" />
              <AlertDescription>Document indexed successfully! You can now quiz on it or ask questions.</AlertDescription>
            </Alert>
          )}

          {/* Drop zone */}
          <div
            className={cn(
              "relative flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-10 text-center transition-colors",
              dragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/60 hover:bg-accent/30"
            )}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
            onDragLeave={() => setDragging(false)}
            onDrop={onDrop}
          >
            <input
              ref={inputRef}
              type="file"
              accept=".pdf"
              className="sr-only"
              onChange={onFileChange}
            />
            {file ? (
              <div className="flex flex-col items-center gap-3">
                <FileText className="h-10 w-10 text-primary" />
                <div>
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-muted-foreground">
                    {(file.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <Badge variant="secondary">PDF</Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground"
                  onClick={(e) => { e.stopPropagation(); setFile(null); }}
                >
                  <X className="h-4 w-4 mr-1" /> Remove
                </Button>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-3">
                <Upload className="h-10 w-10 text-muted-foreground" />
                <div>
                  <p className="font-medium">Drop your PDF here or click to browse</p>
                  <p className="text-sm text-muted-foreground">PDF files only · no size limit</p>
                </div>
              </div>
            )}
          </div>

          {/* Topic input */}
          <div className="space-y-2">
            <Label htmlFor="topic">Topic</Label>
            <Input
              id="topic"
              placeholder="e.g. Machine Learning, Economics, Deep Learning"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Used to filter retrieval. Keep it short and consistent across uploads.
            </p>
          </div>

          <Button className="w-full" onClick={handleUpload} disabled={loading || !file}>
            {loading ? (
              <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Indexing document…</>
            ) : (
              <><Upload className="mr-2 h-4 w-4" /> Upload &amp; Index</>
            )}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
