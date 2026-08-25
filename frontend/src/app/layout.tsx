import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "@/styles/globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "MindLayer - AI-Powered Knowledge Graph",
  description: "Transform scattered information into connected knowledge. Discover insights you didn't know you needed.",
  keywords: ["AI", "knowledge management", "RAG", "document analysis", "insights"],
  openGraph: {
    title: "MindLayer - AI-Powered Knowledge Graph",
    description: "Transform scattered information into connected knowledge",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className={inter.className}>
        {children}
      </body>
    </html>
  );
}
