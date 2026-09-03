import type { Metadata } from "next";
import { DM_Sans } from "next/font/google";
import { ClientProviders } from "@/components/ClientProviders";
import "@/styles/globals.css";

const dmSans = DM_Sans({ 
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800", "900"],
  variable: "--font-dm-sans",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL("https://orivory.ai"),
  title: {
    default: "Orivory - AI Second Brain for Knowledge Management",
    template: "%s | Orivory",
  },
  description: "Open-source AI second brain. Transform scattered information into a unified knowledge graph with semantic search, RAG-powered insights, and intelligent connections.",
  keywords: [
    "AI second brain",
    "knowledge management",
    "RAG",
    "semantic search",
    "document analysis",
    "AI memory",
    "self-hosted",
    "open source AI",
  ],
  authors: [{ name: "Orivory Team", url: "https://orivory.ai" }],
  creator: "Orivory",
  publisher: "Orivory",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  twitter: {
    card: "summary_large_image",
    title: "Orivory - AI Second Brain",
    description: "Open-source AI second brain. Transform scattered information into a unified knowledge graph.",
    images: ["/og-image.png"],
    creator: "@orivoryai",
  },
  openGraph: {
    type: "website",
    locale: "en_US",
    url: "https://orivory.ai",
    siteName: "Orivory",
    title: "Orivory - AI Second Brain for Knowledge Management",
    description: "Open-source AI second brain. Transform scattered information into a unified knowledge graph with semantic search, RAG-powered insights, and intelligent connections.",
    images: [
      {
        url: "/og-image.png",
        width: 1200,
        height: 630,
        alt: "Orivory - AI Second Brain",
      },
    ],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark scroll-smooth">
      <body className={`${dmSans.variable} font-sans antialiased`}>
        <ClientProviders>
          {children}
        </ClientProviders>
      </body>
    </html>
  );
}
