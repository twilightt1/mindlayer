"use client";

import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface BentoGridProps {
  children: ReactNode[];
  className?: string;
}

export function BentoGrid({ children, className }: BentoGridProps) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4",
        className
      )}
    >
      {children}
    </div>
  );
}

interface BentoCardProps {
  children?: ReactNode;
  className?: string;
  icon?: ReactNode;
  title?: string;
  description?: string;
  onClick?: () => void;
}

export function BentoCard({ children, className, icon, title, description, onClick }: BentoCardProps) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "relative row-span-1 rounded-xl border border-border bg-card p-6",
        "hover:border-border/80 transition-all duration-300",
        "hover:shadow-lg hover:shadow-glow-primary/5",
        "group",
        onClick && "cursor-pointer",
        className
      )}
    >
      {/* Gradient overlay on hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      
      {/* Content */}
      <div className="relative z-10">
        {icon && (
          <div className="mb-4 w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
            {icon}
          </div>
        )}
        {title && (
          <h3 className="font-semibold text-foreground mb-1">{title}</h3>
        )}
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
        {children}
      </div>
    </div>
  );
}

// Large featured card that spans 2 columns
export function BentoCardFeatured({ 
  children, 
  className, 
  icon, 
  title, 
  description,
  span = "md:col-span-2",
  onClick
}: BentoCardProps & { span?: string }) {
  return (
    <div
      onClick={onClick}
      className={cn(
        "relative row-span-1 rounded-xl border border-border bg-card p-6",
        "hover:border-border/80 transition-all duration-300",
        "hover:shadow-lg hover:shadow-glow-primary/5",
        "group",
        onClick && "cursor-pointer",
        span,
        className
      )}
    >
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 to-transparent rounded-xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
      
      <div className="relative z-10 h-full flex flex-col">
        {icon && (
          <div className="mb-4 w-12 h-12 rounded-xl bg-primary/10 flex items-center justify-center">
            {icon}
          </div>
        )}
        {title && (
          <h3 className="font-semibold text-lg text-foreground mb-2">{title}</h3>
        )}
        {description && (
          <p className="text-sm text-muted-foreground mb-4">{description}</p>
        )}
        <div className="mt-auto">
          {children}
        </div>
      </div>
    </div>
  );
}
