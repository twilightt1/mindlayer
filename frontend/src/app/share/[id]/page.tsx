"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Calendar, Tag, ExternalLink } from "lucide-react";

interface SharedMemory {
  id: string;
  title: string;
  content: string;
  summary: string | null;
  tags: string[];
  created_at: string;
  source_type: string;
}

export default function SharedMemoryPage() {
  const params = useParams();
  const [memory, setMemory] = useState<SharedMemory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSharedMemory = async () => {
      try {
        const res = await fetch(`/api/v1/memories/${params.id}/share`);
        if (!res.ok) {
          setError("Memory not found or not shared publicly");
          return;
        }
        setMemory(await res.json());
      } catch {
        setError("Failed to load shared memory");
      } finally {
        setLoading(false);
      }
    };

    if (params.id) {
      fetchSharedMemory();
    }
  }, [params.id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-2xl mx-auto space-y-4">
          <Skeleton className="h-8 w-3/4" />
          <Skeleton className="h-4 w-1/4" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (error || !memory) {
    return (
      <div className="min-h-screen bg-background p-8">
        <div className="max-w-2xl mx-auto text-center py-16">
          <h1 className="text-2xl font-bold mb-4">Memory Not Found</h1>
          <p className="text-muted-foreground mb-6">
            {error || "This memory doesn't exist or isn't shared publicly."}
          </p>
          <a
            href="https://mindlayer.app"
            className="inline-flex items-center gap-2 text-primary hover:underline"
          >
            <ExternalLink className="h-4 w-4" />
            Try MindLayer
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background p-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8 text-center">
          <div className="flex items-center justify-center gap-2 text-primary mb-4">
            <span className="font-semibold">MindLayer</span>
            <Badge variant="outline">Shared Memory</Badge>
          </div>
        </div>

        {/* Memory Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-xl">{memory.title}</CardTitle>
            <div className="flex items-center gap-4 text-sm text-muted-foreground">
              <span className="flex items-center gap-1">
                <Calendar className="h-4 w-4" />
                {new Date(memory.created_at).toLocaleDateString()}
              </span>
              <Badge variant="secondary">{memory.source_type}</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Summary */}
            {memory.summary && (
              <div className="p-4 bg-muted rounded-lg">
                <p className="text-sm font-medium text-muted-foreground mb-1">Summary</p>
                <p className="text-sm">{memory.summary}</p>
              </div>
            )}

            {/* Content */}
            <div className="prose prose-sm max-w-none">
              <p className="whitespace-pre-wrap">{memory.content}</p>
            </div>

            {/* Tags */}
            {memory.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-4 border-t">
                {memory.tags.map((tag) => (
                  <Badge key={tag} variant="outline" className="flex items-center gap-1">
                    <Tag className="h-3 w-3" />
                    {tag}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* CTA */}
        <div className="text-center py-8">
          <p className="text-muted-foreground mb-4">
            Want to create your own second brain?
          </p>
          <a
            href="https://mindlayer.app/signup"
            className="inline-flex items-center justify-center gap-2 bg-primary text-primary-foreground px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors"
          >
            Start Free Trial
          </a>
        </div>

        {/* Footer */}
        <div className="text-center text-xs text-muted-foreground pt-8">
          <p>Powered by MindLayer - AI-Powered Second Brain</p>
        </div>
      </div>
    </div>
  );
}
