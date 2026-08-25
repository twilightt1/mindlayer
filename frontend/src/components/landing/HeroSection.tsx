"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";
import Link from "next/link";
import { GlowOrb, GradientText } from "@/components/ui/BackgroundEffects";
import { TypewriterText } from "@/components/ui/AdvancedEffects";

export function HeroSection() {
  const ref = useRef(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start start", "end start"],
  });

  const y = useTransform(scrollYProgress, [0, 1], [0, 200]);
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0]);

  return (
    <section ref={ref} className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Premium Background */}
      <div className="fixed inset-0 -z-10">
        <div className="absolute inset-0 bg-background" />
        
        {/* Animated glow orbs */}
        <GlowOrb color="violet-500" size={600} position={{ top: "10%", left: "30%" }} blur={150} opacity={15} />
        <GlowOrb color="purple-500" size={500} position={{ top: "40%", right: "10%" }} blur={120} opacity={10} />
        <GlowOrb color="pink-500" size={400} position={{ bottom: "20%", left: "20%" }} blur={100} opacity={8} />
        
        {/* Grid overlay */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_50%,black_40%,transparent_100%)]" />
      </div>

      <motion.div style={{ y, opacity }} className="relative z-10 container mx-auto px-6 py-32">
        <div className="max-w-4xl mx-auto text-center">
          {/* Status badge */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mb-10"
          >
            <motion.span 
              className="inline-flex items-center gap-2 px-4 py-2 text-xs font-medium tracking-widest uppercase text-white/60 border border-white/10 rounded-full backdrop-blur-sm bg-white/5 cursor-pointer"
              whileHover={{ scale: 1.02 }}
            >
              <motion.span 
                className="w-1.5 h-1.5 bg-emerald-500 rounded-full"
                animate={{ scale: [1, 1.2, 1], opacity: [1, 0.7, 1] }}
                transition={{ duration: 2, repeat: Infinity }}
              />
              AI-Powered Knowledge Platform
            </motion.span>
          </motion.div>

          {/* Main heading with gradient */}
          <motion.h1
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.1 }}
            className="text-5xl md:text-7xl lg:text-8xl font-black tracking-tighter mb-8 leading-[1.1]"
          >
            <span className="text-white">Transform knowledge</span>
            <br />
            <GradientText from="from-violet-400" to="to-pink-400">
              into intelligence
            </GradientText>
          </motion.h1>

          {/* Typewriter subtitle */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mb-12"
          >
            <TypewriterText 
              text="Connect documents, notes, and data sources. Let AI surface insights and connections." 
              className="text-lg md:text-xl text-white/50 leading-relaxed"
              delay={800}
              speed={30}
            />
          </motion.div>

          {/* CTA buttons with animations */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="flex flex-col sm:flex-row gap-4 justify-center items-center"
          >
            <motion.div
              whileHover={{ scale: 1.02, y: -2 }}
              whileTap={{ scale: 0.98 }}
              className="relative group"
            >
              {/* Glow effect */}
              <div className="absolute -inset-1 rounded-full bg-gradient-to-r from-violet-600 via-purple-600 to-pink-600 opacity-50 blur-lg transition-opacity duration-300 group-hover:opacity-75" />
              
              <Link
                href="/signup"
                className="relative flex items-center gap-2 px-8 py-4 bg-white text-background font-bold rounded-full transition-all duration-300 hover:shadow-[0_0_50px_rgba(139,92,246,0.4)]"
              >
                Start building free
                <motion.span
                  animate={{ x: [0, 4, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                >
                  →
                </motion.span>
              </Link>
            </motion.div>
            
            <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.98 }}>
              <Link
                href="/demo"
                className="px-8 py-4 text-white/70 font-medium rounded-full border border-white/20 backdrop-blur-sm transition-all duration-300 hover:bg-white/5 hover:text-white hover:border-white/30 cursor-pointer"
              >
                Watch demo
              </Link>
            </motion.div>
          </motion.div>

          {/* Trust indicators */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="mt-20 pt-10 border-t border-white/10"
          >
            <p className="text-xs tracking-[0.2em] uppercase text-white/30 mb-6">
              Trusted by teams at
            </p>
            <motion.div 
              className="flex flex-wrap justify-center gap-8 md:gap-12"
              style={{ filter: 'grayscale(100%)', opacity: 0.4 }}
            >
              {['Stripe', 'Vercel', 'Linear', 'Notion', 'Figma'].map((company, i) => (
                <motion.span
                  key={company}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.7 + i * 0.1 }}
                  className="text-sm font-semibold text-white tracking-wide"
                >
                  {company}
                </motion.span>
              ))}
            </motion.div>
          </motion.div>
        </div>

        {/* Product preview with parallax */}
        <motion.div
          initial={{ opacity: 0, y: 100 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 0.5 }}
          className="mt-24 relative"
        >
          {/* Glow behind preview */}
          <motion.div 
            className="absolute inset-0 bg-gradient-to-r from-violet-500/20 via-purple-500/20 to-pink-500/20 blur-[100px] scale-110"
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 4, repeat: Infinity }}
          />
          
          {/* Preview card */}
          <motion.div 
            className="relative rounded-2xl overflow-hidden border border-white/10 bg-white/5 backdrop-blur-xl shadow-[0_0_100px_rgba(139,92,246,0.15)]"
            whileHover={{ y: -5 }}
            transition={{ type: "spring", stiffness: 300, damping: 20 }}
          >
            {/* Window controls */}
            <div className="px-4 py-3 border-b border-white/10 flex items-center gap-2">
              <motion.div 
                className="w-3 h-3 rounded-full bg-red-500/80"
                whileHover={{ scale: 1.2 }}
              />
              <motion.div 
                className="w-3 h-3 rounded-full bg-yellow-500/80"
                whileHover={{ scale: 1.2 }}
              />
              <motion.div 
                className="w-3 h-3 rounded-full bg-green-500/80"
                whileHover={{ scale: 1.2 }}
              />
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
          </motion.div>
        </motion.div>
      </motion.div>

      {/* Bottom fade */}
      <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
      
      {/* Scroll indicator */}
      <motion.div
        className="absolute bottom-8 left-1/2 -translate-x-1/2"
        animate={{ y: [0, 8, 0] }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        <div className="w-6 h-10 rounded-full border-2 border-white/20 flex items-start justify-center p-2">
          <motion.div
            className="w-1 h-2 bg-white/50 rounded-full"
            animate={{ y: [0, 8, 0], opacity: [1, 0, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
        </div>
      </motion.div>
    </section>
  );
}
