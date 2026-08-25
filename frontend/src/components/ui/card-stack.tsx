"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import { motion, AnimatePresence } from "framer-motion";

interface CardStackItem {
  id: number;
  name: string;
  designation?: string;
  content: React.ReactNode;
}

interface CardStackProps {
  cards: CardStackItem[];
  offset?: number;
  scaleFactor?: number;
  className?: string;
}

export function CardStack({ 
  cards, 
  offset = 10, 
  scaleFactor = 0.05,
  className 
}: CardStackProps) {
  const [activeIndex, setActiveIndex] = useState(0);

  const handleNext = () => {
    setActiveIndex((prev) => (prev + 1) % cards.length);
  };

  const handlePrev = () => {
    setActiveIndex((prev) => (prev - 1 + cards.length) % cards.length);
  };

  return (
    <div className={cn("relative", className)}>
      <div className="relative h-[300px] md:h-[400px]">
        {cards.map((card, index) => {
          const isActive = index === activeIndex;
          const offsetFromActive = Math.abs(index - activeIndex);
          const isBehind = index < activeIndex;

          return (
            <motion.div
              key={card.id}
              onClick={handleNext}
              className={cn(
                "absolute inset-0 rounded-xl border border-border bg-card p-6 cursor-pointer",
                "flex flex-col justify-between",
                isBehind && "pointer-events-none"
              )}
              initial={false}
              animate={{
                scale: isActive ? 1 : 1 - offsetFromActive * scaleFactor,
                y: isActive ? 0 : -offsetFromActive * offset,
                zIndex: cards.length - offsetFromActive,
                opacity: isActive ? 1 : 0.6 - offsetFromActive * 0.1,
              }}
              transition={{
                type: "spring",
                stiffness: 300,
                damping: 30,
              }}
            >
              <div className="flex-1">
                {card.content}
              </div>
              {(card.name || card.designation) && (
                <div className="flex items-center gap-3 mt-4 pt-4 border-t border-border">
                  <div className="w-10 h-10 rounded-full bg-primary/20" />
                  <div>
                    {card.name && (
                      <p className="font-medium text-sm text-foreground">{card.name}</p>
                    )}
                    {card.designation && (
                      <p className="text-xs text-muted-foreground">{card.designation}</p>
                    )}
                  </div>
                </div>
              )}
            </motion.div>
          );
        })}
      </div>

      {/* Navigation dots */}
      <div className="flex justify-center gap-2 mt-4">
        {cards.map((_, index) => (
          <button
            key={index}
            onClick={() => setActiveIndex(index)}
            className={cn(
              "w-2 h-2 rounded-full transition-all duration-300",
              index === activeIndex 
                ? "bg-primary w-6" 
                : "bg-muted-foreground/30 hover:bg-muted-foreground/50"
            )}
          />
        ))}
      </div>
    </div>
  );
}

// Expandable card that shows additional info on click
interface ExpandableCardProps {
  title: string;
  description?: string;
  children?: React.ReactNode;
  defaultExpanded?: boolean;
  className?: string;
}

export function ExpandableCard({
  title,
  description,
  children,
  defaultExpanded = false,
  className,
}: ExpandableCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <motion.div
      layout
      className={cn(
        "rounded-xl border border-border bg-card overflow-hidden transition-all duration-300",
        className
      )}
    >
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-4 md:p-6 flex items-center justify-between text-left"
      >
        <div>
          <h3 className="font-semibold text-foreground">{title}</h3>
          {description && (
            <p className="text-sm text-muted-foreground mt-1">{description}</p>
          )}
        </div>
        <motion.div
          animate={{ rotate: isExpanded ? 180 : 0 }}
          transition={{ duration: 0.2 }}
          className="w-6 h-6 flex items-center justify-center text-muted-foreground"
        >
          ▼
        </motion.div>
      </button>
      
      <AnimatePresence initial={false}>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="px-4 md:px-6 pb-4 md:pb-6"
          >
            <div className="border-t border-border pt-4">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
