"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import type { InsightResponse } from "@/types/insights";
import { INSIGHT_TYPE_CONFIG, SURPRISE_LABELS } from "@/types/insights";
import { 
  Sparkles, 
  X, 
  Bookmark, 
  ThumbsUp, 
  ThumbsDown,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Loader2
} from "lucide-react";

interface InsightCardComponentProps {
  insight: InsightResponse;
  onDismiss?: (id: string) => Promise<void>;
  onSave?: (id: string) => Promise<void>;
  onFeedback?: (id: string, helpful: boolean) => Promise<void>;
  onViewSource?: (documentId: string) => void;
  className?: string;
}

function timeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  if (seconds < 604800) return `${Math.floor(seconds / 86400)}d ago`;
  return date.toLocaleDateString();
}

function ConfidenceBar({ confidence }: { confidence: number }) {
  const percent = Math.round(confidence * 100);
  const color = percent >= 80 ? "bg-emerald-500" : percent >= 50 ? "bg-amber-500" : "bg-slate-500";

  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 h-1.5 bg-muted rounded-full overflow-hidden">
        <div 
          className={cn("h-full rounded-full transition-all duration-500", color)}
          style={{ width: `${percent}%` }}
        />
      </div>
      <span className="text-xs text-muted-foreground tabular-nums">{percent}%</span>
    </div>
  );
}

export function InsightCardComponent({
  insight,
  onDismiss,
  onSave,
  onFeedback,
  onViewSource,
  className,
}: InsightCardComponentProps) {
  const [expanded, setExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showFeedback, setShowFeedback] = useState(false);

  const config = INSIGHT_TYPE_CONFIG[insight.insight_type];
  const isSaved = insight.status === "saved";
  const isDismissed = insight.status === "dismissed";

  async function handleAction(action: () => Promise<void> | undefined) {
    if (!action || isLoading) return;
    setIsLoading(true);
    try {
      await action();
    } finally {
      setIsLoading(false);
    }
  }

  async function handleFeedback(helpful: boolean) {
    if (!onFeedback) return;
    await handleAction(async () => onFeedback(insight.id, helpful));
  }

  return (
    <div
      className={cn(
        "group relative bg-card border border-border rounded-xl p-5",
        "transition-all duration-300",
        "hover:border-border/80 hover:shadow-lg hover:shadow-glow-primary/5",
        isDismissed && "opacity-50",
        isSaved && "border-primary/30 bg-primary/5",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-3">
          <span className="text-2xl">{config.emoji}</span>
          <div>
            <h3 className="font-semibold text-foreground leading-tight">
              {insight.title}
            </h3>
            <div className="flex items-center gap-2 mt-1">
              <span className={cn("text-xs font-medium", config.color)}>
                {config.label}
              </span>
              <span className="text-muted-foreground">•</span>
              <span className="text-xs text-muted-foreground">
                {SURPRISE_LABELS[insight.surprise_level]}
              </span>
              <span className="text-muted-foreground">•</span>
              <span className="text-xs text-muted-foreground">
                {timeAgo(insight.created_at)}
              </span>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {onSave && (
            <button
              onClick={() => onSave && handleAction(() => onSave(insight.id))}
              disabled={isLoading}
              className={cn(
                "p-2 rounded-lg transition-colors",
                "hover:bg-accent hover:text-primary",
                isSaved && "text-primary"
              )}
              title="Save insight"
            >
              {isLoading ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Bookmark className={cn("w-4 h-4", isSaved && "fill-current")} />
              )}
            </button>
          )}
          {onDismiss && !isDismissed && (
            <button
              onClick={() => onDismiss && handleAction(() => onDismiss(insight.id))}
              disabled={isLoading}
              className="p-2 rounded-lg hover:bg-accent hover:text-muted-foreground transition-colors"
              title="Dismiss"
            >
              <X className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Summary */}
      <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
        {insight.summary}
      </p>

      {/* Confidence */}
      <div className="mb-3">
        <ConfidenceBar confidence={insight.confidence} />
      </div>

      {/* Expandable Details */}
      {insight.detail && (
        <div className="mb-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
            {expanded ? "Hide details" : "Show details"}
          </button>
          
          {expanded && (
            <div className="mt-2 p-3 bg-muted/50 rounded-lg text-sm text-muted-foreground">
              {insight.detail}
            </div>
          )}
        </div>
      )}

      {/* Source Documents */}
      {insight.source_docs.length > 0 && (
        <div className="mb-4">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
          >
            <ExternalLink className="w-3 h-3" />
            {insight.source_count} source{insight.source_count > 1 ? "s" : ""}
          </button>

          {expanded && (
            <div className="mt-2 space-y-2">
              {insight.source_docs.map((source, idx) => (
                <div 
                  key={idx}
                  className="p-2 bg-muted/30 rounded-lg text-xs"
                >
                  <div className="font-medium text-foreground mb-1">
                    {source.title}
                  </div>
                  {source.excerpt && (
                    <p className="text-muted-foreground line-clamp-2">
                      {source.excerpt}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Footer Actions */}
      <div className="flex items-center justify-between pt-3 border-t border-border/50">
        <div className="flex items-center gap-2">
          {insight.shown_count > 1 && (
            <span className="text-xs text-muted-foreground">
              Shown {insight.shown_count} times
            </span>
          )}
        </div>

        {/* Feedback */}
        <div className="flex items-center gap-2">
          {!showFeedback ? (
            <button
              onClick={() => setShowFeedback(true)}
              className="text-xs text-muted-foreground hover:text-foreground transition-colors"
            >
              Was this helpful?
            </button>
          ) : (
            <div className="flex items-center gap-1">
              <button
                onClick={() => handleFeedback(true)}
                disabled={isLoading}
                className={cn(
                  "p-1.5 rounded-lg transition-colors",
                  insight.helpful === true 
                    ? "bg-green-500/20 text-green-500" 
                    : "hover:bg-accent hover:text-green-500"
                )}
                title="Helpful"
              >
                <ThumbsUp className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => handleFeedback(false)}
                disabled={isLoading}
                className={cn(
                  "p-1.5 rounded-lg transition-colors",
                  insight.helpful === false 
                    ? "bg-red-500/20 text-red-500" 
                    : "hover:bg-accent hover:text-red-500"
                )}
                title="Not helpful"
              >
                <ThumbsDown className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
