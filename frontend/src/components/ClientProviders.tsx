"use client";

import { ReactNode } from "react";
import { AuthProvider } from "@/components/auth/AuthProvider";
import { ToastProvider } from "@/components/ui/Toast";
import { ThemeProvider } from "@/hooks/useTheme";
import { CommandPalette } from "@/components/ui/CommandPalette";
import { FirstTimeOnboarding } from "@/components/onboarding/FirstTimeOnboarding";

export function ClientProviders({ children }: { children: ReactNode }) {
  return (
    <ThemeProvider>
      <AuthProvider>
        <ToastProvider>
          {children}
          <CommandPalette />
          <FirstTimeOnboarding />
        </ToastProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default ClientProviders;
