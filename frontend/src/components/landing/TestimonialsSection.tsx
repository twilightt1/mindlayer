"use client";

import { motion } from "framer-motion";
import { GradientText } from "@/components/ui/BackgroundEffects";
import { NumberCounter } from "@/components/ui/AdvancedEffects";

const testimonials = [
  {
    name: "Sarah Chen",
    role: "Head of Product",
    company: "Stripe",
    quote: "Orivory has transformed how our team discovers information. What used to take hours now takes minutes.",
  },
  {
    name: "Marcus Johnson",
    role: "Research Director",
    company: "Anthropic",
    quote: "The multi-hop discovery is remarkable. I can trace how ideas connect across dozens of documents.",
  },
  {
    name: "Emily Rodriguez",
    role: "CEO",
    company: "Linear",
    quote: "Team knowledge sharing used to be chaos. Now everyone is aligned. Our productivity increased 40%.",
  },
  {
    name: "David Kim",
    role: "Senior Engineer",
    company: "Vercel",
    quote: "The semantic search understands context. I find exactly what I need, every time.",
  },
];

export function TestimonialsSection() {
  return (
    <section className="relative py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-background" />
      
      {/* Subtle glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[500px] bg-gradient-to-r from-violet-500/10 via-purple-500/10 to-pink-500/10 rounded-full blur-[150px]" />

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
            Testimonials
          </motion.span>
          
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tighter text-white mb-6">
            Loved by teams
            <br />
            <span className="text-white/50">everywhere</span>
          </h2>
        </motion.div>

        {/* Testimonials grid */}
        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          {testimonials.map((testimonial, index) => (
            <motion.div
              key={testimonial.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              whileHover={{ y: -5 }}
              className="p-8 rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm transition-all duration-300 hover:bg-white/10 hover:border-violet-500/30 group cursor-pointer"
            >
              {/* Quote */}
              <motion.p 
                className="text-lg text-white/70 mb-6 leading-relaxed"
                initial={{ opacity: 0.7 }}
                whileHover={{ opacity: 1 }}
              >
                "{testimonial.quote}"
              </motion.p>
              
              {/* Author */}
              <div className="flex items-center gap-4">
                <motion.div 
                  className="w-12 h-12 rounded-full bg-gradient-to-br from-violet-500 via-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-lg shadow-lg shadow-violet-500/25"
                  whileHover={{ scale: 1.05 }}
                >
                  {testimonial.name.charAt(0)}
                </motion.div>
                <div>
                  <motion.p 
                    className="font-semibold text-white"
                    whileHover={{ color: "#a78bfa" }}
                  >
                    {testimonial.name}
                  </motion.p>
                  <p className="text-sm text-white/40">
                    {testimonial.role} at {testimonial.company}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Stats with NumberCounter */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8 max-w-3xl mx-auto"
        >
          {[
            { value: 10000, suffix: "+", label: "Active users" },
            { value: 50, suffix: "+", label: "Integrations" },
            { value: 99.9, suffix: "%", label: "Uptime" },
            { value: 4.9, suffix: "", label: "Rating", decimal: true },
          ].map((stat, i) => (
            <motion.div 
              key={stat.label}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.5 + i * 0.1 }}
              className="text-center group"
            >
              <motion.p 
                className="text-4xl md:text-5xl font-black text-white mb-2"
                whileHover={{ scale: 1.05 }}
              >
                <NumberCounter 
                  target={stat.decimal ? Math.floor(stat.value * 10) : stat.value} 
                  className=""
                />
                {stat.decimal ? `.${Math.floor((stat.value % 1) * 10)}` : ""}{stat.suffix}
              </motion.p>
              <p className="text-sm text-white/40 group-hover:text-white/60 transition-colors">
                {stat.label}
              </p>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
