"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/AuthProvider";
import { 
  Home,
  MessageSquare,
  Brain,
  FileText,
  Sparkles,
  BarChart3,
  Settings,
  LogOut,
  ChevronLeft,
  ChevronRight,
  Plus,
  Search,
  Bell
} from "lucide-react";

// ============================================================================
// NAVIGATION ITEMS
// ============================================================================

const NAV_ITEMS = [
  {
    label: "Dashboard",
    href: "/dashboard",
    icon: Home,
    badge: null,
  },
  {
    label: "Chat",
    href: "/chat",
    icon: MessageSquare,
    badge: null,
  },
  {
    label: "Memories",
    href: "/memories",
    icon: Brain,
    badge: null,
  },
  {
    label: "Documents",
    href: "/documents",
    icon: FileText,
    badge: null,
  },
  {
    label: "Insights",
    href: "/insights",
    icon: Sparkles,
    badge: "3",
  },
  {
    label: "Analytics",
    href: "/analytics",
    icon: BarChart3,
    badge: null,
  },
];

const BOTTOM_ITEMS: Array<typeof NAV_ITEMS[0]> = [
  {
    label: "Settings",
    href: "/settings",
    icon: Settings,
    badge: null,
  },
];

// ============================================================================
// SUB-COMPONENTS
// ============================================================================

/**
 * Single nav item with hover effects
 */
function NavItem({ 
  item, 
  isCollapsed,
  isActive 
}: { 
  item: typeof NAV_ITEMS[0]; 
  isCollapsed: boolean;
  isActive: boolean;
}) {
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      className={cn(
        "group relative flex items-center gap-3 px-3 py-2.5 rounded-xl",
        "transition-all duration-300",
        isActive
          ? "bg-gradient-to-r from-violet-500/20 to-purple-500/20"
          : "hover:bg-white/[0.05]"
      )}
    >
      {/* Active indicator */}
      {isActive && (
        <motion.div
          layoutId="activeIndicator"
          className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-gradient-to-b from-violet-500 to-purple-500 rounded-r-full"
        />
      )}

      {/* Icon */}
      <div className={cn(
        "relative z-10 flex items-center justify-center w-9 h-9 rounded-lg",
        isActive
          ? "bg-gradient-to-br from-violet-500 to-purple-600 shadow-lg shadow-violet-500/25"
          : "bg-white/[0.05] group-hover:bg-white/[0.08]"
      )}>
        <Icon className={cn(
          "w-4.5 h-4.5",
          isActive ? "text-white" : "text-white/50 group-hover:text-white/70"
        )} />
      </div>

      {/* Label */}
      <AnimatePresence>
        {!isCollapsed && (
          <motion.span
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: "auto" }}
            exit={{ opacity: 0, width: 0 }}
            className={cn(
              "relative z-10 text-sm font-medium whitespace-nowrap overflow-hidden",
              isActive ? "text-white" : "text-white/50 group-hover:text-white/70"
            )}
          >
            {item.label}
          </motion.span>
        )}
      </AnimatePresence>

      {/* Badge */}
      {!isCollapsed && item.badge && (
        <span className={cn(
          "ml-auto px-2 py-0.5 text-[10px] font-semibold rounded-full",
          "bg-violet-500/20 text-violet-300",
          "border border-violet-500/30"
        )}>
          {item.badge}
        </span>
      )}

      {/* Collapsed badge */}
      {isCollapsed && item.badge && (
        <div className="absolute top-1 right-1 w-2 h-2 bg-violet-500 rounded-full" />
      )}
    </Link>
  );
}

/**
 * User avatar with dropdown
 */
function UserAvatar({ isCollapsed }: { isCollapsed: boolean }) {
  const { user, logout } = useAuth();

  return (
    <div className="relative group">
      <div className={cn(
        "flex items-center gap-3 p-2 rounded-xl",
        "bg-white/[0.03] hover:bg-white/[0.06]",
        "transition-all duration-300 cursor-pointer"
      )}>
        {/* Avatar */}
        <div className={cn(
          "relative flex-shrink-0 rounded-full",
          "bg-gradient-to-br from-violet-500 to-purple-600",
          "flex items-center justify-center",
          isCollapsed ? "w-9 h-9" : "w-10 h-10"
        )}>
          <span className="text-sm font-semibold text-white">
            {user?.name?.[0]?.toUpperCase() || user?.email?.[0]?.toUpperCase() || "U"}
          </span>
          
          {/* Online indicator */}
          <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 rounded-full border-2 border-background" />
        </div>

        {/* Info */}
        {!isCollapsed && (
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">
              {user?.name || "User"}
            </p>
            <p className="text-xs text-white/40 truncate">
              {user?.email}
            </p>
          </div>
        )}

        {/* Logout icon */}
        {!isCollapsed && (
          <LogOut className="w-4 h-4 text-white/30 group-hover:text-red-400 transition-colors" />
        )}
      </div>

      {/* Tooltip when collapsed */}
      {isCollapsed && (
        <div className={cn(
          "absolute left-full ml-2 top-1/2 -translate-y-1/2",
          "px-3 py-2 rounded-lg",
          "bg-background/95 backdrop-blur-xl",
          "border border-white/[0.1]",
          "shadow-xl shadow-black/50",
          "opacity-0 invisible group-hover:opacity-100 group-hover:visible",
          "transition-all duration-200",
          "whitespace-nowrap z-50"
        )}>
          <p className="text-sm text-white">{user?.name || "User"}</p>
          <p className="text-xs text-white/50">{user?.email}</p>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export function AppSidebar() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const pathname = usePathname();

  return (
    <motion.aside
      initial={false}
      animate={{ width: isCollapsed ? 80 : 260 }}
      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        "fixed left-0 top-0 h-screen z-40",
        "flex flex-col",
        "bg-background/80 backdrop-blur-xl",
        "border-r border-white/[0.05]"
      )}
    >
      {/* Header */}
      <div className={cn(
        "flex items-center h-16 px-4",
        isCollapsed ? "justify-center" : "justify-between"
      )}>
        {!isCollapsed && (
          <Link href="/dashboard" className="flex items-center gap-3">
            <div className="relative">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-violet-500/25">
                <span className="text-white font-bold text-base">O</span>
              </div>
              <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-violet-500 to-purple-500 blur-lg opacity-50 -z-10" />
            </div>
            <span className="text-lg font-bold tracking-tight text-white">
              Orivory
            </span>
          </Link>
        )}

        {/* Collapse button */}
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => setIsCollapsed(!isCollapsed)}
          className={cn(
            "p-2 rounded-lg",
            "text-white/40 hover:text-white/70",
            "hover:bg-white/[0.05]",
            "transition-colors"
          )}
        >
          {isCollapsed ? (
            <ChevronRight className="w-4 h-4" />
          ) : (
            <ChevronLeft className="w-4 h-4" />
          )}
        </motion.button>
      </div>

      {/* New chat button */}
      <div className="px-3 pb-4">
        <Link
          href="/chat"
          className={cn(
            "flex items-center justify-center gap-2 w-full",
            "px-4 py-3 rounded-xl",
            "bg-gradient-to-r from-violet-600 to-purple-600",
            "text-white font-medium text-sm",
            "shadow-lg shadow-violet-500/20",
            "hover:shadow-violet-500/30",
            "transition-all duration-300",
            isCollapsed && "px-2"
          )}
        >
          <Plus className="w-4 h-4" />
          {!isCollapsed && <span>New Chat</span>}
        </Link>
      </div>

      {/* Search */}
      {!isCollapsed && (
        <div className="px-3 pb-4">
          <div className={cn(
            "relative rounded-xl border",
            "bg-white/[0.03] border-white/[0.08]",
            "focus-within:border-violet-500/40",
            "transition-all"
          )}>
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" />
            <input
              type="text"
              placeholder="Search..."
              className={cn(
                "w-full pl-10 pr-4 py-2.5",
                "bg-transparent",
                "text-white placeholder:text-white/30 text-sm",
                "focus:outline-none"
              )}
            />
            <kbd className="absolute right-3 top-1/2 -translate-y-1/2 px-1.5 py-0.5 text-[10px] text-white/30 bg-white/[0.05] rounded border border-white/[0.1]">
              ⌘K
            </kbd>
          </div>
        </div>
      )}

      {/* Collapsed search */}
      {isCollapsed && (
        <div className="px-3 pb-4 flex justify-center">
          <button className="p-2.5 rounded-xl bg-white/[0.03] hover:bg-white/[0.06] transition-colors">
            <Search className="w-4 h-4 text-white/40" />
          </button>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => (
          <NavItem
            key={item.href}
            item={item}
            isCollapsed={isCollapsed}
            isActive={pathname === item.href}
          />
        ))}
      </nav>

      {/* Bottom section */}
      <div className="px-3 py-4 border-t border-white/[0.05] space-y-1">
        {BOTTOM_ITEMS.map((item) => (
          <NavItem
            key={item.href}
            item={item}
            isCollapsed={isCollapsed}
            isActive={pathname === item.href}
          />
        ))}
        
        {/* User */}
        <div className="pt-2">
          <UserAvatar isCollapsed={isCollapsed} />
        </div>
      </div>
    </motion.aside>
  );
}

export default AppSidebar;
