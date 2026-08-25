"use client";

import { motion } from "framer-motion";
import Link from "next/link";

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Subtle background gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-white via-slate-50/50 to-white dark:from-black dark:via-slate-950/50 dark:to-black" />
      
      {/* Minimal decorative line */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-px h-32 bg-gradient-to-b from-transparent via-slate-200 dark:via-slate-800 to-transparent" />

      <div className="relative z-10 container mx-auto px-6 py-20">
        <div className="max-w-3xl mx-auto text-center">
          {/* Minimal badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="mb-12"
          >
            <span className="inline-block px-4 py-1.5 text-xs font-medium tracking-widest uppercase text-slate-500 dark:text-slate-400 border border-slate-200 dark:border-slate-800 rounded-full">
              AI Knowledge Platform
            </span>
          </motion.div>

          {/* Main heading - Typography focused */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-5xl md:text-7xl lg:text-8xl font-semibold tracking-tight mb-8 text-slate-900 dark:text-white"
          >
            Where knowledge
            <br />
            <span className="text-slate-400 dark:text-slate-500">connects</span>
          </motion.h1>

          {/* Subheading - Clean and minimal */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-lg md:text-xl text-slate-500 dark:text-slate-400 mb-12 max-w-xl mx-auto leading-relaxed font-light"
          >
            Transform scattered information into a unified knowledge graph. 
            Find answers, discover connections, and unlock insights across all your documents.
          </motion.p>

          {/* CTA - Minimal and elegant */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="flex flex-col sm:flex-row gap-4 justify-center items-center"
          >
            <Link
              href="/signup"
              className="group px-8 py-4 bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-medium rounded-full transition-all duration-300 hover:bg-slate-800 dark:hover:bg-slate-100"
            >
              Start for free
              <span className="inline-block ml-2 transition-transform group-hover:translate-x-1">→</span>
            </Link>
            <Link
              href="/demo"
              className="px-8 py-4 text-slate-600 dark:text-slate-400 font-medium rounded-full border border-slate-200 dark:border-slate-800 transition-all duration-300 hover:border-slate-300 dark:hover:border-slate-700 hover:text-slate-900 dark:hover:text-white"
            >
              Watch demo
            </Link>
          </motion.div>

          {/* Trust - Minimal text only */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.8 }}
            className="mt-20"
          >
            <p className="text-xs tracking-widest uppercase text-slate-400 dark:text-slate-600 mb-6">
              Trusted by teams at
            </p>
            <div className="flex flex-wrap justify-center gap-8 md:gap-12 opacity-40">
              {['Stripe', 'Vercel', 'Linear', 'Notion'].map((company) => (
                <span key={company} className="text-sm font-medium text-slate-500 dark:text-slate-500 tracking-wide">
                  {company}
                </span>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Minimal product preview */}
        <motion.div
          initial={{ opacity: 0, y: 60 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.5 }}
          className="mt-20 max-w-4xl mx-auto"
        >
          <div className="relative rounded-2xl overflow-hidden border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 shadow-2xl shadow-slate-200/50 dark:shadow-black/50">
            {/* Window chrome */}
            <div className="px-4 py-3 border-b border-slate-100 dark:border-slate-800 flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-slate-200 dark:bg-slate-700" />
              <div className="w-3 h-3 rounded-full bg-slate-200 dark:bg-slate-700" />
              <div className="w-3 h-3 rounded-full bg-slate-200 dark:bg-slate-700" />
              <div className="flex-1 mx-4">
                <div className="h-5 bg-slate-100 dark:bg-slate-800 rounded-md max-w-xs mx-auto" />
              </div>
            </div>
            
            {/* Content */}
            <div className="p-8 md:p-12">
              <div className="flex items-start gap-6">
                {/* Sidebar */}
                <div className="hidden md:block w-48 space-y-4">
                  <div className="h-3 w-20 bg-slate-100 dark:bg-slate-800 rounded" />
                  <div className="space-y-2">
                    <div className="h-2 w-32 bg-slate-50 dark:bg-slate-800/50 rounded" />
                    <div className="h-2 w-28 bg-slate-50 dark:bg-slate-800/50 rounded" />
                    <div className="h-2 w-24 bg-slate-50 dark:bg-slate-800/50 rounded" />
                  </div>
                </div>
                
                {/* Main content */}
                <div className="flex-1 space-y-6">
                  <div className="h-8 w-3/4 bg-slate-100 dark:bg-slate-800 rounded-lg" />
                  <div className="space-y-3">
                    <div className="h-3 w-full bg-slate-50 dark:bg-slate-800/50 rounded" />
                    <div className="h-3 w-5/6 bg-slate-50 dark:bg-slate-800/50 rounded" />
                    <div className="h-3 w-4/6 bg-slate-50 dark:bg-slate-800/50 rounded" />
                  </div>
                  <div className="h-20 w-full bg-slate-50 dark:bg-slate-800/50 rounded-lg border border-slate-100 dark:border-slate-800" />
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-slate-200 dark:via-slate-800 to-transparent" />
    </section>
  );
}
