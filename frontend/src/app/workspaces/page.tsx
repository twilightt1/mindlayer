import { Metadata } from "next";
import dynamic from "next/dynamic";
import { Suspense } from "react";
import { PageSkeleton } from "@/components/ui/skeleton";

// Lazy load the heavy dashboard component
const WorkspacesDashboard = dynamic(
  () => import("@/components/workspaces/WorkspacesDashboard").then((mod) => mod.WorkspacesDashboard),
  {
    loading: () => <PageSkeleton />,
    ssr: true,
  }
);

export const metadata: Metadata = {
  title: "Workspaces | MindLayer",
  description: "Collaborate with your team on shared knowledge bases.",
};

export default function WorkspacesPage() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <div className="min-h-screen bg-background">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <WorkspacesDashboard />
        </div>
      </div>
    </Suspense>
  );
}
