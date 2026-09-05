"use client";

import { SecurityDashboard } from "@/components/security/SecurityDashboard";

export default function SecurityPage() {
  return (
    <main className="min-h-screen bg-background">
      <div className="container mx-auto px-6 py-8 max-w-6xl">
        <h1 className="mb-2 text-2xl font-bold">Security &amp; Access</h1>
        <p className="mb-8 text-muted-foreground">
          Which agents can read your memory, what they accessed, and proof of
          every erasure.
        </p>
        <SecurityDashboard />
      </div>
    </main>
  );
}
