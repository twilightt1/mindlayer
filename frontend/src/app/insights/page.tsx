"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { DashboardLayout } from "@/components/layout";
import { InsightCardsWidget } from "@/components/insights/InsightCardsWidget";
import { InsightCardComponent } from "@/components/insights/InsightCardComponent";
import { listInsights, dismissInsight, saveInsight, feedbackInsight } from "@/lib/api/insights";
import type { InsightResponse } from "@/types/insights";
import { 
  Sparkles, 
  Filter, 
  TrendingUp, 
  Clock,
  Check,
  Loader2
} from "lucide-react";

// ============================================================================
// DESIGN TOKENS
// ============================================================================

const DESIGN = {
  colors: {
    surface: "bg-white/[0.03]",
    border: "border-white/[0.08]",
    text: {
      primary: "text-white",
      secondary: "text-white/60",
      muted: "text-white/40",
    },
  },
};

// ============================================================================
// FILTERS
// ============================================================================

const FILTERS = [
  { value: "all", label: "All Insights", icon: Sparkles },
  { value: "new", label: "New", icon: Sparkles },
  { value: "saved", label: "Saved", icon: Check },
  { value: "dismissed", label: "Dismissed", icon: Clock },
];

const TYPE_FILTERS = [
  { value: "all", label: "All Types" },
  { value: "connection", label: "Connections" },
  { value: "pattern", label: "Patterns" },
  { value: "anomaly", label: "Anomalies" },
  { value: "summary", label: "Summaries" },
];

// ============================================================================
// COMPONENTS
// ============================================================================

function FilterChip({ 
  active, 
  onClick, 
  children 
}: { 
  active: boolean; 
  onClick: () => void; 
  children: React.ReactNode;
}) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        "px-3 py-1.5 text-xs rounded-full",
        "transition-all duration-200",
        active
          ? "bg-violet-500/20 text-violet-300 border border-violet-500/40"
          : "bg-white/[0.03] text-white/50 border border-white/[0.08] hover:text-white/70 hover:border-white/[0.15]"
      )}
    >
      {children}
    </motion.button>
  );
}

function InsightsList({ 
  insights, 
  loading,
  onDismiss,
  onSave,
  onFeedback
}: { 
  insights: InsightResponse[];
  loading: boolean;
  onDismiss: (id: string) => Promise<void>;
  onSave: (id: string) => Promise<void>;
  onFeedback: (id: string, helpful: boolean) => Promise<void>;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <Loader2 className="w-8 h-8 animate-spin text-violet-400" />
      </div>
    );
  }

  if (insights.length === 0) {
    return (
      <div className="text-center py-20">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-white/[0.03] border border-white/[0.08] flex items-center justify-center">
          <Sparkles className="w-8 h-8 text-white/20" />
        </div>
        <p className="text-sm font-medium text-white/60 mb-1">No insights yet</p>
        <p className="text-xs text-white/40">Insights are automatically discovered from your documents</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {insights.map((insight, index) => (
        <motion.div
          key={insight.id}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
        >
          <InsightCardComponent
            insight={insight}
            onDismiss={onDismiss}
            onSave={onSave}
            onFeedback={onFeedback}
          />
        </motion.div>
      ))}
    </div>
  );
}

function StatsOverview({ insights }: { insights: InsightResponse[] }) {
  const total = insights.length;
  const saved = insights.filter(i => i.status === "saved").length;
  const newCount = insights.filter(i => i.status === "new").length;
  
  // Calculate this week's insights
  const oneWeekAgo = new Date();
  oneWeekAgo.setDate(oneWeekAgo.getDate() - 7);
  const thisWeek = insights.filter(i => new Date(i.created_at) > oneWeekAgo).length;

  const stats = [
    { label: "Total", value: total, color: "text-violet-400" },
    { label: "New", value: newCount, color: "text-emerald-400" },
    { label: "Saved", value: saved, color: "text-amber-400" },
    { label: "This Week", value: thisWeek, color: "text-pink-400" },
  ];

  return (
    <div className="flex items-center gap-6">
      {stats.map((stat) => (
        <div key={stat.label} className="text-center">
          <p className={cn("text-2xl font-bold", stat.color)}>{stat.value}</p>
          <p className="text-xs text-white/40">{stat.label}</p>
        </div>
      ))}
    </div>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function InsightsPage() {
  const [statusFilter, setStatusFilter] = useState("all");
  const [typeFilter, setTypeFilter] = useState("all");
  const [loading, setLoading] = useState(true);
  const [insights, setInsights] = useState<InsightResponse[]>([]);

  // Fetch insights
  const fetchInsights = useCallback(async () => {
    try {
      setLoading(true);
      const params: any = {};
      if (statusFilter !== "all") params.status = statusFilter;
      if (typeFilter !== "all") params.insight_type = typeFilter;
      params.limit = 50;
      
      const data = await listInsights(params);
      setInsights(data.items);
    } catch (error) {
      console.error("Failed to fetch insights:", error);
    } finally {
      setLoading(false);
    }
  }, [statusFilter, typeFilter]);

  useEffect(() => {
    fetchInsights();
  }, [fetchInsights]);

  // Handle actions
  const handleDismiss = async (id: string) => {
    try {
      await dismissInsight(id);
      setInsights((prev) => prev.map((i) => i.id === id ? { ...i, status: "dismissed" } : i));
    } catch (error) {
      console.error("Failed to dismiss insight:", error);
    }
  };

  const handleSave = async (id: string) => {
    try {
      await saveInsight(id);
      setInsights((prev) => prev.map((i) => i.id === id ? { ...i, status: "saved" } : i));
    } catch (error) {
      console.error("Failed to save insight:", error);
    }
  };

  const handleFeedback = async (id: string, helpful: boolean) => {
    try {
      await feedbackInsight(id, { helpful });
    } catch (error) {
      console.error("Failed to submit feedback:", error);
    }
  };

  return (
    <DashboardLayout>
      <div className="min-h-screen p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-2 text-sm text-white/40 mb-2">
              <Sparkles className="w-4 h-4 text-violet-400" />
              <span>Insights</span>
            </div>
            <h1 className="text-2xl font-bold text-white">Discoveries</h1>
          </div>
          
          <StatsOverview insights={insights} />
        </div>

        {/* Filters */}
        <div className="flex flex-wrap items-center gap-4 mb-8">
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-white/30" />
            {FILTERS.map((filter) => (
              <FilterChip
                key={filter.value}
                active={statusFilter === filter.value}
                onClick={() => setStatusFilter(filter.value)}
              >
                {filter.label}
              </FilterChip>
            ))}
          </div>

          <div className="flex-1" />

          <div className="flex items-center gap-2">
            {TYPE_FILTERS.map((filter) => (
              <FilterChip
                key={filter.value}
                active={typeFilter === filter.value}
                onClick={() => setTypeFilter(filter.value)}
              >
                {filter.label}
              </FilterChip>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main content */}
          <div className="lg:col-span-2">
            <InsightsList 
              insights={insights} 
              loading={loading}
              onDismiss={handleDismiss}
              onSave={handleSave}
              onFeedback={handleFeedback}
            />
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick stats */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-5 rounded-2xl bg-white/[0.02] border border-white/[0.08]"
            >
              <h3 className="text-sm font-semibold text-white mb-4">Quick Stats</h3>
              
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center">
                      <TrendingUp className="w-4 h-4 text-violet-400" />
                    </div>
                    <span className="text-sm text-white/70">Connections Found</span>
                  </div>
                  <span className="text-sm font-medium text-white">47</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-pink-500/10 flex items-center justify-center">
                      <Sparkles className="w-4 h-4 text-pink-400" />
                    </div>
                    <span className="text-sm text-white/70">Patterns Detected</span>
                  </div>
                  <span className="text-sm font-medium text-white">23</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                      <Clock className="w-4 h-4 text-amber-400" />
                    </div>
                    <span className="text-sm text-white/70">Anomalies Spotted</span>
                  </div>
                  <span className="text-sm font-medium text-white">8</span>
                </div>
              </div>
            </motion.div>

            {/* Recent saved */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 }}
              className="p-5 rounded-2xl bg-white/[0.02] border border-white/[0.08]"
            >
              <h3 className="text-sm font-semibold text-white mb-4">Recently Saved</h3>
              
              <div className="space-y-3">
                {[
                  "Q3 planning decisions correlate with Q4 outcomes",
                  "Customer feedback shows consistent theme around UX",
                  "Meeting notes reveal action items not followed up",
                ].map((text, i) => (
                  <div 
                    key={i}
                    className="p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]"
                  >
                    <p className="text-xs text-white/60 line-clamp-2">{text}</p>
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Discover more */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="p-5 rounded-2xl bg-gradient-to-br from-violet-500/10 to-pink-500/10 border border-violet-500/20"
            >
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-5 h-5 text-violet-400" />
                <h3 className="text-sm font-semibold text-white">Discover More</h3>
              </div>
              <p className="text-xs text-white/50 mb-4">
                Upload more documents to unlock deeper insights and connections.
              </p>
              <button className={cn(
                "w-full py-2.5 rounded-xl text-sm font-medium",
                "bg-gradient-to-r from-violet-600 to-purple-600",
                "text-white shadow-lg shadow-violet-500/20",
                "hover:shadow-violet-500/30",
                "transition-all"
              )}>
                Upload Documents
              </button>
            </motion.div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
