"use client";

import { motion } from "framer-motion";
import { 
  Brain, 
  Sparkles, 
  Network, 
  Users, 
  Zap, 
  Shield,
  Search,
  Lightbulb,
  Share2
} from "lucide-react";

const features = [
  {
    icon: Sparkles,
    title: "Insight Cards",
    description: "AI automatically surfaces connections between your documents. Discover patterns and relationships you never knew existed.",
    color: "from-indigo-500 to-purple-500",
  },
  {
    icon: Network,
    title: "Multi-hop Discovery",
    description: "Follow the trail of knowledge across multiple documents. Trace how ideas evolve and connect over time.",
    color: "from-purple-500 to-pink-500",
  },
  {
    icon: Users,
    title: "Team Knowledge Base",
    description: "Share insights across your entire team. Build a collective intelligence that grows with every contribution.",
    color: "from-pink-500 to-rose-500",
  },
  {
    icon: Search,
    title: "Semantic Search",
    description: "Ask questions in natural language. Find answers across all your documents in seconds, not minutes.",
    color: "from-cyan-500 to-blue-500",
  },
  {
    icon: Lightbulb,
    title: "Proactive Intelligence",
    description: "MindLayer learns your interests and surfaces relevant insights before you even ask.",
    color: "from-amber-500 to-orange-500",
  },
  {
    icon: Share2,
    title: "One-click Sharing",
    description: "Share specific insights or entire workspaces with colleagues. Collaborate without friction.",
    color: "from-emerald-500 to-green-500",
  },
];

const capabilities = [
  {
    title: "90%+ Answer Accuracy",
    description: "State-of-the-art RAG ensures you get reliable, sourced answers.",
    icon: Shield,
  },
  {
    title: "< 2s Response Time",
    description: "Lightning-fast retrieval keeps your workflow smooth and productive.",
    icon: Zap,
  },
  {
    title: "Persistent Memory",
    description: "Your AI assistant remembers your preferences and learning history.",
    icon: Brain,
  },
];

export function FeaturesSection() {
  return (
    <section className="relative py-24 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-white to-slate-50 dark:from-slate-950 dark:to-indigo-950/20" />
      
      <div className="relative z-10 container mx-auto px-4">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <span className="inline-block px-4 py-1.5 mb-4 text-sm font-medium bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 rounded-full">
            Powerful Features
          </span>
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-slate-900 dark:text-white">
            Everything you need to transform knowledge
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            MindLayer combines cutting-edge AI with intuitive design to help you 
            discover, understand, and share knowledge at scale.
          </p>
        </motion.div>

        {/* Feature grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8 mb-24">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="group relative"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 to-purple-500/5 rounded-2xl blur-xl group-hover:from-indigo-500/10 group-hover:to-purple-500/10 transition-all duration-300" />
              <div className="relative p-8 bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 hover:border-indigo-200 dark:hover:border-indigo-800 transition-all duration-300">
                <div className={`w-14 h-14 rounded-xl bg-gradient-to-br ${feature.color} p-3 mb-6 shadow-lg group-hover:shadow-xl transition-shadow`}>
                  <feature.icon className="w-full h-full text-white" />
                </div>
                <h3 className="text-xl font-bold mb-3 text-slate-900 dark:text-white">
                  {feature.title}
                </h3>
                <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Capabilities */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="grid md:grid-cols-3 gap-6"
        >
          {capabilities.map((cap, index) => (
            <motion.div
              key={cap.title}
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center gap-4 p-6 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800"
            >
              <div className="w-12 h-12 rounded-lg bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center flex-shrink-0">
                <cap.icon className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
              </div>
              <div>
                <h4 className="font-semibold text-slate-900 dark:text-white">
                  {cap.title}
                </h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  {cap.description}
                </p>
              </div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
