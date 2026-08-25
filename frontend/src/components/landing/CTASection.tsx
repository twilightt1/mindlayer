"use client";

import { motion } from "framer-motion";
import { GradientText } from "@/components/ui/BackgroundEffects";
import { GlowButton } from "@/components/ui/Spotlight";

export function CTASection() {
  return (
    <section className="relative py-32 overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 bg-background" />
      
      {/* Gradient */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-violet-500/10 to-transparent" />

      {/* Glow orbs */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-violet-500/20 rounded-full blur-[120px]" />
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-[120px]" />

      <div className="relative z-10 container mx-auto px-6">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="relative max-w-4xl mx-auto text-center"
        >
          {/* Decorative border */}
          <div className="absolute inset-0 bg-gradient-to-r from-violet-500/20 via-purple-500/20 to-pink-500/20 rounded-3xl blur-xl opacity-50" />
          
          {/* Card */}
          <div className="relative border border-white/10 rounded-3xl bg-gradient-to-b from-white/10 to-transparent backdrop-blur-xl p-16 md:p-20">
            {/* Inner glow */}
            <div className="absolute inset-0 bg-gradient-to-b from-violet-500/10 to-transparent rounded-3xl" />
            
            {/* Content */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
              className="relative"
            >
              <h2 className="text-4xl md:text-5xl lg:text-6xl font-black tracking-tighter text-white mb-6">
                Ready to transform
                <br />
                <GradientText className="from-violet-400 via-purple-400 to-pink-400">
                  your knowledge?
                </GradientText>
              </h2>
              
              <p className="text-lg text-white/50 mb-10 max-w-xl mx-auto">
                Join thousands of teams who have unlocked the power of their knowledge with MindLayer.
              </p>
              
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <GlowButton
                  className="px-8 py-4 bg-gradient-to-r from-violet-600 to-purple-600 text-white font-semibold rounded-full hover:from-violet-500 hover:to-purple-500 shadow-lg shadow-violet-500/25 transition-all duration-300 cursor-pointer"
                >
                  Start free trial
                </GlowButton>
                
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  className="px-8 py-4 bg-white/10 text-white font-semibold rounded-full hover:bg-white/20 border border-white/10 transition-all duration-300 cursor-pointer"
                >
                  Schedule demo
                </motion.button>
              </div>
              
              <p className="mt-6 text-sm text-white/30">
                No credit card required · 14-day free trial
              </p>
            </motion.div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
