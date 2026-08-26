"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { GradientText } from "@/components/ui/BackgroundEffects";

const faqs = [
  {
    question: "How does Orivory work?",
    answer: "Orivory connects to your documents, databases, and knowledge sources. Our AI indexes and understands the relationships between your information, allowing you to query it in natural language and get accurate, context-aware answers."
  },
  {
    question: "What document sources do you support?",
    answer: "We support PDF, DOCX, TXT, Markdown, Notion, Confluence, Slack, Google Drive, GitHub, and many more. Our integrations are continuously expanding."
  },
  {
    question: "Is my data secure?",
    answer: "Absolutely. We use enterprise-grade encryption, SOC 2 compliance, and never train on your data. You maintain full ownership and control of your information."
  },
  {
    question: "How many team members can I add?",
    answer: "Our Pro plan includes unlimited team collaboration. You can invite as many colleagues as you need and manage their access levels easily."
  },
  {
    question: "Can I try it for free?",
    answer: "Yes! Our Free plan gives you 3 document sources and 100 queries per month. No credit card required to get started."
  },
  {
    question: "What happens if I exceed my query limit?",
    answer: "You'll receive a notification when you're approaching your limit. You can upgrade to Pro for unlimited queries or wait until your monthly reset."
  },
];

export function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section id="faq" className="relative py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-background" />
      
      {/* Gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-purple-500/5 to-transparent" />

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
            className="text-xs tracking-[0.2em] uppercase text-purple-400 mb-4 block"
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
          >
            FAQ
          </motion.span>
          
          <h2 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tighter text-white mb-6">
            Frequently asked
            <br />
            <span className="text-white/50">questions</span>
          </h2>
          
          <motion.p
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.2 }}
            className="text-lg text-white/40"
          >
            Everything you need to know about Orivory.
          </motion.p>
        </motion.div>

        {/* FAQ items */}
        <div className="max-w-3xl mx-auto space-y-4">
          {faqs.map((faq, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4, delay: index * 0.05 }}
              className="border border-white/10 rounded-2xl overflow-hidden bg-white/5 backdrop-blur-sm transition-all duration-300 hover:border-white/20"
            >
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full px-8 py-6 text-left flex items-center justify-between cursor-pointer"
              >
                <span className="text-lg font-semibold text-white pr-4">
                  {faq.question}
                </span>
                <motion.span
                  className="w-6 h-6 flex-shrink-0 flex items-center justify-center text-white/60"
                  animate={{ rotate: openIndex === index ? 45 : 0 }}
                  transition={{ duration: 0.2 }}
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="12" y1="5" x2="12" y2="19" />
                    <line x1="5" y1="12" x2="19" y2="12" />
                  </svg>
                </motion.span>
              </button>
              
              <AnimatePresence>
                {openIndex === index && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.3, ease: "easeInOut" }}
                    className="overflow-hidden"
                  >
                    <div className="px-8 pb-6 text-white/60 leading-relaxed border-t border-white/10 pt-4">
                      {faq.answer}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
