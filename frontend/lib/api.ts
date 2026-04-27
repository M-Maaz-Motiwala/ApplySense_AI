export const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

function authHeaders(): HeadersInit {
  const token = process.env.NEXT_PUBLIC_ACCESS_TOKEN || "";
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function getJobs() {
  const res = await fetch(`${API_BASE}/jobs`, {
    headers: { ...authHeaders() },
    cache: "no-store"
  });
  if (!res.ok) throw new Error("Failed to fetch jobs");
  return res.json();
}

export async function getApplications() {
  const res = await fetch(`${API_BASE}/applications`, {
    headers: { ...authHeaders() },
    cache: "no-store"
  });
  if (!res.ok) throw new Error("Failed to fetch applications");
  return res.json();
}

export async function approveApplication(id: string) {
  const res = await fetch(`${API_BASE}/applications/${id}/approve`, {
    method: "POST",
    headers: { ...authHeaders() }
  });
  if (!res.ok) throw new Error("Failed to approve application");
  return res.json();
}

export async function rejectApplication(id: string) {
  const res = await fetch(`${API_BASE}/applications/${id}/reject`, {
    method: "POST",
    headers: { ...authHeaders() }
  });
  if (!res.ok) throw new Error("Failed to reject application");
  return res.json();
}
