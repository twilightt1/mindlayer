"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth/AuthProvider";
import { Eye, EyeOff, Loader2, Check } from "lucide-react";

export default function SignupPage() {
  const router = useRouter();
  const { register, isLoading } = useAuth();
  
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");

  const passwordRequirements = [
    { label: "At least 8 characters", met: password.length >= 8 },
    { label: "Contains a number", met: /\d/.test(password) },
    { label: "Contains uppercase letter", met: /[A-Z]/.test(password) },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!passwordRequirements.every((req) => req.met)) {
      setError("Please meet all password requirements");
      return;
    }

    try {
      await register(email, password, name || undefined);
      // Registration requires email verification — an OTP code is emailed
      // to the user. Route to login with a notice instead of /dashboard.
      router.push("/login?registered=1&email=" + encodeURIComponent(email));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed");
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left side - Decorative */}
      <div className="hidden lg:flex flex-1 items-center justify-center relative overflow-hidden">
        {/* Background effects */}
        <div className="absolute inset-0 bg-gradient-to-br from-violet-900/20 via-purple-900/10 to-pink-900/20" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(139,92,246,0.15)_0%,transparent_50%)]" />
        
        {/* Grid pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px]" />
        
        {/* Content */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.2 }}
          className="relative z-10 text-center max-w-lg px-8"
        >
          <div className="w-20 h-20 mx-auto mb-8 rounded-2xl bg-gradient-to-br from-violet-500/30 to-pink-500/30 border border-violet-500/30 flex items-center justify-center">
            <span className="text-4xl">✨</span>
          </div>
          <h2 className="text-3xl font-bold text-white mb-4">
            Start Building Your Knowledge Graph
          </h2>
          <p className="text-white/60 leading-relaxed mb-8">
            Join thousands of teams who use Orivory to transform scattered information into actionable insights.
          </p>

          {/* Features */}
          <div className="space-y-3 text-left">
            {[
              "Unlimited document uploads",
              "AI-powered semantic search",
              "Automatic insight discovery",
              "Privacy-first, self-hostable",
            ].map((feature) => (
              <div key={feature} className="flex items-center gap-3 text-white/70">
                <div className="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center">
                  <Check className="w-3 h-3 text-emerald-400" />
                </div>
                <span>{feature}</span>
              </div>
            ))}
          </div>
        </motion.div>
      </div>

      {/* Right side - Form */}
      <div className="flex-1 flex items-center justify-center p-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full max-w-md"
        >
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3 mb-8">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 via-purple-500 to-pink-500 flex items-center justify-center shadow-lg shadow-violet-500/25">
              <span className="text-white font-bold text-lg">O</span>
            </div>
            <span className="text-xl font-bold tracking-tight text-white">Orivory</span>
          </Link>

          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Create your account</h1>
            <p className="text-white/50">Start your free trial today</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Name */}
            <div>
              <label className="block text-sm text-white/70 mb-2">Name (optional)</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="John Doe"
                className={cn(
                  "w-full px-4 py-3 rounded-xl",
                  "bg-white/[0.03] border border-white/[0.08]",
                  "text-white placeholder:text-white/30",
                  "focus:outline-none focus:border-violet-500/50",
                  "transition-all"
                )}
              />
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm text-white/70 mb-2">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                className={cn(
                  "w-full px-4 py-3 rounded-xl",
                  "bg-white/[0.03] border border-white/[0.08]",
                  "text-white placeholder:text-white/30",
                  "focus:outline-none focus:border-violet-500/50",
                  "transition-all"
                )}
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-sm text-white/70 mb-2">Password</label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                  className={cn(
                    "w-full px-4 py-3 pr-12 rounded-xl",
                    "bg-white/[0.03] border border-white/[0.08]",
                    "text-white placeholder:text-white/30",
                    "focus:outline-none focus:border-violet-500/50",
                    "transition-all"
                  )}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 text-white/40 hover:text-white/60 transition-colors"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              
              {/* Password requirements */}
              <div className="mt-2 space-y-1">
                {passwordRequirements.map((req) => (
                  <div 
                    key={req.label}
                    className={cn(
                      "flex items-center gap-2 text-xs",
                      req.met ? "text-emerald-400" : "text-white/40"
                    )}
                  >
                    <div className={cn(
                      "w-4 h-4 rounded-full flex items-center justify-center",
                      req.met ? "bg-emerald-500/20" : "bg-white/[0.05]"
                    )}>
                      {req.met ? (
                        <Check className="w-2.5 h-2.5" />
                      ) : (
                        <div className="w-1.5 h-1.5 rounded-full bg-current" />
                      )}
                    </div>
                    {req.label}
                  </div>
                ))}
              </div>
            </div>

            {/* Error */}
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
              >
                {error}
              </motion.div>
            )}

            {/* Terms */}
            <p className="text-xs text-white/40 text-center">
              By signing up, you agree to our{" "}
              <Link href="/terms" className="text-violet-400 hover:text-violet-300">
                Terms of Service
              </Link>{" "}
              and{" "}
              <Link href="/privacy" className="text-violet-400 hover:text-violet-300">
                Privacy Policy
              </Link>
            </p>

            {/* Submit */}
            <motion.button
              type="submit"
              disabled={isLoading}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}
              className={cn(
                "w-full py-3 px-4 rounded-xl",
                "bg-gradient-to-r from-violet-600 to-purple-600",
                "text-white font-semibold",
                "shadow-lg shadow-violet-500/20",
                "hover:shadow-violet-500/30",
                "disabled:opacity-50 disabled:cursor-not-allowed",
                "transition-all duration-300"
              )}
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Creating account...
                </span>
              ) : (
                "Create account"
              )}
            </motion.button>
          </form>

          {/* Login link */}
          <p className="text-center text-sm text-white/50 mt-8">
            Already have an account?{" "}
            <Link href="/login" className="text-violet-400 hover:text-violet-300 font-medium">
              Sign in
            </Link>
          </p>
        </motion.div>
      </div>
    </div>
  );
}
