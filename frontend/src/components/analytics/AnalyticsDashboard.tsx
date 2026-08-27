"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/components/auth";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { 
  BarChart3, 
  TrendingUp, 
  Users, 
  Eye,
  ArrowUpRight,
  ArrowDownRight
} from "lucide-react";

interface FeatureUsageItem {
  feature: string;
  action: string;
  count: number;
}

interface PageViewItem {
  path: string;
  views: number;
}

interface DAUItem {
  date: string;
  active_users: number;
}

export function AnalyticsDashboard() {
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [featureUsage, setFeatureUsage] = useState<FeatureUsageItem[]>([]);
  const [pageViews, setPageViews] = useState<PageViewItem[]>([]);
  const [dauData, setDauData] = useState<DAUItem[]>([]);
  const [timeRange, setTimeRange] = useState(7);

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    if (!token) return;
    
    setLoading(true);
    try {
      const headers = { Authorization: `Bearer ${token}` };
      
      const [usageRes, pagesRes] = await Promise.all([
        fetch(`/api/v1/analytics/usage?days=${timeRange}`, { headers }),
        fetch(`/api/v1/analytics/pages?days=${timeRange}`, { headers }),
      ]);

      if (usageRes.ok) {
        const data = await usageRes.json();
        setFeatureUsage(data.items || []);
      }

      if (pagesRes.ok) {
        const data = await pagesRes.json();
        setPageViews(data.items || []);
      }
    } catch (error) {
      console.error("Failed to fetch analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  const totalViews = pageViews.reduce((sum, p) => sum + p.views, 0);
  const totalActions = featureUsage.reduce((sum, f) => sum + f.count, 0);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Analytics</h2>
          <p className="text-muted-foreground">
            Track your Orivory usage and engagement
          </p>
        </div>
        
        {/* Time range selector */}
        <div className="flex gap-2">
          {[7, 14, 30].map((days) => (
            <button
              key={days}
              onClick={() => setTimeRange(days)}
              className={`px-3 py-1.5 text-sm rounded-md transition-colors ${
                timeRange === days
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted hover:bg-muted/80"
              }`}
            >
              {days}d
            </button>
          ))}
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard
          title="Page Views"
          value={totalViews.toLocaleString()}
          icon={<Eye className="h-4 w-4" />}
          trend={null}
          loading={loading}
        />
        <StatCard
          title="Actions"
          value={totalActions.toLocaleString()}
          icon={<BarChart3 className="h-4 w-4" />}
          trend={null}
          loading={loading}
        />
        <StatCard
          title="Top Feature"
          value={featureUsage[0]?.feature || "—"}
          icon={<TrendingUp className="h-4 w-4" />}
          trend={null}
          loading={loading}
        />
        <StatCard
          title="Most Visited"
          value={pageViews[0]?.path || "—"}
          icon={<Users className="h-4 w-4" />}
          trend={null}
          loading={loading}
        />
      </div>

      {/* Feature Usage */}
      <Card>
        <CardHeader>
          <CardTitle>Feature Usage</CardTitle>
          <CardDescription>
            Your most used Orivory features
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : featureUsage.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              No feature usage data yet. Start exploring Orivory!
            </p>
          ) : (
            <div className="space-y-3">
              {featureUsage.slice(0, 10).map((item, index) => (
                <div
                  key={`${item.feature}-${item.action}`}
                  className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-medium">
                      {index + 1}
                    </div>
                    <div>
                      <p className="font-medium">{item.feature}</p>
                      <p className="text-sm text-muted-foreground">{item.action}</p>
                    </div>
                  </div>
                  <Badge variant="secondary">{item.count}</Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Page Views */}
      <Card>
        <CardHeader>
          <CardTitle>Page Views</CardTitle>
          <CardDescription>
            Most visited pages
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : pageViews.length === 0 ? (
            <p className="text-muted-foreground text-sm">
              No page view data yet. Visit some pages!
            </p>
          ) : (
            <div className="space-y-3">
              {pageViews.slice(0, 10).map((item, index) => (
                <div
                  key={item.path}
                  className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary text-sm font-medium">
                      {index + 1}
                    </div>
                    <code className="text-sm bg-muted px-2 py-1 rounded">
                      {item.path}
                    </code>
                  </div>
                  <Badge variant="secondary">{item.views}</Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function StatCard({
  title,
  value,
  icon,
  trend,
  loading,
}: {
  title: string;
  value: string | number;
  icon: React.ReactNode;
  trend: { value: number; isPositive: boolean } | null;
  loading: boolean;
}) {
  return (
    <Card>
      <CardContent className="pt-6">
        <div className="flex items-center justify-between">
          <div className="p-2 rounded-lg bg-primary/10 text-primary">
            {icon}
          </div>
          {trend && (
            <div
              className={`flex items-center gap-1 text-sm ${
                trend.isPositive ? "text-green-500" : "text-red-500"
              }`}
            >
              {trend.isPositive ? (
                <ArrowUpRight className="h-4 w-4" />
              ) : (
                <ArrowDownRight className="h-4 w-4" />
              )}
              {trend.value}%
            </div>
          )}
        </div>
        <div className="mt-4">
          {loading ? (
            <>
              <Skeleton className="h-8 w-20" />
              <Skeleton className="h-4 w-16 mt-1" />
            </>
          ) : (
            <>
              <p className="text-2xl font-bold truncate">{value}</p>
              <p className="text-sm text-muted-foreground">{title}</p>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
