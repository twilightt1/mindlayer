"use client";

import { ReactNode } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { AppSidebar } from "./AppSidebar";
import { useProtectedRoute } from "@/components/auth";

interface DashboardLayoutProps {
  children: ReactNode;
  className?: string;
}

export function DashboardLayout({ children, className }: DashboardLayoutProps) {
  // Client-side auth gate: the auth_state cookie only signals "a session may
  // exist" (middleware.ts) — verify the real token before rendering the app.
  const { isAuthenticated, isLoading } = useProtectedRoute();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <motion.div
          animate={{ opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1.5, repeat: Infinity }}
          className="text-white/60 text-sm"
        >
          Loading...
        </motion.div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-white/60 text-sm">Redirecting to sign in...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Sidebar */}
      <AppSidebar />
      
      {/* Main content */}
      <motion.main
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className={cn(
          "min-h-screen pl-[260px]", // Account for expanded sidebar
          className
        )}
      >
        {children}
      </motion.main>
    </div>
  );
}

export default DashboardLayout;
