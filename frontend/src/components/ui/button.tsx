"use client";

import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface GlowButtonProps {
  children: ReactNode;
  className?: string;
  onClick?: () => void;
}

export function GlowButton({ children, className, onClick }: GlowButtonProps) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "relative overflow-hidden group",
        className
      )}
    >
      {/* Glow effect */}
      <div className="absolute inset-0 bg-gradient-to-r from-violet-500/0 via-white/10 to-violet-500/0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 -translate-x-full group-hover:translate-x-full" />
      
      {children}
    </button>
  );
}
