"use client";

import { motion } from "framer-motion";

const steps = [
  {
    number: "01",
    title: "Connect your sources",
    description: "Link your documents, notes, and data. We support 50+ integrations including Notion, Google Drive, Slack, and more.",
  },
  {
    number: "02",
    title: "AI builds the graph",
    description: "Our AI analyzes your content, extracts entities, and identifies relationships to create a living knowledge graph.",
  },
  {
    number: "03",
    title: "Discover and share",
    description: "Ask questions, explore connections, and share insights with your team. Knowledge becomes accessible to everyone.",
  },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="relative py-32 overflow-hidden">
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
            Three steps to connected knowledge
          </h2>
        </motion.div>

        {/* Steps - horizontal on desktop */}
        <div className="grid md:grid-cols-3 gap-12 md:gap-8 max-w-5xl mx-auto">
          {steps.map((step, index) => (
            <motion.div
              key={step.number}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.15 }}
              className="relative"
            >
              {/* Step number */}
              <div className="text-5xl font-light text-slate-200 dark:text-slate-800 mb-4">
                {step.number}
              </div>
              
              {/* Content */}
              <h3 className="text-xl font-medium text-slate-900 dark:text-white mb-3 tracking-tight">
                {step.title}
              </h3>
              <p className="text-slate-500 dark:text-slate-400 leading-relaxed">
                {step.description}
              </p>
              
              {/* Divider */}
              {index < steps.length - 1 && (
                <div className="hidden md:block absolute top-8 -right-4 lg:-right-6 w-8 lg:w-12 h-px bg-slate-200 dark:bg-slate-800" />
              )}
            </motion.div>
          ))}
        </div>

        {/* Minimal CTA */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="mt-20 text-center"
        >
          <p className="text-sm text-slate-500 dark:text-slate-400">
            Start in minutes, not months
          </p>
        </motion.div>
      </div>
    </section>
  );
}
