import { Metadata } from "next";
import { WorkspacesDashboard } from "@/components/workspaces/WorkspacesDashboard";

export const metadata: Metadata = {
  title: "Workspaces | MindLayer",
  description: "Collaborate with your team on shared knowledge bases.",
};

export default function WorkspacesPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <WorkspacesDashboard />
      </div>
    </div>
  );
}
