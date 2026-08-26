import type { Metadata } from "next";
import { DM_Sans } from "next/font/google";
import "@/styles/globals.css";

const dmSans = DM_Sans({ 
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
  variable: "--font-dm-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Orivory - AI Knowledge Platform",
  description: "Transform scattered information into a unified knowledge graph. Find answers, discover connections, and unlock insights.",
  keywords: ["AI", "knowledge management", "RAG", "document analysis", "insights"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body className={`${dmSans.variable} font-sans antialiased`}>
        {children}
      </body>
    </html>
  );
}
