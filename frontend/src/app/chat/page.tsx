"use client";

import { ChatInterface } from "@/components/chat/ChatInterface";

export default function ChatPage() {
  return (
    <main className="min-h-screen bg-background">
      <div className="h-screen">
        <ChatInterface />
      </div>
    </main>
  );
}
