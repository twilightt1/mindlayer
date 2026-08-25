"use client";

import { motion } from "framer-motion";
import Link from "next/link";

export function CTASection() {
  return (
    <section className="relative py-32 overflow-hidden">
      {/* Subtle background */}
      <div className="absolute inset-0 bg-slate-900 dark:bg-slate-950" />
      
      <div className="relative z-10 container mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="max-w-2xl mx-auto text-center"
        >
          <h2 className="text-3xl md:text-4xl font-semibold tracking-tight text-white mb-6">
            Ready to transform how your team works?
          </h2>
          <p className="text-lg text-slate-400 mb-10">
            Join thousands of teams who've already made the switch.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/signup"
              className="px-8 py-4 bg-white text-slate-900 font-medium rounded-full transition-all duration-300 hover:bg-slate-100"
            >
              Start for free
            </Link>
            <Link
              href="/contact"
              className="px-8 py-4 text-white font-medium rounded-full border border-slate-700 transition-all duration-300 hover:border-slate-500"
            >
              Talk to sales
            </Link>
          </div>
          
          <p className="mt-8 text-sm text-slate-500">
            14-day free trial · No credit card required · Cancel anytime
          </p>
        </motion.div>
      </div>
    </section>
  );
}
