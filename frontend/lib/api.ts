// Server-side (SSR) runs inside Docker → must use the service name "backend"
// Client-side (browser) runs on the host → must use "localhost"
const isServer = typeof window === "undefined";
export const API_BASE = isServer
  ? (process.env.INTERNAL_API_BASE_URL || "http://backend:8000/api/v1")
  : (process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1");

// CLIENT_API_BASE is always localhost — used by client components
export const CLIENT_API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

import { getToken } from "./auth";

async function authHeaders(): Promise<HeadersInit> {
  const token = await getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getJobs() {
  const res = await fetch(`${API_BASE}/jobs`, {
    headers: { ...(await authHeaders()) },
    cache: "no-store"
  });
  if (!res.ok) throw new Error("Failed to fetch jobs");
  return res.json();
}

export async function getApplications() {
  const res = await fetch(`${API_BASE}/applications`, {
    headers: { ...(await authHeaders()) },
    cache: "no-store"
  });
  if (!res.ok) throw new Error("Failed to fetch applications");
  return res.json();
}

export async function approveApplication(id: string) {
  const res = await fetch(`${API_BASE}/applications/${id}/approve`, {
    method: "POST",
    headers: { ...(await authHeaders()) }
  });
  if (!res.ok) throw new Error("Failed to approve application");
  return res.json();
}

export async function rejectApplication(id: string) {
  const res = await fetch(`${API_BASE}/applications/${id}/reject`, {
    method: "POST",
    headers: { ...(await authHeaders()) }
  });
  if (!res.ok) throw new Error("Failed to reject application");
  return res.json();
}
