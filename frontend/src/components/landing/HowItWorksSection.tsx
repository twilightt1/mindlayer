"use client";

import { motion } from "framer-motion";
import { GradientText } from "@/components/ui/BackgroundEffects";

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
      {/* Background */}
      <div className="absolute inset-0 bg-background" />
      
      {/* Gradient accent */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[600px] bg-gradient-to-b from-violet-500/10 to-transparent rounded-full blur-[150px]" />

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
            How it works
          </motion.span>
          
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tighter text-white mb-6">
            Three steps to
            <br />
            <GradientText from="from-violet-400" to="to-purple-400">
              connected knowledge
            </GradientText>
          </h2>
        </motion.div>

        {/* Steps */}
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {steps.map((step, index) => (
            <motion.div
              key={step.number}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.15 }}
              className="relative group"
            >
              {/* Card */}
              <motion.div 
                className="relative p-8 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm transition-all duration-300 group-hover:bg-white/10 group-hover:border-violet-500/30 overflow-hidden"
                whileHover={{ y: -5 }}
              >
                {/* Animated gradient on hover */}
                <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500">
                  <div className="absolute inset-0 bg-gradient-to-br from-violet-500/10 to-purple-500/10" />
                </div>
                
                {/* Number - Large decorative */}
                <motion.div 
                  className="text-7xl md:text-8xl font-black text-white/5 select-none mb-2"
                  whileHover={{ scale: 1.05 }}
                >
                  {step.number}
                </motion.div>
                
                {/* Connector line */}
                {index < steps.length - 1 && (
                  <motion.div 
                    className="hidden md:block absolute top-1/2 -right-4 lg:-right-8 w-8 lg:w-16 h-px bg-gradient-to-r from-violet-500/50 to-transparent"
                    initial={{ scaleX: 0 }}
                    whileInView={{ scaleX: 1 }}
                    viewport={{ once: true }}
                    transition={{ delay: 0.5 + index * 0.2 }}
                  />
                )}
                
                <div className="relative">
                  <h3 className="text-xl md:text-2xl font-bold text-white mb-3 tracking-tight">
                    {step.title}
                  </h3>
                  <p className="text-white/50 leading-relaxed">
                    {step.description}
                  </p>
                </div>
              </motion.div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
