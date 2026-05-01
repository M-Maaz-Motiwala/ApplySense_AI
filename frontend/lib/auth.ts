"use server";

import { cookies } from "next/headers";
import { API_BASE } from "./api";

export async function login(formData: FormData) {
  const email = formData.get("email");
  const password = formData.get("password");

  if (!email || !password) {
    return { error: "Email and password are required." };
  }

  try {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
      cache: "no-store",
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      return { error: errorData.detail || "Invalid credentials." };
    }

    const data = await res.json();
    if (data.access_token) {
      const cookieStore = await cookies();
      cookieStore.set("access_token", data.access_token, {
        httpOnly: true,
        secure: process.env.NODE_ENV === "production",
        sameSite: "lax",
        path: "/",
        maxAge: 60 * 60 * 2,
      });
      return { success: true };
    }
  } catch (err) {
    return { error: "Failed to connect to the server." };
  }
  
  return { error: "Unexpected error occurred." };
}

export async function register(payload: any) {
  try {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store",
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      return { error: errorData.detail || "Registration failed." };
    }

    // Auto-login after registration
    const loginFormData = new FormData();
    loginFormData.append("email", payload.email);
    loginFormData.append("password", payload.password);
    return await login(loginFormData);
  } catch (err) {
    return { error: "Failed to connect to the server." };
  }
}

export async function logout() {
  const cookieStore = await cookies();
  cookieStore.delete("access_token");
}

export async function getToken(): Promise<string> {
  if (process.env.NEXT_PUBLIC_ACCESS_TOKEN) {
    return process.env.NEXT_PUBLIC_ACCESS_TOKEN;
  }
  const cookieStore = await cookies();
  return cookieStore.get("access_token")?.value || "";
}
