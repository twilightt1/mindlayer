"use client";

import { motion } from "framer-motion";

const features = [
  {
    title: "Unified Knowledge Graph",
    description: "Connect all your documents, notes, and data sources into a single, searchable knowledge graph.",
    highlight: "One source of truth",
  },
  {
    title: "AI-Powered Search",
    description: "Ask questions in natural language. Get instant, accurate answers with citations.",
    highlight: "90%+ accuracy",
  },
  {
    title: "Hidden Connections",
    description: "Surface relationships between concepts you didn't know existed. Let AI reveal patterns.",
    highlight: "Multi-hop discovery",
  },
  {
    title: "Team Intelligence",
    description: "Build shared understanding across your organization. Insights discovered by one, available to all.",
    highlight: "Collaborative",
  },
];

export function FeaturesSection() {
  return (
    <section id="features" className="relative py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-background" />
      
      {/* Subtle gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-violet-500/5 via-transparent to-transparent" />

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
            Features
          </span>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-6">
            Built for how knowledge
            <br />
            <span className="text-white/50">actually works</span>
          </h2>
          <p className="text-lg text-white/40 leading-relaxed">
            MindLayer understands that information doesn't exist in isolation. 
            It connects, evolves, and compounds over time.
          </p>
        </motion.div>

        {/* Features grid */}
        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="group relative p-8 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm hover:bg-white/10 transition-all duration-300"
            >
              {/* Hover glow */}
              <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-violet-500/0 to-purple-500/0 group-hover:from-violet-500/10 group-hover:to-purple-500/10 transition-all duration-500" />
              
              <div className="relative">
                {/* Highlight tag */}
                <span className="inline-block px-3 py-1 text-xs font-medium text-violet-400 bg-violet-500/10 rounded-full mb-4">
                  {feature.highlight}
                </span>
                
                <h3 className="text-xl font-semibold text-white mb-3 tracking-tight">
                  {feature.title}
                </h3>
                <p className="text-white/50 leading-relaxed">
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
