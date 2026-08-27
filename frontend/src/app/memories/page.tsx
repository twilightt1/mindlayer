"use client";

import { MemoryDashboard } from "@/components/memories/MemoryDashboard";

export default function MemoriesPage() {
  return (
    <main className="min-h-screen bg-background">
      <div className="container mx-auto px-6 py-8 max-w-6xl">
        <MemoryDashboard />
      </div>
    </main>
  );
}
