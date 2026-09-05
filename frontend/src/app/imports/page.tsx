"use client";

import { ImportDashboard } from "@/components/imports/ImportDashboard";

export default function ImportsPage() {
  return (
    <main className="min-h-screen bg-background">
      <div className="container mx-auto px-6 py-8 max-w-4xl">
        <h1 className="mb-2 text-2xl font-bold">Import memories</h1>
        <p className="mb-8 text-muted-foreground">
          Bring an existing assistant&apos;s history into your Orivory brain.
        </p>
        <ImportDashboard />
      </div>
    </main>
  );
}
