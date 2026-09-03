"use client";

import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { 
  listMemories, 
  getMemoryStats, 
  deleteMemory,
  searchMemories,
  type Memory,
  type MemoryStats 
} from "@/lib/api/memories";
import { 
  Brain, 
  Search, 
  Filter, 
  Plus, 
  Trash2, 
  Link2, 
  Calendar, 
  Sparkles,
  X,
  ChevronRight,
  ExternalLink,
  Clock,
  TrendingUp
} from "lucide-react";

// ============================================================================
// DESIGN TOKENS - Consistent with Orivory's Nebulous Precision
// ============================================================================

const DESIGN = {
  colors: {
    bg: "bg-background",
    surface: "bg-white/[0.03]",
    surfaceHover: "hover:bg-white/[0.06]",
    border: "border-white/[0.08]",
    text: {
      primary: "text-white",
      secondary: "text-white/60",
      muted: "text-white/40",
    },
    accent: {
      violet: "text-violet-400",
      pink: "text-pink-400",
      gradient: "bg-gradient-to-r from-violet-400 to-pink-400",
    },
    type: {
      entity: { bg: "bg-violet-500/10", border: "border-violet-500/30", text: "text-violet-400" },
      relationship: { bg: "bg-pink-500/10", border: "border-pink-500/30", text: "text-pink-400" },
      observation: { bg: "bg-emerald-500/10", border: "border-emerald-500/30", text: "text-emerald-400" },
      concept: { bg: "bg-amber-500/10", border: "border-amber-500/30", text: "text-amber-400" },
    },
  },
  spacing: {
    xs: "p-2",
    sm: "p-3",
    md: "p-4",
    lg: "p-6",
  },
  radius: {
    sm: "rounded-lg",
    md: "rounded-xl",
    lg: "rounded-2xl",
  },
  transition: "transition-all duration-300 ease-out",
};

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface MemoryDashboardProps {
  className?: string;
  workspaceId?: string;
}

type MemoryType = Memory["type"];

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

/**
 * Memory type badge
 */
function TypeBadge({ type }: { type: MemoryType }) {
  const styles = DESIGN.colors.type[type];
  
  return (
    <span className={cn(
      "inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider rounded-full",
      styles.bg,
      styles.border,
      styles.text
    )}>
      <span className="w-1 h-1 rounded-full bg-current" />
      {type}
    </span>
  );
}

/**
 * Stats card for the dashboard
 */
function StatCard({ 
  title, 
  value, 
  icon: Icon,
  trend 
}: { 
  title: string; 
  value: number | string; 
  icon: any;
  trend?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "p-4 rounded-xl",
        "bg-white/[0.03] border border-white/[0.08]",
        "hover:border-white/[0.15]",
        DESIGN.transition
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className={cn("text-xs text-white/40 mb-1", DESIGN.colors.text.muted)}>
            {title}
          </p>
          <p className={cn("text-2xl font-bold", DESIGN.colors.text.primary)}>
            {value}
          </p>
          {trend !== undefined && (
            <div className={cn(
              "flex items-center gap-1 mt-1 text-xs",
              trend >= 0 ? "text-emerald-400" : "text-red-400"
            )}>
              <TrendingUp className={cn("w-3 h-3", trend < 0 && "rotate-180")} />
              <span>{Math.abs(trend)}%</span>
            </div>
          )}
        </div>
        <div className={cn(
          "w-10 h-10 rounded-lg",
          "bg-white/[0.05] border border-white/[0.1]",
          "flex items-center justify-center"
        )}>
          <Icon className="w-5 h-5 text-violet-400" />
        </div>
      </div>
    </motion.div>
  );
}

/**
 * Memory card component
 */
function MemoryCard({ 
  memory, 
  onDelete,
  onClick 
}: { 
  memory: Memory; 
  onDelete: (id: string) => void;
  onClick: (memory: Memory) => void;
}) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      whileHover={{ y: -2 }}
      onClick={() => onClick(memory)}
      className={cn(
        "group p-4 rounded-xl cursor-pointer",
        "bg-white/[0.02] border border-white/[0.08]",
        "hover:border-violet-500/30 hover:bg-violet-500/5",
        DESIGN.transition
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <TypeBadge type={memory.type} />
          </div>
          <h3 className={cn(
            "text-sm font-medium truncate",
            DESIGN.colors.text.primary
          )}>
            {memory.name}
          </h3>
        </div>
        
        <motion.button
          whileHover={{ scale: 1.1 }}
          onClick={(e) => {
            e.stopPropagation();
            onDelete(memory.id);
          }}
          className={cn(
            "p-1.5 rounded-md opacity-0 group-hover:opacity-100",
            "text-white/40 hover:text-red-400",
            "hover:bg-red-500/10",
            "transition-all"
          )}
        >
          <Trash2 className="w-4 h-4" />
        </motion.button>
      </div>

      {/* Description */}
      {memory.description && (
        <p className={cn(
          "text-xs text-white/50 line-clamp-2 mb-3",
          DESIGN.colors.text.secondary
        )}>
          {memory.description}
        </p>
      )}

      {/* Meta info */}
      <div className="flex items-center gap-3 text-[10px] text-white/30">
        <div className="flex items-center gap-1">
          <Clock className="w-3 h-3" />
          <span>{new Date(memory.updated_at).toLocaleDateString()}</span>
        </div>
        {memory.access_count > 0 && (
          <div className="flex items-center gap-1">
            <Sparkles className="w-3 h-3" />
            <span>{memory.access_count} views</span>
          </div>
        )}
      </div>

      {/* Tags */}
      {memory.tags && memory.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3">
          {memory.tags.slice(0, 3).map((tag) => (
            <span
              key={tag}
              className={cn(
                "px-2 py-0.5 text-[10px]",
                "bg-white/[0.03] border border-white/[0.05]",
                "text-white/40 rounded-full"
              )}
            >
              #{tag}
            </span>
          ))}
          {memory.tags.length > 3 && (
            <span className="text-[10px] text-white/30">
              +{memory.tags.length - 3}
            </span>
          )}
        </div>
      )}
    </motion.div>
  );
}

/**
 * Search and filter bar
 */
function SearchBar({ 
  onSearch, 
  onFilterChange,
  activeFilter 
}: { 
  onSearch: (query: string) => void;
  onFilterChange: (filter: MemoryType | "all") => void;
  activeFilter: MemoryType | "all";
}) {
  const [query, setQuery] = useState("");
  
  const handleSearch = (value: string) => {
    setQuery(value);
    onSearch(value);
  };

  const filters: { value: MemoryType | "all"; label: string }[] = [
    { value: "all", label: "All" },
    { value: "entity", label: "Entities" },
    { value: "relationship", label: "Relations" },
    { value: "observation", label: "Observations" },
    { value: "concept", label: "Concepts" },
  ];

  return (
    <div className="space-y-3">
      {/* Search input */}
      <div className={cn(
        "relative rounded-xl border",
        "bg-white/[0.02] border-white/[0.08]",
        "focus-within:border-violet-500/40",
        "transition-all"
      )}>
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
        <input
          type="text"
          value={query}
          onChange={(e) => handleSearch(e.target.value)}
          placeholder="Search memories..."
          className={cn(
            "w-full pl-11 pr-4 py-3",
            "bg-transparent",
            "text-white placeholder:text-white/30 text-sm",
            "focus:outline-none"
          )}
        />
      </div>

      {/* Filter chips */}
      <div className="flex flex-wrap gap-2">
        {filters.map((filter) => (
          <motion.button
            key={filter.value}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => onFilterChange(filter.value)}
            className={cn(
              "px-3 py-1.5 text-xs rounded-full",
              "transition-all duration-200",
              activeFilter === filter.value
                ? "bg-violet-500/20 border border-violet-500/40 text-violet-300"
                : "bg-white/[0.03] border border-white/[0.08] text-white/50 hover:text-white/70 hover:border-white/[0.15]"
            )}
          >
            {filter.label}
          </motion.button>
        ))}
      </div>
    </div>
  );
}

/**
 * Memory detail modal
 */
function MemoryDetail({ 
  memory, 
  onClose 
}: { 
  memory: Memory; 
  onClose: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
    >
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95, y: 20 }}
        className={cn(
          "relative w-full max-w-2xl max-h-[80vh] overflow-hidden",
          "rounded-2xl",
          "bg-background/95 backdrop-blur-xl",
          "border border-white/[0.1]",
          "shadow-2xl shadow-black/50"
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-white/[0.05]">
          <div className="flex items-center gap-3">
            <div className={cn(
              "w-10 h-10 rounded-xl",
              "bg-gradient-to-br from-violet-500/20 to-pink-500/20",
              "border border-violet-500/30",
              "flex items-center justify-center"
            )}>
              <Brain className="w-5 h-5 text-violet-400" />
            </div>
            <div>
              <TypeBadge type={memory.type} />
              <h2 className={cn("text-lg font-semibold mt-1", DESIGN.colors.text.primary)}>
                {memory.name}
              </h2>
            </div>
          </div>
          
          <button
            onClick={onClose}
            className={cn(
              "p-2 rounded-lg",
              "text-white/40 hover:text-white/70",
              "hover:bg-white/[0.05]",
              "transition-colors"
            )}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(80vh-140px)]">
          {memory.description && (
            <div className="mb-6">
              <h3 className={cn("text-xs uppercase tracking-wider text-white/40 mb-2")}>
                Description
              </h3>
              <p className={cn("text-sm leading-relaxed", DESIGN.colors.text.secondary)}>
                {memory.description}
              </p>
            </div>
          )}

          {memory.content && (
            <div className="mb-6">
              <h3 className={cn("text-xs uppercase tracking-wider text-white/40 mb-2")}>
                Content
              </h3>
              <div className={cn(
                "p-4 rounded-lg",
                "bg-white/[0.02] border border-white/[0.05]"
              )}>
                <p className={cn("text-sm leading-relaxed whitespace-pre-wrap", DESIGN.colors.text.secondary)}>
                  {memory.content}
                </p>
              </div>
            </div>
          )}

          {/* Meta */}
          <div className="grid grid-cols-2 gap-4">
            <div className={cn(
              "p-3 rounded-lg",
              "bg-white/[0.02] border border-white/[0.05]"
            )}>
              <p className={cn("text-[10px] uppercase tracking-wider text-white/40 mb-1")}>
                Created
              </p>
              <p className={cn("text-sm", DESIGN.colors.text.secondary)}>
                {new Date(memory.created_at).toLocaleDateString()}
              </p>
            </div>
            <div className={cn(
              "p-3 rounded-lg",
              "bg-white/[0.02] border border-white/[0.05]"
            )}>
              <p className={cn("text-[10px] uppercase tracking-wider text-white/40 mb-1")}>
                Access Count
              </p>
              <p className={cn("text-sm", DESIGN.colors.text.secondary)}>
                {memory.access_count} views
              </p>
            </div>
          </div>

          {/* Tags */}
          {memory.tags && memory.tags.length > 0 && (
            <div className="mt-6">
              <h3 className={cn("text-xs uppercase tracking-wider text-white/40 mb-2")}>
                Tags
              </h3>
              <div className="flex flex-wrap gap-2">
                {memory.tags.map((tag) => (
                  <span
                    key={tag}
                    className={cn(
                      "px-3 py-1 text-xs",
                      "bg-white/[0.03] border border-white/[0.08]",
                      "text-white/60 rounded-full"
                    )}
                  >
                    #{tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Source documents */}
          {memory.source_document_ids && memory.source_document_ids.length > 0 && (
            <div className="mt-6">
              <h3 className={cn("text-xs uppercase tracking-wider text-white/40 mb-2")}>
                Source Documents
              </h3>
              <div className="space-y-2">
                {memory.source_document_ids.map((docId) => (
                  <div
                    key={docId}
                    className={cn(
                      "flex items-center gap-2 p-2 rounded-lg",
                      "bg-white/[0.02] border border-white/[0.05]",
                      "text-sm text-white/50 cursor-pointer",
                      "hover:bg-white/[0.05] hover:text-white/70"
                    )}
                  >
                    <ExternalLink className="w-4 h-4" />
                    <span className="flex-1">{docId}</span>
                    <ChevronRight className="w-4 h-4" />
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function MemoryDashboard({ className, workspaceId }: MemoryDashboardProps) {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<MemoryType | "all">("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedMemory, setSelectedMemory] = useState<Memory | null>(null);

  // Fetch memories
  const fetchMemories = useCallback(async () => {
    try {
      setLoading(true);
      const params: any = {};
      
      if (filter !== "all") {
        params.type = filter;
      }
      
      if (searchQuery) {
        const results = await searchMemories(searchQuery);
        setMemories(results);
        return;
      }
      
      const data = await listMemories(params);
      setMemories(data);
    } catch (error) {
      console.error("Failed to fetch memories:", error);
    } finally {
      setLoading(false);
    }
  }, [filter, searchQuery]);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const data = await getMemoryStats();
      setStats(data);
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  }, []);

  useEffect(() => {
    fetchMemories();
    fetchStats();
  }, [fetchMemories, fetchStats]);

  // Handle search
  const handleSearch = useCallback((query: string) => {
    setSearchQuery(query);
  }, []);

  // Handle delete
  const handleDelete = async (id: string) => {
    if (!confirm("Are you sure you want to delete this memory?")) return;
    
    try {
      await deleteMemory(id);
      setMemories((prev) => prev.filter((m) => m.id !== id));
      fetchStats();
    } catch (error) {
      console.error("Failed to delete memory:", error);
    }
  };

  return (
    <div className={cn("flex flex-col h-full", className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className={cn(
            "w-10 h-10 rounded-xl",
            "bg-gradient-to-br from-violet-500/20 to-pink-500/20",
            "border border-violet-500/30",
            "flex items-center justify-center"
          )}>
            <Brain className="w-5 h-5 text-violet-400" />
          </div>
          <div>
            <h2 className={cn("text-lg font-semibold", DESIGN.colors.text.primary)}>
              Memory Graph
            </h2>
            <p className={cn("text-xs", DESIGN.colors.text.muted)}>
              Entities, relationships, and concepts
            </p>
          </div>
        </div>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <StatCard title="Total" value={stats.total_memories} icon={Brain} />
          <StatCard title="Entities" value={stats.entities} icon={Sparkles} />
          <StatCard title="Relations" value={stats.relationships} icon={Link2} />
          <StatCard title="Concepts" value={stats.concepts} icon={Calendar} />
        </div>
      )}

      {/* Search and filter */}
      <SearchBar
        onSearch={handleSearch}
        onFilterChange={setFilter}
        activeFilter={filter}
      />

      {/* Memory list */}
      <div className="flex-1 mt-6 overflow-y-auto">
        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div
                key={i}
                className={cn(
                  "h-32 rounded-xl",
                  "bg-white/[0.02] border border-white/[0.05]",
                  "animate-pulse"
                )}
              />
            ))}
          </div>
        ) : memories.length === 0 ? (
          <div className="text-center py-12">
            <div className={cn(
              "w-16 h-16 mx-auto mb-4 rounded-2xl",
              "bg-white/[0.03] border border-white/[0.08]",
              "flex items-center justify-center"
            )}>
              <Brain className="w-8 h-8 text-white/20" />
            </div>
            <p className={cn("text-sm font-medium mb-1", DESIGN.colors.text.primary)}>
              No memories yet
            </p>
            <p className={cn("text-xs", DESIGN.colors.text.muted)}>
              Memories are automatically extracted from your documents
            </p>
          </div>
        ) : (
          <motion.div 
            layout
            className="grid gap-3 md:grid-cols-2"
          >
            <AnimatePresence mode="popLayout">
              {memories.map((memory) => (
                <MemoryCard
                  key={memory.id}
                  memory={memory}
                  onDelete={handleDelete}
                  onClick={setSelectedMemory}
                />
              ))}
            </AnimatePresence>
          </motion.div>
        )}
      </div>

      {/* Detail modal */}
      <AnimatePresence>
        {selectedMemory && (
          <MemoryDetail
            memory={selectedMemory}
            onClose={() => setSelectedMemory(null)}
          />
        )}
      </AnimatePresence>
    </div>
  );
}

export default MemoryDashboard;
