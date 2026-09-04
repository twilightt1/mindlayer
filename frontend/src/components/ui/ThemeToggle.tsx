"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useTheme } from "@/hooks/useTheme";
import { useToast } from "@/components/ui/Toast";
import { Moon, Sun, Monitor, Check } from "lucide-react";
import { cn } from "@/lib/utils";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const { success } = useToast();
  const [isOpen, setIsOpen] = useState(false);

  const themes = [
    { id: "dark", label: "Dark", icon: Moon, description: "Easy on the eyes" },
    { id: "light", label: "Light", icon: Sun, description: "Bright and clean" },
    { id: "system", label: "System", icon: Monitor, description: "Follow your OS" },
  ] as const;

  const handleThemeChange = (newTheme: "dark" | "light" | "system") => {
    setTheme(newTheme);
    setIsOpen(false);
    success(`${newTheme.charAt(0).toUpperCase() + newTheme.slice(1)} theme applied`);
  };

  const currentTheme = themes.find((t) => t.id === theme);
  const CurrentIcon = currentTheme?.icon || Moon;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className={cn(
          "flex items-center gap-2 px-3 py-2 rounded-lg",
          "text-white/70 hover:text-white",
          "hover:bg-white/5 transition-colors"
        )}
      >
        <CurrentIcon className="w-4 h-4" />
        <span className="text-sm hidden sm:inline">{currentTheme?.label}</span>
      </button>

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <div
              className="fixed inset-0 z-40"
              onClick={() => setIsOpen(false)}
            />

            {/* Dropdown */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: -10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: -10 }}
              transition={{ duration: 0.15 }}
              className="absolute right-0 top-full mt-2 w-56 z-50"
            >
              <div className="bg-background/95 backdrop-blur-xl rounded-xl border border-white/10 shadow-xl overflow-hidden">
                <div className="p-2">
                  <p className="px-3 py-2 text-xs text-white/40 font-medium uppercase tracking-wider">
                    Theme
                  </p>
                  {themes.map((t) => {
                    const Icon = t.icon;
                    const isActive = theme === t.id;

                    return (
                      <button
                        key={t.id}
                        onClick={() => handleThemeChange(t.id)}
                        className={cn(
                          "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-colors",
                          isActive
                            ? "bg-violet-500/10 text-violet-400"
                            : "text-white/70 hover:text-white hover:bg-white/5"
                        )}
                      >
                        <Icon className="w-4 h-4" />
                        <div className="flex-1 text-left">
                          <p className="text-sm font-medium">{t.label}</p>
                          <p className="text-xs text-white/40">{t.description}</p>
                        </div>
                        {isActive && <Check className="w-4 h-4" />}
                      </button>
                    );
                  })}
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
}

export default ThemeToggle;
