"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronDown, HelpCircle } from "lucide-react";

const faqs = [
  {
    question: "How does MindLayer work?",
    answer: "MindLayer connects to your document sources and uses advanced AI to analyze the content, extract entities, identify relationships, and build a dynamic knowledge graph. When you ask a question, our AI searches across all your documents and provides answers with source citations.",
  },
  {
    question: "What document sources are supported?",
    answer: "MindLayer supports 50+ integrations including Notion, Google Drive, Dropbox, Slack, Email, Confluence, SharePoint, and more. We're constantly adding new integrations based on user requests.",
  },
  {
    question: "Is my data secure?",
    answer: "Security is our top priority. We use industry-standard encryption (AES-256) for data at rest and TLS 1.3 for data in transit. We're SOC 2 Type II certified and GDPR compliant. Your data is never used to train AI models.",
  },
  {
    question: "How accurate are the answers?",
    answer: "MindLayer achieves 90%+ answer accuracy through our state-of-the-art RAG (Retrieval Augmented Generation) system. Every answer includes source citations so you can verify the information.",
  },
  {
    question: "Can I collaborate with my team?",
    answer: "Absolutely! Team workspaces allow you to share knowledge, insights, and documents with colleagues. You can set permission levels (view, edit, admin) and track who's contributed what.",
  },
  {
    question: "What are Insight Cards?",
    answer: "Insight Cards are AI-generated observations that surface hidden connections and patterns in your knowledge base. They proactively highlight relationships between documents you might not have discovered on your own.",
  },
  {
    question: "How does multi-hop discovery work?",
    answer: "Multi-hop discovery allows you to trace how ideas connect across multiple documents. Instead of simple Q&A, you can explore chains of related concepts, see how topics evolve over time, and find indirect connections.",
  },
  {
    question: "Can I cancel anytime?",
    answer: "Yes, you can cancel your subscription at any time. There's no long-term commitment, and you won't be charged after your current billing period ends.",
  },
];

export function FAQSection() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section className="relative py-24 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-gradient-to-b from-white to-slate-50 dark:from-slate-950 dark:to-indigo-950/20" />
      
      <div className="relative z-10 container mx-auto px-4">
        {/* Section header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <span className="inline-block px-4 py-1.5 mb-4 text-sm font-medium bg-amber-100 dark:bg-amber-900/50 text-amber-600 dark:text-amber-400 rounded-full">
            FAQ
          </span>
          <h2 className="text-4xl md:text-5xl font-bold mb-6 text-slate-900 dark:text-white">
            Frequently asked questions
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Everything you need to know about MindLayer. Can't find what you're looking for? Contact our support team.
          </p>
        </motion.div>

        {/* FAQs */}
        <div className="max-w-3xl mx-auto space-y-4">
          {faqs.map((faq, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: index * 0.05 }}
              className="relative group"
            >
              <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500/5 to-purple-500/5 rounded-2xl blur-xl group-hover:from-indigo-500/10 group-hover:to-purple-500/10 transition-all duration-300" />
              <div className="relative bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 overflow-hidden">
                <button
                  onClick={() => setOpenIndex(openIndex === index ? null : index)}
                  className="w-full flex items-center justify-between p-6 text-left"
                >
                  <div className="flex items-center gap-4">
                    <div className="w-10 h-10 rounded-lg bg-indigo-100 dark:bg-indigo-900/50 flex items-center justify-center flex-shrink-0">
                      <HelpCircle className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                    </div>
                    <span className="font-semibold text-slate-900 dark:text-white">
                      {faq.question}
                    </span>
                  </div>
                  <motion.div
                    animate={{ rotate: openIndex === index ? 180 : 0 }}
                    transition={{ duration: 0.2 }}
                    className="flex-shrink-0"
                  >
                    <ChevronDown className="w-5 h-5 text-slate-400" />
                  </motion.div>
                </button>
                <AnimatePresence>
                  {openIndex === index && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3 }}
                      className="overflow-hidden"
                    >
                      <div className="px-6 pb-6 pt-0">
                        <div className="pl-14">
                          <p className="text-slate-600 dark:text-slate-400 leading-relaxed">
                            {faq.answer}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
}
