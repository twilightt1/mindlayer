import { Metadata } from "next";
import { DiscoveryDashboard } from "@/components/discovery/DiscoveryDashboard";

export const metadata: Metadata = {
  title: "Discovery | MindLayer",
  description: "Explore hidden connections across your knowledge with guided discovery journeys.",
};

export default function DiscoveryPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <DiscoveryDashboard />
      </div>
    </div>
  );
}
