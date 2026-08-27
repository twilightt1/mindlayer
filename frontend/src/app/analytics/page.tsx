"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { DashboardLayout } from "@/components/layout";
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  FileText, 
  MessageSquare,
  Brain,
  BarChart3,
  Calendar,
  ArrowUpRight,
  ArrowDownRight,
  Loader2
} from "lucide-react";
import { getFeatureUsage, getPageViews, getDAUStats, type FeatureUsageItem, type PageViewItem, type DAUItem } from "@/lib/api/analytics";

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
// COMPONENTS
// ============================================================================

interface StatItem {
  label: string;
  value: string;
  change: number;
  icon: any;
  color: string;
  accent: string;
}

function StatCard({ stat, index }: { stat: StatItem; index: number }) {
  const isPositive = stat.change >= 0;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
      className="relative p-5 rounded-2xl overflow-hidden bg-white/[0.02] border border-white/[0.08]"
    >
      <div className={cn(
        "absolute inset-0 opacity-50",
        `bg-gradient-to-br ${stat.color}`
      )} />
      
      <div className="relative z-10">
        <div className="flex items-start justify-between mb-4">
          <div className="w-11 h-11 rounded-xl flex items-center justify-center bg-white/[0.05] border border-white/[0.1]">
            <stat.icon className={cn("w-5 h-5", stat.accent)} />
          </div>
          <div className={cn(
            "flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-full",
            isPositive 
              ? "bg-emerald-500/10 text-emerald-400" 
              : "bg-red-500/10 text-red-400"
          )}>
            {isPositive ? (
              <ArrowUpRight className="w-3 h-3" />
            ) : (
              <ArrowDownRight className="w-3 h-3" />
            )}
            {Math.abs(stat.change)}%
          </div>
        </div>
        
        <p className="text-3xl font-bold text-white mb-1">{stat.value}</p>
        <p className="text-sm text-white/50">{stat.label}</p>
      </div>
    </motion.div>
  );
}

interface ChartData {
  day: string;
  queries: number;
  insights: number;
}

interface QueryData {
  query: string;
  count: number;
  trend: string;
}

interface DocTypeData {
  type: string;
  count: number;
  percentage: number;
  color: string;
}

function WeeklyChart({ data }: { data: ChartData[] }) {
  const maxQueries = Math.max(...data.map((d: ChartData) => d.queries), 1);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 }}
      className="p-6 rounded-2xl bg-white/[0.02] border border-white/[0.08]"
    >
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-lg font-semibold text-white">Weekly Activity</h3>
          <p className="text-xs text-white/40 mt-1">Queries and insights generated</p>
        </div>
        <div className="flex gap-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-violet-500" />
            <span className="text-xs text-white/50">Queries</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-pink-500" />
            <span className="text-xs text-white/50">Insights</span>
          </div>
        </div>
      </div>
      
      <div className="flex items-end justify-between h-48 gap-2">
        {data.map((day, i) => (
          <div key={day.day} className="flex-1 flex flex-col items-center gap-2">
            <motion.div 
              initial={{ height: 0 }}
              animate={{ height: "100%" }}
              transition={{ delay: 0.3 + i * 0.05, duration: 0.5 }}
              className="w-full flex flex-col justify-end gap-1"
            >
              <div 
                className="w-full bg-gradient-to-t from-violet-600/50 to-violet-500/30 rounded-t-lg relative group"
                style={{ height: `${(day.queries / maxQueries) * 100}%` }}
              >
                <div className="absolute -top-8 left-1/2 -translate-x-1/2 px-2 py-1 bg-background/90 rounded text-xs text-white opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                  {day.queries.toLocaleString()} queries
                </div>
              </div>
              <div 
                className="w-1/2 bg-gradient-to-t from-pink-600/50 to-pink-500/30 rounded-t-lg"
                style={{ height: `${(day.insights / maxQueries) * 80}%` }}
              />
            </motion.div>
            <span className="text-xs text-white/40">{day.day}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

function TopQueries({ data }: { data: QueryData[] }) {
  if (data.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="p-6 rounded-2xl bg-white/[0.02] border border-white/[0.08]"
      >
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-white">Top Queries</h3>
        </div>
        <p className="text-sm text-white/50 text-center py-4">No query data yet</p>
      </motion.div>
    );
  }
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="p-6 rounded-2xl bg-white/[0.02] border border-white/[0.08]"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Top Queries</h3>
        <span className="text-xs text-violet-400 cursor-pointer hover:text-violet-300">View all →</span>
      </div>
      
      <div className="space-y-3">
        {data.map((item, i) => (
          <motion.div
            key={item.query}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 + i * 0.05 }}
            className="flex items-center gap-4 p-3 rounded-xl hover:bg-white/[0.02] transition-colors"
          >
            <span className="text-sm text-white/30 font-medium w-5">{i + 1}</span>
            <div className="flex-1 min-w-0">
              <p className="text-sm text-white/70 truncate">{item.query}</p>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-xs text-white/40">{item.count}</span>
              <span className={cn(
                "text-xs px-2 py-0.5 rounded-full",
                item.trend.startsWith("+")
                  ? "bg-emerald-500/10 text-emerald-400"
                  : "bg-red-500/10 text-red-400"
              )}>
                {item.trend}
              </span>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}

function DocumentBreakdown({ data }: { data: DocTypeData[] }) {
  const maxCount = Math.max(...data.map((d: DocTypeData) => d.count), 1);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.4 }}
      className="p-6 rounded-2xl bg-white/[0.02] border border-white/[0.08]"
    >
      <h3 className="text-lg font-semibold text-white mb-4">Document Types</h3>
      
      <div className="space-y-4">
        {data.map((doc, i) => (
          <div key={doc.type}>
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <div className={cn("w-3 h-3 rounded-full", doc.color)} />
                <span className="text-sm text-white/70">{doc.type}</span>
              </div>
              <span className="text-sm text-white/40">{doc.count} files</span>
            </div>
            <div className="h-2 bg-white/[0.05] rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${doc.percentage}%` }}
                transition={{ delay: 0.5 + i * 0.1, duration: 0.5 }}
                className={cn("h-full rounded-full", doc.color)}
              />
            </div>
            <span className="text-xs text-white/30 mt-1 block">{doc.percentage}%</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

function UsageCalendar() {
  const days = Array.from({ length: 28 }, (_, i) => {
    const intensity = Math.random();
    return { day: i + 1, intensity };
  });
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="p-6 rounded-2xl bg-white/[0.02] border border-white/[0.08]"
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Activity Calendar</h3>
        <span className="text-xs text-white/40">Last 4 weeks</span>
      </div>
      
      <div className="grid grid-cols-7 gap-1.5">
        {days.map((day, i) => (
          <motion.div
            key={day.day}
            initial={{ opacity: 0, scale: 0 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6 + i * 0.01 }}
            className={cn(
              "aspect-square rounded-md",
              day.intensity > 0.7 
                ? "bg-violet-500" 
                : day.intensity > 0.4 
                ? "bg-violet-500/50" 
                : day.intensity > 0.1 
                ? "bg-violet-500/20" 
                : "bg-white/[0.05]"
            )}
            title={`${day.day} users: ${Math.floor(day.intensity * 100)}`}
          />
        ))}
      </div>
      
      <div className="flex items-center justify-end gap-2 mt-4">
        <span className="text-xs text-white/30">Less</span>
        <div className="w-3 h-3 rounded bg-white/[0.05]" />
        <div className="w-3 h-3 rounded bg-violet-500/20" />
        <div className="w-3 h-3 rounded bg-violet-500/50" />
        <div className="w-3 h-3 rounded bg-violet-500" />
        <span className="text-xs text-white/30">More</span>
      </div>
    </motion.div>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function AnalyticsPage() {
  const [featureUsage, setFeatureUsage] = useState<FeatureUsageItem[]>([]);
  const [pageViews, setPageViews] = useState<PageViewItem[]>([]);
  const [dauData, setDauData] = useState<DAUItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState<"7d" | "30d" | "90d">("7d");

  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      const days = period === "7d" ? 7 : period === "30d" ? 30 : 90;
      
      const [usage, views, dau] = await Promise.all([
        getFeatureUsage(days).catch(() => ({ items: [], total: 0 })),
        getPageViews(days).catch(() => ({ items: [], total: 0 })),
        getDAUStats(days).catch(() => ({ items: [] })),
      ]);
      
      setFeatureUsage(usage.items);
      setPageViews(views.items);
      setDauData(dau.items);
    } catch (error) {
      console.error("Failed to fetch analytics:", error);
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  // Build stats from feature usage data
  const totalActions = featureUsage.reduce((sum, item) => sum + item.count, 0);
  const stats = [
    { 
      label: "Total Actions", 
      value: totalActions.toLocaleString(), 
      change: 0, 
      icon: MessageSquare,
      color: "from-violet-500/20 to-purple-500/20",
      accent: "text-violet-400"
    },
    { 
      label: "Page Views", 
      value: pageViews.reduce((sum, p) => sum + p.views, 0).toLocaleString(), 
      change: 0, 
      icon: FileText,
      color: "from-blue-500/20 to-cyan-500/20",
      accent: "text-blue-400"
    },
    { 
      label: "Active Days", 
      value: dauData.length.toString(), 
      change: 0, 
      icon: Users,
      color: "from-emerald-500/20 to-teal-500/20",
      accent: "text-emerald-400"
    },
    { 
      label: "Features Used", 
      value: new Set(featureUsage.map(f => f.feature)).size.toString(), 
      change: 0, 
      icon: Brain,
      color: "from-pink-500/20 to-rose-500/20",
      accent: "text-pink-400"
    },
  ];

  // Build weekly data from DAU
  const weeklyData = dauData.length > 0 ? dauData.map(item => ({
    day: new Date(item.date).toLocaleDateString("en-US", { weekday: "short" }),
    queries: item.active_users * 10, // Estimate queries from active users
    insights: Math.floor(item.active_users * 2.5), // Estimate insights
  })) : [
    { day: "Mon", queries: 0, insights: 0 },
    { day: "Tue", queries: 0, insights: 0 },
    { day: "Wed", queries: 0, insights: 0 },
    { day: "Thu", queries: 0, insights: 0 },
    { day: "Fri", queries: 0, insights: 0 },
    { day: "Sat", queries: 0, insights: 0 },
    { day: "Sun", queries: 0, insights: 0 },
  ];

  // Build top queries from feature usage
  const topQueries = featureUsage
    .filter(f => f.feature === "search" || f.action === "query")
    .slice(0, 5)
    .map((item, i) => ({
      query: `${item.feature}: ${item.action}`,
      count: item.count,
      trend: "+0%",
    }));

  // Build document types from page views (placeholder)
  const documentTypes = pageViews.slice(0, 5).map((page, i) => ({
    type: page.path.split("/").pop() || "other",
    count: page.views,
    percentage: pageViews.length > 0 ? Math.round((page.views / pageViews.reduce((s, p) => s + p.views, 0)) * 100) : 0,
    color: i === 0 ? "bg-red-500" : i === 1 ? "bg-blue-500" : i === 2 ? "bg-emerald-500" : i === 3 ? "bg-amber-500" : "bg-white/20",
  }));

  if (loading) {
    return (
      <DashboardLayout>
        <div className="min-h-screen flex items-center justify-center">
          <Loader2 className="w-8 h-8 animate-spin text-violet-400" />
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="min-h-screen p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-2 text-sm text-white/40 mb-2">
              <BarChart3 className="w-4 h-4" />
              <span>Analytics</span>
            </div>
            <h1 className="text-2xl font-bold text-white">Dashboard Analytics</h1>
          </div>
          
          <div className="flex items-center gap-3">
            <select 
              value={period}
              onChange={(e) => setPeriod(e.target.value as any)}
              className={cn(
                "px-4 py-2 rounded-xl text-sm",
                "bg-white/[0.03] border border-white/[0.08]",
                "text-white/70",
                "focus:outline-none focus:border-violet-500/50"
              )}
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
            </select>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {stats.map((stat, i) => (
            <StatCard key={stat.label} stat={stat} index={i} />
          ))}
        </div>

        {/* Charts */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2">
            <WeeklyChart data={weeklyData} />
          </div>
          <div>
            <DocumentBreakdown data={documentTypes} />
          </div>
        </div>

        {/* Bottom */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <TopQueries data={topQueries} />
          <UsageCalendar />
        </div>
      </div>
    </DashboardLayout>
  );
}
