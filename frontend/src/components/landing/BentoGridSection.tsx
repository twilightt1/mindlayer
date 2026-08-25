"use client";

import { motion } from "framer-motion";

const features = [
  {
    title: "Semantic Understanding",
    description: "AI that comprehends context and meaning, not just keywords.",
  },
  {
    title: "Real-time Sync",
    description: "Changes in your sources are reflected instantly.",
  },
  {
    title: "Privacy First",
    description: "Your data stays yours. SOC 2 certified.",
  },
  {
    title: "Developer API",
    description: "Build custom integrations with our REST API.",
  },
];

export function BentoGridSection() {
  return (
    <section className="relative py-32 overflow-hidden">
      <div className="absolute inset-0 bg-slate-50/50 dark:bg-slate-950/50" />
      
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
            The details that matter
          </h2>
        </motion.div>

        {/* Bento grid - minimal */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-5xl mx-auto">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="group p-8 bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl transition-all duration-300 hover:border-slate-200 dark:hover:border-slate-700 hover:shadow-sm"
            >
              <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2 tracking-tight">
                {feature.title}
              </h3>
              <p className="text-sm text-slate-500 dark:text-slate-400 leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
