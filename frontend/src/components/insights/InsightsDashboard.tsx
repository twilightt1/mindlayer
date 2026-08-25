"use client";

import { useState, useEffect, useCallback } from "react";
import { InsightCardComponent } from "./InsightCardComponent";
import type { InsightResponse, InsightStatus, InsightType } from "@/types/insights";
import { INSIGHT_TYPE_CONFIG } from "@/types/insights";
import {
  listInsights,
  generateInsights,
  dismissInsight,
  saveInsight,
  feedbackInsight,
  refreshInsights,
} from "@/lib/api/insights";
import {
  Sparkles,
  RefreshCw,
  Filter,
  Loader2,
  Plus,
  AlertCircle,
  TrendingUp,
} from "lucide-react";
import { cn } from "@/lib/utils";

type StatusOption = InsightStatus | "all";

const STATUS_OPTIONS: { value: StatusOption; label: string }[] = [
  { value: "all", label: "All" },
  { value: "new", label: "New" },
  { value: "shown", label: "Seen" },
  { value: "saved", label: "Saved" },
  { value: "dismissed", label: "Dismissed" },
];

const TYPE_OPTIONS: { value: InsightType | "all"; label: string }[] = [
  { value: "all", label: "All Types" },
  { value: "connection", label: "🔗 Connections" },
  { value: "contradiction", label: "⚡ Contradictions" },
  { value: "evolution", label: "📈 Evolution" },
  { value: "pattern", label: "🔄 Patterns" },
  { value: "gap", label: "❓ Gaps" },
  { value: "confirmation", label: "✅ Confirmations" },
  { value: "synthesis", label: "💡 Synthesis" },
];

interface InsightsDashboardProps {
  className?: string;
}

export function InsightsDashboard({ className }: InsightsDashboardProps) {
  const [insights, setInsights] = useState<InsightResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<StatusOption>("new");
  const [typeFilter, setTypeFilter] = useState<InsightType | "all">("all");
  const [showFilters, setShowFilters] = useState(false);

  // Pagination
  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [hasMore, setHasMore] = useState(false);

  const fetchInsights = useCallback(async (reset = false) => {
    setLoading(true);
    setError(null);
    try {
      const newOffset = reset ? 0 : offset;
      const response = await listInsights({
        status: statusFilter === "all" ? undefined : statusFilter,
        insight_type: typeFilter === "all" ? undefined : typeFilter,
        limit,
        offset: newOffset,
      });

      if (reset) {
        setInsights(response.items);
      } else {
        setInsights((prev) => [...prev, ...response.items]);
      }
      setTotal(response.total);
      setHasMore(response.items.length === limit);
      setOffset(newOffset + response.items.length);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load insights");
    } finally {
      setLoading(false);
    }
  }, [statusFilter, typeFilter, limit, offset]);

  useEffect(() => {
    fetchInsights(true);
  }, [statusFilter, typeFilter]);

  async function handleGenerate() {
    setGenerating(true);
    setError(null);
    try {
      await generateInsights({ max_insights: 5 });
      await fetchInsights(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate insights");
    } finally {
      setGenerating(false);
    }
  }

  async function handleRefresh() {
    setRefreshing(true);
    setError(null);
    try {
      const result = await refreshInsights();
      await fetchInsights(true);
      // Show notification if new insights were generated
      if (result.new_insights.length > 0) {
        // Could show a toast here
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to refresh insights");
    } finally {
      setRefreshing(false);
    }
  }

  async function handleDismiss(id: string) {
    const updated = await dismissInsight(id);
    setInsights((prev) =>
      prev.map((insight) => (insight.id === id ? updated : insight))
    );
  }

  async function handleSave(id: string) {
    const updated = await saveInsight(id);
    setInsights((prev) =>
      prev.map((insight) => (insight.id === id ? updated : insight))
    );
  }

  async function handleFeedback(id: string, helpful: boolean) {
    const updated = await feedbackInsight(id, { helpful });
    setInsights((prev) =>
      prev.map((insight) => (insight.id === id ? updated : insight))
    );
  }

  function loadMore() {
    fetchInsights(false);
  }

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-primary" />
            Discoveries
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Hidden connections from your knowledge
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className={cn(
              "p-2.5 rounded-lg border border-border hover:bg-accent transition-colors",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
            title="Refresh insights"
          >
            <RefreshCw className={cn("w-4 h-4", refreshing && "animate-spin")} />
          </button>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              "p-2.5 rounded-lg border border-border hover:bg-accent transition-colors",
              showFilters && "bg-accent"
            )}
          >
            <Filter className="w-4 h-4" />
          </button>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className={cn(
              "btn-premium px-4 py-2.5 rounded-lg text-sm font-medium flex items-center gap-2",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            {generating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Discovering...
              </>
            ) : (
              <>
                <Plus className="w-4 h-4" />
                Discover
              </>
            )}
          </button>
        </div>
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="flex flex-wrap gap-4 p-4 bg-card border border-border rounded-xl">
          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground">Status</label>
            <div className="flex flex-wrap gap-1">
              {STATUS_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setStatusFilter(option.value)}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
                    statusFilter === option.value
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-muted/80 text-muted-foreground"
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs text-muted-foreground">Type</label>
            <div className="flex flex-wrap gap-1">
              {TYPE_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => setTypeFilter(option.value as InsightType | "all")}
                  className={cn(
                    "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors",
                    typeFilter === option.value
                      ? "bg-primary text-primary-foreground"
                      : "bg-muted hover:bg-muted/80 text-muted-foreground"
                  )}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="flex items-center gap-4 text-sm">
        <span className="text-muted-foreground">
          {total} insight{total !== 1 ? "s" : ""}
        </span>
        {statusFilter !== "all" && (
          <span className="text-muted-foreground">
            • showing {statusFilter}
          </span>
        )}
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">{error}</span>
        </div>
      )}

      {/* Loading */}
      {loading && insights.length === 0 && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {/* Empty State */}
      {!loading && insights.length === 0 && !error && (
        <div className="text-center py-12">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-muted rounded-full mb-4">
            <TrendingUp className="w-8 h-8 text-muted-foreground" />
          </div>
          <h3 className="text-lg font-medium mb-2">No insights yet</h3>
          <p className="text-sm text-muted-foreground mb-6 max-w-sm mx-auto">
            Add more memories and documents to unlock hidden connections and patterns.
          </p>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="btn-premium px-4 py-2 rounded-lg text-sm font-medium"
          >
            {generating ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <Sparkles className="w-4 h-4 inline mr-2" />
                Discover Now
              </>
            )}
          </button>
        </div>
      )}

      {/* Insights List */}
      {insights.length > 0 && (
        <div className="space-y-4">
          {insights.map((insight) => (
            <InsightCardComponent
              key={insight.id}
              insight={insight}
              onDismiss={handleDismiss}
              onSave={handleSave}
              onFeedback={handleFeedback}
            />
          ))}

          {/* Load More */}
          {hasMore && (
            <div className="flex justify-center pt-4">
              <button
                onClick={loadMore}
                disabled={loading}
                className="px-4 py-2 rounded-lg border border-border hover:bg-accent transition-colors text-sm"
              >
                {loading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  "Load more"
                )}
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
