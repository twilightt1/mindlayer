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
      {/* Background */}
      <div className="absolute inset-0 bg-background" />

      <div className="relative z-10 container mx-auto px-6">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-2xl mx-auto text-center mb-20"
        >
          <span className="text-xs tracking-[0.2em] uppercase text-violet-400 mb-4 block">
            Details
          </span>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-6">
            The details
            <br />
            <span className="text-white/50">that matter</span>
          </h2>
        </motion.div>

        {/* Bento grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 max-w-5xl mx-auto">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="group p-6 rounded-2xl border border-white/10 bg-white/5 hover:bg-white/10 transition-all duration-300"
            >
              <h3 className="text-lg font-medium text-white mb-2 tracking-tight">
                {feature.title}
              </h3>
              <p className="text-sm text-white/50 leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
