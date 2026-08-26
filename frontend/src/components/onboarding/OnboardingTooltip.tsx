"use client";

import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { useOnboarding, OnboardingStep } from "./OnboardingProvider";
import { X, ChevronLeft, ChevronRight } from "lucide-react";

interface OnboardingTooltipProps {
  className?: string;
}

export function OnboardingTooltip({ className }: OnboardingTooltipProps) {
  const { state, nextStep, prevStep, skipTour, getCurrentStep, getTourSteps } = useOnboarding();
  const [targetRect, setTargetRect] = useState<DOMRect | null>(null);
  const [position, setPosition] = useState<{ top: number; left: number }>({ top: 0, left: 0 });
  const tooltipRef = useRef<HTMLDivElement>(null);
  
  const currentStep = getCurrentStep();
  const steps = getTourSteps();
  
  // Find target element and calculate position
  useEffect(() => {
    if (!currentStep?.target) return;
    
    const updatePosition = () => {
      const element = document.querySelector(currentStep.target);
      if (element) {
        const rect = element.getBoundingClientRect();
        setTargetRect(rect);
        
        const tooltip = tooltipRef.current;
        if (tooltip) {
          const tooltipRect = tooltip.getBoundingClientRect();
          const placement = currentStep.placement || "bottom";
          
          let top = 0;
          let left = 0;
          
          switch (placement) {
            case "top":
              top = rect.top - tooltipRect.height - 16;
              left = rect.left + (rect.width - tooltipRect.width) / 2;
              break;
            case "bottom":
              top = rect.bottom + 16;
              left = rect.left + (rect.width - tooltipRect.width) / 2;
              break;
            case "left":
              top = rect.top + (rect.height - tooltipRect.height) / 2;
              left = rect.left - tooltipRect.width - 16;
              break;
            case "right":
              top = rect.top + (rect.height - tooltipRect.height) / 2;
              left = rect.right + 16;
              break;
          }
          
          // Keep tooltip within viewport
          left = Math.max(16, Math.min(left, window.innerWidth - tooltipRect.width - 16));
          top = Math.max(16, top);
          
          setPosition({ top, left });
        }
      }
    };
    
    updatePosition();
    
    // Recalculate on resize
    window.addEventListener("resize", updatePosition);
    return () => window.removeEventListener("resize", updatePosition);
  }, [currentStep, state.currentStep]);

  if (!state.isActive || !currentStep) return null;

  const isFirstStep = state.currentStep === 0;
  const isLastStep = state.currentStep === steps.length - 1;

  return (
    <>
      {/* Backdrop overlay */}
      <div 
        className="fixed inset-0 z-[9998] pointer-events-none"
        style={{
          background: "radial-gradient(circle at var(--spotlight-x, 50%) var(--spotlight-y, 50%), transparent 0%, rgba(0,0,0,0.5) 100%)",
        }}
      />
      
      {/* Highlight ring around target */}
      {targetRect && (
        <div
          className="fixed z-[9999] border-2 border-primary rounded-lg pointer-events-none animate-pulse"
          style={{
            top: targetRect.top - 4,
            left: targetRect.left - 4,
            width: targetRect.width + 8,
            height: targetRect.height + 8,
            boxShadow: "0 0 0 4px rgba(var(--primary-rgb, 99, 102, 241), 0.3)",
          }}
        />
      )}
      
      {/* Tooltip */}
      <div
        ref={tooltipRef}
        className={cn(
          "fixed z-[10000] w-80 bg-card border border-border rounded-xl shadow-2xl",
          "animate-in fade-in zoom-in-95 duration-200",
          className
        )}
        style={{
          top: position.top,
          left: position.left,
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-xs font-medium text-primary">
              {state.currentStep + 1}
            </div>
            <span className="text-xs text-muted-foreground">
              Step {state.currentStep + 1} of {state.totalSteps}
            </span>
          </div>
          <button
            onClick={skipTour}
            className="p-1 rounded-md hover:bg-accent transition-colors"
            aria-label="Skip tour"
          >
            <X className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
        
        {/* Content */}
        <div className="p-4">
          <h3 className="font-semibold text-foreground mb-2">
            {currentStep.title}
          </h3>
          <p className="text-sm text-muted-foreground">
            {currentStep.description}
          </p>
        </div>
        
        {/* Footer */}
        <div className="flex items-center justify-between p-4 border-t border-border bg-muted/30 rounded-b-xl">
          <button
            onClick={prevStep}
            disabled={isFirstStep}
            className={cn(
              "flex items-center gap-1 text-sm transition-colors",
              isFirstStep ? "text-muted-foreground/50 cursor-not-allowed" : "text-muted-foreground hover:text-foreground"
            )}
          >
            <ChevronLeft className="w-4 h-4" />
            Back
          </button>
          
          <button
            onClick={nextStep}
            className="btn-premium px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-1"
          >
            {isLastStep ? "Finish" : "Next"}
            {!isLastStep && <ChevronRight className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </>
  );
}
