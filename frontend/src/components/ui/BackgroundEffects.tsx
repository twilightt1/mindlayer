"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";

interface ParallaxSectionProps {
  children: React.ReactNode;
  className?: string;
  speed?: number;
}

export function ParallaxSection({ children, className = "", speed = 0.5 }: ParallaxSectionProps) {
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  });

  const y = useTransform(scrollYProgress, [0, 1], [0, -100 * speed]);

  return (
    <motion.div ref={ref} style={{ y }} className={className}>
      {children}
    </motion.div>
  );
}

interface GradientTextProps {
  children: React.ReactNode;
  className?: string;
  from?: string;
  to?: string;
}

export function GradientText({ 
  children, 
  className = "", 
  from = "from-violet-400", 
  to = "to-purple-400" 
}: GradientTextProps) {
  return (
    <span className={`bg-gradient-to-r ${from} ${to} bg-clip-text text-transparent ${className}`}>
      {children}
    </span>
  );
}

interface RippleEffectProps {
  children: React.ReactNode;
  className?: string;
}

export function RippleEffect({ children, className = "" }: RippleEffectProps) {
  return (
    <div className={`relative overflow-hidden ${className}`}>
      {children}
      <div className="absolute inset-0 pointer-events-none">
        <div className="absolute inset-0 bg-gradient-to-r from-violet-500/0 via-purple-500/0 to-pink-500/0 opacity-0 hover:opacity-20 transition-opacity duration-500" />
      </div>
    </div>
  );
}

interface ShimmerProps {
  children: React.ReactNode;
  className?: string;
}

export function Shimmer({ children, className = "" }: ShimmerProps) {
  return (
    <div className={`relative overflow-hidden ${className}`}>
      {children}
      <div className="absolute inset-0 -translate-x-full animate-[shimmer_2s_infinite] bg-gradient-to-r from-transparent via-white/10 to-transparent" />
      <style jsx>{`
        @keyframes shimmer {
          100% {
            transform: translateX(100%);
          }
        }
      `}</style>
    </div>
  );
}

interface GlowOrbProps {
  color?: string;
  size?: number;
  position?: { top?: string; bottom?: string; left?: string; right?: string };
  blur?: number;
  opacity?: number;
}

export function GlowOrb({ 
  color = "violet-500", 
  size = 400, 
  position = {}, 
  blur = 120, 
  opacity = 20 
}: GlowOrbProps) {
  return (
    <motion.div
      className={`absolute rounded-full bg-${color} opacity-${opacity}`}
      style={{
        width: size,
        height: size,
        filter: `blur(${blur}px)`,
        ...position,
      }}
      animate={{
        scale: [1, 1.1, 1],
        opacity: [opacity * 0.01, opacity * 0.02, opacity * 0.01],
      }}
      transition={{
        duration: 6,
        repeat: Infinity,
        ease: "easeInOut",
      }}
    />
  );
}

export function PremiumBackground() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
      {/* Base gradient */}
      <div className="absolute inset-0 bg-background" />
      
      {/* Primary glow */}
      <GlowOrb 
        color="violet-500" 
        size={600} 
        position={{ top: "10%", left: "30%" }}
        blur={150}
        opacity={15}
      />
      
      {/* Secondary glow */}
      <GlowOrb 
        color="purple-500" 
        size={500} 
        position={{ top: "40%", right: "10%" }}
        blur={120}
        opacity={10}
      />
      
      {/* Tertiary glow */}
      <GlowOrb 
        color="pink-500" 
        size={400} 
        position={{ bottom: "20%", left: "20%" }}
        blur={100}
        opacity={8}
      />
      
      {/* Grid overlay */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_50%,black_40%,transparent_100%)]" />
      
      {/* Noise texture */}
      <div className="absolute inset-0 opacity-[0.015]" style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
      }} />
    </div>
  );
}

interface CardGlowProps {
  children: React.ReactNode;
  className?: string;
  glowColor?: string;
}

export function CardGlow({ children, className = "", glowColor = "violet" }: CardGlowProps) {
  return (
    <div className={`relative group ${className}`}>
      {/* Glow layer */}
      <div className={`absolute -inset-0.5 rounded-2xl bg-gradient-to-r from-${glowColor}-500/0 via-${glowColor}-500/50 to-${glowColor}-500/0 opacity-0 group-hover:opacity-100 blur transition-all duration-500`} />
      {/* Card */}
      <div className="relative rounded-2xl bg-white/5 border border-white/10 backdrop-blur-sm transition-all duration-300 group-hover:bg-white/10 group-hover:border-white/20">
        {children}
      </div>
    </div>
  );
}

interface AnimatedBorderProps {
  children: React.ReactNode;
  className?: string;
}

export function AnimatedBorder({ children, className = "" }: AnimatedBorderProps) {
  return (
    <div className={`relative p-[1px] overflow-hidden rounded-2xl ${className}`}>
      <div 
        className="absolute inset-0"
        style={{
          background: "linear-gradient(var(--angle, 0deg), #8b5cf6, #a855f7, #ec4899, #8b5cf6)",
          animation: "rotate 4s linear infinite",
        }}
      />
      <div className="relative rounded-2xl bg-background">
        {children}
      </div>
      <style jsx global>{`
        @keyframes rotate {
          to {
            --angle: 360deg;
          }
        }
        @property --angle {
          syntax: '<angle>';
          initial-value: 0deg;
          inherits: false;
        }
      `}</style>
    </div>
  );
}
