"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { sendChatMessage, type ChatMessage, type ChatSession } from "@/lib/api/chat";
import { Sparkles, Send, Trash2, ChevronDown, Settings, X, Copy, CheckCheck } from "lucide-react";

// ============================================================================
// DESIGN TOKENS - Consistent with Orivory's Nebulous Precision
// ============================================================================

const DESIGN = {
  colors: {
    bg: "bg-background",
    surface: "bg-white/[0.03]",
    surfaceHover: "hover:bg-white/[0.06]",
    border: "border-white/[0.08]",
    borderHover: "hover:border-white/[0.15]",
    text: {
      primary: "text-white",
      secondary: "text-white/60",
      muted: "text-white/40",
    },
    accent: {
      violet: "text-violet-400",
      pink: "text-pink-400",
      gradient: "bg-gradient-to-r from-violet-400 to-pink-400",
    },
    glow: {
      violet: "shadow-[0_0_30px_rgba(139,92,246,0.15)]",
      pink: "shadow-[0_0_30px_rgba(236,72,153,0.15)]",
    },
  },
  spacing: {
    xs: "p-2",
    sm: "p-3",
    md: "p-4",
    lg: "p-6",
  },
  radius: {
    sm: "rounded-lg",
    md: "rounded-xl",
    lg: "rounded-2xl",
  },
  transition: "transition-all duration-300 ease-out",
};

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface ChatInterfaceProps {
  className?: string;
  workspaceId?: string;
  initialSessionId?: string;
  onSessionChange?: (session: ChatSession | null) => void;
}

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

/**
 * Message bubble with streaming support and sources
 */
function MessageBubble({ 
  message, 
  isStreaming = false 
}: { 
  message: ChatMessage; 
  isStreaming?: boolean;
}) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "flex gap-3 group",
        isUser && "flex-row-reverse"
      )}
    >
      {/* Avatar */}
      <div className={cn(
        "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium",
        isUser 
          ? "bg-gradient-to-br from-violet-500 to-purple-600 text-white" 
          : "bg-white/[0.05] border border-white/[0.1]"
      )}>
        {isUser ? (
          <span>U</span>
        ) : (
          <Sparkles className="w-4 h-4 text-violet-400" />
        )}
      </div>

      {/* Message content */}
      <div className={cn(
        "flex-1 max-w-[75%]",
        isUser && "flex flex-col items-end"
      )}>
        <div className={cn(
          "relative",
          isUser && "items-end"
        )}>
          {/* Message bubble */}
          <div className={cn(
            "px-4 py-3",
            isUser 
              ? "bg-gradient-to-r from-violet-600/30 to-purple-600/30 border border-violet-500/20" 
              : "bg-white/[0.03] border border-white/[0.08]",
            DESIGN.radius.md,
            DESIGN.transition
          )}>
            {/* Streaming cursor */}
            {isStreaming && (
              <motion.span
                className="inline-block w-0.5 h-4 bg-violet-400 ml-1 align-middle"
                animate={{ opacity: [1, 0, 1] }}
                transition={{ duration: 0.8, repeat: Infinity }}
              />
            )}
            
            <p className={cn(
              "text-sm leading-relaxed whitespace-pre-wrap",
              isUser ? "text-white" : "text-white/90"
            )}>
              {message.content}
            </p>
          </div>

          {/* Actions */}
          <div className={cn(
            "absolute -top-2 right-0 flex gap-1 opacity-0 group-hover:opacity-100",
            isUser && "right-auto left-0"
          )}>
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-md bg-background/90 border border-white/[0.1] hover:bg-white/[0.1] transition-colors"
              title="Copy"
            >
              {copied ? (
                <CheckCheck className="w-3 h-3 text-emerald-400" />
              ) : (
                <Copy className="w-3 h-3 text-white/50" />
              )}
            </button>
          </div>
        </div>

        {/* Sources */}
        {message.sources && message.sources.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            className="mt-2 w-full"
          >
            <div className="space-y-1">
              <p className="text-xs text-white/40 uppercase tracking-wider mb-2">
                Sources
              </p>
              {message.sources.map((source, i) => (
                <div
                  key={i}
                  className="px-3 py-2 bg-white/[0.02] border border-white/[0.05] rounded-lg"
                >
                  <p className="text-xs text-white/60 truncate">{source.title}</p>
                  <p className="text-xs text-white/40 line-clamp-1 mt-0.5">
                    {source.snippet}
                  </p>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* Timestamp */}
        <span className="text-[10px] text-white/30 mt-1 block">
          {message.timestamp.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </span>
      </div>
    </motion.div>
  );
}

/**
 * Input area with suggestion chips
 */
function ChatInput({ 
  onSend, 
  disabled = false,
  placeholder = "Ask anything about your knowledge base..."
}: { 
  onSend: (message: string) => void; 
  disabled?: boolean;
  placeholder?: string;
}) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput("");
      textareaRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  return (
    <div className={cn(
      "relative rounded-xl border",
      "bg-white/[0.02] border-white/[0.08]",
      "focus-within:border-violet-500/40 focus-within:bg-white/[0.04]",
      "transition-all duration-300"
    )}>
      {/* Gradient border effect on focus */}
      <div className="absolute inset-0 rounded-xl bg-gradient-to-r from-violet-500/0 via-violet-500/20 to-pink-500/0 opacity-0 focus-within:opacity-100 transition-opacity duration-300 -z-10 blur-sm" />
      
      <textarea
        ref={textareaRef}
        value={input}
        onChange={(e) => setInput(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        disabled={disabled}
        className={cn(
          "w-full px-4 py-3 pr-12 bg-transparent",
          "text-white placeholder:text-white/30",
          "text-sm leading-relaxed resize-none",
          "focus:outline-none",
          "disabled:opacity-50"
        )}
        rows={1}
      />
      
      <div className="absolute right-2 bottom-2 flex items-center gap-1">
        <motion.button
          onClick={handleSubmit}
          disabled={!input.trim() || disabled}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className={cn(
            "p-2 rounded-lg",
            "bg-gradient-to-r from-violet-600 to-purple-600",
            "disabled:opacity-30 disabled:cursor-not-allowed",
            "shadow-lg shadow-violet-500/20",
            "transition-all duration-200"
          )}
        >
          <Send className="w-4 h-4 text-white" />
        </motion.button>
      </div>
    </div>
  );
}

/**
 * Quick suggestion chips
 */
const SUGGESTIONS = [
  "What did I last read about AI agents?",
  "Summarize my meeting notes from yesterday",
  "Find connections between my recent documents",
  "What insights can you share today?",
];

function SuggestionChips({ onSelect }: { onSelect: (text: string) => void }) {
  return (
    <div className="flex flex-wrap gap-2">
      {SUGGESTIONS.map((suggestion) => (
        <motion.button
          key={suggestion}
          whileHover={{ scale: 1.02, y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => onSelect(suggestion)}
          className={cn(
            "px-3 py-1.5 text-xs",
            "bg-white/[0.03] border border-white/[0.08]",
            "text-white/60 hover:text-white",
            "rounded-full",
            "transition-all duration-200",
            "hover:border-violet-500/30 hover:bg-violet-500/5"
          )}
        >
          {suggestion}
        </motion.button>
      ))}
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function ChatInterface({ 
  className,
  workspaceId,
  initialSessionId,
  onSessionChange,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, streamingContent, scrollToBottom]);

  // Handle sending message
  const handleSend = async (content: string) => {
    // Add user message immediately
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content,
      timestamp: new Date(),
    };
    
    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);
    setStreamingContent("");

    try {
      await sendChatMessage(
        {
          content,
          workspace_id: workspaceId,
          session_id: currentSession?.id || initialSessionId,
        },
        // On chunk
        (chunk) => {
          setStreamingContent((prev) => prev + chunk);
        },
        // On complete
        (fullMessage) => {
          const assistantMessage: ChatMessage = {
            id: `assistant-${Date.now()}`,
            role: "assistant",
            content: fullMessage,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, assistantMessage]);
          setStreamingContent("");
        },
        // On error
        (error) => {
          const errorMessage: ChatMessage = {
            id: `error-${Date.now()}`,
            role: "assistant",
            content: `Sorry, I encountered an error: ${error.message}`,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, errorMessage]);
          setStreamingContent("");
        }
      );
    } catch (error) {
      // Error handled in callback
    } finally {
      setIsLoading(false);
    }
  };

  // Clear chat
  const handleClear = () => {
    setMessages([]);
    setStreamingContent("");
  };

  return (
    <div className={cn(
      "flex flex-col h-full",
      DESIGN.colors.bg,
      className
    )}>
      {/* Header */}
      <div className={cn(
        "flex items-center justify-between px-4 py-3",
        "border-b border-white/[0.05]"
      )}>
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className={cn(
              "w-8 h-8 rounded-lg",
              "bg-gradient-to-br from-violet-500/20 to-pink-500/20",
              "border border-violet-500/30"
            )}>
              <Sparkles className="w-4 h-4 text-violet-400 absolute inset-0 m-auto" />
            </div>
            {/* Pulsing indicator */}
            {isLoading && (
              <motion.div
                className="absolute -inset-1 rounded-xl border border-violet-500/50"
                animate={{ opacity: [0.5, 1, 0.5] }}
                transition={{ duration: 1.5, repeat: Infinity }}
              />
            )}
          </div>
          <div>
            <h3 className={cn("text-sm font-medium", DESIGN.colors.text.primary)}>
              Chat
            </h3>
            <p className={cn("text-xs", DESIGN.colors.text.muted)}>
              {currentSession?.title || "New conversation"}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleClear}
            className={cn(
              "p-2 rounded-lg",
              "text-white/40 hover:text-white/70",
              "hover:bg-white/[0.05]",
              "transition-colors"
            )}
            title="Clear chat"
          >
            <Trash2 className="w-4 h-4" />
          </motion.button>
          
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={() => setShowSettings(!showSettings)}
            className={cn(
              "p-2 rounded-lg",
              showSettings ? "text-violet-400 bg-violet-500/10" : "text-white/40 hover:text-white/70",
              "hover:bg-white/[0.05]",
              "transition-colors"
            )}
            title="Settings"
          >
            <Settings className="w-4 h-4" />
          </motion.button>
        </div>
      </div>

      {/* Messages area */}
      <div 
        ref={messagesContainerRef}
        className="flex-1 overflow-y-auto px-4 py-6"
      >
        <div className="max-w-3xl mx-auto space-y-6">
          {/* Welcome state */}
          {messages.length === 0 && !streamingContent && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center py-12"
            >
              <div className="mb-6">
                <div className="relative inline-block">
                  <div className={cn(
                    "w-16 h-16 rounded-2xl",
                    "bg-gradient-to-br from-violet-500/20 to-pink-500/20",
                    "border border-violet-500/30",
                    "flex items-center justify-center",
                    "shadow-xl shadow-violet-500/10"
                  )}>
                    <Sparkles className="w-8 h-8 text-violet-400" />
                  </div>
                </div>
              </div>
              
              <h2 className={cn(
                "text-xl font-semibold mb-2",
                DESIGN.colors.text.primary
              )}>
                What would you like to discover?
              </h2>
              <p className={cn(
                "text-sm mb-8 max-w-md mx-auto",
                DESIGN.colors.text.secondary
              )}>
                Ask questions about your documents, get insights from your knowledge base, or explore connections.
              </p>
              
              <SuggestionChips onSelect={handleSend} />
            </motion.div>
          )}

          {/* Messages */}
          <AnimatePresence mode="popLayout">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
          </AnimatePresence>

          {/* Streaming message */}
          {streamingContent && (
            <MessageBubble 
              message={{
                id: "streaming",
                role: "assistant",
                content: streamingContent,
                timestamp: new Date(),
              }}
              isStreaming={true}
            />
          )}

          {/* Loading indicator */}
          {isLoading && !streamingContent && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex items-center gap-3"
            >
              <div className={cn(
                "w-8 h-8 rounded-full",
                "bg-white/[0.05] border border-white/[0.1]",
                "flex items-center justify-center"
              )}>
                <Sparkles className="w-4 h-4 text-violet-400" />
              </div>
              <div className="flex gap-1">
                {[0, 1, 2].map((i) => (
                  <motion.div
                    key={i}
                    className="w-2 h-2 bg-violet-400/50 rounded-full"
                    animate={{ y: [0, -4, 0], opacity: [0.5, 1, 0.5] }}
                    transition={{
                      duration: 0.6,
                      repeat: Infinity,
                      delay: i * 0.1,
                    }}
                  />
                ))}
              </div>
            </motion.div>
          )}
        </div>
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className={cn(
        "px-4 py-4",
        "border-t border-white/[0.05]",
        "bg-gradient-to-t from-background via-background/95 to-transparent"
      )}>
        <div className="max-w-3xl mx-auto">
          <ChatInput 
            onSend={handleSend} 
            disabled={isLoading}
          />
          <p className={cn(
            "text-[10px] text-center mt-2",
            DESIGN.colors.text.muted
          )}>
            AI may make mistakes. Consider verifying important information.
          </p>
        </div>
      </div>

      {/* Settings panel */}
      <AnimatePresence>
        {showSettings && (
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: 20 }}
            className={cn(
              "absolute right-4 top-16 w-72",
              "bg-background/95 backdrop-blur-xl",
              "border border-white/[0.1]",
              "rounded-xl p-4",
              "shadow-2xl shadow-black/50",
              "z-50"
            )}
          >
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-sm font-medium text-white">Settings</h4>
              <button
                onClick={() => setShowSettings(false)}
                className="p-1 rounded hover:bg-white/[0.05]"
              >
                <X className="w-4 h-4 text-white/50" />
              </button>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="text-xs text-white/50 mb-1 block">
                  Response style
                </label>
                <select className={cn(
                  "w-full px-3 py-2 text-sm",
                  "bg-white/[0.05] border border-white/[0.1]",
                  "rounded-lg text-white/80",
                  "focus:outline-none focus:border-violet-500/50"
                )}>
                  <option value="balanced">Balanced</option>
                  <option value="concise">Concise</option>
                  <option value="detailed">Detailed</option>
                </select>
              </div>
              
              <div>
                <label className="text-xs text-white/50 mb-1 block">
                  Include sources
                </label>
                <div className="flex items-center gap-2">
                  <input 
                    type="checkbox" 
                    defaultChecked
                    className="w-4 h-4 rounded border-white/[0.2] bg-white/[0.05]"
                  />
                  <span className="text-xs text-white/60">
                    Show document citations
                  </span>
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default ChatInterface;
