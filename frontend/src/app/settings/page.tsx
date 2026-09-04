"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { DashboardLayout } from "@/components/layout";
import { useAuth } from "@/components/auth";
import { useToast } from "@/components/ui/Toast";
import { 
  User, 
  Shield, 
  Bell, 
  Palette, 
  Globe, 
  Key, 
  Mail,
  Check,
  Loader2,
  Save,
  Keyboard,
  Command,
  Moon,
  Sun,
  Monitor
} from "lucide-react";

// ============================================================================
// DESIGN TOKENS
// ============================================================================

const DESIGN = {
  colors: {
    surface: "bg-white/[0.03]",
    border: "border-white/[0.08]",
    text: {
      primary: "text-white",
      secondary: "text-white/60",
      muted: "text-white/40",
    },
  },
  transition: "transition-all duration-300",
};

// ============================================================================
// KEYBOARD SHORTCUTS
// ============================================================================

const SHORTCUTS = [
  { keys: ["⌘", "K"], description: "Open command palette" },
  { keys: ["⌘", "Enter"], description: "Send message" },
  { keys: ["Esc"], description: "Close modal/dialog" },
  { keys: ["⌘", "N"], description: "New chat" },
  { keys: ["↑", "↓"], description: "Navigate suggestions" },
  { keys: ["⌘", "B"], description: "Toggle sidebar" },
];

// ============================================================================
// SECTIONS
// ============================================================================

const SETTINGS_SECTIONS = [
  { id: "profile", label: "Profile", icon: User },
  { id: "security", label: "Security", icon: Shield },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "appearance", label: "Appearance", icon: Palette },
  { id: "shortcuts", label: "Keyboard Shortcuts", icon: Keyboard },
  { id: "api", label: "API Keys", icon: Key },
];

// ============================================================================
// PROFILE SECTION
// ============================================================================

function ProfileSection() {
  const { user, refreshUser } = useAuth();
  const { success, error } = useToast();
  const [name, setName] = useState(user?.display_name || user?.name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      const token = typeof window !== "undefined" ? localStorage.getItem("auth_token") : null;
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/users/me`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ display_name: name }),
      });
      if (!response.ok) {
        const errBody = await response.json().catch(() => ({}));
        throw new Error(errBody?.detail || `HTTP ${response.status}`);
      }
      await refreshUser();
      success("Profile saved successfully!");
    } catch (e) {
      error(e instanceof Error ? e.message : "Failed to save profile. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-1">Profile Settings</h3>
        <p className="text-sm text-white/50">Manage your account information</p>
      </div>

      {/* Avatar */}
      <div className="flex items-center gap-4">
        <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-2xl font-bold text-white">
          {name?.[0]?.toUpperCase() || email?.[0]?.toUpperCase() || "U"}
        </div>
        <div>
          <button className="px-4 py-2 text-sm font-medium text-white/70 hover:text-white bg-white/[0.05] hover:bg-white/[0.1] border border-white/[0.1] hover:border-white/[0.2] rounded-lg transition-all">
            Change avatar
          </button>
          <p className="text-xs text-white/30 mt-1">JPG, PNG or GIF. Max 2MB.</p>
        </div>
      </div>

      {/* Fields */}
      <div className="grid gap-4">
        <div>
          <label className="block text-sm text-white/70 mb-2">Display Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Your name"
            className={cn(
              "w-full px-4 py-3 rounded-xl",
              "bg-white/[0.03] border border-white/[0.08]",
              "text-white placeholder:text-white/30",
              "focus:outline-none focus:border-violet-500/50",
              "transition-all"
            )}
          />
        </div>

        <div>
          <label className="block text-sm text-white/70 mb-2">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            className={cn(
              "w-full px-4 py-3 rounded-xl",
              "bg-white/[0.03] border border-white/[0.08]",
              "text-white placeholder:text-white/30",
              "focus:outline-none focus:border-violet-500/50",
              "transition-all"
            )}
          />
        </div>
      </div>

      {/* Save */}
      <div className="flex items-center gap-4 pt-4 border-t border-white/[0.05]">
        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.99 }}
          onClick={handleSave}
          disabled={saving}
          className={cn(
            "flex items-center gap-2 px-6 py-2.5 rounded-xl",
            "bg-gradient-to-r from-violet-600 to-purple-600",
            "text-white font-medium text-sm",
            "shadow-lg shadow-violet-500/20",
            "hover:shadow-violet-500/30",
            "transition-all",
            saving && "opacity-50 cursor-not-allowed"
          )}
        >
          {saving ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Save className="w-4 h-4" />
          )}
          {saving ? "Saving..." : "Save changes"}
        </motion.button>
      </div>
    </div>
  );
}

// ============================================================================
// KEYBOARD SHORTCUTS SECTION
// ============================================================================

function ShortcutsSection() {
  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-1">Keyboard Shortcuts</h3>
        <p className="text-sm text-white/50">Quick actions to navigate faster</p>
      </div>

      <div className="grid gap-3">
        {SHORTCUTS.map((shortcut, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className={cn(
              "flex items-center justify-between p-4 rounded-xl",
              "bg-white/[0.03] border border-white/[0.08]",
              "hover:border-white/[0.15]",
              "transition-all"
            )}
          >
            <span className="text-sm text-white/70">{shortcut.description}</span>
            <div className="flex items-center gap-1.5">
              {shortcut.keys.map((key, i) => (
                <kbd
                  key={i}
                  className={cn(
                    "px-2.5 py-1.5 rounded-lg text-xs font-medium",
                    "bg-white/[0.05] border border-white/[0.1]",
                    "text-white/80"
                  )}
                >
                  {key}
                </kbd>
              ))}
            </div>
          </motion.div>
        ))}
      </div>

      <div className={cn(
        "p-4 rounded-xl",
        "bg-violet-500/5 border border-violet-500/20"
      )}>
        <p className="text-sm text-white/60">
          <span className="text-violet-400 font-medium">Pro tip:</span> Press <kbd className="px-1.5 py-0.5 rounded text-xs bg-white/5 border border-white/10">⌘K</kbd> anywhere to open the command palette for quick navigation.
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// SETTINGS PAGE
// ============================================================================

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState("profile");

  const sections: Record<string, JSX.Element> = {
    profile: <ProfileSection />,
    shortcuts: <ShortcutsSection />,
    security: <div className="text-white/50">Security settings coming soon...</div>,
    notifications: <div className="text-white/50">Notification settings coming soon...</div>,
    appearance: <div className="text-white/50">Appearance settings coming soon...</div>,
    api: <div className="text-white/50">API key management coming soon...</div>,
  };

  return (
    <DashboardLayout>
      <div className="p-8 max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white mb-2">Settings</h1>
          <p className="text-white/50">Manage your account and preferences</p>
        </div>

        <div className="grid lg:grid-cols-[280px_1fr] gap-8">
          {/* Sidebar */}
          <div className="space-y-1">
            {SETTINGS_SECTIONS.map((section) => {
              const Icon = section.icon;
              const isActive = activeSection === section.id;

              return (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left",
                    "transition-all",
                    isActive
                      ? "bg-violet-500/10 text-violet-400"
                      : "text-white/60 hover:text-white hover:bg-white/[0.03]"
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{section.label}</span>
                </button>
              );
            })}
          </div>

          {/* Content */}
          <div className={cn(
            "p-6 rounded-2xl",
            "bg-white/[0.02] border border-white/[0.08]",
            "backdrop-blur-xl"
          )}>
            {sections[activeSection] || <ProfileSection />}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
