"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const faqs = [
  {
    question: "How does MindLayer work?",
    answer: "MindLayer connects to your document sources and uses advanced AI to analyze content, extract entities, identify relationships, and build a dynamic knowledge graph. When you ask a question, our AI searches across all your documents and provides answers with source citations.",
  },
  {
    question: "What document sources are supported?",
    answer: "MindLayer supports 50+ integrations including Notion, Google Drive, Dropbox, Slack, Email, Confluence, SharePoint, and more.",
  },
  {
    question: "Is my data secure?",
    answer: "Security is our top priority. We use industry-standard encryption for data at rest and in transit. We're SOC 2 Type II certified and GDPR compliant. Your data is never used to train AI models.",
  },
  {
    question: "How accurate are the answers?",
    answer: "MindLayer achieves 90%+ answer accuracy through our RAG system. Every answer includes source citations so you can verify the information.",
  },
  {
    question: "Can I collaborate with my team?",
    answer: "Yes. Team workspaces allow you to share knowledge, insights, and documents with colleagues. You can set permission levels and track contributions.",
  },
];

export function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <section id="faq" className="relative py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-background" />

      <div className="relative z-10 container mx-auto px-6">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-2xl mx-auto text-center mb-16"
        >
          <span className="text-xs tracking-[0.2em] uppercase text-violet-400 mb-4 block">
            FAQ
          </span>
          <h2 className="text-4xl md:text-5xl font-bold tracking-tight text-white mb-6">
            Common questions
          </h2>
        </motion.div>

        {/* FAQs */}
        <div className="max-w-2xl mx-auto space-y-3">
          {faqs.map((faq, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.3, delay: index * 0.05 }}
              className="rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm overflow-hidden"
            >
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full flex items-center justify-between p-5 text-left"
              >
                <span className="font-medium text-white pr-4">
                  {faq.question}
                </span>
                <span className={`flex-shrink-0 text-white/40 transition-transform duration-200 ${openIndex === index ? 'rotate-45' : ''}`}>
                  +
                </span>
              </button>
              <AnimatePresence>
                {openIndex === index && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="overflow-hidden"
                  >
                    <div className="px-5 pb-5 pt-0">
                      <p className="text-white/60 leading-relaxed">
                        {faq.answer}
                      </p>
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
