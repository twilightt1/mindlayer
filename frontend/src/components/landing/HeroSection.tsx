"use client";

import { motion } from "framer-motion";
import Link from "next/link";

export function HeroSection() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Background with subtle glow */}
      <div className="absolute inset-0 bg-background" />
      
      {/* Ambient glow orbs */}
      <div className="absolute inset-0 overflow-hidden">
        {/* Primary glow */}
        <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-gradient-to-r from-violet-500/20 to-purple-500/20 rounded-full blur-[120px] animate-pulse-glow" />
        
        {/* Secondary glow */}
        <div className="absolute bottom-1/4 right-1/4 w-[600px] h-[600px] bg-gradient-to-l from-purple-500/10 to-pink-500/10 rounded-full blur-[100px] animate-pulse-glow" style={{ animationDelay: '1.5s' }} />
        
        {/* Subtle grid */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_50%,black_40%,transparent_100%)]" />
      </div>

      <div className="relative z-10 container mx-auto px-6 py-32">
        <div className="max-w-4xl mx-auto text-center">
          {/* Badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-10"
          >
            <span className="inline-flex items-center gap-2 px-4 py-2 text-xs font-medium tracking-widest uppercase text-white/60 border border-white/10 rounded-full backdrop-blur-sm bg-white/5">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
              AI-Powered Knowledge Platform
            </span>
          </motion.div>

          {/* Main heading with gradient */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-8 leading-[1.1]"
          >
            <span className="text-white">Transform knowledge</span>
            <br />
            <span className="bg-gradient-to-r from-violet-400 via-purple-400 to-pink-400 bg-clip-text text-transparent">
              into intelligence
            </span>
          </motion.h1>

          {/* Subheading */}
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-lg md:text-xl text-white/50 mb-12 max-w-2xl mx-auto leading-relaxed"
          >
            Connect your documents, notes, and data sources. 
            Let AI surface insights and connections you never knew existed.
          </motion.p>

          {/* CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-4 justify-center items-center"
          >
            <Link
              href="/signup"
              className="group relative px-8 py-4 bg-white text-background font-semibold rounded-full transition-all duration-300 hover:scale-105 hover:shadow-[0_0_40px_rgba(139,92,246,0.4)]"
            >
              <span>Start building free</span>
              <span className="inline-block ml-2 transition-transform group-hover:translate-x-1">→</span>
            </Link>
            <Link
              href="/demo"
              className="px-8 py-4 text-white/70 font-medium rounded-full border border-white/20 backdrop-blur-sm transition-all duration-300 hover:bg-white/5 hover:text-white hover:border-white/30"
            >
              Watch demo
            </Link>
          </motion.div>

          {/* Trust indicators */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.5 }}
            className="mt-20 pt-10 border-t border-white/10"
          >
            <p className="text-xs tracking-[0.2em] uppercase text-white/40 mb-6">
              Trusted by teams at
            </p>
            <div className="flex flex-wrap justify-center gap-8 md:gap-12 opacity-40"
              style={{ filter: 'grayscale(100%)' }}
            >
              {['Stripe', 'Vercel', 'Linear', 'Notion', 'Figma'].map((company) => (
                <span key={company} className="text-sm font-medium text-white tracking-wide">
                  {company}
                </span>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Product preview */}
        <motion.div
          initial={{ opacity: 0, y: 60 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.4 }}
          className="mt-20 relative"
        >
          {/* Glow effect behind preview */}
          <div className="absolute inset-0 bg-gradient-to-r from-violet-500/20 via-purple-500/20 to-pink-500/20 blur-[80px] scale-110" />
          
          {/* Preview card */}
          <div className="relative rounded-2xl overflow-hidden border border-white/10 bg-white/5 backdrop-blur-xl shadow-[0_0_80px_rgba(139,92,246,0.15)]">
            {/* Window controls */}
            <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500/80" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
              <div className="w-3 h-3 rounded-full bg-green-500/80" />
              <div className="flex-1 mx-4">
                <div className="h-6 bg-white/5 rounded-md max-w-sm mx-auto" />
              </div>
            </div>
            
            {/* Content */}
            <div className="p-8 md:p-12">
              <div className="flex items-start gap-8">
                {/* Sidebar mock */}
                <div className="hidden md:block w-40 space-y-4">
                  <div className="h-3 w-16 bg-white/10 rounded" />
                  <div className="space-y-2">
                    <div className="h-2 w-full bg-white/5 rounded" />
                    <div className="h-2 w-3/4 bg-white/5 rounded" />
                    <div className="h-2 w-full bg-white/5 rounded" />
                    <div className="h-2 w-2/3 bg-white/5 rounded" />
                  </div>
                </div>
                
                {/* Main content mock */}
                <div className="flex-1 space-y-6">
                  <div className="h-8 w-3/4 bg-gradient-to-r from-white/20 to-white/10 rounded-lg" />
                  <div className="space-y-3">
                    <div className="h-3 w-full bg-white/5 rounded" />
                    <div className="h-3 w-5/6 bg-white/5 rounded" />
                    <div className="h-3 w-4/6 bg-white/5 rounded" />
                  </div>
                  <div className="h-32 w-full bg-gradient-to-br from-violet-500/10 to-purple-500/10 rounded-xl border border-white/10" />
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
    </section>
  );
}
