"use client";

import { ReactNode } from "react";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { ToastProvider } from "@/components/ui/Toast";
import { ThemeProvider } from "@/hooks/useTheme";
import { CommandPalette } from "@/components/ui/CommandPalette";
import { FirstTimeOnboarding } from "@/components/onboarding/FirstTimeOnboarding";
import { ProactiveInsightToast } from "@/components/insights/ProactiveInsightToast";
import { usePageTracking } from "@/lib/analytics";

/** Tracks page views on every route change. Lives inside AuthProvider so
 * usePageTracking's flush carries a valid access token. */
function PageViewTracker() {
  usePageTracking();
  return null;
}

export function ClientProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          <PageViewTracker />
          {children}
          <CommandPalette />
          <FirstTimeOnboarding />
          <ProactiveInsightToast />
        </ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default ClientProviders;
