import { Metadata } from "next";
import dynamic from "next/dynamic";
import { Suspense } from "react";
import { PageSkeleton } from "@/components/ui/skeleton";

// Lazy load the heavy dashboard component
const InsightsDashboard = dynamic(
  () => import("@/components/insights/InsightsDashboard").then((mod) => mod.InsightsDashboard),
  {
    loading: () => <PageSkeleton />,
    ssr: true,
  }
);

export const metadata: Metadata = {
  title: "Discoveries | Orivory",
  description: "Discover hidden connections and insights from your knowledge base.",
};

export default function InsightsPage() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <div className="min-h-screen bg-background">
        <div className="max-w-4xl mx-auto px-4 py-8">
          <InsightsDashboard />
        </div>
      </div>
    </Suspense>
  );
}
