"use client";

import { useState, useRef, useEffect } from "react";
import { motion, useMotionValue, useSpring, AnimatePresence } from "framer-motion";

interface SpotlightCardProps {
  children: React.ReactNode;
  className?: string;
}

export function SpotlightCard({ children, className = "" }: SpotlightCardProps) {
  const divRef = useRef<HTMLDivElement>(null);
  const [isHovered, setIsHovered] = useState(false);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  const smoothOptions = { damping: 20, stiffness: 300, mass: 0.5 };
  const smoothMouseX = useSpring(mouseX, smoothOptions);
  const smoothMouseY = useSpring(mouseY, smoothOptions);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!divRef.current) return;
    const rect = divRef.current.getBoundingClientRect();
    mouseX.set(e.clientX - rect.left);
    mouseY.set(e.clientY - rect.top);
  };

  return (
    <div
      ref={divRef}
      className={`relative overflow-hidden rounded-2xl ${className}`}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onMouseMove={handleMouseMove}
    >
      {/* Spotlight */}
      <motion.div
        className="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-300"
        style={{
          background: useMotionValue(
            `radial-gradient(circle at var(--x) var(--y), rgba(139, 92, 246, 0.15) 0%, transparent 50%)`
          ),
          opacity: isHovered ? 1 : 0,
        }}
        animate={{
          background: `radial-gradient(circle at ${smoothMouseX}px ${smoothMouseY}px, rgba(139, 92, 246, 0.15) 0%, transparent 50%)`,
        }}
      />
      
      {/* Border glow on hover */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-violet-500/0 via-purple-500/0 to-pink-500/0 opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
      
      {children}
    </div>
  );
}

interface MovingBorderProps {
  children: React.ReactNode;
  className?: string;
  duration?: number;
}

export function MovingBorder({ 
  children, 
  className = "", 
  duration = 3000 
}: MovingBorderProps) {
  return (
    <div className={`relative rounded-2xl p-[1px] overflow-hidden ${className}`}>
      <div
        className="absolute inset-0 rounded-2xl"
        style={{
          background: `linear-gradient(var(--angle, 0deg), #8b5cf6, #a855f7, #ec4899, #8b5cf6)`,
          animation: `rotate ${duration}ms linear infinite`,
        }}
      />
      <div className="relative h-full w-full rounded-2xl bg-background">
        {children}
      </div>
      <style jsx>{`
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

interface BentoCardProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}

export function BentoCard({ children, className = "", delay = 0 }: BentoCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
      className={`group relative rounded-2xl border border-white/10 bg-white/5 backdrop-blur-sm p-6 transition-all duration-300 hover:bg-white/10 hover:border-violet-500/30 ${className}`}
    >
      {/* Subtle glow on hover */}
      <div className="absolute inset-0 rounded-2xl bg-gradient-to-r from-violet-500/0 to-purple-500/0 opacity-0 transition-opacity duration-500 group-hover:opacity-20" />
      {children}
    </motion.div>
  );
}

interface FadeInProps {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  direction?: "up" | "down" | "left" | "right" | "none";
}

export function FadeIn({ 
  children, 
  className = "", 
  delay = 0, 
  direction = "up" 
}: FadeInProps) {
  const getInitial = () => {
    switch (direction) {
      case "up": return { y: 30, opacity: 0 };
      case "down": return { y: -30, opacity: 0 };
      case "left": return { x: 30, opacity: 0 };
      case "right": return { x: -30, opacity: 0 };
      default: return { opacity: 0 };
    }
  };

  return (
    <motion.div
      initial={getInitial()}
      whileInView={{ x: 0, y: 0, opacity: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.6, delay, ease: [0.25, 0.46, 0.45, 0.94] }}
      className={className}
    >
      {children}
    </motion.div>
  );
}

interface TextGenerateProps {
  children: string;
  className?: string;
  delay?: number;
}

export function TextGenerate({ children, className = "", delay = 0 }: TextGenerateProps) {
  return (
    <motion.span
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      transition={{ duration: 0.5, delay }}
      className={className}
    >
      {children.split("").map((char, i) => (
        <motion.span
          key={i}
          initial={{ opacity: 0, y: 10 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.3, delay: delay + i * 0.03 }}
        >
          {char === " " ? "\u00A0" : char}
        </motion.span>
      ))}
    </motion.span>
  );
}

interface ParallaxScrollProps {
  children: React.ReactNode;
  className?: string;
}

export function ParallaxScroll({ children, className = "" }: ParallaxScrollProps) {
  return (
    <div className={`relative overflow-hidden ${className}`}>
      <motion.div
        initial={{ y: 0 }}
        whileInView={{ y: "-20%" }}
        viewport={{ once: true }}
        transition={{ duration: 0.8 }}
        className="will-change-transform"
      >
        {children}
      </motion.div>
    </div>
  );
}

interface GlowButtonProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export function GlowButton({ children, className = "", onClick }: GlowButtonProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={`relative group cursor-pointer ${className}`}
    >
      {/* Glow effect */}
      <div className="absolute -inset-1 rounded-full bg-gradient-to-r from-violet-600 via-purple-600 to-pink-600 opacity-50 blur-lg transition-opacity duration-300 group-hover:opacity-75" />
      
      {/* Button */}
      <div className="relative rounded-full bg-gradient-to-r from-violet-600 via-purple-600 to-pink-600 px-8 py-4 text-white font-semibold transition-all duration-300 group-hover:from-violet-500 group-hover:via-purple-500 group-hover:to-pink-500">
        {children}
      </div>
    </motion.button>
  );
}

interface AnimatedGridProps {
  children: React.ReactNode;
  className?: string;
}

export function AnimatedGrid({ children, className = "" }: AnimatedGridProps) {
  return (
    <div className={`relative ${className}`}>
      {/* Grid background */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] [mask-image:radial-gradient(ellipse_80%_50%_at_50%_50%,black_40%,transparent_100%)]" />
      
      {/* Animated gradient overlay */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-b from-violet-500/10 via-transparent to-purple-500/10"
        animate={{
          y: [-20, 20, -20],
        }}
        transition={{
          duration: 8,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />
      
      <div className="relative z-10">{children}</div>
    </div>
  );
}

interface FloatingOrbsProps {
  count?: number;
}

export function FloatingOrbs({ count = 3 }: FloatingOrbsProps) {
  const orbs = Array.from({ length: count }, (_, i) => ({
    size: 300 + i * 200,
    delay: i * 2,
    color: i === 0 ? "from-violet-500/20" : i === 1 ? "from-purple-500/15" : "from-pink-500/10",
  }));

  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {orbs.map((orb, i) => (
        <motion.div
          key={i}
          className={`absolute rounded-full bg-gradient-to-br ${orb.color} to-transparent blur-[100px]`}
          style={{
            width: orb.size,
            height: orb.size,
            left: i === 0 ? "50%" : i === 1 ? "0%" : "auto",
            right: i === 2 ? "0%" : "auto",
            top: i === 1 ? "30%" : "20%",
            transform: "translateX(-50%)",
          }}
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.5, 0.7, 0.5],
            y: [0, -30, 0],
          }}
          transition={{
            duration: 6 + i * 2,
            repeat: Infinity,
            delay: orb.delay,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}
