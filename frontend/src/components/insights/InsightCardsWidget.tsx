"use client";

import { useState, useEffect } from "react";
import { InsightCardComponent } from "./InsightCardComponent";
import type { InsightResponse } from "@/types/insights";
import { listInsights, dismissInsight, saveInsight } from "@/lib/api/insights";
import { Sparkles, Loader2, ExternalLink } from "lucide-react";
import { cn } from "@/lib/utils";
import Link from "next/link";

interface InsightCardsWidgetProps {
  maxItems?: number;
  compact?: boolean;
  className?: string;
}

export function InsightCardsWidget({ maxItems = 3, compact = false, className }: InsightCardsWidgetProps) {
  const [insights, setInsights] = useState<InsightResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchInsights() {
      try {
        const response = await listInsights({ 
          status: "new",
          limit: maxItems 
        });
        setInsights(response.items);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    }
    fetchInsights();
  }, [maxItems]);

  async function handleDismiss(id: string) {
    const updated = await dismissInsight(id);
    setInsights((prev) => prev.map((i) => (i.id === id ? updated : i)));
  }

  async function handleSave(id: string) {
    const updated = await saveInsight(id);
    setInsights((prev) => prev.map((i) => (i.id === id ? updated : i)));
  }

  if (loading) {
    return (
      <div className={cn("flex items-center justify-center p-6", className)}>
        <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || insights.length === 0) {
    return null; // Don't show widget if no insights
  }

  return (
    <div className={cn("space-y-3", className)}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-primary" />
          <span className="text-sm font-medium">Discoveries</span>
        </div>
        <Link 
          href="/insights"
          className="text-xs text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
        >
          View all
          <ExternalLink className="w-3 h-3" />
        </Link>
      </div>

      <div className="space-y-2">
        {insights.slice(0, maxItems).map((insight) => (
          <InsightCardComponent
            key={insight.id}
            insight={insight}
            onDismiss={handleDismiss}
            onSave={handleSave}
            onFeedback={async () => {}}
          />
        ))}
      </div>
    </div>
  );
}
