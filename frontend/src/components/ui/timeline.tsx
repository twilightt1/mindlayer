"use client";

import { useRef } from "react";
import { cn } from "@/lib/utils";
import { motion, useScroll, useTransform } from "framer-motion";

interface TimelineEntry {
  title: string;
  content: React.ReactNode;
  date?: string;
}

interface TimelineProps {
  entries: TimelineEntry[];
  className?: string;
}

export function Timeline({ entries, className }: TimelineProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start center", "end end"],
  });

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      {/* Vertical line */}
      <div className="absolute left-4 md:left-1/2 top-0 bottom-0 w-px bg-gradient-to-b from-primary via-border to-transparent" />
      
      <div className="space-y-12">
        {entries.map((entry, index) => {
          const isLeft = index % 2 === 0;
          
          return (
            <div
              key={index}
              className="relative flex md:justify-center"
            >
              {/* Timeline dot */}
              <motion.div
                initial={{ scale: 0, opacity: 0 }}
                whileInView={{ scale: 1, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="absolute left-4 md:left-1/2 -translate-x-1/2 w-3 h-3 rounded-full bg-primary border-2 border-background z-10"
              />
              
              {/* Content */}
              <motion.div
                initial={{ opacity: 0, x: isLeft ? -20 : 20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 + 0.2 }}
                className={cn(
                  "ml-12 md:ml-0 md:w-[calc(50%-2rem)]",
                  isLeft ? "md:mr-auto md:pr-8" : "md:ml-auto md:pl-8"
                )}
              >
                {entry.date && (
                  <span className="inline-block px-2 py-1 text-xs font-medium text-primary bg-primary/10 rounded-full mb-2">
                    {entry.date}
                  </span>
                )}
                <h3 className="font-semibold text-foreground mb-2">{entry.title}</h3>
                <div className="text-sm text-muted-foreground">
                  {entry.content}
                </div>
              </motion.div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// Simple vertical timeline with bullets
export function SimpleTimeline({ entries, className }: TimelineProps) {
  return (
    <div className={cn("relative", className)}>
      <div className="absolute left-2 top-2 bottom-2 w-px bg-border" />
      
      <div className="space-y-6">
        {entries.map((entry, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: index * 0.1 }}
            className="relative pl-8"
          >
            {/* Bullet */}
            <div className="absolute left-0 top-1.5 w-4 h-4 rounded-full bg-primary/20 border-2 border-primary" />
            
            {entry.date && (
              <span className="text-xs text-muted-foreground">{entry.date}</span>
            )}
            <h4 className="font-medium text-foreground">{entry.title}</h4>
            <div className="mt-1 text-sm text-muted-foreground">
              {entry.content}
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
