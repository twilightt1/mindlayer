"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { DashboardLayout } from "@/components/layout";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { InsightCardsWidget } from "@/components/insights/InsightCardsWidget";
import { useAuth } from "@/components/auth";
import { getMemoryStats, listMemories } from "@/lib/api/memories";
import { listSources } from "@/lib/api/sources";
import { listInsights } from "@/lib/api/insights";
import { listDocuments } from "@/lib/api/documents";
import { cn } from "@/lib/utils";
import { 
  Sparkles, 
  TrendingUp, 
  FileText, 
  Brain, 
  ArrowRight,
  Zap,
  Loader2
} from "lucide-react";

// ============================================================================
// DESIGN TOKENS
// ============================================================================

const DESIGN = {
  colors: {
    bg: "bg-background",
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
// TYPES
// ============================================================================

interface DashboardStats {
  documents: number;
  insights: number;
  memories: number;
  queries: number;
  documentChange: string;
  insightChange: string;
  memoryChange: string;
  queryChange: string;
}

// ============================================================================
// STATS CARD
// ============================================================================

function StatsCard({ 
  stat, 
  index,
  loading 
}: { 
  stat: {
    label: string;
    value: string;
    change: string;
    icon: any;
    color: string;
    accent: string;
  }; 
  index: number;
  loading?: boolean;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="relative p-5 rounded-2xl overflow-hidden bg-white/[0.02] border border-white/[0.08] hover:border-white/[0.15] transition-all duration-300"
    >
      <div className={cn("absolute inset-0 opacity-50 bg-gradient-to-br", stat.color)} />
      
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <div className="w-11 h-11 rounded-xl flex items-center justify-center bg-white/[0.05] border border-white/[0.1]">
            {loading ? (
              <Loader2 className={cn("w-5 h-5 animate-spin", stat.accent)} />
            ) : (
              <stat.icon className={cn("w-5 h-5", stat.accent)} />
            )}
          </div>
          <span
            className={cn(
              "text-xs font-medium px-2 py-1 rounded-full border",
              stat.change === "Get started" || stat.change === "None yet"
                ? "bg-white/[0.05] text-white/40 border-white/[0.1]"
                : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20"
            )}
          >
            {stat.change}
          </span>
        </div>
        
        <p className="text-3xl font-bold text-white mb-1">
          {loading ? "—" : stat.value}
        </p>
        <p className="text-sm text-white/50">{stat.label}</p>
      </div>
    </motion.div>
  );
}

// ============================================================================
// QUICK ACTIONS
// ============================================================================

const QUICK_ACTIONS = [
  {
    label: "Upload Documents",
    description: "Add files to your knowledge base",
    icon: FileText,
    href: "/documents",
    color: "from-blue-500 to-cyan-500",
  },
  {
    label: "Start Chat",
    description: "Ask questions about your data",
    icon: Sparkles,
    href: "/chat",
    color: "from-violet-500 to-purple-500",
  },
  {
    label: "Discover Insights",
    description: "Find hidden connections",
    icon: Brain,
    href: "/insights",
    color: "from-pink-500 to-rose-500",
  },
];

function QuickAction({ action, index }: { action: typeof QUICK_ACTIONS[0]; index: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ delay: 0.3 + index * 0.1 }}
    >
      <Link
        href={action.href}
        className="group relative flex items-center gap-4 p-4 rounded-2xl bg-white/[0.02] border border-white/[0.08] hover:border-white/[0.15] hover:bg-white/[0.04] transition-all duration-300"
      >
        <div className={cn(
          "relative w-12 h-12 rounded-xl flex items-center justify-center bg-gradient-to-br shadow-lg",
          action.color,
          "group-hover:scale-110 transition-transform duration-300"
        )}>
          <action.icon className="w-6 h-6 text-white" />
        </div>
        
        <div className="flex-1">
          <p className="text-sm font-medium text-white mb-0.5">{action.label}</p>
          <p className="text-xs text-white/40">{action.description}</p>
        </div>
        
        <motion.div
          animate={{ x: [0, 4, 0] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="text-white/30 group-hover:text-white/60 transition-colors"
        >
          <ArrowRight className="w-5 h-5" />
        </motion.div>
      </Link>
    </motion.div>
  );
}

// ============================================================================
// RECENT ACTIVITY
// ============================================================================

interface ActivityItem {
  type: "chat" | "upload" | "insight";
  text: string;
  time: string;
}

function ActivityItemComponent({ item, index }: { item: ActivityItem; index: number }) {
  const icons = {
    chat: Sparkles,
    upload: FileText,
    insight: Brain,
  };
  const Icon = icons[item.type];

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.5 + index * 0.1 }}
      className="flex items-center gap-3 py-3 border-b border-white/[0.05] last:border-0"
    >
      <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-white/[0.05]">
        <Icon className="w-4 h-4 text-white/50" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white/70 truncate">{item.text}</p>
      </div>
      <span className="text-xs text-white/30 whitespace-nowrap">{item.time}</span>
    </motion.div>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function DashboardPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<DashboardStats>({
    documents: 0,
    insights: 0,
    memories: 0,
    queries: 0,
    documentChange: "",
    insightChange: "",
    memoryChange: "",
    queryChange: "",
  });
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([]);
  const [loading, setLoading] = useState(true);

  // Fetch dashboard data
  useEffect(() => {
    async function fetchData() {
      try {
        // Fetch all data in parallel
        const [sourcesData, memoriesData, insightsData, docsData] = await Promise.allSettled([
          listSources({ limit: 1 }).catch(() => ({ total: 0 })),
          getMemoryStats().catch(() => ({ total_memories: 0 })),
          listInsights({ status: "new", limit: 100 }).catch(() => ({ items: [] })),
          listDocuments().catch(() => []),
        ]);

        const docCount = docsData.status === "fulfilled" ? docsData.value.length : 0;
        const insightCount = insightsData.status === "fulfilled" ? insightsData.value.items.length : 0;
        const memoryCount = memoriesData.status === "fulfilled" ? memoriesData.value.total_memories : 0;

        // Honest per-stat context instead of a fake "+0" delta.
        const ctx = (n: number, noun: string) => (n > 0 ? "All time" : noun);

        // Update stats
        setStats({
          documents: docCount,
          insights: insightCount,
          memories: memoryCount,
          queries: 0, // Chat queries not tracked yet
          documentChange: ctx(docCount, "Get started"),
          insightChange: ctx(insightCount, "None yet"),
          memoryChange: ctx(memoryCount, "None yet"),
          queryChange: "Coming soon",
        });

        // Generate recent activity from insights
        const activities: ActivityItem[] = [];
        
        if (insightsData.status === "fulfilled") {
          insightsData.value.items.slice(0, 4).forEach((insight: any, i: number) => {
            activities.push({
              type: "insight",
              text: insight.title || "New insight discovered",
              time: insight.created_at ? `${Math.floor((Date.now() - new Date(insight.created_at).getTime()) / 60000)}m ago` : "Recently",
            });
          });
        }

        if (sourcesData.status === "fulfilled" && sourcesData.value.total > 0) {
          activities.push({
            type: "upload",
            text: "Documents indexed in your workspace",
            time: "Recently",
          });
        }

        setRecentActivity(activities.length > 0 ? activities : [
          { type: "chat", text: "Welcome! Start a conversation to explore your knowledge", time: "Now" },
        ]);

      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  const STATS = [
    {
      label: "Documents",
      value: stats.documents.toLocaleString(),
      change: stats.documentChange,
      icon: FileText,
      color: "from-blue-500/20 to-cyan-500/20",
      accent: "text-blue-400",
    },
    {
      label: "Insights Found",
      value: stats.insights.toLocaleString(),
      change: stats.insightChange,
      icon: Sparkles,
      color: "from-violet-500/20 to-purple-500/20",
      accent: "text-violet-400",
    },
    {
      label: "Memories",
      value: stats.memories.toLocaleString(),
      change: stats.memoryChange,
      icon: Brain,
      color: "from-pink-500/20 to-rose-500/20",
      accent: "text-pink-400",
    },
    {
      label: "Questions Answered",
      value: stats.queries.toLocaleString(),
      change: stats.queryChange,
      icon: TrendingUp,
      color: "from-emerald-500/20 to-teal-500/20",
      accent: "text-emerald-400",
    },
  ];

  return (
    <DashboardLayout>
      <div className="min-h-screen p-8">
        {/* Header */}
        <div className="mb-8">
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex items-center gap-2 text-sm text-white/40 mb-2"
          >
            <Zap className="w-4 h-4 text-violet-400" />
            <span>Welcome back</span>
          </motion.div>
          <motion.h1
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-3xl font-bold text-white"
          >
            Dashboard
          </motion.h1>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {STATS.map((stat, i) => (
            <StatsCard key={stat.label} stat={stat} index={i} loading={loading} />
          ))}
        </div>

        {/* Main content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left column - Chat + Activity */}
          <div className="lg:col-span-2 space-y-8">
            {/* Chat widget */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="h-[500px] rounded-2xl overflow-hidden border border-white/[0.08]"
            >
              <ChatInterface />
            </motion.div>

            {/* Recent Activity */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="rounded-2xl overflow-hidden bg-white/[0.02] border border-white/[0.08]"
            >
              <div className="px-5 py-4 border-b border-white/[0.05]">
                <h2 className="text-sm font-semibold text-white">Recent Activity</h2>
              </div>
              <div className="px-5">
                {recentActivity.length > 0 ? (
                  recentActivity.map((item, i) => (
                    <ActivityItemComponent key={i} item={item} index={i} />
                  ))
                ) : (
                  <div className="py-8 text-center text-sm text-white/40">
                    No recent activity yet. Start by uploading documents or chatting!
                  </div>
                )}
              </div>
            </motion.div>
          </div>

          {/* Right column - Quick Actions + Insights */}
          <div className="space-y-6">
            {/* Quick Actions */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
            >
              <h2 className="text-sm font-semibold text-white mb-4">Quick Actions</h2>
              <div className="space-y-3">
                {QUICK_ACTIONS.map((action, i) => (
                  <QuickAction key={action.label} action={action} index={i} />
                ))}
              </div>
            </motion.div>

            {/* Insights Preview */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.4 }}
            >
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-semibold text-white">New Insights</h2>
                <Link 
                  href="/insights"
                  className="text-xs text-violet-400 hover:text-violet-300 transition-colors"
                >
                  View all →
                </Link>
              </div>
              <InsightCardsWidget maxItems={3} compact />
            </motion.div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
