"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/auth-context";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Copy, Mail, Link2, Trophy, Users, Gift } from "lucide-react";

interface ReferralStats {
  total_referrals: number;
  pending_referrals: number;
  unclaimed_rewards: number;
  referral_code: string;
  referral_link: string;
}

interface LeaderboardEntry {
  user_id: string;
  referral_count: number;
}

export function ReferralDashboard() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<ReferralStats | null>(null);
  const [shareEmail, setShareEmail] = useState("");
  const [shareStatus, setShareStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (token) fetchStats();
  }, [token]);

  const fetchStats = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const res = await fetch("/api/v1/referral/stats", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setStats(await res.json());
      }
    } catch (e) {
      console.error("Failed to fetch stats:", e);
    } finally {
      setLoading(false);
    }
  };

  const copyLink = async () => {
    if (!stats?.referral_link) return;
    await navigator.clipboard.writeText(stats.referral_link);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const shareViaEmail = async () => {
    if (!shareEmail || !token) return;
    setShareStatus("loading");
    try {
      const res = await fetch("/api/v1/referral/share", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ email: shareEmail }),
      });
      if (res.ok) {
        setShareStatus("success");
        setShareEmail("");
      } else {
        setShareStatus("error");
      }
    } catch {
      setShareStatus("error");
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 md:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold">Refer & Earn</h2>
        <p className="text-muted-foreground">
          Invite friends to Orivory and earn free months
        </p>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard
          title="Total Referrals"
          value={stats?.total_referrals ?? 0}
          icon={<Users className="h-4 w-4" />}
        />
        <StatCard
          title="Pending"
          value={stats?.pending_referrals ?? 0}
          icon={<Link2 className="h-4 w-4" />}
        />
        <StatCard
          title="Rewards Earned"
          value={stats?.unclaimed_rewards ?? 0}
          icon={<Gift className="h-4 w-4" />}
        />
        <StatCard
          title="Your Code"
          value={stats?.referral_code ?? "—"}
          icon={<Trophy className="h-4 w-4" />}
          small
        />
      </div>

      {/* Share Section */}
      <Card>
        <CardHeader>
          <CardTitle>Share Your Referral Link</CardTitle>
          <CardDescription>
            Copy your link or invite by email
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Copy Link */}
          <div className="flex gap-2">
            <Input
              value={stats?.referral_link ?? ""}
              readOnly
              className="font-mono text-sm"
            />
            <Button onClick={copyLink} variant="secondary">
              <Copy className="h-4 w-4 mr-2" />
              {copied ? "Copied!" : "Copy"}
            </Button>
          </div>

          {/* Share via Email */}
          <div className="flex gap-2">
            <Input
              type="email"
              placeholder="friend@example.com"
              value={shareEmail}
              onChange={(e) => setShareEmail(e.target.value)}
              disabled={shareStatus === "loading"}
            />
            <Button onClick={shareViaEmail} disabled={!shareEmail || shareStatus === "loading"}>
              <Mail className="h-4 w-4 mr-2" />
              {shareStatus === "loading" ? "Sending..." : "Invite"}
            </Button>
          </div>
          
          {shareStatus === "success" && (
            <p className="text-sm text-green-600">Invitation sent!</p>
          )}
          {shareStatus === "error" && (
            <p className="text-sm text-red-600">Failed to send invitation</p>
          )}
        </CardContent>
      </Card>

      {/* Rewards Info */}
      <Card>
        <CardHeader>
          <CardTitle>How It Works</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex gap-4">
              <Badge variant="secondary">1-4 Referrals</Badge>
              <span className="text-sm">1 free month each</span>
            </div>
            <div className="flex gap-4">
              <Badge variant="default">5+ Referrals</Badge>
              <span className="text-sm">3 free months each</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
  small = false,
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  small?: boolean;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center gap-2 text-muted-foreground mb-2">
          {icon}
          <span className="text-sm">{title}</span>
        </div>
        <p className={`font-bold truncate ${small ? "text-lg font-mono" : "text-2xl"}`}>
          {value}
        </p>
      </CardContent>
    </Card>
  );
}
