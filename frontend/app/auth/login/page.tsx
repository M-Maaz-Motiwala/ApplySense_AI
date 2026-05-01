"use client";

import { useState } from "react";
import { login } from "../../../lib/auth";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setLoading(true);
    setError("");

    const formData = new FormData(e.currentTarget);
    const res = await login(formData);

    if (res?.error) {
      setError(res.error);
      setLoading(false);
    } else {
      router.push("/jobs");
      router.refresh();
    }
  }

  return (
    <main className="auth-container">
      <div className="glass-panel auth-card">
        <h1>Welcome Back</h1>
        <p>Login to your ApplySense AI account</p>

        {error && <div className="alert-error">{error}</div>}

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input type="email" id="email" name="email" required />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input type="password" id="password" name="password" required />
          </div>

          <button type="submit" className="btn-primary full-width" disabled={loading}>
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
        
        <div className="auth-links">
          <p>Don't have an account? <Link href="/auth/register">Register</Link></p>
        </div>
      </div>
    </main>
  );
}
