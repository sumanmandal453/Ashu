"use client";
import { useAuth } from "@clerk/nextjs";
import { useCallback } from "react";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

/**
 * Backend-ready client. Sends the Clerk session token as
 *   Authorization: Bearer <CLERK_SESSION_TOKEN>
 * The FastAPI backend must verify this JWT against Clerk's JWKS. Never trust it unverified.
 */
export function useApiClient() {
  const { getToken } = useAuth();
  return useCallback(
    async <T>(path: string, init: RequestInit = {}): Promise<T> => {
      if (!BASE) throw new Error("Backend not configured: set NEXT_PUBLIC_API_BASE_URL.");
      const token = await getToken(); // fresh, auto-refreshed by Clerk
      const headers = new Headers(init.headers);
      if (!headers.has("Content-Type") && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
      if (token) headers.set("Authorization", `Bearer ${token}`);
      const res = await fetch(`${BASE}${path}`, { ...init, headers });
      if (!res.ok) throw new Error(`API request failed (${res.status})`);
      return (await res.json()) as T;
    },
    [getToken],
  );
}
