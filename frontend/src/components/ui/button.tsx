"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { ReactNode } from "react";

// ============================================================================
// GLOW BUTTON - Aceternity-inspired
// ============================================================================

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

// ============================================================================
// SHADCN-STYLE BUTTON
// ============================================================================

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "destructive" | "outline" | "secondary" | "ghost" | "link";
  size?: "default" | "sm" | "lg" | "icon";
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "default", ...props }, ref) => {
    const variants = {
      default: "bg-gradient-to-r from-violet-600 to-purple-600 text-white hover:shadow-lg hover:shadow-violet-500/25",
      destructive: "bg-red-500 text-white hover:bg-red-600",
      outline: "border border-white/10 bg-transparent text-white/70 hover:bg-white/5 hover:border-white/20",
      secondary: "bg-white/10 text-white/70 hover:bg-white/15",
      ghost: "hover:bg-white/5 text-white/70",
      link: "text-violet-400 underline-offset-4 hover:underline",
    };

    const sizes = {
      default: "h-10 px-4 py-2",
      sm: "h-9 rounded-md px-3",
      lg: "h-11 rounded-md px-8",
      icon: "h-10 w-10",
    };

    return (
      <button
        className={cn(
          "inline-flex items-center justify-center rounded-xl text-sm font-medium ring-offset-background transition-all",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-500 focus-visible:ring-offset-2",
          "disabled:pointer-events-none disabled:opacity-50",
          variants[variant],
          sizes[size],
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";

export { Button };
