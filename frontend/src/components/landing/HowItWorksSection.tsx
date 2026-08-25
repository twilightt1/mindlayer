"use client";

import { motion } from "framer-motion";
import { FileText, Brain, Sparkles, Users } from "lucide-react";

const steps = [
  {
    number: "01",
    icon: FileText,
    title: "Connect Your Sources",
    description: "Link your documents, notes, emails, and databases. MindLayer supports 50+ integrations including Notion, Google Drive, Slack, and more.",
    color: "indigo",
  },
  {
    number: "02",
    icon: Brain,
    title: "AI Builds the Knowledge Graph",
    description: "Our AI analyzes your content, extracts entities, identifies relationships, and creates a dynamic knowledge graph that evolves with your information.",
    color: "purple",
  },
  {
    number: "03",
    icon: Sparkles,
    title: "Discover Hidden Insights",
    description: "Ask questions, explore connections, and let MindLayer surface insights you didn't know you were looking for.",
    color: "pink",
  },
  {
    number: "04",
    icon: Users,
    title: "Share & Collaborate",
    description: "Invite your team to explore the same knowledge base. Build collective intelligence where everyone benefits from what others discover.",
    color: "cyan",
  },
];

const colorMap: Record<string, { bg: string; text: string; border: string; gradient: string }> = {
  indigo: {
    bg: "bg-indigo-100 dark:bg-indigo-900/50",
    text: "text-indigo-600 dark:text-indigo-400",
    border: "border-indigo-200 dark:border-indigo-800",
    gradient: "from-indigo-500 to-indigo-600",
  },
  purple: {
    bg: "bg-purple-100 dark:bg-purple-900/50",
    text: "text-purple-600 dark:text-purple-400",
    border: "border-purple-200 dark:border-purple-800",
    gradient: "from-purple-500 to-purple-600",
  },
  pink: {
    bg: "bg-pink-100 dark:bg-pink-900/50",
    text: "text-pink-600 dark:text-pink-400",
    border: "border-pink-200 dark:border-pink-800",
    gradient: "from-pink-500 to-pink-600",
  },
  cyan: {
    bg: "bg-cyan-100 dark:bg-cyan-900/50",
    text: "text-cyan-600 dark:text-cyan-400",
    border: "border-cyan-200 dark:border-cyan-800",
    gradient: "from-cyan-500 to-cyan-600",
  },
};

export function HowItWorksSection() {
  return (
    <section className="relative py-24 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-slate-50 dark:bg-slate-950" />
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-indigo-500/5 via-transparent to-transparent" />
      
      <div className="relative z-10 container mx-auto px-4">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-3xl mx-auto mb-20"
        >
          <span className="inline-block px-4 py-1.5 mb-4 text-sm font-medium bg-purple-100 dark:bg-purple-900/50 text-purple-600 dark:text-purple-400 rounded-full">
            How It Works
          </span>
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-slate-900 dark:text-white">
            From scattered docs to connected knowledge
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            In four simple steps, transform how your team discovers and shares knowledge.
          </p>
        </motion.div>

        {/* Steps */}
        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {steps.map((step, index) => {
            const colors = colorMap[step.color];
            return (
              <motion.div
                key={step.number}
                initial={{ opacity: 0, x: index % 2 === 0 ? -20 : 20, y: 20 }}
                whileInView={{ opacity: 1, x: 0, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.15 }}
                className="relative"
              >
                <div className={`absolute -inset-4 bg-gradient-to-r ${colors.bg} rounded-3xl blur-xl opacity-50`} />
                <div className={`relative p-8 bg-white dark:bg-slate-900 rounded-2xl border ${colors.border} shadow-lg`}>
                  {/* Step number */}
                  <div className="flex items-center gap-4 mb-6">
                    <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${colors.gradient} flex items-center justify-center shadow-lg`}>
                      <step.icon className="w-8 h-8 text-white" />
                    </div>
                    <span className={`text-4xl font-bold ${colors.text} opacity-50`}>
                      {step.number}
                    </span>
                  </div>
                  
                  <h3 className="text-2xl font-bold mb-3 text-slate-900 dark:text-white">
                    {step.title}
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                    {step.description}
                  </p>
                </div>

                {/* Connector line */}
                {index < steps.length - 1 && (
                  <div className="hidden md:block absolute left-1/2 -bottom-8 w-0.5 h-8 bg-gradient-to-b from-slate-300 dark:from-slate-700 to-transparent" />
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Animated diagram */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: 0.6 }}
          className="mt-24 max-w-4xl mx-auto"
        >
          <div className="relative p-8 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-xl">
            <div className="flex flex-wrap justify-center items-center gap-8">
              {/* Sources */}
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 rounded-xl bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center border-2 border-indigo-200 dark:border-indigo-800">
                  <FileText className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
                </div>
                <span className="text-sm font-medium text-slate-600 dark:text-slate-400">Documents</span>
              </div>

              {/* Arrow */}
              <motion.div
                animate={{ x: [0, 5, 0] }}
                transition={{ duration: 2, repeat: Infinity }}
                className="text-slate-400"
              >
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </motion.div>

              {/* AI */}
              <div className="flex flex-col items-center gap-3">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-purple-500/25">
                  <Brain className="w-10 h-10 text-white" />
                </div>
                <span className="text-sm font-medium text-slate-600 dark:text-slate-400">AI Processing</span>
              </div>

              {/* Arrow */}
              <motion.div
                animate={{ x: [0, 5, 0] }}
                transition={{ duration: 2, repeat: Infinity, delay: 0.3 }}
                className="text-slate-400"
              >
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </motion.div>

              {/* Graph */}
              <div className="relative w-20 h-20">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
                  className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center shadow-lg shadow-cyan-500/25"
                >
                  <div className="w-4 h-4 bg-white rounded-full" />
                  <div className="absolute w-2 h-2 bg-white/50 rounded-full top-2 right-2" />
                  <div className="absolute w-2 h-2 bg-white/50 rounded-full bottom-2 left-2" />
                </motion.div>
              </div>
              <span className="text-sm font-medium text-slate-600 dark:text-slate-400">Knowledge Graph</span>

              {/* Arrow */}
              <motion.div
                animate={{ x: [0, 5, 0] }}
                transition={{ duration: 2, repeat: Infinity, delay: 0.6 }}
                className="text-slate-400"
              >
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </motion.div>

              {/* Insights */}
              <div className="flex flex-col items-center gap-3">
                <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center shadow-lg shadow-amber-500/25">
                  <Sparkles className="w-8 h-8 text-white" />
                </div>
                <span className="text-sm font-medium text-slate-600 dark:text-slate-400">Insights</span>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
