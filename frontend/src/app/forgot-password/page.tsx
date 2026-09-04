"use client";

import { Suspense, useEffect, useState } from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";
import { Eye, EyeOff, Loader2, MailCheck } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function ForgotPasswordForm() {
  const searchParams = useSearchParams();
  // Flow: "email" → "otp" → "reset" → "done".
  // A ?token= param (from the email verify-link) jumps straight to "reset".
  const [step, setStep] = useState<"email" | "otp" | "reset" | "done">(
    searchParams.get("token") ? "reset" : "email"
  );
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [resetToken, setResetToken] = useState(searchParams.get("token") || "");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (searchParams.get("error") === "invalid_token") {
      setError("This reset link is invalid or has expired. Please request a new one.");
      setStep("email");
    }
  }, [searchParams]);

  const post = async (path: string, body: unknown) => {
    const res = await fetch(`${API}/api/v1/auth/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || "Request failed");
    return data;
  };

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const data = await post("forgot-password", { email });
      setNotice(data.message || "Check your email for the reset code.");
      setStep("otp");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not send reset email");
    } finally {
      setBusy(false);
    }
  };

  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      const data = await post("forgot-password/verify-otp", {
        email,
        otp_code: otp.trim(),
      });
      setResetToken(data.reset_token);
      setStep("reset");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid code");
    } finally {
      setBusy(false);
    }
  };

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (newPassword !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }
    if (newPassword.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    setBusy(true);
    try {
      await post("reset-password", { token: resetToken, new_password: newPassword });
      setStep("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not reset password");
    } finally {
      setBusy(false);
    }
  };

  const inputCls = cn(
    "w-full px-4 py-3 rounded-xl",
    "bg-white/[0.03] border border-white/[0.08]",
    "text-white placeholder:text-white/30",
    "focus:outline-none focus:border-violet-500/50",
    "transition-all"
  );
  const buttonCls = cn(
    "w-full py-3 px-4 rounded-xl",
    "bg-gradient-to-r from-violet-600 to-purple-600",
    "text-white font-semibold",
    "shadow-lg shadow-violet-500/20",
    "disabled:opacity-50 disabled:cursor-not-allowed",
    "transition-all duration-300"
  );

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left side - Form */}
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
            <h1 className="text-3xl font-bold text-white mb-2">Reset your password</h1>
            <p className="text-white/50">
              {step === "email" && "Enter your email and we'll send you a reset code"}
              {step === "otp" && `Enter the 6-digit code sent to ${email}`}
              {step === "reset" && "Choose a new password for your account"}
              {step === "done" && "Your password has been updated"}
            </p>
          </div>

          {error && (
            <div role="alert" className="mb-5 p-3 rounded-xl bg-red-500/10 border border-red-500/20">
              <p className="text-sm text-red-400">{error}</p>
            </div>
          )}
          {notice && !error && (
            <div role="status" className="mb-5 p-3 rounded-xl bg-violet-500/[0.06] border border-violet-500/20">
              <p className="text-sm text-violet-300">{notice}</p>
            </div>
          )}

          {/* Step 1 — request reset */}
          {step === "email" && (
            <form onSubmit={handleRequestReset} className="space-y-5">
              <div>
                <label htmlFor="fp-email" className="block text-sm text-white/70 mb-2">Email</label>
                <input
                  id="fp-email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  required
                  className={inputCls}
                />
              </div>
              <motion.button type="submit" disabled={busy} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }} className={buttonCls}>
                {busy ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" /> Sending...
                  </span>
                ) : (
                  "Send reset code"
                )}
              </motion.button>
            </form>
          )}

          {/* Step 2 — OTP */}
          {step === "otp" && (
            <form onSubmit={handleVerifyOtp} className="space-y-5">
              <div>
                <label htmlFor="fp-otp" className="block text-sm text-white/70 mb-2">Reset code</label>
                <input
                  id="fp-otp"
                  type="text"
                  inputMode="numeric"
                  autoComplete="one-time-code"
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                  placeholder="000000"
                  required
                  className={cn(inputCls, "text-center text-2xl font-mono tracking-[0.5em]")}
                />
              </div>
              <motion.button type="submit" disabled={busy || otp.length !== 6} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }} className={buttonCls}>
                {busy ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" /> Verifying...
                  </span>
                ) : (
                  "Verify code"
                )}
              </motion.button>
              <button
                type="button"
                onClick={() => { setStep("email"); setError(""); setNotice(""); }}
                className="w-full text-xs text-white/40 hover:text-violet-400 transition-colors"
              >
                Use a different email
              </button>
            </form>
          )}

          {/* Step 3 — new password */}
          {step === "reset" && (
            <form onSubmit={handleReset} className="space-y-5">
              <div className="relative">
                <label htmlFor="fp-new-pass" className="block text-sm text-white/70 mb-2">New password</label>
                <input
                  id="fp-new-pass"
                  type={showPassword ? "text" : "password"}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  minLength={8}
                  required
                  className={inputCls}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((v) => !v)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                  className="absolute right-3 top-[38px] text-white/30 hover:text-white/60"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <div>
                <label htmlFor="fp-confirm-pass" className="block text-sm text-white/70 mb-2">Confirm new password</label>
                <input
                  id="fp-confirm-pass"
                  type={showPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  minLength={8}
                  required
                  className={inputCls}
                />
              </div>
              <motion.button type="submit" disabled={busy} whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }} className={buttonCls}>
                {busy ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" /> Saving...
                  </span>
                ) : (
                  "Set new password"
                )}
              </motion.button>
            </form>
          )}

          {/* Done */}
          {step === "done" && (
            <div className="space-y-5">
              <div className="p-5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-center">
                <MailCheck className="w-8 h-8 text-emerald-400 mx-auto mb-2" />
                <p className="text-sm text-emerald-300">Password reset successfully. You can now sign in with your new password.</p>
              </div>
              <Link
                href="/login"
                className={cn(buttonCls, "block text-center no-underline")}
              >
                Back to sign in
              </Link>
            </div>
          )}

          <p className="mt-8 text-sm text-white/40">
            Remembered it?{" "}
            <Link href="/login" className="text-violet-400 hover:text-violet-300">
              Sign in
            </Link>
          </p>
        </motion.div>
      </div>

      {/* Right side - Branding */}
      <div className="hidden lg:flex flex-1 items-center justify-center p-16 bg-gradient-to-br from-violet-950/30 via-background to-pink-950/20">
        <div className="max-w-md text-center">
          <div className="text-5xl mb-6">🔐</div>
          <h2 className="text-2xl font-bold text-white mb-3">Account recovery</h2>
          <p className="text-white/50">
            Orivory never stores your password in plain text. A one-time code keeps
            your second brain — and everything inside it — yours alone.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function ForgotPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-background" />}>
      <ForgotPasswordForm />
    </Suspense>
  );
}
