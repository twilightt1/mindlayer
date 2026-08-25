"use client";

import { motion } from "framer-motion";

const features = [
  {
    title: "Unified Knowledge",
    description: "Connect documents, notes, and data sources. Create a single source of truth your entire team can explore.",
  },
  {
    title: "AI-Powered Search",
    description: "Ask questions in natural language. Get instant answers with citations from your connected sources.",
  },
  {
    title: "Hidden Connections",
    description: "Surface relationships between concepts you didn't know existed. Let AI reveal patterns across your knowledge.",
  },
  {
    title: "Team Intelligence",
    description: "Build shared understanding across your organization. Insights discovered by one become available to all.",
  },
];

export function FeaturesSection() {
  return (
    <section id="features" className="relative py-32 overflow-hidden">
      <div className="absolute inset-0 bg-white dark:bg-black" />
      
      <div className="relative z-10 container mx-auto px-6">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-2xl mx-auto text-center mb-20"
        >
          <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-slate-900 dark:text-white mb-6">
            Built for how knowledge actually works
          </h2>
          <p className="text-lg text-slate-500 dark:text-slate-400 leading-relaxed">
            MindLayer understands that information doesn't exist in isolation. 
            It connects, evolves, and compounds over time.
          </p>
        </motion.div>

        {/* Features grid - typography focused */}
        <div className="grid md:grid-cols-2 gap-12 md:gap-16 max-w-4xl mx-auto">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="relative"
            >
              {/* Minimal accent */}
              <div className="absolute left-0 top-0 w-8 h-px bg-slate-200 dark:bg-slate-800" />
              
              <div className="pl-10">
                <h3 className="text-xl font-medium text-slate-900 dark:text-white mb-3 tracking-tight">
                  {feature.title}
                </h3>
                <p className="text-slate-500 dark:text-slate-400 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
