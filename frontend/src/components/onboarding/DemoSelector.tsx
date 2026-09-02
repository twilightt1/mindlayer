"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useToast } from "@/components/ui/Toast";
import { DEMO_PERSONAS, seedDemoData, type DemoPersona } from "@/lib/api/demo";
import { Loader2, Sparkles, ArrowRight, X } from "lucide-react";

interface DemoSelectorProps {
  onComplete: () => void;
  onSkip: () => void;
}

export function DemoSelector({ onComplete, onSkip }: DemoSelectorProps) {
  const [selectedPersona, setSelectedPersona] = useState<DemoPersona | null>(null);
  const [loading, setLoading] = useState(false);
  const { success, error } = useToast();

  const handleStartDemo = async () => {
    setLoading(true);
    try {
      const result = await seedDemoData();
      if (result.success) {
        success(`Created ${result.memory_count} demo memories!`);
        onComplete();
      } else {
        error(result.message);
      }
    } catch (err) {
      console.error("Failed to seed demo data:", err);
      error("Failed to load demo data. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative w-full max-w-2xl mx-4"
      >
        <div className="bg-background/95 backdrop-blur-xl rounded-2xl border border-white/10 shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="relative px-8 pt-8 pb-6 text-center">
            <button
              onClick={onSkip}
              className="absolute top-4 right-4 p-2 rounded-lg text-white/40 hover:text-white hover:bg-white/5 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-violet-500/20 to-purple-500/20 border border-violet-500/30 flex items-center justify-center"
            >
              <Sparkles className="w-8 h-8 text-violet-400" />
            </motion.div>

            <h2 className="text-2xl font-bold text-white mb-2">
              Try Orivory with Sample Data
            </h2>
            <p className="text-white/60">
              Get instant access to a pre-loaded knowledge base and see Orivory in action — no setup required.
            </p>
          </div>

          {/* Personas */}
          <div className="px-8 pb-6">
            <div className="grid gap-3">
              {DEMO_PERSONAS.map((persona) => (
                <motion.button
                  key={persona.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  whileHover={{ scale: 1.01 }}
                  whileTap={{ scale: 0.99 }}
                  onClick={() => setSelectedPersona(persona)}
                  className={cn(
                    "relative w-full p-4 rounded-xl border text-left transition-all duration-200",
                    selectedPersona?.id === persona.id
                      ? "bg-violet-500/10 border-violet-500/50"
                      : "bg-white/5 border-white/10 hover:bg-white/10 hover:border-white/20"
                  )}
                >
                  <div className="flex items-start gap-4">
                    <span className="text-3xl">{persona.emoji}</span>
                    <div className="flex-1">
                      <h3 className="font-medium text-white mb-1">{persona.name}</h3>
                      <p className="text-sm text-white/50">{persona.description}</p>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-white/40">
                      <span>{persona.memory_count} memories</span>
                    </div>
                  </div>

                  {selectedPersona?.id === persona.id && (
                    <motion.div
                      layoutId="selected-persona"
                      className="absolute inset-0 rounded-xl border-2 border-violet-500 pointer-events-none"
                    />
                  )}
                </motion.button>
              ))}
            </div>
          </div>

          {/* Footer */}
          <div className="px-8 pb-8 pt-4 border-t border-white/5">
            <div className="flex items-center gap-3">
              <button
                onClick={onSkip}
                className="px-4 py-2.5 rounded-xl text-sm font-medium text-white/60 hover:text-white hover:bg-white/5 transition-colors"
              >
                Start Fresh
              </button>
              <div className="flex-1" />
              <motion.button
                initial={{ scale: 0.95 }}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={handleStartDemo}
                disabled={loading || !selectedPersona}
                className={cn(
                  "flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-medium transition-all",
                  selectedPersona
                    ? "bg-gradient-to-r from-violet-600 to-purple-600 text-white shadow-lg shadow-violet-500/25 hover:shadow-violet-500/40"
                    : "bg-white/10 text-white/40 cursor-not-allowed"
                )}
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Setting up...
                  </>
                ) : (
                  <>
                    Start Demo
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </motion.button>
            </div>
          </div>
        </div>

        {/* Feature highlights */}
        <div className="mt-4 grid grid-cols-3 gap-3 px-4">
          {[
            { icon: "💬", text: "Chat with AI" },
            { icon: "🔍", text: "Discover connections" },
            { icon: "💡", text: "Get insights" },
          ].map((feature, i) => (
            <motion.div
              key={feature.text}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + i * 0.05 }}
              className="text-center p-3 rounded-xl bg-white/5 border border-white/5"
            >
              <span className="text-xl mb-1 block">{feature.icon}</span>
              <span className="text-xs text-white/50">{feature.text}</span>
            </motion.div>
          ))}
        </div>
      </motion.div>
    </div>
  );
}
