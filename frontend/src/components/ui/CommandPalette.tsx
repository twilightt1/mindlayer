"use client";

import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useRouter } from "next/navigation";
import { 
  Search,
  Home,
  MessageSquare,
  Brain,
  FileText,
  Sparkles,
  BarChart3,
  Settings,
  Plus,
  Command,
  ArrowRight,
  Moon,
  Sun,
  Keyboard
} from "lucide-react";
import { cn } from "@/lib/utils";

// ============================================================================
// TYPES
// ============================================================================

interface Command {
  id: string;
  label: string;
  description?: string;
  icon: React.ElementType;
  action: () => void;
  shortcut?: string;
  category: "navigation" | "action" | "theme";
}

// ============================================================================
// COMMANDS
// ============================================================================

const COMMANDS: Command[] = [
  {
    id: "dashboard",
    label: "Go to Dashboard",
    icon: Home,
    action: () => {},
    category: "navigation",
  },
  {
    id: "chat",
    label: "New Chat",
    icon: MessageSquare,
    action: () => {},
    category: "navigation",
  },
  {
    id: "memories",
    label: "Go to Memories",
    icon: Brain,
    action: () => {},
    category: "navigation",
  },
  {
    id: "documents",
    label: "Go to Documents",
    icon: FileText,
    action: () => {},
    category: "navigation",
  },
  {
    id: "insights",
    label: "Go to Insights",
    icon: Sparkles,
    action: () => {},
    category: "navigation",
  },
  {
    id: "analytics",
    label: "Go to Analytics",
    icon: BarChart3,
    action: () => {},
    category: "navigation",
  },
  {
    id: "settings",
    label: "Go to Settings",
    icon: Settings,
    action: () => {},
    category: "navigation",
  },
];

// ============================================================================
// COMPONENT
// ============================================================================

export function CommandPalette() {
  const router = useRouter();
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  // Filter commands based on query
  const filteredCommands = COMMANDS.filter((cmd) =>
    cmd.label.toLowerCase().includes(query.toLowerCase())
  );

  // Open palette with keyboard shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Open palette
      if ((e.metaKey || e.ctrlKey) && e.key === "k") {
        e.preventDefault();
        setIsOpen(true);
      }
      
      // Close palette
      if (e.key === "Escape") {
        setIsOpen(false);
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, []);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setQuery("");
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Handle keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      switch (e.key) {
        case "ArrowDown":
          e.preventDefault();
          setSelectedIndex((i) => Math.min(i + 1, filteredCommands.length - 1));
          break;
        case "ArrowUp":
          e.preventDefault();
          setSelectedIndex((i) => Math.max(i - 1, 0));
          break;
        case "Enter":
          e.preventDefault();
          if (filteredCommands[selectedIndex]) {
            executeCommand(filteredCommands[selectedIndex]);
          }
          break;
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, filteredCommands, selectedIndex]);

  const executeCommand = (command: Command) => {
    setIsOpen(false);
    
    // Navigate based on command
    switch (command.id) {
      case "dashboard":
        router.push("/dashboard");
        break;
      case "chat":
        router.push("/chat");
        break;
      case "memories":
        router.push("/memories");
        break;
      case "documents":
        router.push("/documents");
        break;
      case "insights":
        router.push("/insights");
        break;
      case "analytics":
        router.push("/analytics");
        break;
      case "settings":
        router.push("/settings");
        break;
    }
  };

  return (
    <>
      {/* Keyboard shortcut hint */}
      <button
        onClick={() => setIsOpen(true)}
        className={cn(
          "hidden md:flex items-center gap-2 px-3 py-1.5",
          "rounded-lg bg-white/5 border border-white/10",
          "text-xs text-white/50 hover:text-white/70",
          "transition-colors"
        )}
      >
        <Keyboard className="w-3 h-3" />
        <span>⌘K</span>
      </button>

      {/* Palette */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
          >
            {/* Backdrop */}
            <div 
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              onClick={() => setIsOpen(false)}
            />

            {/* Palette */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -20 }}
              className="relative w-full max-w-lg mx-4 bg-background/95 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl overflow-hidden"
            >
              {/* Search input */}
              <div className="flex items-center gap-3 px-4 py-4 border-b border-white/5">
                <Search className="w-5 h-5 text-white/40" />
                <input
                  ref={inputRef}
                  type="text"
                  value={query}
                  onChange={(e) => {
                    setQuery(e.target.value);
                    setSelectedIndex(0);
                  }}
                  placeholder="Search commands..."
                  className="flex-1 bg-transparent text-white placeholder:text-white/30 focus:outline-none"
                />
                <kbd className="px-2 py-1 text-[10px] text-white/40 bg-white/5 rounded border border-white/10">
                  ESC
                </kbd>
              </div>

              {/* Results */}
              <div className="max-h-80 overflow-y-auto py-2">
                {filteredCommands.length === 0 ? (
                  <div className="px-4 py-8 text-center text-white/40">
                    No commands found
                  </div>
                ) : (
                  filteredCommands.map((command, index) => {
                    const Icon = command.icon;
                    const isSelected = index === selectedIndex;

                    return (
                      <button
                        key={command.id}
                        onClick={() => executeCommand(command)}
                        onMouseEnter={() => setSelectedIndex(index)}
                        className={cn(
                          "w-full flex items-center gap-3 px-4 py-3 transition-colors",
                          isSelected
                            ? "bg-violet-500/10 text-white"
                            : "text-white/70 hover:bg-white/5"
                        )}
                      >
                        <div className={cn(
                          "w-8 h-8 rounded-lg flex items-center justify-center",
                          isSelected
                            ? "bg-violet-500/20 text-violet-400"
                            : "bg-white/5 text-white/40"
                        )}>
                          <Icon className="w-4 h-4" />
                        </div>
                        <div className="flex-1 text-left">
                          <p className="text-sm font-medium">{command.label}</p>
                          {command.description && (
                            <p className="text-xs text-white/40">{command.description}</p>
                          )}
                        </div>
                        {isSelected && (
                          <ArrowRight className="w-4 h-4 text-violet-400" />
                        )}
                      </button>
                    );
                  })
                )}
              </div>

              {/* Footer */}
              <div className="px-4 py-3 border-t border-white/5 flex items-center justify-between text-xs text-white/40">
                <div className="flex items-center gap-4">
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-white/5 rounded border border-white/10">↑</kbd>
                    <kbd className="px-1.5 py-0.5 bg-white/5 rounded border border-white/10">↓</kbd>
                    Navigate
                  </span>
                  <span className="flex items-center gap-1">
                    <kbd className="px-1.5 py-0.5 bg-white/5 rounded border border-white/10">↵</kbd>
                    Select
                  </span>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

export default CommandPalette;
