"use client";

import { motion } from "framer-motion";

const testimonials = [
  {
    name: "Sarah Chen",
    role: "Head of Product",
    company: "Stripe",
    quote: "MindLayer has transformed how our team discovers information. What used to take hours now takes minutes.",
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
            What teams are saying
          </h2>
        </motion.div>

        {/* Testimonials grid */}
        <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto">
          {testimonials.map((testimonial, index) => (
            <motion.div
              key={testimonial.name}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="p-8 bg-white dark:bg-slate-900 border border-slate-100 dark:border-slate-800 rounded-2xl"
            >
              {/* Quote */}
              <p className="text-lg text-slate-700 dark:text-slate-300 mb-6 leading-relaxed">
                "{testimonial.quote}"
              </p>
              
              {/* Author */}
              <div>
                <p className="font-medium text-slate-900 dark:text-white">
                  {testimonial.name}
                </p>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                  {testimonial.role} at {testimonial.company}
                </p>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Stats - minimal */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-20 grid grid-cols-2 md:grid-cols-4 gap-8 max-w-3xl mx-auto"
        >
          {[
            { value: "10K+", label: "Active users" },
            { value: "50+", label: "Integrations" },
            { value: "99.9%", label: "Uptime" },
            { value: "4.9", label: "Average rating" },
          ].map((stat) => (
            <div key={stat.label} className="text-center">
              <p className="text-3xl md:text-4xl font-semibold text-slate-900 dark:text-white mb-1">
                {stat.value}
              </p>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                {stat.label}
              </p>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
