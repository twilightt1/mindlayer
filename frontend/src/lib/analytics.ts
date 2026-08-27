"use client";

import { useCallback, useEffect, useRef } from "react";
import { useAuth } from "@/components/auth";

export type AnalyticsEvent = {
  name: string;
  properties?: Record<string, string | number | boolean>;
  timestamp?: number;
};

export type PageView = {
  path: string;
  title?: string;
  referrer?: string;
  timestamp?: number;
};

// Event queue for batching
let eventQueue: AnalyticsEvent[] = [];
let flushTimeout: ReturnType<typeof setTimeout> | null = null;

const FLUSH_INTERVAL = 5000; // 5 seconds
const MAX_QUEUE_SIZE = 10;

/**
 * Analytics hook for tracking user interactions
 */
export function useAnalytics() {
  const { user } = useAuth();
  const userId = user?.id;

  // Flush events to backend
  const flush = useCallback(async () => {
    if (eventQueue.length === 0) return;

    const events = [...eventQueue];
    eventQueue = [];

    try {
      await fetch("/api/v1/analytics/events", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ events, userId }),
      });
    } catch (error) {
      // Re-queue failed events
      eventQueue = [...events, ...eventQueue];
      console.warn("Analytics flush failed:", error);
    }
  }, [userId]);

  // Schedule flush
  const scheduleFlush = useCallback(() => {
    if (flushTimeout) return;
    
    flushTimeout = setTimeout(() => {
      flush();
      flushTimeout = null;
    }, FLUSH_INTERVAL);

    // Flush immediately if queue is full
    if (eventQueue.length >= MAX_QUEUE_SIZE) {
      if (flushTimeout) {
        clearTimeout(flushTimeout);
        flushTimeout = null;
      }
      flush();
    }
  }, [flush]);

  // Track event
  const track = useCallback(
    (name: string, properties?: Record<string, string | number | boolean>) => {
      const event: AnalyticsEvent = {
        name,
        properties: {
          ...properties,
          url: typeof window !== "undefined" ? window.location.pathname : "",
        },
        timestamp: Date.now(),
      };

      eventQueue.push(event);
      scheduleFlush();
    },
    [scheduleFlush]
  );

  // Track page view
  const trackPageView = useCallback(
    (page: PageView) => {
      track("page_view", {
        path: page.path,
        title: page.title || "",
        referrer: page.referrer || "",
      });
    },
    [track]
  );

  // Track feature usage
  const trackFeature = useCallback(
    (feature: string, action: string, metadata?: Record<string, string | number | boolean>) => {
      track(`feature_${feature}`, {
        action,
        ...metadata,
      });
    },
    [track]
  );

  // Track user action
  const trackAction = useCallback(
    (action: string, metadata?: Record<string, string | number | boolean>) => {
      track(`action_${action}`, metadata);
    },
    [track]
  );

  // Flush on unmount
  useEffect(() => {
    return () => {
      if (flushTimeout) {
        clearTimeout(flushTimeout);
      }
      flush();
    };
  }, [flush]);

  return {
    track,
    trackPageView,
    trackFeature,
    trackAction,
    flush,
  };
}

/**
 * Auto-track page views
 */
export function usePageTracking() {
  const { trackPageView } = useAnalytics();

  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleRouteChange = () => {
      trackPageView({
        path: window.location.pathname,
        title: document.title,
        referrer: document.referrer,
      });
    };

    // Track initial page
    handleRouteChange();

    // Listen for navigation
    const observer = new MutationObserver(() => {
      // Re-check on any DOM changes (Next.js router updates)
    });

    observer.observe(document.body, { childList: true, subtree: true });

    return () => {
      observer.disconnect();
    };
  }, [trackPageView]);
}

/**
 * Hook for specific feature analytics
 */
export function useFeatureAnalytics(feature: string) {
  const { trackFeature } = useAnalytics();

  return {
    trackUsage: (action: string, metadata?: Record<string, string | number | boolean>) =>
      trackFeature(feature, action, metadata),
    trackClick: (element: string, metadata?: Record<string, string | number | boolean>) =>
      trackFeature(feature, "click", { element, ...metadata }),
    trackError: (error: string, metadata?: Record<string, string | number | boolean>) =>
      trackFeature(feature, "error", { error, ...metadata }),
    trackSuccess: (metadata?: Record<string, string | number | boolean>) =>
      trackFeature(feature, "success", metadata),
    trackConversion: (step: string, metadata?: Record<string, string | number | boolean>) =>
      trackFeature(feature, "conversion", { step, ...metadata }),
  };
}
