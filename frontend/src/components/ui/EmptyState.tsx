"use client";

import { cn } from "@/lib/utils";
import { Button } from "./button";

interface EmptyStateProps {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  secondaryAction?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

export function EmptyState({
  icon,
  title,
  description,
  action,
  secondaryAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center py-16 px-4 text-center",
        className
      )}
    >
      {icon && (
        <div className="mb-4 p-4 rounded-full bg-muted text-muted-foreground">
          {icon}
        </div>
      )}
      
      <h3 className="text-lg font-semibold text-foreground mb-2">{title}</h3>
      
      {description && (
        <p className="text-sm text-muted-foreground max-w-md mb-6">
          {description}
        </p>
      )}
      
      <div className="flex gap-3">
        {action && (
          <Button onClick={action.onClick}>
            {action.label}
          </Button>
        )}
        {secondaryAction && (
          <Button variant="outline" onClick={secondaryAction.onClick}>
            {secondaryAction.label}
          </Button>
        )}
      </div>
    </div>
  );
}

// Pre-built empty states for common use cases
export const EmptyStates = {
  Memories: {
    title: "No memories yet",
    description:
      "Start building your second brain by capturing your first memory.",
    actionLabel: "Capture your first memory",
  },
  
  Discovery: {
    title: "Explore your knowledge graph",
    description:
      "Start a discovery journey to find hidden connections between your memories.",
    actionLabel: "Start discovery",
  },
  
  Insights: {
    title: "No insights yet",
    description:
      "Insights are generated automatically as you add more memories. Keep capturing!",
    actionLabel: "Add more memories",
  },
  
  Workspaces: {
    title: "No workspaces yet",
    description:
      "Create a workspace to share knowledge with your team.",
    actionLabel: "Create workspace",
  },
  
  Sources: {
    title: "No sources connected",
    description:
      "Connect your apps to automatically capture memories from your daily work.",
    actionLabel: "Connect a source",
  },
  
  Search: {
    title: "No results found",
    description:
      "Try different keywords or ask a question in natural language.",
  },
};
