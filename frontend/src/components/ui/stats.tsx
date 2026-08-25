"use client";

import { useEffect, useState, useRef } from "react";
import { cn } from "@/lib/utils";
import { motion, useInView } from "framer-motion";

interface StatItem {
  label: string;
  value: number | string;
  suffix?: string;
  prefix?: string;
  description?: string;
}

interface StatsProps {
  items: StatItem[];
  className?: string;
  columns?: 2 | 3 | 4;
  animate?: boolean;
}

function AnimatedNumber({ value, animate = true }: { value: number; animate?: boolean }) {
  const [displayValue, setDisplayValue] = useState(0);
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });

  useEffect(() => {
    if (!animate || !isInView) {
      setDisplayValue(value);
      return;
    }

    const duration = 2000;
    const startTime = Date.now();
    
    const animateValue = () => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayValue(Math.round(value * eased));
      
      if (progress < 1) {
        requestAnimationFrame(animateValue);
      }
    };

    requestAnimationFrame(animateValue);
  }, [value, animate, isInView]);

  return <span ref={ref}>{displayValue}</span>;
}

export function Stats({ items, className, columns = 4, animate = true }: StatsProps) {
  const gridCols = {
    2: "grid-cols-2",
    3: "grid-cols-3",
    4: "grid-cols-4",
  };

  return (
    <div className={cn("grid", gridCols[columns], "gap-4 md:gap-8", className)}>
      {items.map((item, index) => (
        <motion.div
          key={index}
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ delay: index * 0.1 }}
          className="text-center"
        >
          <div className="text-3xl md:text-4xl font-bold text-foreground tracking-tight">
            {item.prefix}
            {typeof item.value === "number" ? (
              <AnimatedNumber value={item.value} animate={animate} />
            ) : (
              item.value
            )}
            {item.suffix}
          </div>
          <div className="text-sm font-medium text-muted-foreground mt-1">
            {item.label}
          </div>
          {item.description && (
            <div className="text-xs text-muted-foreground mt-1">
              {item.description}
            </div>
          )}
        </motion.div>
      ))}
    </div>
  );
}

interface StatCardProps {
  label: string;
  value: number | string;
  change?: number;
  changeLabel?: string;
  icon?: React.ReactNode;
  className?: string;
}

export function StatCard({ label, value, change, changeLabel, icon, className }: StatCardProps) {
  const isPositive = change && change > 0;
  const isNegative = change && change < 0;

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      whileInView={{ opacity: 1, scale: 1 }}
      viewport={{ once: true }}
      className={cn(
        "relative rounded-xl border border-border bg-card p-4 md:p-6",
        "hover:border-border/80 transition-all duration-300",
        className
      )}
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm text-muted-foreground">{label}</p>
          <p className="text-2xl md:text-3xl font-bold text-foreground mt-1">
            {typeof value === "number" ? (
              <AnimatedNumber value={value} />
            ) : (
              value
            )}
          </p>
        </div>
        {icon && (
          <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center text-primary">
            {icon}
          </div>
        )}
      </div>
      
      {change !== undefined && (
        <div className="mt-3 flex items-center gap-1">
          <span
            className={cn(
              "text-sm font-medium",
              isPositive && "text-green-500",
              isNegative && "text-red-500",
              !isPositive && !isNegative && "text-muted-foreground"
            )}
          >
            {isPositive && "+"}
            {change}%
          </span>
          {changeLabel && (
            <span className="text-xs text-muted-foreground">{changeLabel}</span>
          )}
        </div>
      )}
    </motion.div>
  );
}
