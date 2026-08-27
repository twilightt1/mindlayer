"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import { DashboardLayout } from "@/components/layout";
import { useAuth } from "@/components/auth";
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
  Save
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
// SECTIONS
// ============================================================================

const SETTINGS_SECTIONS = [
  { id: "profile", label: "Profile", icon: User },
  { id: "security", label: "Security", icon: Shield },
  { id: "notifications", label: "Notifications", icon: Bell },
  { id: "appearance", label: "Appearance", icon: Palette },
  { id: "api", label: "API Keys", icon: Key },
];

// ============================================================================
// PROFILE SECTION
// ============================================================================

function ProfileSection() {
  const { user } = useAuth();
  const [name, setName] = useState(user?.name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    setSaving(false);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
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
            "px-5 py-2.5 rounded-xl",
            "bg-gradient-to-r from-violet-600 to-purple-600",
            "text-white font-medium text-sm",
            "shadow-lg shadow-violet-500/20",
            "disabled:opacity-50",
            "transition-all"
          )}
        >
          {saving ? (
            <span className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />
              Saving...
            </span>
          ) : saved ? (
            <span className="flex items-center gap-2">
              <Check className="w-4 h-4" />
              Saved!
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Save className="w-4 h-4" />
              Save changes
            </span>
          )}
        </motion.button>
      </div>
    </div>
  );
}

// ============================================================================
// SECURITY SECTION
// ============================================================================

function SecuritySection() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-1">Security</h3>
        <p className="text-sm text-white/50">Manage your password and security settings</p>
      </div>

      {/* Password */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm text-white/70 mb-2">Current Password</label>
          <input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            placeholder="••••••••"
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
          <label className="block text-sm text-white/70 mb-2">New Password</label>
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            placeholder="••••••••"
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
          <label className="block text-sm text-white/70 mb-2">Confirm New Password</label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            placeholder="••••••••"
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

      <motion.button
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        className={cn(
          "px-5 py-2.5 rounded-xl",
          "bg-white/[0.05] border border-white/[0.1]",
          "text-white font-medium text-sm",
          "hover:bg-white/[0.1] hover:border-white/[0.15]",
          "transition-all"
        )}
      >
        Update Password
      </motion.button>

      {/* 2FA */}
      <div className="pt-6 border-t border-white/[0.05]">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-white">Two-Factor Authentication</h4>
            <p className="text-xs text-white/40 mt-0.5">Add an extra layer of security</p>
          </div>
          <button className={cn(
            "px-4 py-2 rounded-lg text-sm font-medium",
            "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20",
            "hover:bg-emerald-500/20"
          )}>
            Enable
          </button>
        </div>
      </div>

      {/* Sessions */}
      <div className="pt-6 border-t border-white/[0.05]">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h4 className="text-sm font-medium text-white">Active Sessions</h4>
            <p className="text-xs text-white/40 mt-0.5">Manage your logged-in devices</p>
          </div>
          <button className="text-sm text-red-400 hover:text-red-300">
            Sign out all
          </button>
        </div>
        
        <div className="space-y-2">
          {[
            { device: "Chrome on macOS", location: "Current session", time: "Active now" },
            { device: "Safari on iPhone", location: "San Francisco, CA", time: "2 hours ago" },
          ].map((session, i) => (
            <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-white/[0.02] border border-white/[0.05]">
              <div className="flex items-center gap-3">
                <Globe className="w-4 h-4 text-white/40" />
                <div>
                  <p className="text-sm text-white">{session.device}</p>
                  <p className="text-xs text-white/40">{session.location}</p>
                </div>
              </div>
              <span className={cn(
                "text-xs px-2 py-1 rounded-full",
                session.time === "Active now" 
                  ? "bg-emerald-500/10 text-emerald-400"
                  : "text-white/40"
              )}>
                {session.time}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// NOTIFICATIONS SECTION
// ============================================================================

function NotificationsSection() {
  const [settings, setSettings] = useState({
    emailDigest: true,
    weeklyReport: true,
    newInsights: true,
    chatMentions: true,
    securityAlerts: true,
  });

  const toggle = (key: keyof typeof settings) => {
    setSettings((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-1">Notifications</h3>
        <p className="text-sm text-white/50">Configure how you receive updates</p>
      </div>

      <div className="space-y-4">
        {[
          { key: "emailDigest", label: "Daily Email Digest", description: "Summary of your daily activity" },
          { key: "weeklyReport", label: "Weekly Report", description: "Weekly insights and analytics" },
          { key: "newInsights", label: "New Insights", description: "When new insights are discovered" },
          { key: "chatMentions", label: "Chat Mentions", description: "When someone mentions you in chat" },
          { key: "securityAlerts", label: "Security Alerts", description: "Important security notifications" },
        ].map((item) => (
          <div key={item.key} className="flex items-center justify-between p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
            <div className="flex items-center gap-3">
              <Bell className="w-5 h-5 text-white/40" />
              <div>
                <p className="text-sm font-medium text-white">{item.label}</p>
                <p className="text-xs text-white/40">{item.description}</p>
              </div>
            </div>
            <button
              onClick={() => toggle(item.key as keyof typeof settings)}
              className={cn(
                "relative w-12 h-6 rounded-full transition-colors",
                settings[item.key as keyof typeof settings]
                  ? "bg-violet-500"
                  : "bg-white/[0.1]"
              )}
            >
              <motion.div
                animate={{ x: settings[item.key as keyof typeof settings] ? 24 : 2 }}
                className="absolute top-1 w-4 h-4 rounded-full bg-white shadow-sm"
              />
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============================================================================
// APPEARANCE SECTION
// ============================================================================

function AppearanceSection() {
  const [theme, setTheme] = useState("dark");
  const [fontSize, setFontSize] = useState("medium");

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-1">Appearance</h3>
        <p className="text-sm text-white/50">Customize the look and feel</p>
      </div>

      {/* Theme */}
      <div>
        <label className="block text-sm text-white/70 mb-3">Theme</label>
        <div className="grid grid-cols-3 gap-3">
          {[
            { value: "dark", label: "Dark", icon: "🌙" },
            { value: "light", label: "Light", icon: "☀️" },
            { value: "system", label: "System", icon: "💻" },
          ].map((option) => (
            <button
              key={option.value}
              onClick={() => setTheme(option.value)}
              className={cn(
                "flex flex-col items-center gap-2 p-4 rounded-xl border transition-all",
                theme === option.value
                  ? "bg-violet-500/10 border-violet-500/50 text-white"
                  : "bg-white/[0.02] border-white/[0.08] text-white/60 hover:border-white/[0.15]"
              )}
            >
              <span className="text-2xl">{option.icon}</span>
              <span className="text-sm font-medium">{option.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Font size */}
      <div>
        <label className="block text-sm text-white/70 mb-3">Font Size</label>
        <div className="flex gap-2">
          {["small", "medium", "large"].map((size) => (
            <button
              key={size}
              onClick={() => setFontSize(size)}
              className={cn(
                "flex-1 py-3 rounded-xl border text-sm font-medium transition-all capitalize",
                fontSize === size
                  ? "bg-violet-500/10 border-violet-500/50 text-white"
                  : "bg-white/[0.02] border-white/[0.08] text-white/60 hover:border-white/[0.15]"
              )}
            >
              {size}
            </button>
          ))}
        </div>
      </div>

      {/* Sidebar */}
      <div className="pt-6 border-t border-white/[0.05]">
        <div className="flex items-center justify-between">
          <div>
            <h4 className="text-sm font-medium text-white">Compact Sidebar</h4>
            <p className="text-xs text-white/40 mt-0.5">Use a narrower sidebar by default</p>
          </div>
          <button className="relative w-12 h-6 rounded-full bg-white/[0.1]">
            <div className="absolute top-1 left-1 w-4 h-4 rounded-full bg-white shadow-sm" />
          </button>
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// API SECTION
// ============================================================================

function ApiSection() {
  const [apiKey, setApiKey] = useState("sk_live_your_key_here");
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(apiKey);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold text-white mb-1">API Keys</h3>
        <p className="text-sm text-white/50">Manage your API keys for integrations</p>
      </div>

      {/* Current key */}
      <div className="p-4 rounded-xl bg-white/[0.02] border border-white/[0.05]">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-white/50">Your API Key</span>
          <button
            onClick={handleCopy}
            className="text-xs text-violet-400 hover:text-violet-300"
          >
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
        <div className="flex items-center gap-2">
          <code className="flex-1 text-sm text-white/70 font-mono bg-white/[0.03] px-3 py-2 rounded-lg">
            {apiKey}
          </code>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button className={cn(
          "px-4 py-2 rounded-lg text-sm font-medium",
          "bg-white/[0.05] border border-white/[0.1]",
          "text-white/70 hover:text-white",
          "hover:bg-white/[0.1] hover:border-white/[0.15]",
          "transition-all"
        )}>
          Regenerate Key
        </button>
        <button className={cn(
          "px-4 py-2 rounded-lg text-sm font-medium",
          "bg-red-500/10 border border-red-500/20",
          "text-red-400 hover:text-red-300",
          "hover:bg-red-500/20",
          "transition-all"
        )}>
          Revoke All
        </button>
      </div>

      {/* Docs link */}
      <div className="pt-6 border-t border-white/[0.05]">
        <p className="text-sm text-white/50">
          Need help?{" "}
          <a href="/docs/api" className="text-violet-400 hover:text-violet-300">
            Read the API documentation →
          </a>
        </p>
      </div>
    </div>
  );
}

// ============================================================================
// MAIN PAGE
// ============================================================================

export default function SettingsPage() {
  const [activeSection, setActiveSection] = useState("profile");

  const renderSection = () => {
    switch (activeSection) {
      case "profile": return <ProfileSection />;
      case "security": return <SecuritySection />;
      case "notifications": return <NotificationsSection />;
      case "appearance": return <AppearanceSection />;
      case "api": return <ApiSection />;
      default: return <ProfileSection />;
    }
  };

  return (
    <DashboardLayout>
      <div className="min-h-screen p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-white">Settings</h1>
          <p className="text-sm text-white/50 mt-1">Manage your account and preferences</p>
        </div>

        <div className="flex gap-8">
          {/* Sidebar */}
          <div className="w-64 flex-shrink-0">
            <nav className="space-y-1">
              {SETTINGS_SECTIONS.map((section) => (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={cn(
                    "w-full flex items-center gap-3 px-4 py-3 rounded-xl text-left",
                    "transition-all duration-200",
                    activeSection === section.id
                      ? "bg-violet-500/10 text-white border border-violet-500/30"
                      : "text-white/50 hover:text-white hover:bg-white/[0.03]"
                  )}
                >
                  <section.icon className="w-5 h-5" />
                  <span className="text-sm font-medium">{section.label}</span>
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <motion.div
            key={activeSection}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex-1 max-w-2xl"
          >
            <div className={cn(
              "p-6 rounded-2xl",
              "bg-white/[0.02] border border-white/[0.08]"
            )}>
              {renderSection()}
            </div>
          </motion.div>
        </div>
      </div>
    </DashboardLayout>
  );
}
