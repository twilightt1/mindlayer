import { Metadata } from "next";
import { InsightsDashboard } from "@/components/insights/InsightsDashboard";

export const metadata: Metadata = {
  title: "Discoveries | MindLayer",
  description: "Discover hidden connections and insights from your knowledge base.",
};

export default function InsightsPage() {
  return (
    <div className="min-h-screen bg-background">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <InsightsDashboard />
      </div>
    </div>
  );
}
