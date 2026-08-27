"use client";

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from "react";

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface User {
  id: string;
  email: string;
  display_name?: string;
  name?: string;
  avatar_url?: string;
  role: string;
  is_verified: boolean;
  onboarding_done: boolean;
  created_at: string;
}

export interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

interface AuthContextType extends AuthState {
  token: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (email: string, password: string, name?: string) => Promise<{ requiresVerification: boolean }>;
  verifyEmail: (email: string, code: string) => Promise<void>;
  completeOnboarding: (displayName: string) => Promise<void>;
  refreshToken: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const TOKEN_KEY = "auth_token";
const REFRESH_KEY = "refresh_token";

// ============================================================================
// TOKEN MANAGEMENT
// ============================================================================

function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(REFRESH_KEY);
}

function setTokens(accessToken: string, refreshToken?: string | null) {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, accessToken);
  if (refreshToken) {
    localStorage.setItem(REFRESH_KEY, refreshToken);
  }
}

function clearTokens() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

// ============================================================================
// API HELPERS
// ============================================================================

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Request failed" }));
    throw new Error(error.detail || error.message || `HTTP ${response.status}`);
  }
  return response.json();
}

// ============================================================================
// AUTH PROVIDER
// ============================================================================

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch current user
  const fetchUser = useCallback(async () => {
    const token = getAccessToken();
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_BASE}/api/v1/users/me`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await handleResponse<{ user: User }>(response);
        setUser(data.user);
      } else {
        // Token invalid, try refresh
        const refreshed = await tryRefreshToken();
        if (!refreshed) {
          clearTokens();
          setUser(null);
        }
      }
    } catch (error) {
      console.error("Failed to fetch user:", error);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Try to refresh token
  const tryRefreshToken = async (): Promise<boolean> => {
    const refreshToken = getRefreshToken();
    if (!refreshToken) return false;

    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });

      if (response.ok) {
        const data = await handleResponse<{ access_token: string; refresh_token: string }>(response);
        setTokens(data.access_token, data.refresh_token);
        await fetchUser();
        return true;
      }
    } catch (error) {
      console.error("Token refresh failed:", error);
    }
    return false;
  };

  // Initial load
  useEffect(() => {
    const initialToken = getAccessToken();
    if (initialToken) setToken(initialToken);
    fetchUser();
  }, [fetchUser]);

  // Login
  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true);
    
    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      const data = await handleResponse<{
        access_token: string;
        refresh_token?: string;
        user: User;
        requires_onboarding?: boolean;
      }>(response);

      setTokens(data.access_token, data.refresh_token);
      setToken(data.access_token);
      setUser(data.user);

      // If user needs onboarding, redirect will happen in the component
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Register
  const register = useCallback(async (email: string, password: string, name?: string) => {
    setIsLoading(true);
    
    try {
      await fetch(`${API_BASE}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      // Registration successful, needs email verification
      return { requiresVerification: true };
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Verify email with OTP
  const verifyEmail = useCallback(async (email: string, code: string) => {
    setIsLoading(true);
    
    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/verify-email/otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp_code: code }),
      });

      const data = await handleResponse<{ access_token: string }>(response);
      setTokens(data.access_token);
      await fetchUser();
    } finally {
      setIsLoading(false);
    }
  }, [fetchUser]);

  // Complete onboarding
  const completeOnboarding = useCallback(async (displayName: string) => {
    setIsLoading(true);
    
    try {
      const token = getAccessToken();
      const response = await fetch(`${API_BASE}/api/v1/auth/onboarding`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ display_name: displayName }),
      });

      const data = await handleResponse<{
        access_token: string;
        refresh_token?: string;
        user: User;
      }>(response);

      setTokens(data.access_token, data.refresh_token);
      setUser(data.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Refresh token manually
  const refreshToken = useCallback(async () => {
    const success = await tryRefreshToken();
    if (!success) {
      clearTokens();
      setUser(null);
    }
  }, []);

  // Logout
  const logout = useCallback(async () => {
    const token = getAccessToken();
    
    try {
      if (token) {
        await fetch(`${API_BASE}/api/v1/auth/logout`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        });
      }
    } catch (error) {
      console.error("Logout API call failed:", error);
    } finally {
      clearTokens();
      setUser(null);
    }
  }, []);

  // Refresh user
  const refreshUser = useCallback(async () => {
    await fetchUser();
  }, [fetchUser]);

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    register,
    verifyEmail,
    completeOnboarding,
    refreshToken,
    refreshUser,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

// ============================================================================
// HOOK
// ============================================================================

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}

// ============================================================================
// PROTECTED ROUTE HOOK
// ============================================================================

export function useProtectedRoute(redirectTo = "/login") {
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      window.location.href = redirectTo;
    }
  }, [isAuthenticated, isLoading, redirectTo]);

  return { isAuthenticated, isLoading };
}

// ============================================================================
// AUTH HEADER HELPER (for API calls)
// ============================================================================

export function getAuthHeaders(): HeadersInit {
  const token = getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
