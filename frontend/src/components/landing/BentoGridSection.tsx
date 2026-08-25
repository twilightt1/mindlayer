"use client";

import { motion } from "framer-motion";
import { 
  Brain, 
  Network, 
  Sparkles, 
  Search, 
  Zap,
  Users
} from "lucide-react";

const features = [
  {
    title: "Neural Processing",
    description: "Advanced AI that understands context and nuance across all your documents.",
    icon: Brain,
    className: "col-span-1 md:col-span-2 row-span-2",
    gradient: "from-indigo-500 to-purple-600",
  },
  {
    title: "Knowledge Graphs",
    description: "Visual representation of how your information connects.",
    icon: Network,
    className: "col-span-1",
    gradient: "from-purple-500 to-pink-600",
  },
  {
    title: "Real-time Insights",
    description: "Instant analysis as you add new content.",
    icon: Sparkles,
    className: "col-span-1",
    gradient: "from-pink-500 to-rose-600",
  },
  {
    title: "Semantic Search",
    description: "Natural language queries across all sources.",
    icon: Search,
    className: "col-span-1 md:col-span-2",
    gradient: "from-cyan-500 to-blue-600",
  },
  {
    title: "Lightning Fast",
    description: "Sub-second responses to complex queries.",
    icon: Zap,
    className: "col-span-1",
    gradient: "from-amber-500 to-orange-600",
  },
  {
    title: "Team Sync",
    description: "Real-time collaboration across your organization.",
    icon: Users,
    className: "col-span-1 md:col-span-2",
    gradient: "from-emerald-500 to-green-600",
  },
];

export function BentoGridSection() {
  return (
    <section className="relative py-24 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-slate-50 dark:bg-slate-950" />
      
      {/* Animated grid pattern */}
      <div className="absolute inset-0 opacity-30">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px]" />
      </div>
      
      <div className="relative z-10 container mx-auto px-4">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <span className="inline-block px-4 py-1.5 mb-4 text-sm font-medium bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 rounded-full">
            Bento Grid
          </span>
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-slate-900 dark:text-white">
            Powerful capabilities in one place
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Explore our key features through an interactive grid layout.
          </p>
        </motion.div>

        {/* Bento Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 max-w-5xl mx-auto">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.1 }}
              className={`${feature.className} group relative`}
            >
              {/* Glow effect */}
              <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-2xl blur opacity-0 group-hover:opacity-30 transition-opacity duration-500" />
              
              {/* Card */}
              <div className="relative h-full bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 p-6 overflow-hidden hover:border-indigo-200 dark:hover:border-indigo-800 transition-all duration-300">
                {/* Gradient overlay */}
                <div className={`absolute top-0 right-0 w-32 h-32 bg-gradient-to-br ${feature.gradient} opacity-10 rounded-full blur-2xl -translate-y-1/2 translate-x-1/2`} />
                
                <div className="relative z-10 h-full flex flex-col">
                  {/* Icon */}
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.gradient} p-3 mb-4 shadow-lg`}>
                    <feature.icon className="w-full h-full text-white" />
                  </div>
                  
                  {/* Content */}
                  <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">
                    {feature.title}
                  </h3>
                  <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed flex-1">
                    {feature.description}
                  </p>
                  
                  {/* Hover indicator */}
                  <div className="mt-4 flex items-center gap-2 text-sm font-medium text-indigo-600 dark:text-indigo-400 opacity-0 group-hover:opacity-100 transition-opacity">
                    <span>Learn more</span>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                    </svg>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
