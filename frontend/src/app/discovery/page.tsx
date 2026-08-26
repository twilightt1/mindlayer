import { Metadata } from "next";
import dynamic from "next/dynamic";
import { Suspense } from "react";
import { PageSkeleton } from "@/components/ui/skeleton";

// Lazy load the heavy dashboard component
const DiscoveryDashboard = dynamic(
  () => import("@/components/discovery/DiscoveryDashboard").then((mod) => mod.DiscoveryDashboard),
  {
    loading: () => <PageSkeleton />,
    ssr: true,
  }
);

export const metadata: Metadata = {
  title: "Discovery | Orivory",
  description: "Explore hidden connections across your knowledge with guided discovery journeys.",
};

export default function DiscoveryPage() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <div className="min-h-screen bg-background">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <DiscoveryDashboard />
        </div>
      </div>
    </Suspense>
  );
}
