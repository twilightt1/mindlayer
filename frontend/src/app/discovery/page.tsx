"use client";

import { useState, useCallback } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { DashboardLayout } from "@/components/layout";
import { 
  Sparkles, 
  Brain,
  Lightbulb,
  TrendingUp,
  Link2,
  RefreshCw,
  Play,
  Loader2
} from "lucide-react";

// ============================================================================
// TYPES
// ============================================================================

interface Insight {
  id: string;
  title: string;
  description: string;
  type: "connection" | "pattern" | "anomaly" | "summary";
  confidence: number;
}

interface DiscoveryState {
  isRunning: boolean;
  progress: number;
  message: string;
  insights: Insight[];
}

// ============================================================================
// MOCK DATA
// ============================================================================

const MOCK_INSIGHTS: Insight[] = [
  {
    id: "1",
    title: "Meeting notes reveal missed deadlines",
    description: "Multiple project meetings show a pattern of action items without clear owners or deadlines.",
    type: "anomaly",
    confidence: 0.87,
  },
  {
    id: "2",
    title: "Customer feedback connects to feature requests",
    description: "Support tickets and feature requests show strong correlation with recent product updates.",
    type: "connection",
    confidence: 0.92,
  },
  {
    id: "3",
    title: "Weekly report pattern identified",
    description: "Your team consistently generates project status reports every Friday at 4pm.",
    type: "pattern",
    confidence: 0.78,
  },
  {
    id: "4",
    title: "Budget data suggests Q4 adjustment",
    description: "Historical spending patterns indicate you may need to adjust Q4 allocations.",
    type: "anomaly",
    confidence: 0.65,
  },
];

// ============================================================================
// COMPONENTS
// ============================================================================

function DiscoveryCard({ insight }: { insight: Insight }) {
  const icons = {
    connection: Link2,
    pattern: TrendingUp,
    anomaly: Sparkles,
    summary: Lightbulb,
  };
  
  const colors = {
    connection: "from-violet-500 to-purple-500",
    pattern: "from-blue-500 to-cyan-500",
    anomaly: "from-pink-500 to-rose-500",
    summary: "from-amber-500 to-orange-500",
  };

  const Icon = icons[insight.type];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "p-5 rounded-2xl",
        "bg-white/[0.02] border border-white/[0.08]",
        "hover:border-white/[0.15] hover:bg-white/[0.03]",
        "transition-all duration-300"
      )}
    >
      <div className="flex items-start gap-4">
        <div className={cn(
          "w-10 h-10 rounded-xl flex items-center justify-center",
          "bg-gradient-to-br shadow-lg",
          colors[insight.type]
        )}>
          <Icon className="w-5 h-5 text-white" />
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-white mb-1">
            {insight.title}
          </h3>
          <p className="text-xs text-white/50 mb-3 line-clamp-2">
            {insight.description}
          </p>
          
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <div className="w-16 h-1.5 bg-white/[0.1] rounded-full overflow-hidden">
                <div 
                  className="h-full bg-gradient-to-r from-violet-500 to-pink-500 rounded-full"
                  style={{ width: `${insight.confidence * 100}%` }}
                />
              </div>
              <span className="text-xs text-white/30">
                {Math.round(insight.confidence * 100)}%
              </span>
            </div>
            
            <span className={cn(
              "px-2 py-0.5 text-[10px] uppercase tracking-wider rounded-full capitalize",
              insight.type === "connection" && "bg-violet-500/20 text-violet-400",
              insight.type === "pattern" && "bg-blue-500/20 text-blue-400",
              insight.type === "anomaly" && "bg-pink-500/20 text-pink-400",
              insight.type === "summary" && "bg-amber-500/20 text-amber-400",
            )}>
              {insight.type}
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

function ProgressIndicator({ progress, message }: { progress: number; message: string }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="p-6 rounded-2xl bg-white/[0.02] border border-white/[0.08]"
    >
      <div className="flex items-center gap-4 mb-4">
        <div className="relative">
          <Loader2 className="w-8 h-8 text-violet-400 animate-spin" />
        </div>
        <div>
          <p className="text-sm font-medium text-white">Analyzing your knowledge base</p>
          <p className="text-xs text-white/40">{message}</p>
        </div>
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-white/50">Progress</span>
          <span className="text-violet-400">{progress}%</span>
        </div>
        <div className="w-full h-2 bg-white/[0.05] rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.3 }}
            className="h-full bg-gradient-to-r from-violet-500 to-pink-500 rounded-full"
          />
        </div>
      </div>
    </motion.div>
  );
}

function DiscoveryTypes() {
  const types = [
    { 
      id: "connections", 
      label: "Connections", 
      description: "Find relationships between documents",
      icon: Link2,
      color: "from-violet-500 to-purple-500"
    },
    { 
      id: "patterns", 
      label: "Patterns", 
      description: "Identify recurring themes and behaviors",
      icon: TrendingUp,
      color: "from-blue-500 to-cyan-500"
    },
    { 
      id: "anomalies", 
      label: "Anomalies", 
      description: "Detect outliers and unusual data points",
      icon: Sparkles,
      color: "from-pink-500 to-rose-500"
    },
    { 
      id: "summaries", 
      label: "Summaries", 
      description: "Generate concise overviews",
      icon: Lightbulb,
      color: "from-amber-500 to-orange-500"
    },
  ];

  const [selected, setSelected] = useState<string[]>(["connections", "patterns", "anomalies"]);

  const toggle = (id: string) => {
    setSelected((prev) => 
      prev.includes(id) 
        ? prev.filter((x) => x !== id)
        : [...prev, id]
    );
  };

  return (
    <div className="grid grid-cols-2 gap-3">
      {types.map((type) => {
        const isActive = selected.includes(type.id);
        return (
          <motion.button
            key={type.id}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => toggle(type.id)}
            className={cn(
              "flex items-center gap-3 p-4 rounded-xl text-left",
              "border transition-all duration-200",
              isActive
                ? "bg-white/[0.05] border-white/[0.15]"
                : "bg-white/[0.02] border-white/[0.08] opacity-50"
            )}
          >
            <div className={cn(
              "w-10 h-10 rounded-lg flex items-center justify-center",
              "bg-gradient-to-br shadow-lg",
              type.color,
              !isActive && "grayscale opacity-50"
            )}>
              <type.icon className="w-5 h-5 text-white" />
            </div>
            <div>
              <p className="text-sm font-medium text-white">{type.label}</p>
              <p className="text-xs text-white/40">{type.description}</p>
            </div>
          </motion.button>
        );
      })}
    </div>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function DiscoveryPage() {
  const [state, setState] = useState<DiscoveryState>({
    isRunning: false,
    progress: 0,
    message: "Initializing...",
    insights: MOCK_INSIGHTS,
  });

  const runDiscovery = useCallback(() => {
    setState((prev) => ({
      ...prev,
      isRunning: true,
      progress: 0,
      message: "Scanning documents...",
      insights: [],
    }));

    const messages = [
      { progress: 20, message: "Scanning 127 documents..." },
      { progress: 40, message: "Extracting entities..." },
      { progress: 60, message: "Finding connections..." },
      { progress: 80, message: "Analyzing patterns..." },
      { progress: 100, message: "Generating insights..." },
    ];

    let index = 0;
    const interval = setInterval(() => {
      if (index < messages.length) {
        setState((prev) => ({
          ...prev,
          progress: messages[index].progress,
          message: messages[index].message,
        }));
        index++;
      } else {
        clearInterval(interval);
        setState((prev) => ({
          ...prev,
          isRunning: false,
          message: "Complete!",
          insights: MOCK_INSIGHTS,
        }));
      }
    }, 1000);
  }, []);

  return (
    <DashboardLayout>
      <div className="min-h-screen p-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <div className="flex items-center gap-2 text-sm text-white/40 mb-2">
              <Brain className="w-4 h-4 text-violet-400" />
              <span>Discovery</span>
            </div>
            <h1 className="text-2xl font-bold text-white">Proactive Discovery</h1>
          </div>
          
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={runDiscovery}
            disabled={state.isRunning}
            className={cn(
              "flex items-center gap-2 px-5 py-2.5 rounded-xl",
              "bg-gradient-to-r from-violet-600 to-purple-600",
              "text-white font-medium text-sm",
              "shadow-lg shadow-violet-500/20",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-all"
            )}
          >
            {state.isRunning ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Play className="w-4 h-4" />
                Run Discovery
              </>
            )}
          </motion.button>
        </div>

        {/* Discovery types */}
        <div className="mb-8">
          <h2 className="text-sm font-semibold text-white mb-4">Discovery Types</h2>
          <DiscoveryTypes />
        </div>

        {/* Progress or results */}
        {state.isRunning ? (
          <ProgressIndicator progress={state.progress} message={state.message} />
        ) : state.insights.length > 0 ? (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-semibold text-white">
                Found {state.insights.length} Insights
              </h2>
              <button className="flex items-center gap-2 text-xs text-violet-400 hover:text-violet-300">
                <RefreshCw className="w-3 h-3" />
                Refresh
              </button>
            </div>
            
            <div className="grid gap-4 md:grid-cols-2">
              {state.insights.map((insight) => (
                <DiscoveryCard key={insight.id} insight={insight} />
              ))}
            </div>
          </div>
        ) : (
          <div className="text-center py-20 rounded-2xl bg-white/[0.02] border border-white/[0.08]">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-violet-500/20 to-pink-500/20 border border-violet-500/30 flex items-center justify-center">
              <Sparkles className="w-8 h-8 text-violet-400" />
            </div>
            <h3 className="text-lg font-semibold text-white mb-2">Ready to Discover</h3>
            <p className="text-sm text-white/50 mb-6 max-w-md mx-auto">
              Run discovery to analyze your knowledge base and find hidden connections, patterns, and anomalies.
            </p>
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={runDiscovery}
              className={cn(
                "inline-flex items-center gap-2 px-6 py-3 rounded-xl",
                "bg-gradient-to-r from-violet-600 to-purple-600",
                "text-white font-medium",
                "shadow-lg shadow-violet-500/20",
                "transition-all"
              )}
            >
              <Play className="w-4 h-4" />
              Start Discovery
            </motion.button>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
