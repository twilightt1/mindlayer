"use client";

import { motion } from "framer-motion";
import { ReactNode } from "react";

interface AnimatedGradientBorderProps {
  children: ReactNode;
  className?: string;
  gradientColors?: string[];
}

export function AnimatedGradientBorder({
  children,
  className = "",
  gradientColors = ["#6366f1", "#a855f7", "#ec4899", "#6366f1"],
}: AnimatedGradientBorderProps) {
  return (
    <div className={`relative ${className}`}>
      {/* Animated gradient border */}
      <motion.div
        className="absolute -inset-0.5 rounded-2xl"
        style={{
          background: `linear-gradient(var(--angle, 0deg), ${gradientColors.join(", ")})`,
          animation: "rotate 3s linear infinite",
        }}
      />
      
      {/* Inner content */}
      <div className="relative bg-white dark:bg-slate-900 rounded-2xl">
        {children}
      </div>
      
      {/* CSS for animation */}
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

// Simplified version without CSS variables for broader compatibility
export function GradientBorderCard({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`relative ${className}`}>
      <div className="absolute -inset-0.5 bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500 rounded-2xl opacity-75 hover:opacity-100 transition-opacity duration-300" />
      <div className="relative bg-white dark:bg-slate-900 rounded-2xl">
        {children}
      </div>
    </div>
  );
}
