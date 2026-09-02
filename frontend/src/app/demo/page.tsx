import { redirect } from "next/navigation";

// The landing page's "Watch demo" CTA points here. Route it to the
// features section until a dedicated demo page/video ships.
export default function DemoPage() {
  redirect("/#features");
}
