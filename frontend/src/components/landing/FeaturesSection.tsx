"use client";

import { motion } from "framer-motion";
import { GradientText } from "@/components/ui/BackgroundEffects";
import { BentoCard } from "@/components/ui/bento-grid";

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
      
      {/* Gradient accent */}
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
          <motion.span 
            className="text-xs tracking-[0.2em] uppercase text-violet-400 mb-4 block"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
          >
            Features
          </motion.span>
          
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tighter text-white mb-6">
            Built for how knowledge
            <br />
            <span className="text-white/50">actually works</span>
          </h2>
          
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-lg text-white/40 leading-relaxed"
          >
            Orivory understands that information doesn't exist in isolation. 
            It connects, evolves, and compounds over time.
          </motion.p>
        </motion.div>

        {/* Features grid with BentoCard */}
        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          {features.map((feature, index) => (
            <BentoCard key={feature.title} delay={index * 0.1}>
              {/* Hover glow effect */}
              <motion.div
                className="absolute inset-0 rounded-2xl bg-gradient-to-r from-violet-500/0 to-purple-500/0 opacity-0 transition-opacity duration-500"
                whileHover={{ opacity: 1 }}
              />
              
              <div className="relative">
                {/* Highlight tag */}
                <motion.span 
                  className="inline-flex items-center px-3 py-1 text-xs font-medium text-violet-400 bg-violet-500/10 rounded-full mb-4"
                  whileHover={{ scale: 1.05 }}
                >
                  {feature.highlight}
                </motion.span>
                
                <h3 className="text-xl md:text-2xl font-bold text-white mb-3 tracking-tight">
                  {feature.title}
                </h3>
                <p className="text-white/50 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </BentoCard>
          ))}
        </div>
      </div>
    </section>
  );
}
