"use client";

import { useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";

interface ShortcutHandlers {
  onQuickCapture?: () => void;
  onSearch?: () => void;
  onNewMemory?: () => void;
  onToggleHelp?: () => void;
}

/**
 * Global keyboard shortcuts for MindLayer
 * 
 * Shortcuts:
 * - Cmd/Ctrl + K: Quick capture / Search
 * - Cmd/Ctrl + N: New memory
 * - Cmd/Ctrl + /: Show help
 * - Escape: Close modals
 */
export function KeyboardShortcuts({
  onQuickCapture,
  onSearch,
  onNewMemory,
  onToggleHelp,
}: ShortcutHandlers) {
  const router = useRouter();

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const isMac = navigator.platform.toUpperCase().indexOf("MAC") >= 0;
      const modifier = isMac ? e.metaKey : e.ctrlKey;

      // Cmd/Ctrl + K: Quick capture / Search
      if (modifier && e.key === "k") {
        e.preventDefault();
        if (onQuickCapture) {
          onQuickCapture();
        } else {
          // Default: open search/command palette
          const event = new CustomEvent("open-quick-capture");
          window.dispatchEvent(event);
        }
      }

      // Cmd/Ctrl + N: New memory
      if (modifier && e.key === "n") {
        e.preventDefault();
        if (onNewMemory) {
          onNewMemory();
        } else {
          // Default: navigate to capture page
          const event = new CustomEvent("open-new-memory");
          window.dispatchEvent(event);
        }
      }

      // Cmd/Ctrl + /: Toggle help
      if (modifier && e.key === "/") {
        e.preventDefault();
        if (onToggleHelp) {
          onToggleHelp();
        } else {
          const event = new CustomEvent("toggle-shortcuts-help");
          window.dispatchEvent(event);
        }
      }
    },
    [onQuickCapture, onSearch, onNewMemory, onToggleHelp]
  );

  useEffect(() => {
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleKeyDown]);

  return null;
}

/**
 * Shortcut definitions for help display
 */
export const SHORTCUTS = [
  {
    category: "Navigation",
    items: [
      { keys: ["G", "D"], description: "Go to Discovery" },
      { keys: ["G", "I"], description: "Go to Insights" },
      { keys: ["G", "W"], description: "Go to Workspaces" },
      { keys: ["G", "S"], description: "Go to Sources" },
      { keys: ["G", "H"], description: "Go to Home" },
    ],
  },
  {
    category: "Actions",
    items: [
      { keys: ["⌘", "K"], description: "Quick capture / Search" },
      { keys: ["⌘", "N"], description: "New memory" },
      { keys: ["?"], description: "Toggle this help" },
      { keys: ["Esc"], description: "Close modal" },
    ],
  },
  {
    category: "Discovery",
    items: [
      { keys: ["S"], description: "Start new session" },
      { keys: ["←", "→"], description: "Navigate steps" },
      { keys: ["E"], description: "View graph" },
    ],
  },
];

/**
 * Shortcut badge component
 */
export function ShortcutBadge({ keys }: { keys: string[] }) {
  return (
    <div className="flex gap-1">
      {keys.map((key, i) => (
        <kbd
          key={i}
          className="px-2 py-1 text-xs font-medium bg-muted rounded border border-border"
        >
          {key}
        </kbd>
      ))}
    </div>
  );
}

/**
 * Help modal content for shortcuts
 */
export function ShortcutsHelp() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-sm font-semibold mb-3">Keyboard Shortcuts</h3>
        <div className="space-y-4">
          {SHORTCUTS.map((group) => (
            <div key={group.category}>
              <p className="text-xs text-muted-foreground mb-2">
                {group.category}
              </p>
              <div className="space-y-2">
                {group.items.map((item, i) => (
                  <div
                    key={i}
                    className="flex justify-between items-center text-sm"
                  >
                    <span className="text-muted-foreground">
                      {item.description}
                    </span>
                    <ShortcutBadge keys={item.keys} />
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
